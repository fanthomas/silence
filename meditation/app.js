(() => {
      'use strict';

      const $ = (id) => document.getElementById(id);
      const el = Object.fromEntries([
        'status', 'title', 'description', 'stateText', 'clock', 'peek', 'fieldSvg', 'fieldSheen', 'fieldCenterDot', 'fieldVeilOuter', 'fieldVeilInner',
        'fieldWaveOuter', 'fieldWaveOuterFine', 'fieldWaveMiddle', 'fieldWaveMiddleFine',
        'fieldWaveSatellite', 'fieldWaveInner', 'fieldWaveInnerFine', 'fieldWaveCore', 'fieldWaveCoreFine', 'setup', 'modeFree',
        'delay', 'tone', 'volume', 'testSound', 'motion', 'dark', 'wake', 'wakeHint', 'start', 'activeControls',
        'pauseResume', 'stop',
        'audioRecover', 'audioRecoverText', 'soundStatus', 'rearm', 'notice', 'veil', 'preferences', 'settingsButton', 'closeSettings', 'installButton'
      ].map((id) => [id, $(id)]));

      const SETTINGS_KEY = 'silence.settings.v2';
      const SESSION_KEY = 'silence.session.v2';
      const MINUTE = 60_000;
      const supportsWakeLock = !!(navigator.wakeLock && typeof navigator.wakeLock.request === 'function');
      // Palette embarquée dans le même fichier que le lecteur : aucune requête
      // supplémentaire ne peut manquer lors d'un lancement PWA hors ligne.
      const SOFT_TONES = Object.freeze({
        nacre:     { name:'Nacre',     notes:[[0,392,1],[1.08,493.88,.72]], duration:3.5, attack:.24, decay:1.28, h2:.17, h3:.035, flutter:.008 },
        aube:      { name:'Aube',      notes:[[0,329.63,1],[1.28,440,.68]], duration:3.8, attack:.38, decay:1.46, h2:.12, h3:.015, flutter:.011 },
        halo:      { name:'Halo',      notes:[[0,440,1],[.87,554.37,.48],[1.7,659.25,.27]], duration:4.0,attack:.23,decay:1.22,h2:.09,h3:.018,flutter:.006 },
        velours:   { name:'Velours',   notes:[[0,293.66,1],[1.16,349.23,.67]], duration:3.8, attack:.43, decay:1.40, h2:.24, h3:.05, flutter:.012 },
        rosee:     { name:'Rosée',     notes:[[0,523.25,1],[1.22,659.25,.58]], duration:3.6, attack:.17, decay:1.19, h2:.12, h3:.025, flutter:.003 },
        sillage:   { name:'Sillage',   notes:[[0,349.23,1],[1.03,392,.76]], duration:3.7, attack:.28, decay:1.58, h2:.16, h3:.025, flutter:.016 },
        brume:     { name:'Brume',     notes:[[0,311.13,1],[1.48,369.99,.61]], duration:4.1, attack:.51, decay:1.61, h2:.09, h3:.01, flutter:.017 },
        clairiere: { name:'Clairière', notes:[[0,392,1],[.95,523.25,.62],[1.93,587.33,.34]], duration:4.1,attack:.19,decay:1.20,h2:.19,h3:.043,flutter:.009 },
        dune:      { name:'Dune',      notes:[[0,277.18,1],[1.3,369.99,.69]], duration:4.0, attack:.45, decay:1.50, h2:.26, h3:.045, flutter:.013 },
        equilibre: { name:'Équilibre', notes:[[0,369.99,1],[1.18,466.16,.65]], duration:3.9, attack:.31, decay:1.34, h2:.13, h3:.03, flutter:.007 }
      });
      function createSoftToneBuffer(context, name, brief = false) {
        const tone=SOFT_TONES[name];
        if (!tone) throw new Error('Repère inconnu : ' + name);
        const rate=context.sampleRate;
        // Mode libre : un seul petit tintement, au lieu d'une mélodie de 4 secondes.
        // Mode fixe : conserver le son de fin complet, déjà plus audible.
        const duration=brief ? .9 : tone.duration;
        const attack=brief ? Math.max(.075,Math.min(.12,tone.attack*.32)) : tone.attack;
        const decayTime=brief ? .37 : tone.decay;
        const total=Math.ceil(duration*rate);
        const buffer=context.createBuffer(1,total,rate);
        const samples=buffer.getChannelData(0);
        const tau=2*Math.PI;
        const endFade=brief ? .20 : .38;
        for (const [start,frequency,weight] of (brief ? tone.notes.slice(0,1) : tone.notes)) {
          for (let i=Math.ceil(start*rate);i<total;i++) {
            const t=i/rate-start;
            const rise=Math.sin(Math.PI/2*Math.min(1,t/attack))**2;
            const decay=Math.exp(-t/decayTime);
            const tail=Math.sin(Math.PI/2*Math.min(1,Math.max(0,(duration-i/rate)/endFade)))**2;
            const breathe=1-tone.flutter*(1-Math.cos(tau*1.15*t));
            const fundamental=Math.sin(tau*frequency*t);
            const second=tone.h2*Math.sin(tau*2*frequency*t+.18);
            const third=tone.h3*Math.sin(tau*3*frequency*t+.38);
            samples[i]+=weight*rise*decay*tail*breathe*(fundamental+second+third);
          }
        }
        let peak=0;
        for (const sample of samples) peak=Math.max(peak,Math.abs(sample));
        const normalize=(brief ? .72 : .80)/Math.max(.0001,peak);
        for (let i=0;i<samples.length;i++) samples[i]*=normalize;
        return buffer;
      }
    
      const SOUND_NAMES = { bol:'Bol feutré', bambou:'Bois doux', goutte:'Goutte douce',
        ...Object.fromEntries(Object.entries(SOFT_TONES).map(([key, tone]) => [key, tone.name])) };
      const defaults = { mode: 'free', minutes: 15, delay: true, tone: 'bol', volume: 65, motion: true, dark: false, wake: true };
      const savedSettings = readStorage(SETTINGS_KEY, {});
      const settings = { ...defaults, ...savedSettings };
      // L'écran noir, l'animation et le maintien de l'écran allumé sont indépendants.
      delete settings.marker; // Ancienne option supplémentaire, supprimée.
      if (!['free', 'fixed'].includes(settings.mode)) settings.mode = 'free';
      if (![10, 12, 15, 20].includes(settings.minutes)) settings.minutes = 15;
      settings.tone = ({ cristal: 'bol', bois: 'bambou', foret: 'bol', oiseau: 'bol', sousbois: 'bol', pepiement: 'bol' })[settings.tone] || settings.tone;
      if (!Object.hasOwn(SOUND_NAMES, settings.tone)) settings.tone = 'bol';
      settings.volume = Math.max(0, Math.min(100, Number(settings.volume) || 0));

      let phase = 'idle'; // idle, running, paused
      let startAt = 0; // début effectif (après l'installation) en ms epoch
      let elapsedAtPause = 0;
      let lastStage = '';
      let dimTimeout = null;
      let audioContext = null;
      let soundNodes = [];
      let previewNodes = [];
      let audioScheduleToken = 0;
      let nextSoundRefreshAt = 0;
      let previewToken = 0;
      const bufferCache = new Map();
      const pendingBuffers = new Map();
      let soundArmed = false;
      let audioNeedsRecovery = false;
      let wakeLock = null;
      let wakeRequestPending = false;
      let wakeWarningShown = false;
      let tickTimer = null;

      function readStorage(key, fallback) {
        try { const item = localStorage.getItem(key); return item ? JSON.parse(item) : fallback; }
        catch (_) { return fallback; }
      }
      function writeStorage(key, data) { try { localStorage.setItem(key, JSON.stringify(data)); } catch (_) { /* Stockage optionnel */ } }
      function removeStorage(key) { try { localStorage.removeItem(key); } catch (_) { /* Stockage optionnel */ } }
      function saveSettings() { writeStorage(SETTINGS_KEY, settings); }
      function saveSession() {
        if (phase === 'idle') { removeStorage(SESSION_KEY); return; }
        writeStorage(SESSION_KEY, { version: 2, phase, startAt, elapsedAtPause, settings: { ...settings }, savedAt: Date.now() });
      }
      function showNotice(message) { el.notice.textContent = message || ''; }
      function format(ms) {
        const sec = Math.floor(Math.max(0, ms) / 1000);
        return `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`;
      }
      function elapsed() {
        if (phase === 'running') return Math.max(0, Date.now() - startAt);
        if (phase === 'paused') return elapsedAtPause;
        return 0;
      }
      function hasStarted() { return phase === 'running' && Date.now() >= startAt; }
      function sessionDurationMs() { return settings.minutes * MINUTE; }
      function preparing() { return phase === 'running' && Date.now() < startAt; }
      function stage() {
        if (phase !== 'running') return phase;
        if (preparing()) return 'preparing';
        if (settings.mode === 'free' && elapsed() >= 10 * MINUTE) return 'freeReached';
        return 'running';
      }

      // Échantillons audio inclus dans app.js : pas de fichiers MP3 à charger.
      // La reprise du contexte audio doit partir d'un geste utilisateur (Android/iOS).
      const SOUND_DATA = {"bol":"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AAD7//b/8f/s/+f/4//e/9r/1//U/9H/z//O/83/zf/O/8//0P/T/9b/2f/d/+H/5v/r//D/9f/6/wAABAAJAA4AEwAYABwAIAAkACcAKQArAC0ALgAvAC8ALwAuAC0AKwApACcAJAAhAB0AGgAWABEADQAIAAMAAAD7//b/8f/t/+n/5P/h/93/2v/X/9X/0//S/9H/0f/S/9P/1P/W/9n/3P/f/+P/6P/s//H/9v/7/wAABAAJAA4AEgAXABoAHgAhACMAJQAmACcAJwAnACYAJQAkACIAHwAcABoAFgATABAADAAJAAYAAgAAAP3/+//4//b/9P/y//D/7//u/+3/7P/s/+z/6//r/+v/7P/s/+z/7f/t/+7/7//v//D/8f/y//P/9P/2//f/+P/6//z//v///wAAAgAEAAYACAAKAAwADgAQABEAEwAUABUAFgAXABcAFwAXABYAFgAVABQAEgARAA8ADQALAAgABgAEAAEAAAD+//v/+f/3//X/8//x//D/7v/t/+z/6//r/+r/6v/q/+r/6//r/+z/7f/u//D/8f/z//X/9//5//v//f///wEAAwAFAAcACgAMAA4AEAASABMAFQAWABcAFwAYABgAGAAXABYAFQAUABIAEAAOAAwACgAHAAQAAgAAAP3/+//4//b/8//x//D/7v/t/+z/6//r/+r/6//r/+z/7f/u/+//8f/z//X/9v/4//v//f///wAAAQADAAUABgAIAAkACgALAAsADAAMAA0ADQANAA0ADAAMAAwACwAKAAoACQAIAAcABwAGAAUABAADAAIAAQAAAAAAAAD///7//f/8//v/+//6//n/+f/4//j/9//3//f/9//3//f/9//3//j/+P/5//n/+v/7//v//P/9//7///8AAAAAAAABAAIAAwAEAAQABQAFAAYABgAHAAcABwAHAAcABwAHAAcABwAHAAYABgAGAAUABQAEAAQAAwADAAIAAQABAAAAAAD//////v/9//z//P/7//v/+v/5//n/+f/4//j/+P/4//j/+P/5//n/+v/6//v//P/8//3//v///wAAAAABAAIAAwAEAAQABQAGAAYABwAHAAcABwAHAAcABwAHAAYABgAGAAUABAAEAAMAAgABAAEAAAAAAAAA///+//7//f/9//3//P/8//z//P/8//z//P/8//z//P/8//z//f/9//3//v/+//7//////wAAAAAAAAAAAAAAAAEAAQABAAEAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgABAAEAAQABAAEAAAAAAAAAAAAAAAAAAAAAAAAA//////////////////////////////////////////////////8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEAAQABAAEAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=","bambou":"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LwAvAC8ALgAsACoAKAAlACIAHgAaABYAEQAMAAgAAwD///r/9f/x/+z/6P/l/+H/3v/b/9n/2P/W/9b/1f/W/9b/1//Z/9v/3v/h/+T/6P/r/+//9P/4//z/AAAEAAgADQARABQAGAAbAB4AIAAiACQAJQAmACYAJgAmACUAIwAiAB8AHQAaABcAFAAQAAwACAAEAAAA/f/6//b/8v/v/+v/6f/m/+T/4v/g/9//3v/e/97/3v/f/+D/4f/j/+X/6P/r/+7/8f/0//j/+////wEABQAIAAwADwASABQAFwAZABsAHAAdAB4AHwAfAB4AHgAdABwAGgAYABYAEwARAA4ACwAIAAUAAgAAAP3/+v/3//T/8f/v/+3/6//p/+f/5v/m/+X/5f/l/+b/5v/n/+n/6v/s/+7/8P/z//X/+P/7//7/AAACAAUACAAKAAwADwARABIAFAAVABYAFwAYABgAGAAXABcAFgAVABMAEgAQAA4ADAAKAAcABQADAAAA///8//r/+P/2//T/8v/w/+//7v/t/+z/6//r/+v/6//s/+3/7v/v//D/8v/z//X/9//5//v//f///wAAAwAFAAcACAAKAAwADQAPABAAEQARABIAEgASABIAEgARABAADwAOAA0ACwAKAAgABgAFAAMAAQAAAP7//f/7//n/+P/2//X/9P/z//L/8f/x//H/8P/x//H/8f/y//P/9P/1//b/9//5//r//P/9////AAABAAMABAAFAAcACAAJAAoACwAMAAwADQANAA0ADQANAA0ADAALAAsACgAJAAgABwAFAAQAAwABAAAAAAD+//3//P/7//r/+f/4//f/9v/2//X/9f/1//X/9f/1//b/9v/3//j/+P/5//r/+//8//7///8AAAAAAQACAAMABAAFAAYABwAHAAgACAAJAAkACQAJAAkACQAIAAgACAAHAAYABgAFAAQAAwACAAEAAAAAAP/////+//3//P/7//v/+v/6//n/+f/5//n/+f/5//n/+f/5//r/+v/7//v//P/9//3//v///wAAAAAAAAEAAgACAAMAAwAEAAQABQAFAAUABgAGAAYABgAGAAUABQAFAAUABAAEAAMAAwACAAIAAQAAAAAAAAAAAP///v/+//7//f/9//z//P/8//z//P/8//z//P/8//z//P/8//3//f/+//7//v//////AAAAAAAAAAABAAEAAQACAAIAAgADAAMAAwADAAMAAwADAAMAAwADAAMAAwACAAIAAgACAAEAAQABAAAAAAAAAAAAAAAAAP////////7//v/+//7//v/+//7//v/+//7//v/+//7//v//////////////AAAAAAAAAAAAAAAAAAAAAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP////////////////////////////8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="};
      const NATURE_FILES = {goutte:'./sounds/goutte.wav'}; // Signal original ponctuel, sans ambiance continue.

      function audioMessage(message) {
        el.soundStatus.textContent = message;
      }
      function unlockAudio() {
        try {
          const AudioCtor = window.AudioContext || window.webkitAudioContext;
          if (!AudioCtor) throw new Error('AudioContext indisponible');
          if (!audioContext || audioContext.state === 'closed') {
             audioContext = new AudioCtor({latencyHint:'interactive'});
             audioContext.addEventListener('statechange', () => {
               if (phase === 'running' && soundArmed && audioContext.state !== 'running') {
                 soundArmed = false;
                 audioNeedsRecovery = true;
                 showNotice('Le navigateur a suspendu les sons. Appuie sur « Réactiver les sons ».');
                 render();
               }
             });
           }
          // Important : resume() est appelé avant le premier await, dans le clic réel.
          const request = audioContext.state === 'running' ? Promise.resolve() : audioContext.resume();
          return request.then(() => {
            if (audioContext.state !== 'running') throw new Error('Audio suspendu par le navigateur');
            soundArmed = true;
            return audioContext;
          });
        } catch (error) {
          soundArmed = false;
          return Promise.reject(error);
        }
      }
      function makeBackupSound(ctx, name) {
        // Secours discret en cas d'échec de décodage WAV, sans timbres aigus.
        const sr = ctx.sampleRate;
        const durations = {bol:.70,bambou:.42};
        const fundamentals = {bol:385,bambou:410};
        const duration = durations[name] || .58;
        const buffer = ctx.createBuffer(1,Math.ceil(sr*duration),sr);
        const data = buffer.getChannelData(0);
        const attack = .035;
        for (let i=0;i<data.length;i++) {
          const t=i/sr;
          const rise=Math.sin(Math.PI*.5*Math.min(1,t/attack))**2;
          const tail=Math.min(1,Math.max(0,(duration-t)/.12))**2;
          data[i]=.42*rise*Math.exp(-t/(name==='bambou'?.13:.24))*tail*Math.sin(2*Math.PI*fundamentals[name]*t);
        }
        return buffer;
      }
      function loadSound(ctx, name, mode = 'fixed') {
        // Un nom invalide ne doit jamais générer une fréquence undefined,
        // ce qui produisait un buffer silencieux à la place du vrai son.
        if (!Object.hasOwn(SOUND_NAMES, name)) {
          return Promise.reject(new Error('Repère sonore inconnu : ' + name));
        }
        const key=Object.hasOwn(SOFT_TONES, name) ? name+':'+mode : name;
        if (bufferCache.has(key)) return Promise.resolve(bufferCache.get(key));
        if (pendingBuffers.has(key)) return pendingBuffers.get(key);
        const loading = Promise.resolve().then(async () => {
          try {
            // Nouveaux sons : création locale, sans téléchargement.
            if (Object.hasOwn(SOFT_TONES, name)) return createSoftToneBuffer(ctx, name, mode === 'free');
            if (NATURE_FILES[name]) {
              const response = await fetch(NATURE_FILES[name], {cache:'force-cache'});
              if (!response.ok) throw new Error('Enregistrement naturel indisponible');
              const decoded = await ctx.decodeAudioData(await response.arrayBuffer());
              if (!decoded || !decoded.length) throw new Error('Enregistrement naturel vide');
              return decoded;
            }
            const raw = atob(SOUND_DATA[name]);
            const data = new Uint8Array(raw.length);
            for (let i = 0; i < raw.length; i++) data[i] = raw.charCodeAt(i);
            const buffer = await ctx.decodeAudioData(data.buffer);
            if (!buffer || !buffer.length) throw new Error('Audio décodé vide');
            return buffer;
          } catch (error) {
            // Son fonctionnel même si le décodeur MP3 est absent.
            if (NATURE_FILES[name]) throw error;
            return makeBackupSound(ctx, name);
          }
        }).then(buffer => { bufferCache.set(key, buffer); return buffer; })
          .finally(() => pendingBuffers.delete(key));
        pendingBuffers.set(key, loading);
        return loading;
      }
      function playSound(ctx, buffer, at, strength, collection) {
        if (settings.volume <= 0) return false;
        const src = ctx.createBufferSource();
        const gain = ctx.createGain();
        src.buffer = buffer;
        const volume = Math.pow(settings.volume / 100, 1.1);
        const level = Math.min(1, volume * strength);
        let filter = null;
        if (settings.tone === 'bol') {
          // Bol feutré : une attaque douce, des aigus arrondis et un fondu court.
          filter = ctx.createBiquadFilter();
          filter.type = 'lowpass';
          filter.frequency.value = 1250;
          filter.Q.value = .55;
          // Corrige la coupure artificielle à 125 ms : le bol garde sa résonance.
          gain.gain.setValueAtTime(.0001, at);
          gain.gain.linearRampToValueAtTime(level, at + .065);
          src.connect(filter);
          filter.connect(gain);
        } else {
          // Bois doux conserve exactement son enveloppe initiale.
          gain.gain.setValueAtTime(level, at);
          src.connect(gain);
        }
        gain.connect(ctx.destination);
        src.start(at);
        collection.push(src);
        src.addEventListener('ended', () => {
          try { src.disconnect(); filter?.disconnect(); gain.disconnect(); } catch (_) { /* Déconnecté */ }
          const index = collection.indexOf(src);
          if (index !== -1) collection.splice(index, 1);
        }, {once:true});
        return true;
      }
      function stopCollection(collection) {
        for (const src of collection) {
          try { src.stop(); } catch (_) { /* Son déjà terminé */ }
          try { src.disconnect(); } catch (_) { /* Déconnecté */ }
        }
        collection.length = 0;
      }
      function stopPreview() { previewToken++; stopCollection(previewNodes); }
      function stopAudio() { audioScheduleToken++; nextSoundRefreshAt = 0; stopCollection(soundNodes); stopPreview(); }
      // Mode libre : une sonnerie chaque 10 min. Les huit prochaines sont
      // prévues par Web Audio ; le planning est renouvelé entre deux repères.
      function cueDates(mode, start, minutes, now) {
        if (mode === 'fixed') {
          const end = start + minutes * MINUTE;
          return end > now + 100 ? [end] : [];
        }
        const interval = 10 * MINUTE;
        const next = Math.max(1, Math.floor((now + 100 - start) / interval) + 1);
        return Array.from({length: 8}, (_, i) => start + (next + i) * interval);
      }
      async function scheduleSounds() {
        stopCollection(soundNodes);
        const token = ++audioScheduleToken;
        nextSoundRefreshAt = 0;
        if (!soundArmed || !audioContext || audioContext.state !== 'running' || phase !== 'running') return;
        const ctx = audioContext, selected = settings.tone, mode = settings.mode;
        try {
          const buffer = await loadSound(ctx, selected, mode);
          if (token !== audioScheduleToken || phase !== 'running' || settings.mode !== mode || !soundArmed || ctx.state !== 'running') return;
          const now = Date.now();
          const dates = cueDates(mode, startAt, settings.minutes, now);
          for (const date of dates) {
            // Même niveau interne en méditation et pendant le test « Écouter ».
             playSound(ctx, buffer, ctx.currentTime + Math.max(.08, (date - now) / 1000), 1, soundNodes);
          }
          // Renouveler deux minutes avant un repère, jamais exactement à son déclenchement.
          if (mode === 'free') nextSoundRefreshAt = dates[5] - 2 * MINUTE;
        } catch (error) {
          if (token === audioScheduleToken) {
            soundArmed = false;
            audioNeedsRecovery = true;
            nextSoundRefreshAt = 0;
            showNotice('Impossible de programmer le son. Réactive-le depuis la séance.');
            render();
          }
        }
      }
      async function previewSound() {
        stopPreview();
        const token = previewToken;
        const selected = settings.tone, mode = settings.mode;
        audioMessage('Préparation du son…');
        // Le contexte est débloqué immédiatement pendant l'interaction utilisateur.
        const unlocking = unlockAudio();
        try {
          const ctx = await unlocking;
          const buffer = await loadSound(ctx, selected, mode);
          if (token !== previewToken || settings.tone !== selected || settings.mode !== mode) return;
          if (ctx.state !== 'running') throw new Error('Contexte suspendu');
          if (settings.volume === 0) {
            audioMessage('Le volume est à zéro.');
            return;
          }
          if (!SOUND_NAMES[selected]) throw new Error('Repère sonore absent : ' + selected);
          if (!playSound(ctx, buffer, ctx.currentTime + .035, 1, previewNodes)) {
            throw new Error('Impossible de démarrer le son');
          }
          audioMessage('Écoute : ' + SOUND_NAMES[selected] + (mode === 'free' ? ' · repère 10 min' : ' · fin de séance'));
        } catch (error) {
          soundArmed = false;
          audioMessage('Lecture impossible. Vérifie le volume multimédia du téléphone et réessaie.');
          showNotice('Le son n’a pas pu démarrer.');
        }
      }

      async function requestWakeLock() {
        if (!supportsWakeLock || !settings.wake || !['running'].includes(phase) || document.visibilityState !== 'visible' || wakeLock || wakeRequestPending) return;
        wakeRequestPending = true;
        try {
          const sentinel = await navigator.wakeLock.request('screen');
          if (!settings.wake || !['running'].includes(phase)) { void sentinel.release().catch(() => {}); return; }
          wakeLock = sentinel;
          sentinel.addEventListener('release', () => {
            if (wakeLock === sentinel) wakeLock = null;
          }, { once: true });
        } catch (_) {
          if (!wakeWarningShown) showNotice('L’écran ne peut pas rester actif sur cet appareil.');
          wakeWarningShown = true;
        } finally { wakeRequestPending = false; }
      }
      function releaseWakeLock() {
        const old = wakeLock; wakeLock = null;
        if (old) void old.release().catch(() => {});
      }

      function hideVeil() {
        el.veil.classList.remove('active');
        clearTimeout(dimTimeout);
        syncFieldAnimation();
      }
      function scheduleDim() {
        hideVeil();
        if (!settings.dark || phase !== 'running' || document.visibilityState !== 'visible') return;
        dimTimeout = setTimeout(() => {
          if (settings.dark && phase === 'running' && document.visibilityState === 'visible') {
            el.veil.classList.add('active');
            syncFieldAnimation();
          }
        }, 20_000);
      }
      function updateClock() {
        // Le cercle reste contemplatif : aucune action ne révèle le chronomètre.
        el.clock.classList.add('hidden');
      }

      // Un véritable champ vectoriel : les points des courbes évoluent, pas seulement leur rotation.
      // Cadence plafonnée à 30 i/s pour préserver l'autonomie des téléphones.
      const fieldMotionPreference = window.matchMedia?.('(prefers-reduced-motion: reduce)');
      const fieldRings = [
        // Plusieurs orbites se rapprochent puis se séparent : les pensées passent, le centre reste.
        { node: el.fieldWaveOuter, radius: 165, amplitude: 18.0, phase: .15, oval: 1.05 },
        { node: el.fieldWaveOuterFine, radius: 151, amplitude: 24.0, phase: .41, oval: 1.07 },
        { node: el.fieldWaveMiddle, radius: 136, amplitude: 19.0, phase: 1.3, oval: .975 },
        { node: el.fieldWaveMiddleFine, radius: 123, amplitude: 20.0, phase: 1.86, oval: 1.03 },
        { node: el.fieldWaveSatellite, radius: 114, amplitude: 17.0, phase: 2.21, oval: .985 },
        { node: el.fieldWaveInner, radius: 98, amplitude: 14.0, phase: 3.13, oval: 1.015 },
        { node: el.fieldWaveInnerFine, radius: 85, amplitude: 11.0, phase: 3.71, oval: .98 },
        { node: el.fieldWaveCore, radius: 70, amplitude: 8.0, phase: 4.56, oval: 1.025 },
        { node: el.fieldWaveCoreFine, radius: 55, amplitude: 6.0, phase: 5.24, oval: 1.0 }
      ];
      let fieldFrameId = 0;
      let fieldFrameTime = 0;
      let fieldLastPaint = 0;
      let fieldElapsed = 0;
      let fieldHasDrawn = false;
      function fieldPath(ring, time) {
        // Courbe de Catmull-Rom périodique, transformée en Bézier fermée.
        // Tangentes identiques au raccord : aucun début ni fin de trait perceptible.
        const segments = 112;
        const points = [];
        const angleOffset = Math.sin(time * .09 + ring.phase) * .08;
        const oval = ring.oval + Math.sin(time * .13 + ring.phase) * .012;
        for (let i = 0; i < segments; i++) {
          const a = i * Math.PI * 2 / segments;
          const wave =
            .65 * Math.sin(2 * a + time * .31 + ring.phase) +
            .38 * Math.cos(3 * a - time * .23 + ring.phase * .75) +
            .19 * Math.sin(5 * a + time * .17 - ring.phase * .5);
          const radius = ring.radius + ring.amplitude * wave;
          points.push({
            x: 200 + Math.cos(a + angleOffset) * radius * oval,
            y: 200 + Math.sin(a + angleOffset) * radius / oval
          });
        }
        const coord = (value) => value.toFixed(2);
        let path = 'M' + coord(points[0].x) + ' ' + coord(points[0].y);
        for (let i = 0; i < segments; i++) {
          const previous = points[(i + segments - 1) % segments];
          const from = points[i];
          const to = points[(i + 1) % segments];
          const next = points[(i + 2) % segments];
          const c1x = from.x + (to.x - previous.x) / 6;
          const c1y = from.y + (to.y - previous.y) / 6;
          const c2x = to.x - (next.x - from.x) / 6;
          const c2y = to.y - (next.y - from.y) / 6;
          path += 'C' + coord(c1x) + ' ' + coord(c1y) +
            ' ' + coord(c2x) + ' ' + coord(c2y) +
            ' ' + coord(to.x) + ' ' + coord(to.y);
        }
        return path + 'Z';
      }
      function paintField(time) {
        const paths = fieldRings.map((ring) => fieldPath(ring, time));
        fieldRings.forEach((ring, i) => ring.node.setAttribute('d', paths[i]));
        // Voiles transparents entre deux orbites fermées ; aucune image n'est déplacée.
        el.fieldVeilOuter.setAttribute('d', paths[0] + ' ' + paths[2]);
        el.fieldVeilInner.setAttribute('d', paths[3] + ' ' + paths[5]);
        const direction = time * .12;
        const dx = Math.cos(direction) * 175;
        const dy = Math.sin(direction) * 175;
        el.fieldSheen.setAttribute('x1', (200 - dx).toFixed(2));
        el.fieldSheen.setAttribute('y1', (200 - dy).toFixed(2));
        el.fieldSheen.setAttribute('x2', (200 + dx).toFixed(2));
        el.fieldSheen.setAttribute('y2', (200 + dy).toFixed(2));
        fieldHasDrawn = true;
      }
      function frameField(now) {
        if (!fieldFrameTime) fieldFrameTime = now;
        fieldElapsed += Math.min(now - fieldFrameTime, 45);
        fieldFrameTime = now;
        if (!fieldLastPaint || now - fieldLastPaint >= 33) {
          paintField(fieldElapsed / 1000);
          fieldLastPaint = now;
        }
        fieldFrameId = requestAnimationFrame(frameField);
      }
      function stopFieldAnimation() {
        if (fieldFrameId) cancelAnimationFrame(fieldFrameId);
        fieldFrameId = 0;
        fieldFrameTime = 0;
        fieldLastPaint = 0;
      }
      function syncFieldAnimation() {
        const enabled = settings.motion && phase !== 'paused'
          && document.visibilityState === 'visible' && !el.veil.classList.contains('active')
          && !fieldMotionPreference?.matches;
        el.peek.classList.toggle('is-field-active', enabled);
        if (!fieldHasDrawn) paintField(0);
        if (enabled && !fieldFrameId) fieldFrameId = requestAnimationFrame(frameField);
        else if (!enabled && fieldFrameId) stopFieldAnimation();
      }

      function renderSetup() {
        el.modeFree.setAttribute('aria-pressed', String(settings.mode === 'free'));
        document.querySelectorAll('.duration').forEach((button) => {
          button.setAttribute('aria-pressed', String(settings.mode === 'fixed' && Number(button.dataset.minutes) === settings.minutes));
        });
        el.delay.checked = settings.delay;
        el.tone.value = settings.tone;
        el.volume.value = String(settings.volume);
        el.motion.checked = settings.motion;
        el.dark.checked = settings.dark;
        el.wake.checked = supportsWakeLock && settings.wake;
        el.wake.disabled = !supportsWakeLock;
      }
      function render() {
        const s = stage();
        const active = ['running', 'paused'].includes(phase);
        el.setup.classList.toggle('hidden', phase !== 'idle');
        el.settingsButton.classList.toggle('hidden', phase !== 'idle');
        el.activeControls.classList.toggle('hidden', !active);
        el.peek.classList.toggle('is-breathing', settings.motion && phase === 'running');
        el.pauseResume.classList.toggle('is-paused', phase === 'paused');
        el.pauseResume.setAttribute('aria-label', phase === 'paused' ? 'Reprendre' : 'Pause');
        el.pauseResume.title = phase === 'paused' ? 'Reprendre' : 'Pause';
        el.audioRecover.classList.toggle('hidden', !audioNeedsRecovery || !active);
        const copy = {
          idle: ['PRÊT', 'Prêt à méditer', 'Choisis un mode et commence.'],
          preparing: ['INSTALLATION', 'Installation', 'La séance commence dans dix secondes.'],
          running: ['MÉDITATION', 'Séance en cours', 'Le temps reste masqué.'],
          freeReached: ['DIX MINUTES', 'Dix minutes écoulées', 'Tu peux continuer librement.'],
          paused: ['PAUSE', 'En pause', 'Le chronomètre est suspendu.']
        };
        [el.status.textContent, el.title.textContent, el.description.textContent] = copy[s];
        el.stateText.textContent = '';
        el.stateText.classList.add('hidden');
        updateClock();
        syncFieldAnimation();
        lastStage = s;
      }
      function tick() {
        if (phase === 'running' && settings.mode === 'fixed' && Date.now() >= startAt + sessionDurationMs()) {
          elapsedAtPause = sessionDurationMs();
          completeSession();
          return;
        }
        if (settings.mode === 'free' && nextSoundRefreshAt > 0 && Date.now() >= nextSoundRefreshAt
            && soundArmed && audioContext?.state === 'running') {
          nextSoundRefreshAt = 0;
          void scheduleSounds();
        }
        if (lastStage !== stage()) render();
        else updateClock();
      }
      function beginTicking() { clearInterval(tickTimer); tickTimer = setInterval(tick, 250); }
      function clearTimers() { clearInterval(tickTimer); tickTimer = null; }
      function completeSession() {
        // Ne pas stopper le repère final déjà programmé au moment du retour à l'accueil.
        // Android peut cependant avoir suspendu le contexte Web Audio.
        const unavailable = !soundArmed || !audioContext || audioContext.state !== 'running';
        reset(true);
        if (unavailable && settings.volume > 0) {
          showNotice('Le son final a pu être bloqué. Vérifie le volume multimédia et réactive les sons avant la prochaine séance.');
        }
      }
      function beginSession() {
        clearTimers();
        stopAudio();
        phase = 'running';
        startAt = Date.now() + (settings.delay ? 10_000 : 0);
        elapsedAtPause = 0;
        soundArmed = false;
        audioNeedsRecovery = false;
        // L'interface démarre immédiatement, même si l'audio est indisponible.
        const unlocking = unlockAudio();
        saveSession();
        showNotice('');
        void requestWakeLock();
        beginTicking();
        scheduleDim();
        render();
        void unlocking.then(() => {
          audioNeedsRecovery = false;
          if (phase === 'running') { void scheduleSounds(); render(); }
        }).catch(() => {
          soundArmed = false;
          audioNeedsRecovery = true;
          showNotice('Les sons sont bloqués. Appuie sur « Réactiver les sons ».');
          render();
        });
      }
      function pause() {
        elapsedAtPause = elapsed();
        phase = 'paused';
        stopAudio();
        releaseWakeLock();
        clearTimers();
        hideVeil();
        saveSession();
        render();
      }
      function resume() {
        phase = 'running';
        startAt = Date.now() - elapsedAtPause;
        soundArmed = false;
        audioNeedsRecovery = false;
        const unlocking = unlockAudio();
        showNotice('');
        saveSession();
        beginTicking();
        void requestWakeLock();
        scheduleDim();
        render();
        void unlocking.then(() => {
          audioNeedsRecovery = false;
          if (phase === 'running') { void scheduleSounds(); render(); }
        }).catch(() => { soundArmed = false; audioNeedsRecovery = true; showNotice('Les sons sont suspendus.'); render(); });
      }
      function reset(keepFinalSound = false) {
        // Manuel : arrêt immédiat des sons. Automatique : repère final préservé.
        if (!keepFinalSound) stopAudio();
        releaseWakeLock();
        clearTimers();
        hideVeil();
        phase = 'idle';
        startAt = elapsedAtPause = 0;
        soundArmed = false;
        audioNeedsRecovery = false;
        showNotice('');
        removeStorage(SESSION_KEY);
        renderSetup();
        render();
      }
      function recoverSession() {
        const saved = readStorage(SESSION_KEY, null);
        if (saved?.phase === 'settling') { removeStorage(SESSION_KEY); return; }
        if (!saved || saved.version !== 2 || !['running', 'paused'].includes(saved.phase)) return;
        if (!Number.isFinite(saved.startAt) || !Number.isFinite(saved.savedAt) || Date.now() - saved.savedAt > 5 * 60 * MINUTE) return;
        if (!saved.settings || !['free', 'fixed'].includes(saved.settings.mode)) return;
        Object.assign(settings, saved.settings);
        delete settings.marker;
        if (![10, 12, 15, 20].includes(settings.minutes)) settings.minutes = 15;
        settings.tone = ({ cristal: 'bol', bois: 'bambou', foret: 'bol', oiseau: 'bol', sousbois: 'bol', pepiement: 'bol' })[settings.tone] || settings.tone;
        if (!Object.hasOwn(SOUND_NAMES, settings.tone)) settings.tone = 'bol';
        settings.volume = Math.max(0, Math.min(100, Number(settings.volume) || 0));
        phase = saved.phase;
        startAt = saved.startAt;
        elapsedAtPause = Number(saved.elapsedAtPause) || 0;
        soundArmed = false; // Après un rechargement, le navigateur exige un nouveau clic pour le son.
        audioNeedsRecovery = true;
        if (phase === 'running' && elapsed() > 4 * 60 * MINUTE) { phase = 'idle'; return; }
        tick();
        if (phase === 'running') beginTicking();
        showNotice('Séance retrouvée. Réactive les sons si tu veux entendre les prochains repères.');
      }

      // Paramètres volontairement à l'écart de l'écran principal.
      el.settingsButton.addEventListener('click', () => el.preferences.showModal());
      el.closeSettings.addEventListener('click', () => el.preferences.close());
      el.preferences.addEventListener('click', (event) => {
        if (event.target === el.preferences) el.preferences.close();
      });
      let installPrompt = null;
      window.addEventListener('beforeinstallprompt', (event) => {
        event.preventDefault();
        installPrompt = event;
        el.installButton.classList.remove('hidden');
      });
      el.installButton.addEventListener('click', async () => {
        if (!installPrompt) return;
        const prompt = installPrompt;
        installPrompt = null;
        el.installButton.classList.add('hidden');
        await prompt.prompt();
      });
      window.addEventListener('appinstalled', () => {
        installPrompt = null;
        el.installButton.classList.add('hidden');
      });

      el.modeFree.addEventListener('click', () => { settings.mode = 'free'; saveSettings(); renderSetup(); render(); });
      document.querySelectorAll('.duration').forEach((button) => button.addEventListener('click', () => {
        settings.mode = 'fixed';
        settings.minutes = Number(button.dataset.minutes);
        saveSettings(); renderSetup(); render();
      }));
      for (const key of ['delay', 'motion', 'dark', 'wake']) {
        el[key].addEventListener('change', () => {
          settings[key] = el[key].checked;
          saveSettings(); renderSetup(); render();
          if (key === 'dark') scheduleDim();
        });
      }
      el.volume.addEventListener('input', () => { settings.volume = Number(el.volume.value); saveSettings(); });
      el.tone.addEventListener('change', () => {
        stopPreview(); settings.tone = el.tone.value; saveSettings();
        audioMessage('');
      });
      el.testSound.addEventListener('click', () => { void previewSound(); });
      el.start.addEventListener('click', beginSession);
      el.pauseResume.addEventListener('click', () => { if (phase === 'running') pause(); else if (phase === 'paused') resume(); });
      el.stop.addEventListener('click', () => reset());
      el.veil.addEventListener('click', scheduleDim);
      el.rearm.addEventListener('click', () => {
        if (!['running', 'paused'].includes(phase)) return;
        const unlocking = unlockAudio();
        void unlocking.then(() => {
          audioNeedsRecovery = false;
          showNotice('');
          if (phase === 'running') void scheduleSounds();
          scheduleDim(); render();
        }).catch(() => {
          soundArmed = false;
          audioNeedsRecovery = true;
          showNotice('Le navigateur bloque les sons. Vérifie le volume média.');
          render();
        });
      });
      document.addEventListener('visibilitychange', () => {
        syncFieldAnimation();
        if (document.visibilityState === 'visible') {
          if (['running'].includes(phase)) {
            tick();
            void requestWakeLock();
            if (!soundArmed || audioContext?.state === 'suspended') {
              soundArmed = false;
              audioNeedsRecovery = true;
              hideVeil();
              showNotice('Le son peut avoir été suspendu : touche « Réactiver les sons ».');
            } else scheduleDim();
            render();
          }
        } else { hideVeil(); }
      });
      window.addEventListener('pageshow', (event) => { if (event.persisted) { tick(); if (['running'].includes(phase)) void requestWakeLock(); } });
      window.addEventListener('pagehide', () => { releaseWakeLock(); stopFieldAnimation(); });
      window.addEventListener('pageshow', syncFieldAnimation);
      fieldMotionPreference?.addEventListener?.('change', syncFieldAnimation);
      window.addEventListener('beforeunload', saveSession);
      // La PWA vérifie les mises à jour à l'ouverture et au retour au premier plan.
      // Jamais de rechargement automatique pendant une méditation.
      if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
        // Le nouveau service worker prend effet à la prochaine navigation.
        // Un rechargement forcé ici couperait l'introduction de la PWA.
        window.addEventListener('load', async () => {
          try {
            const registration = await navigator.serviceWorker.register('./sw.js', { updateViaCache: 'none' });
            const check = () => {
              if (navigator.onLine && document.visibilityState === 'visible') void registration.update().catch(() => {});
            };
            check();
            document.addEventListener('visibilitychange', check);
            window.addEventListener('online', check);
            setInterval(check, 60 * 60_000);
          } catch (_) { /* L'installation reste facultative */ }
        });
      }




      let cancelOpening = null;
      let openingHasPlayed = false;
      let lastHiddenAt = 0;

      function showOpening() {
        const body = document.body;
        if (cancelOpening) cancelOpening();
        if (phase !== 'idle' || document.visibilityState !== 'visible'
            || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
            || el.preferences.open) {
          body.classList.remove('is-opening', 'intro-go');
          return;
        }
        const brand = document.querySelector('.topbar .brand');
        const overlay = document.querySelector('.opening-overlay');
        if (!brand || !overlay) {
          body.classList.remove('is-opening', 'intro-go');
          return;
        }

        let done = false, delay = 0, safety = 0, frameA = 0, frameB = 0, travel = null;
        const cleanup = () => {
          if (done) return;
          done = true;
          clearTimeout(delay);
          clearTimeout(safety);
          cancelAnimationFrame(frameA);
          cancelAnimationFrame(frameB);
          window.removeEventListener('resize', cleanup);
          overlay.removeEventListener('pointerdown', cleanup);
          brand.removeEventListener('pointerdown', cleanup);
          travel?.cancel();
          brand.style.removeProperty('transform');
          body.classList.remove('is-opening', 'intro-go');
          if (cancelOpening === cleanup) cancelOpening = null;
        };
        cancelOpening = cleanup;
        overlay.addEventListener('pointerdown', cleanup, { once: true });
        brand.addEventListener('pointerdown', cleanup, { once: true });
        window.addEventListener('resize', cleanup, { once: true });

        try {
          // Le logo se positionne AVANT le premier rendu de l'interface.
          // L'écran de lancement natif Android disparaît au premier rendu ;
          // on laisse ensuite ce logo centré visible avant son déplacement.
          const rect = brand.getBoundingClientRect();
          const dx = document.documentElement.clientWidth / 2 - (rect.left + rect.right) / 2;
          const dy = window.innerHeight / 2 - (rect.top + rect.bottom) / 2;
          const initial = 'translate3d(' + dx + 'px, ' + dy + 'px, 0) scale(1.6)';
          brand.style.transform = initial;
          body.classList.add('is-opening', 'intro-go');
          openingHasPlayed = true;

          const begin = () => {
            if (done) return;
            if (document.visibilityState !== 'visible' || phase !== 'idle') {
              cleanup();
              return;
            }
            try {
              travel = brand.animate([
                { transform: initial },
                { transform: 'translate3d(0px, 0px, 0px) scale(1)' }
              ], {
                duration: 1800,
                easing: 'cubic-bezier(.42, 0, .22, 1)',
                fill: 'forwards'
              });
              travel.onfinish = cleanup;
            } catch (_) {
              cleanup();
            }
          };

          // Deux rendus + une courte présence statique pour éviter que le
          // système Android ne masque toute l'animation durant son propre splash.
          frameA = requestAnimationFrame(() => {
            frameB = requestAnimationFrame(() => {
              if (!done) delay = window.setTimeout(begin, 350);
            });
          });
          safety = window.setTimeout(cleanup, 2600);
        } catch (_) {
          cleanup();
        }
      }

      // Une PWA déjà en mémoire revient au premier plan sans recharger app.js.
      // Réanimer seulement après un vrai retour depuis l'arrière-plan, au repos.
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
          lastHiddenAt = Date.now();
          cancelOpening?.();
          return;
        }
        const installed = window.matchMedia?.('(display-mode: standalone)').matches
          || navigator.standalone === true;
        if (phase === 'idle' && !el.preferences.open
            && (!openingHasPlayed || (installed && lastHiddenAt
               && Date.now() - lastHiddenAt >= 3000))) {
          lastHiddenAt = 0;
          showOpening();
        }
      });

      recoverSession();
      renderSetup();
      render();
      document.documentElement.dataset.silenceReady = 'true';
      showOpening();
    })();
