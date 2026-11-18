from pathlib import Path
from playwright.sync_api import sync_playwright
import re, json
ROOT=Path(__file__).resolve().parents[1]
files=ROOT/'meditation'
html=(files/'index.html').read_text()
html=re.sub(r'<link[^>]+rel="(?:stylesheet|manifest|icon|apple-touch-icon)"[^>]*>', '', html)
html=re.sub(r'<script src=".*?" defer></script>', '', html)
css=(files/'styles.css').read_text()
js=(files/'app.js').read_text()
soft_tones=(files/'sounds'/'soft-tones.js').read_text()
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


def init(page, stored=None):
 page.set_content(html,wait_until='domcontentloaded')
 if stored is None: stored={}
 page.evaluate('''stored => {
  window.__testStorage = {...stored};
  Object.defineProperty(window,'localStorage',{configurable:true,value:{
    getItem: key => Object.hasOwn(window.__testStorage,key)? window.__testStorage[key] : null,
    setItem: (key,value) => window.__testStorage[key] = String(value),
    removeItem: key => delete window.__testStorage[key]
  }});
 }''',stored)
 page.add_style_tag(content=css)
 page.add_script_tag(content=soft_tones)
 page.add_script_tag(content=js)
 assert page.locator('html').get_attribute('data-silence-ready')=='true'
 if not page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches"):
  page.wait_for_function("document.body.classList.contains('intro-go')",timeout=1200)
  page.wait_for_function("""() => document.querySelector('.brand').getAnimations()
    .some(a=>a.effect?.getKeyframes().length===2)""",timeout=2200)
  assert page.locator('.opening-word').count()==0
  assert page.locator('#openingParticle').count()==0
  assert page.locator('#openingTrail').count()==0
  assert page.locator('.opening-overlay').evaluate("""el => {
   const style = getComputedStyle(el, '::before');
   return style.animationName === 'opening-screen' &&
     style.animationDelay === '1.88s' &&
     style.animationDuration === '0.3s';
 }""")
  assert page.locator('.brand').evaluate("""brand => {
    const a=brand.getAnimations().find(x=>x.effect?.getKeyframes().length===2);
    if(!a)return false;
    const old=a.currentTime;a.pause();
    const at=t=>{a.currentTime=t;const r=brand.getBoundingClientRect();return [(r.left+r.right)/2,(r.top+r.bottom)/2];};
    const start=at(0),mid=at(900),end=at(1800);
    a.currentTime=old;a.play();
    const dx=end[0]-start[0],dy=end[1]-start[1];
    return Math.abs(start[0]-innerWidth/2)<2 && Math.abs(start[1]-innerHeight/2)<2 &&
      Math.abs((mid[0]-start[0])*dy-(mid[1]-start[1])*dx)/Math.hypot(dx,dy)<2;
  }""")

 page.wait_for_function("!document.body.classList.contains('is-opening')",timeout=6500)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,**({'executable_path': '/usr/bin/chromium'} if Path('/usr/bin/chromium').exists() else {}),args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
 mobile=browser.new_context(viewport={'width':360,'height':780},device_scale_factor=1,is_mobile=True,has_touch=True)
 page=mobile.new_page()
 page.on('pageerror',lambda error: errors.append(str(error)))
 init(page)
 assert page.locator('#setup').is_visible()
 assert page.locator('#tone option').count()==13
 assert page.locator('.field-art').count()==0
 assert page.locator('#fieldSvg').count()==1
 assert page.locator('#fieldSvg').evaluate("el => el.namespaceURI==='http://www.w3.org/2000/svg'")
 assert page.locator('#peek').evaluate("el => el.classList.contains('is-field-active')")
 page.wait_for_function("document.querySelector('#fieldWaveMiddle').getAttribute('d')?.length > 1000", timeout=7000)
 original_shape=page.locator('#fieldWaveMiddle').get_attribute('d')
 page.wait_for_timeout(260)
 assert original_shape!=page.locator('#fieldWaveMiddle').get_attribute('d'), 'Organic SVG must change geometry'
 # screenshot skipped in CI
 page.locator('#settingsButton').click()
 assert page.get_by_text('Version 3.16.0').is_visible()
 assert page.locator('#motion').is_checked()
 assert not page.locator('#dark').is_checked()
 page.locator('#delay').uncheck()
 page.locator('#testSound').click()
 page.wait_for_function("document.querySelector('#soundStatus').textContent.includes('Écoute')",timeout=8000)
 print('SOUND bol:',page.locator('#soundStatus').text_content())
 page.locator('#tone').select_option('bambou')
 page.locator('#testSound').click()
 page.wait_for_function("document.querySelector('#soundStatus').textContent.includes('Bois')",timeout=8000)
 print('SOUND bambou:',page.locator('#soundStatus').text_content())
 page.locator('#tone').select_option('aube')
 page.locator('#testSound').click()
 page.wait_for_function("document.querySelector('#soundStatus').textContent.includes('Aube')",timeout=5000)
 page.locator('#tone').select_option('goutte')
 # Dans le test DOM, le fichier WAV externe n'est pas servi; le chargement complet est testé par HTTP.
 
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

 # Le point central ne change jamais de position, seule une très légère pulsation est autorisée.
 assert page.locator('#fieldCenterDot').count()==1
 assert page.locator('#fieldCenterDot').evaluate("(el)=>el.getAttribute('cx')==='200' && el.getAttribute('cy')==='200'")
 assert page.locator('#fieldCenterDot').evaluate("(el)=>getComputedStyle(el).animationName==='field-center-breathe'")
 center_before=page.locator('#fieldCenterDot').evaluate("(el)=>[el.cx.baseVal.value,el.cy.baseVal.value]")
 page.wait_for_timeout(280)
 center_after=page.locator('#fieldCenterDot').evaluate("(el)=>[el.cx.baseVal.value,el.cy.baseVal.value]")
 assert center_before==center_after==[200,200], (center_before,center_after)
 assert page.locator('.field-lines > path').count()==9
 assert page.locator('#fieldVeilOuter').get_attribute('d').count('M')==2
 assert page.locator('#fieldVeilInner').get_attribute('d').count('M')==2
 # Les lignes demeurent des courbes réelles, et non une image de fond.
 assert page.locator('#fieldSvg image').count()==0
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
 assert page.locator('#stateText').is_hidden()
 page.locator('#pauseResume').click()
 assert_geometry(original,geometry(page),'resume')
 assert page.locator('#pauseResume').get_attribute('aria-label')=='Pause'
 page.locator('#stop').click()
 assert_geometry(original,geometry(page),'stop')
 assert page.locator('#setup').is_visible(), 'Stop should return to duration picker'
 assert page.locator('#activeControls').is_hidden()
 assert page.locator('#stateText').is_hidden()
 print('MANUAL STOP -> setup: OK')
 assert page.locator('#gentleEnd').count()==0
 assert page.locator('#settle').count()==0
 print('SILENT RETURN REMOVED: OK')
 page.locator('#settingsButton').click()
 assert page.locator('#marker').count()==0
 page.locator('#dark').check()
 assert page.locator('#motion').is_checked()
 page.locator('#motion').uncheck()
 assert page.locator('#dark').is_checked()
 page.locator('#motion').check()
 assert page.locator('#dark').is_checked()
 page.locator('#closeSettings').click()
 print('INDEPENDENT VISUAL MODES: OK')
 # Simulated time for fixed 10-min automatic return
 page.locator('.duration[data-minutes="10"]').click()
 page.locator('#settingsButton').click()
 page.locator('#closeSettings').click()
 page.clock.install()
 page.locator('#start').click()
 assert page.locator('#setup').is_hidden()
 page.clock.fast_forward(21000)
 assert page.locator('#veil').evaluate("el=>el.classList.contains('active')"), 'The screen should darken after 20 seconds without depending on audio'
 page.locator('#veil').click()
 assert not page.locator('#veil').evaluate("el=>el.classList.contains('active')"), 'Tap should show the screen again'
 page.clock.fast_forward(580000)
 assert page.locator('#setup').is_visible(), 'Auto completion must return to setup'
 assert page.locator('#stateText').is_hidden()
 print('AUTO END after 10 min -> setup: OK')
 mobile.close()
 # Regression: both display modes stay active; unknown sound falls back to bol
 migration=browser.new_context(viewport={'width':360,'height':780})
 p2=migration.new_page(); p2.on('pageerror',lambda error: errors.append('migration: '+str(error)))
 saved={'silence.settings.v2':json.dumps({'mode':'free','minutes':15,'motion':True,'dark':True,'tone':'invalid-old-tone','delay':False,'volume':60})}
 init(p2,saved)
 p2.locator('#settingsButton').click()
 assert p2.locator('#motion').is_checked()
 assert p2.locator('#dark').is_checked()
 assert p2.locator('#marker').count()==0
 assert p2.locator('#tone').input_value()=='bol'
 print('MIGRATION v3.4: OK')
 migration.close()
 # Desktop screenshot
 desktop=browser.new_context(viewport={'width':1280,'height':820})
 dp=desktop.new_page(); dp.on('pageerror',lambda error: errors.append('desktop: '+str(error)))
 init(dp)
 # screenshot skipped in CI
 assert dp.locator('#start').is_visible()
 desktop.close()
 # Motion accessibility
 reduced=browser.new_context(viewport={'width':360,'height':780},reduced_motion='reduce')
 rp=reduced.new_page(); rp.on('pageerror',lambda error: errors.append('reduced: '+str(error)))
 init(rp)
 rp.locator('#settingsButton').click(); rp.locator('#delay').uncheck(); rp.locator('#closeSettings').click(); rp.locator('#start').click()
 anim=rp.locator('.field-svg').evaluate('(el) => getComputedStyle(el).animationName')
 assert anim=='none',anim
 print('REDUCED MOTION: OK')
 reduced.close()
 browser.close()
print('JS ERRORS:',errors)
assert not errors,errors
print('ALL BROWSER DOM TESTS PASSED')
