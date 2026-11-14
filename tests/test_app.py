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

with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,**({'executable_path': '/usr/bin/chromium'} if Path('/usr/bin/chromium').exists() else {}),args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
 context=browser.new_context(viewport={'width':360,'height':780},device_scale_factor=1,is_mobile=True,has_touch=True,service_workers='allow')
 page=context.new_page()
 page.on('pageerror', lambda exc: errors.append(str(exc)))
 page.on('console', lambda msg: errors.append('console error: '+msg.text) if msg.type=='error' else None)
 page.goto(f'http://localhost:{PORT}/meditation/',wait_until='networkidle')
 assert page.locator('html').get_attribute('data-silence-ready')=='true'
 assert page.get_by_text('Version 3.6').is_hidden() # settings not open
 assert page.locator('#setup').is_visible()
 assert page.locator('#tone option').count()==5
 # screenshot skipped in CI
 page.locator('#settingsButton').click()
 assert page.get_by_text('Version 3.6').is_visible()
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
 for tone,label in [('foret','Forêt'),('oiseau','Oiseau'),('sousbois','Sous-bois')]:
  page.locator('#tone').select_option(tone)
  page.locator('#testSound').click()
  page.wait_for_function("(label) => document.querySelector('#soundStatus').textContent.includes('Écoute : ' + label)",arg=label,timeout=8000)
  print('SOUND',tone,page.locator('#soundStatus').text_content())
 page.locator('#closeSettings').click()
 page.locator('#start').click()
 assert page.locator('#setup').is_hidden()
 assert page.locator('#activeControls').is_visible()
 assert page.locator('#stop').is_visible()
 assert page.locator('#pauseResume').is_visible()
 assert page.locator('#stop').bounding_box()['width']==68
 assert page.locator('#stop').bounding_box()['height']==68
 assert page.locator('#peek').get_attribute('class').find('is-breathing')>=0
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
 # screenshot skipped in CI
 page.locator('#pauseResume').click()
 assert page.locator('#pauseResume').get_attribute('aria-label')=='Reprendre'
 assert page.locator('#pauseResume').locator('.play-symbol').is_visible()
 page.locator('#pauseResume').click()
 assert page.locator('#pauseResume').get_attribute('aria-label')=='Pause'
 page.locator('#stop').click()
 assert page.locator('#setup').is_visible(),'Stop should return to duration picker'
 assert page.locator('#activeControls').is_hidden()
 assert page.locator('#stateText').is_hidden()
 print('MANUAL STOP -> duration choices: OK')
 # 2nd cycle test also finishing via button
 page.locator('#start').click()
 page.locator('#gentleEnd').click()
 assert page.locator('#settlingControls').is_visible()
 page.locator('#finishNow').click()
 assert page.locator('#setup').is_visible()
 print('GENTLE END -> Stop -> setup: OK')
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
 assert 'silence-v3.6.0' in page.evaluate('async () => await caches.keys()')
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
