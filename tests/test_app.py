import threading, http.server, socketserver, json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8765
class SilentHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
class Server(socketserver.ThreadingMixIn,http.server.HTTPServer):
 daemon_threads=True

def serve():
 import os
 os.chdir(ROOT)
 server=Server(('127.0.0.1',PORT),SilentHandler)
 server.serve_forever()
th=threading.Thread(target=serve,daemon=True); th.start()
errors=[]
def geometry(page):
 return page.evaluate("""() => {
  const bounds = selector => { const r=document.querySelector(selector).getBoundingClientRect(); return [r.x,r.y,r.width,r.height]; };
  return [bounds('.brand'),bounds('#peek')];
 }""")
def assert_geometry(before,after,action):
 for a,b in zip(before,after):
  for x,y in zip(a,b):
   assert abs(x-y)<1.3, f'{action}: layout shifted {before} => {after}'


with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,**({'executable_path': '/usr/bin/chromium'} if Path('/usr/bin/chromium').exists() else {}),args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
 context=browser.new_context(viewport={'width':360,'height':780},device_scale_factor=1,is_mobile=True,has_touch=True,service_workers='allow')
 page=context.new_page()
 page.on('pageerror', lambda exc: errors.append(str(exc)))
 page.on('console', lambda msg: errors.append('console error: '+msg.text) if msg.type=='error' else None)
 page.goto(f'http://localhost:{PORT}/meditation/',wait_until='networkidle')
 assert page.locator('html').get_attribute('data-silence-ready')=='true'
 assert page.get_by_text('Version 3.11.1').is_hidden() # settings not open
 assert page.locator('body').evaluate("(el)=>el.classList.contains('intro-go')"), "Intro must start on idle page"
 assert page.locator('.opening-word').evaluate("(el)=>el.getAnimations().some(anim=>anim.animationName==='opening-word')"), "Brand must travel from center to header"
 assert page.locator('.visual').evaluate("(el)=>getComputedStyle(el,'::before').animationName==='intro-ripple'"), "First water ripple must run"
 intro_geometry=page.evaluate("""() => {
   const brand=document.querySelector('.opening-word');
   const animation=brand.getAnimations().find(a=>a.animationName==='opening-word');
   animation.currentTime=420;
   const center=brand.getBoundingClientRect();
   animation.currentTime=1950;
   const end=brand.getBoundingClientRect();
   return {cx:center.x+center.width/2,cy:center.y+center.height/2,endX:end.x};
 }""")
 assert abs(intro_geometry['cx'] - 180)<3, intro_geometry
 assert abs(intro_geometry['cy'] - 390)<3, intro_geometry
 assert intro_geometry['endX']<80,intro_geometry
 page.wait_for_function("!document.body.classList.contains('is-opening')",timeout=6500)
 assert page.locator('#setup').is_visible()
 assert page.locator('#tone option').count()==3
 assert page.locator('.field-art').count()==0
 assert page.locator('#fieldSvg').count()==1
 assert page.locator('#fieldSvg').evaluate("el => el.namespaceURI==='http://www.w3.org/2000/svg'")
 assert page.locator('#fieldSvg').evaluate("el => getComputedStyle(el).pointerEvents==='none'")
 page.wait_for_function("document.querySelector('#fieldWaveOuter').getAttribute('d')?.length > 1000", timeout=7000)
 first_shape=page.locator('#fieldWaveOuter').get_attribute('d')
 page.wait_for_timeout(270)
 assert page.locator('#fieldWaveOuter').get_attribute('d')!=first_shape, 'The SVG shape must morph over time'
 assert page.locator('#peek').evaluate("el=>el.classList.contains('is-field-active')")
 # Métadonnées de partage et visuels servent de vrais fichiers image.
 assert page.locator('link[rel="canonical"]').get_attribute('href')=='https://mebius.cc/meditation/'
 assert page.locator('meta[property="og:image"]').get_attribute('content')=='https://mebius.cc/meditation/og-image.jpg?v=3.11.1'
 assert page.locator('meta[property="og:image:width"]').get_attribute('content')=='1200'
 assert page.locator('meta[property="og:image:height"]').get_attribute('content')=='630'
 assert page.locator('meta[name="twitter:card"]').get_attribute('content')=='summary_large_image'
 assert page.locator('script[type="application/ld+json"]').count()==1
 assert page.locator('html').evaluate("(el)=>getComputedStyle(el).scrollbarWidth==='none'")
 assert 'scrollbar-width:none' in page.locator('head style').first.inner_text()
 images=page.evaluate("""async () => {
   const load = src => new Promise((resolve,reject) => {
      const img=new Image(); img.onload=()=>resolve([img.naturalWidth,img.naturalHeight]);img.onerror=reject;img.src=src;
   });
   return {og:await load('./og-image.jpg'),favicon:await load('./icons/favicon-32.png'),app:await load('./icons/icon-512.png')};
 }""")
 assert images=={'og':[1200,630],'favicon':[32,32],'app':[512,512]},images
 # screenshot skipped in CI
 page.locator('#settingsButton').click()
 assert page.get_by_text('Version 3.11.1').is_visible()
 assert page.locator('#motion').is_checked()
 assert not page.locator('#dark').is_checked()
 # Désactiver l'attente, puis vérifier les deux aperçus audio réels
 page.locator('#delay').uncheck()
 page.locator('#testSound').click()
 page.wait_for_function("document.querySelector('#soundStatus').textContent.includes('Écoute')",timeout=5000)
 print('SOUND bol:',page.locator('#soundStatus').text_content())
 page.locator('#tone').select_option('bambou')
 page.locator('#testSound').click()
 page.wait_for_function("document.querySelector('#soundStatus').textContent.includes('Bois')",timeout=5000)
 print('SOUND bambou:',page.locator('#soundStatus').text_content())
 page.locator('#tone').select_option('goutte')
 page.locator('#testSound').click()
 page.wait_for_function("document.querySelector('#soundStatus').textContent.includes('Goutte douce')",timeout=7000)
 print('SOUND goutte:',page.locator('#soundStatus').text_content())
 duration=page.evaluate("""async () => {
   const response=await fetch('./sounds/goutte.wav');
   if(!response.ok) throw new Error('No audio file');
   const context=new AudioContext();
   const buffer=await context.decodeAudioData(await response.arrayBuffer());
   await context.close();
   return buffer.duration;
 }""")
 assert .33 <= duration <= .38, duration
 
 page.locator('#closeSettings').click()
 original=geometry(page)
 page.locator('#start').click()
 assert_geometry(original,geometry(page),'start')
 assert page.locator('#setup').is_hidden()
 assert page.locator('#activeControls').is_visible()
 assert page.locator('#stop').is_visible()
 assert page.locator('#pauseResume').is_visible()
 assert page.locator('#stop').bounding_box()['width']==68
 assert page.locator('#stop').bounding_box()['height']==68
 assert page.locator('#peek').get_attribute('class').find('is-breathing')>=0
 # Le cercle n'est ni un bouton, ni une commande : cliquer n'affiche jamais le chronomètre.
 assert page.locator('#peek').evaluate("(el)=>el.tagName==='DIV' && !el.hasAttribute('tabindex') && getComputedStyle(el).pointerEvents==='none'")
 assert page.locator('#clock').is_hidden()
 ring=page.locator('#peek').bounding_box()
 page.mouse.click(ring['x']+ring['width']/2,ring['y']+ring['height']/2)
 assert page.locator('#clock').is_hidden(), 'Aucune interaction avec le cercle ne doit dévoiler le temps'

 # Le champ est entièrement organique : ni point central, ni cercle fixe, ni halo elliptique.
 assert page.locator('.center-symbol').count()==0
 assert page.locator('.orb').count()==0
 assert page.locator('.field-underlay').count()==0
 assert page.locator('.field-glint').count()==0
 assert page.evaluate("getComputedStyle(document.body).backgroundImage==='none'"), 'No horizontal elliptical halo'
 path_element=page.locator('#fieldWaveMiddle')
 path_data=path_element.get_attribute('d')
 assert path_data.startswith('M') and path_data.endswith('Z') and 'C' in path_data and 'L' not in path_data, 'Closed cubic curve without visible line endpoints'
 continuity=path_element.evaluate("""el => {
   const len=el.getTotalLength();
   const start=el.getPointAtLength(0), end=el.getPointAtLength(len);
   const previous=el.getPointAtLength(len-.5), next=el.getPointAtLength(.5);
   const a=[start.x-previous.x,start.y-previous.y];
   const b=[next.x-start.x,next.y-start.y];
   const dot=a[0]*b[0]+a[1]*b[1];
   const length=Math.hypot(...a)*Math.hypot(...b);
   return {distance:Math.hypot(start.x-end.x,start.y-end.y),tangent:dot/length};
 }""")
 assert continuity['distance']<.2 and continuity['tangent']>.97, continuity
 assert page.locator('.field-sheen').first.evaluate("(el)=>getComputedStyle(el).strokeDasharray==='none'")
 name=page.locator('.field-svg').evaluate('(el)=>getComputedStyle(el).animationName')
 assert name=='quiet-pulse',name
 samples=page.evaluate("""() => {
   const element=document.querySelector('.field-svg');
   const anim=element.getAnimations().find(a=>a.animationName==='quiet-pulse');
   anim.currentTime=0; const a=getComputedStyle(element).transform;
   anim.currentTime=7000; const b=getComputedStyle(element).transform;
   anim.currentTime=3500;
   return {a,b};
 }""")
 assert samples['a']!=samples['b'],samples
 # screenshot skipped in CI
 page.locator('#pauseResume').click()
 assert_geometry(original,geometry(page),'pause')
 assert page.locator('#pauseResume').get_attribute('aria-label')=='Reprendre'
 assert page.locator('#pauseResume').locator('.play-symbol').is_visible()
 assert page.locator('#stateText').is_hidden(), 'Do not show En pause next to Play control'
 page.locator('#pauseResume').click()
 assert_geometry(original,geometry(page),'resume')
 assert page.locator('#pauseResume').get_attribute('aria-label')=='Pause'
 page.locator('#stop').click()
 assert_geometry(original,geometry(page),'stop')
 assert page.locator('#setup').is_visible(),'Stop should return to duration picker'
 assert page.locator('#activeControls').is_hidden()
 assert page.locator('#stateText').is_hidden()
 print('MANUAL STOP -> duration choices: OK')
 # Retour silencieux supprimé, aucun contrôle supplémentaire à afficher.
 assert page.locator('#gentleEnd').count()==0
 assert page.locator('#settle').count()==0
 print('SILENT RETURN REMOVED: OK')
 # toggles mutually exclusive
 page.locator('#settingsButton').click()
 page.locator('#dark').check()
 assert not page.locator('#motion').is_checked()
 page.locator('#motion').check()
 assert not page.locator('#dark').is_checked()
 page.locator('#closeSettings').click()
 print('EXCLUSIVE modes: OK')
 # Regression: saved both on, and old tone, migrate to bol
 page.evaluate('''() => localStorage.setItem('silence.settings.v2',JSON.stringify({mode:'free',minutes:15,motion:true,dark:true,tone:'invalid-old-tone',delay:false,volume:60}))''')
 page.reload(wait_until='networkidle')
 page.locator('#settingsButton').click()
 assert page.locator('#motion').is_checked()
 assert not page.locator('#dark').is_checked()
 assert page.locator('#tone').input_value()=='bol'
 page.locator('#closeSettings').click()
 print('MIGRATION v3.4: OK')
 # SW version tested on localhost
 page.wait_for_function("'serviceWorker' in navigator && !!navigator.serviceWorker.controller",timeout=12000)
 print('CACHES:',page.evaluate('async () => (await caches.keys()).filter(k=>k.startsWith("silence"))'))
 assert 'silence-v3.11.1' in page.evaluate('async () => await caches.keys()')
 # Check off-line resilience for cached local assets
 context.set_offline(True)
 page.reload(wait_until='domcontentloaded')
 assert page.locator('html').get_attribute('data-silence-ready')=='true'
 assert page.locator('#start').is_visible()
 print('OFFLINE reload: OK')
 context.close()
 # Desktop layout
 desktop=browser.new_context(viewport={'width':1280,'height':820},device_scale_factor=1,service_workers='block')
 dpage=desktop.new_page()
 dpage.on('pageerror', lambda exc: errors.append('desktop: '+str(exc)))
 dpage.goto(f'http://127.0.0.1:{PORT}/meditation/',wait_until='domcontentloaded')
 # screenshot skipped in CI
 assert dpage.locator('#start').is_visible()
 desktop.close()
 # Reduced motion follows accessibility preference
 reduced=browser.new_context(viewport={'width':360,'height':780},reduced_motion='reduce',service_workers='block')
 rpage=reduced.new_page()
 rpage.goto(f'http://127.0.0.1:{PORT}/meditation/')
 assert not rpage.locator('body').evaluate("(el)=>el.classList.contains('is-opening')"), 'Reduced motion should skip intro'
 rpage.locator('#settingsButton').click()
 rpage.locator('#delay').uncheck()
 rpage.locator('#closeSettings').click()
 rpage.locator('#start').click()
 animation=rpage.locator('.orb').evaluate('(el) => getComputedStyle(el).animationName')
 assert animation=='none',animation
 print('REDUCED MOTION: OK')
 reduced.close()
 browser.close()
print('PAGE ERRORS:',errors)
assert not errors,errors
print('ALL BROWSER TESTS PASSED')
