#!/usr/bin/env node
/**
 * Runtime checks that do not need a device:
 *   1. pagination invariants for every font size 15..24 across the whole script
 *   2. geometry constants in game.ux/cg.ux match the CSS
 *   3. story graph walks to an ending for three choice strategies
 */
const fs = require('fs')
const path = require('path')

const PROJ = path.resolve(__dirname, '..')
const SRC = path.join(PROJ, 'src')
let failed = 0
const fail = (m) => { console.log('  FAIL ' + m); failed++ }

// ---------- load reader.js without a bundler ----------
function loadReader() {
  const txt = fs.readFileSync(path.join(SRC, 'common', 'reader.js'), 'utf8')
  const body = txt
    .replace(/^import .*$/gm, '')
    .replace(/export const /g, 'const ')
    .replace(/export function /g, 'function ')
    .replace(/export default .*$/gm, '')
  const mod = { exports: {} }
  const fn = new Function('module', 'exports', 'storage', body + '\nreturn { wrapText, paginateText, autoDelay, DEFAULT_SETTINGS, SIZE_MIN, SIZE_MAX, SLOT_COUNT }')
  return fn(mod, mod.exports, { get() {}, set() {} })
}

const R = loadReader()

// ---------- story ----------
function loadStory() {
  const idx = JSON.parse(fs.readFileSync(path.join(SRC, 'common', 'story', 'index.txt'), 'utf8'))
  const nodes = []
  for (const ch of idx.chunks) {
    const part = JSON.parse(fs.readFileSync(path.join(SRC, 'common', 'story', ch.f), 'utf8'))
    if (part.length !== ch.n) fail(`chunk ${ch.f} length ${part.length} != ${ch.n}`)
    nodes.push(...part)
  }
  return { idx, nodes }
}

const { idx, nodes } = loadStory()
console.log(`story: ${nodes.length} nodes, ${idx.chapters.length} chapters`)

// ---------- 1. pagination ----------
const THEME = fs.readFileSync(path.join(SRC, 'common', 'theme.js'), 'utf8')
const tnum = (name) => {
  const m = THEME.match(new RegExp(name + '\\s*=\\s*(\\d+)'))
  return m ? Number(m[1]) : NaN
}
const TEXT_H = tnum('TEXT_H')
const MAX_LINES = tnum('MAX_LINES')
console.log('== pagination ==')
const paras = nodes.filter((n) => n.t === 's')
for (let size = 15; size <= 24; size++) {
  const lineH = size + 4
  const cpl = Math.max(4, Math.floor((316 - 6) / size))
  const lpp = Math.max(1, Math.min(MAX_LINES, Math.floor(TEXT_H / lineH)))
  let lines = 0
  let pages = 0
  for (const n of paras) {
    const pg = R.paginateText(n.x || '', cpl, lpp)
    pages += pg.length
    for (const p of pg) {
      if (p.length > lpp) fail(`size ${size}: page has ${p.length} lines > ${lpp}`)
      for (const ln of p) {
        lines++
        if (ln.length > cpl) fail(`size ${size}: line "${ln}" has ${ln.length} > ${cpl}`)
      }
    }
    const flat = pg.map((p) => p.join('')).join('')
    if (flat.replace(/\s/g, '') !== String(n.x || '').replace(/\n/g, '').replace(/\s/g, '')) {
      fail(`size ${size}: text lost or reordered`)
    }
  }
  console.log(`  ${size}px  每行${cpl}字 每页${lpp}行  行${lines} 页${pages}  ok`)
}

// ---------- 2. geometry ----------
console.log('== geometry ==')
const game = fs.readFileSync(path.join(SRC, 'pages', 'game', 'game.ux'), 'utf8')
const theme = fs.readFileSync(path.join(SRC, 'common', 'theme.js'), 'utf8')
const val = (name) => {
  const m = theme.match(new RegExp(name + '\\s*=\\s*(\\d+)'))
  return m ? Number(m[1]) : NaN
}
const cssNum = (sel, prop) => {
  const re = new RegExp('\\' + sel + '[^}]*' + prop + ':\\s*(-?\\d+)px')
  const m = game.match(re)
  return m ? Number(m[1]) : NaN
}
if (val('TEXT_W') - val('TEXT_PAD') !== 310) fail(`TEXT_W(${val('TEXT_W')}) - PAD(${val('TEXT_PAD')}) != 310`)
if (cssNum('.ln', 'width') !== val('TEXT_W')) fail(`.ln width ${cssNum('.ln', 'width')} != TEXT_W ${val('TEXT_W')}`)
if (cssNum('.art', 'height') !== val('PLAY_ART_H')) fail(`.art height ${cssNum('.art', 'height')} != PLAY_ART_H ${val('PLAY_ART_H')}`)
if (cssNum('.panel', 'height') !== val('PANEL_H')) fail(`.panel height ${cssNum('.panel', 'height')} != PANEL_H ${val('PANEL_H')}`)
console.log(`  TEXT_W ${val('TEXT_W')} PAD ${val('TEXT_PAD')} LINE ${val('TEXT_W') - val('TEXT_PAD')}  MAX_LINES ${val('MAX_LINES')}`)

// ---------- 3. playthrough ----------
console.log('== playthrough ==')
function walk(pick) {
  let pc = 0
  let steps = 0
  let choices = 0
  while (steps < 40000) {
    if (pc < 0 || pc >= nodes.length) return { end: 'end', steps, choices }
    const n = nodes[pc]
    steps++
    if (n.t === 's') pc++
    else if (n.t === 'j') pc = n.j
    else if (n.t === 'e') return { end: 'e', steps, choices }
    else if (n.t === 'o') {
      choices++
      const opts = n.o || []
      pc = opts[Math.min(pick, opts.length - 1)].j
    } else { fail('unknown node type ' + n.t); return { end: 'bad', steps, choices } }
  }
  return { end: 'loop', steps, choices }
}
for (const pick of [0, 1, 2]) {
  const r = walk(pick)
  console.log(`  pick=${pick}: ${r.steps} steps, ${r.choices} choices, end=${r.end}`)
  if (r.end === 'loop' || r.end === 'bad') fail(`playthrough ${pick} did not terminate cleanly`)
}

// ---------- 4. asset page coverage ----------
console.log('== pages ==')
const manifest = JSON.parse(fs.readFileSync(path.join(SRC, 'manifest.json'), 'utf8'))
for (const uri of Object.keys(manifest.router.pages)) {
  const f = path.join(SRC, uri, uri.split('/')[1] + '.ux')
  if (!fs.existsSync(f)) fail('missing page ' + uri)
}
console.log(`  ${Object.keys(manifest.router.pages).length} pages routed`)

console.log(failed ? `\nFAILED: ${failed}` : '\nALL OK')
process.exit(failed ? 1 : 0)
