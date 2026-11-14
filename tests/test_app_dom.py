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
 page.add_script_tag(content=js)
 assert page.locator('html').get_attribute('data-silence-ready')=='true'
 if not page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches"):
  assert page.locator('body').evaluate("(el)=>el.classList.contains('intro-go')")
  assert page.locator('.opening-word').evaluate("(el)=>el.getAnimations().some(a=>a.animationName==='opening-word')")
  assert page.locator('.visual').evaluate("(el)=>getComputedStyle(el,'::after').animationName==='intro-ripple'")
 page.wait_for_function("!document.body.classList.contains('is-opening')",timeout=6500)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,**({'executable_path': '/usr/bin/chromium'} if Path('/usr/bin/chromium').exists() else {}),args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
 mobile=browser.new_context(viewport={'width':360,'height':780},device_scale_factor=1,is_mobile=True,has_touch=True)
 page=mobile.new_page()
 page.on('pageerror',lambda error: errors.append(str(error)))
 init(page)
 assert page.locator('#setup').is_visible()
 assert page.locator('#tone option').count()==2
 # screenshot skipped in CI
 page.locator('#settingsButton').click()
 assert page.get_by_text('Version 3.8').is_visible()
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
 name=page.locator('.orb').evaluate('(el)=>getComputedStyle(el).animationName')
 assert name=='quiet-pulse',name
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
 assert '0.91' in samples['a'] and '1.105' in samples['b'],samples
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
 page.locator('#dark').check()
 assert not page.locator('#motion').is_checked()
 page.locator('#motion').check()
 assert not page.locator('#dark').is_checked()
 page.locator('#closeSettings').click()
 print('EXCLUSIVE modes: OK')
 # Simulated time for fixed 10-min automatic return
 page.locator('.duration[data-minutes="10"]').click()
 page.locator('#settingsButton').click()
 page.locator('#closeSettings').click()
 page.clock.install()
 page.locator('#start').click()
 assert page.locator('#setup').is_hidden()
 page.clock.fast_forward(601000)
 assert page.locator('#setup').is_visible(), 'Auto completion must return to setup'
 assert page.locator('#stateText').is_hidden()
 print('AUTO END after 10 min -> setup: OK')
 mobile.close()
 # Regression: saved both toggles true and rejected sound -> default bol
 migration=browser.new_context(viewport={'width':360,'height':780})
 p2=migration.new_page(); p2.on('pageerror',lambda error: errors.append('migration: '+str(error)))
 saved={'silence.settings.v2':json.dumps({'mode':'free','minutes':15,'motion':True,'dark':True,'tone':'goutte','delay':False,'volume':60})}
 init(p2,saved)
 p2.locator('#settingsButton').click()
 assert p2.locator('#motion').is_checked()
 assert not p2.locator('#dark').is_checked()
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
 anim=rp.locator('.orb').evaluate('(el) => getComputedStyle(el).animationName')
 assert anim=='none',anim
 print('REDUCED MOTION: OK')
 reduced.close()
 browser.close()
print('JS ERRORS:',errors)
assert not errors,errors
print('ALL BROWSER DOM TESTS PASSED')
