// Vérifie le code exact de planification des sons sans accélérer ni simuler une vraie méditation.
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('meditation/app.js', 'utf8');
const match = source.match(/      function cueDates\(mode, start, minutes, now\) \{[\s\S]*?\n      \}\n      async function scheduleSounds/);
assert.ok(match, 'La fonction de programmation des repères doit exister.');
const context = vm.createContext({ MINUTE: 60_000 });
vm.runInContext(match[0].replace(/\n      async function scheduleSounds$/, '') + '\nthis.plan = cueDates;', context);
const plan = (mode, start, mins, now) => Array.from(context.plan(mode, start, mins, now));

for (const mins of [10, 12, 15, 20]) {
  assert.deepEqual(plan('fixed', 0, mins, 0), [mins * 60_000],
    'Durée fixe : un seul son, précisément à la fin.');
  assert.deepEqual(plan('fixed', 0, mins, mins * 60_000), [],
    'Pas de son supplémentaire après la fin.');
}
assert.deepEqual(plan('fixed', 0, 20, 10 * 60_000), [20 * 60_000],
  'Une séance de 20 min ne sonne PAS à 10 min.');
assert.deepEqual(plan('free', 0, 15, 0), [10, 20, 30, 40, 50, 60, 70, 80].map(n => n * 60_000),
  'Libre : toutes les 10 minutes sans fin automatique.');
assert.deepEqual(plan('free', 10_000, 15, 0),
  [10, 20, 30, 40, 50, 60, 70, 80].map(n => n * 60_000 + 10_000),
  'Départ différé : les dix minutes commencent réellement après le délai.');
assert.equal(plan('free', 0, 15, 20 * 60_000)[0], 30 * 60_000,
  'Ne pas rejouer le repère qui vient de sonner.');
assert.equal(plan('free', 0, 15, 58 * 60_000)[0], 60 * 60_000,
  'Renouvellement : le repère de 60 minutes est conservé.');
assert.equal(plan('free', 0, 15, 121 * 60_000)[0], 130 * 60_000,
  'Libre : fonctionne également au-delà de deux heures.');

// Après 7 minutes méditées puis une pause de 5 minutes, le prochain repère reste 3 minutes plus tard.
const resumedAt = 12 * 60_000;
const shiftedStart = resumedAt - 7 * 60_000;
assert.equal(plan('free', shiftedStart, 15, resumedAt)[0], 15 * 60_000,
  'Pause / reprise : le temps de pause ne compte pas.');
assert.ok(!source.includes('settings.marker') || source.includes('delete settings.marker'),
  'Le réglage supplémentaire historique ne doit plus produire de son.');
console.log('Repères audio : durée fixe unique, libre toutes les dix minutes, délai, pause et reprise : OK');
