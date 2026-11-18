/* silence. : dix repères originaux, générés localement et disponibles hors ligne.
 * Attaques progressives, fondamentales médium et harmoniques discrètes.
 * Aucune fréquence n'est présentée comme ayant un effet thérapeutique.
 */
(() => {
  'use strict';
  const tones = Object.freeze({
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
  function createBuffer(context, name) {
    const tone=tones[name];
    if (!tone) throw new Error('Repère inconnu : ' + name);
    const rate=context.sampleRate;
    const total=Math.ceil(tone.duration*rate);
    const buffer=context.createBuffer(1,total,rate);
    const samples=buffer.getChannelData(0);
    const tau=2*Math.PI;
    const endFade=.38;
    for (const [start,frequency,weight] of tone.notes) {
      for (let i=Math.ceil(start*rate);i<total;i++) {
        const t=i/rate-start;
        const rise=Math.sin(Math.PI/2*Math.min(1,t/tone.attack))**2;
        const decay=Math.exp(-t/tone.decay);
        const tail=Math.sin(Math.PI/2*Math.min(1,Math.max(0,(tone.duration-i/rate)/endFade)))**2;
        const breathe=1-tone.flutter*(1-Math.cos(tau*1.15*t));
        const fundamental=Math.sin(tau*frequency*t);
        const second=tone.h2*Math.sin(tau*2*frequency*t+.18);
        const third=tone.h3*Math.sin(tau*3*frequency*t+.38);
        samples[i]+=weight*rise*decay*tail*breathe*(fundamental+second+third);
      }
    }
    let peak=0;
    for (const sample of samples) peak=Math.max(peak,Math.abs(sample));
    const normalize=.80/Math.max(.0001,peak);
    for (let i=0;i<samples.length;i++) samples[i]*=normalize;
    return buffer;
  }
  window.SilenceSoftTones=Object.freeze({tones,createBuffer});
})();