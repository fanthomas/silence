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
 assert page.get_by_text('Version 3.9').is_hidden() # settings not open
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
 assert page.locator('#tone option').count()==2
 # Métadonnées de partage et visuels servent de vrais fichiers image.
 assert page.locator('link[rel="canonical"]').get_attribute('href')=='https://mebius.cc/meditation/'
 assert page.locator('meta[property="og:image"]').get_attribute('content')=='https://mebius.cc/meditation/og-image.jpg'
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
 assert page.get_by_text('Version 3.9').is_visible()
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
 # L'onde intérieure et le point central animent une oscillation lente de 14 secondes.
 assert page.locator('.orb').evaluate("(el)=>getComputedStyle(el,'::after').animationName==='field-wave'")
 assert page.locator('.center-symbol').evaluate("(el)=>getComputedStyle(el,'::after').animationName==='thought-drift'")
 assert page.locator('.center-symbol').evaluate("(el)=>getComputedStyle(el,'::after').animationDuration==='14s'")
 
 name=page.locator('.orb').evaluate('(el) => getComputedStyle(el).animationName')
 assert name=='quiet-pulse',name
 # Forcer une position intermédiaire de l'animation pour garantir une variation visible réelle
 samples=page.evaluate('''() => {
   const orb = document.querySelector('.orb');
   const anim=orb.getAnimations()[0];
   anim.currentTime = 0; const a=getComputedStyle(orb).transform;
   anim.currentTime = 7000; const b=getComputedStyle(orb).transform;
   anim.currentTime = 3500;
   return {a,b,mid:getComputedStyle(orb).transform};
 }''')
 print('ANIMATION transforms:',samples)
 assert samples['a']!=samples['b'],samples
 assert samples['a'].startswith('matrix(1, ') and '1.105' in samples['b'],samples
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
 page.evaluate('''() => localStorage.setItem('silence.settings.v2',JSON.stringify({mode:'free',minutes:15,motion:true,dark:true,tone:'goutte',delay:false,volume:60}))''')
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
 assert 'silence-v3.9.0' in page.evaluate('async () => await caches.keys()')
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
