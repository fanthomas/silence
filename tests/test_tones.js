// Tests de la palette : 10 timbres, attaque sans choc, crêtes plafonnées et fin sans clic.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
// Vérifie le vrai moteur de production, sans script audio externe.
const app=fs.readFileSync('meditation/app.js','utf8');
const from=app.indexOf('const SOFT_TONES = Object.freeze({');
const to=app.indexOf('const SOUND_NAMES =',from);
assert.ok(from>=0&&to>from,'Palette intégrée au moteur principal');
const context={};
vm.runInNewContext(app.slice(from,to)+'\nthis.__lib={tones:SOFT_TONES,createBuffer:createSoftToneBuffer};',context);
const lib=context.__lib;
assert.ok(!app.includes('window.SilenceSoftTones'),'No dependent secondary script');
assert.ok(lib);
const ids=Object.keys(lib.tones);
assert.equal(ids.length,10);
const rate=24000;
const fake={
 sampleRate:rate,
 createBuffer(channels,length,sr){
   assert.equal(channels,1);
   assert.equal(sr,rate);
   const samples=new Float32Array(length);
   return {length,numberOfChannels:channels,duration:length/sr,sampleRate:sr,getChannelData(){return samples;}};
 }
};
const fingerprints=new Set();
for(const name of ids){
 const buffer=lib.createBuffer(fake,name);
 assert.ok(buffer.duration>=3.4&&buffer.duration<=4.2,name+' duration');
 const samples=buffer.getChannelData(0);
 let peak=0,energy=0,startEnergy=0;
 for(let i=0;i<samples.length;i++){
   const v=samples[i];
   assert.ok(Number.isFinite(v),name+' nonfinite sample');
   peak=Math.max(peak,Math.abs(v));
   energy+=v*v;
   if(i<rate*.035)startEnergy+=v*v;
 }
 const rms=Math.sqrt(energy/samples.length);
 const onset=Math.sqrt(startEnergy/(rate*.035));
 assert.ok(peak>.78&&peak<=.801,name+' peak='+peak);
 assert.ok(rms>.065&&rms<.40,name+' rms='+rms);
 assert.ok(onset<rms*.32,name+' abrupt onset '+onset);
 assert.ok(Math.abs(samples[0])<.000001,name+' start click');
 assert.ok(Math.abs(samples[samples.length-1])<.0001,name+' end click');
 fingerprints.add(samples[Math.floor(rate*.31)].toFixed(3)+':'+samples[Math.floor(rate*.62)].toFixed(3));
}
assert.equal(fingerprints.size,10,'The ten signals must be distinct');
console.log('Palette sonore : dix timbres originaux et doux, durées/crêtes/enveloppes vérifiées.');
