import storage from '@system.storage'

// ---------- storage ----------
export function readJSON(key, fallback, done) {
  storage.get({
    key: key,
    default: '',
    success: (v) => {
      if (!v) return done(fallback)
      try { done(JSON.parse(v)) } catch (e) { done(fallback) }
    },
    fail: () => done(fallback)
  })
}

export function writeJSON(key, value, done) {
  storage.set({
    key: key,
    value: JSON.stringify(value),
    success: () => { if (done) done(true) },
    fail: () => { if (done) done(false) }
  })
}

// ---------- settings ----------
export const DEFAULT_SETTINGS = {
  size: 18,
  speed: 26,
  autoMs: 0,
  fast: false,
  keepOn: true,
  longpress: 'on',
  anim: true
}
export const SIZE_MIN = 15
export const SIZE_MAX = 24
export const SPEED_MIN = 0
export const SPEED_MAX = 120
export const AUTO_MIN = 0
export const AUTO_MAX = 200
export const SLOT_COUNT = 30

function clampInt(v, lo, hi, dflt) {
  const n = parseInt(v, 10)
  if (isNaN(n)) return dflt
  return Math.max(lo, Math.min(hi, n))
}

export function normalizeSettings(s) {
  const o = s || {}
  return {
    size: clampInt(o.size, SIZE_MIN, SIZE_MAX, DEFAULT_SETTINGS.size),
    speed: clampInt(o.speed, SPEED_MIN, SPEED_MAX, DEFAULT_SETTINGS.speed),
    autoMs: clampInt(o.autoMs, AUTO_MIN, AUTO_MAX, DEFAULT_SETTINGS.autoMs),
    fast: false,
    keepOn: o.keepOn === undefined ? true : !!o.keepOn,
    longpress: o.longpress === 'off' ? 'off' : 'on',
    anim: o.anim === undefined ? true : !!o.anim
  }
}

export function loadSettings(done) {
  readJSON('settings', DEFAULT_SETTINGS, (s) => done(normalizeSettings(s)))
}

export function saveSettings(s) {
  const t = normalizeSettings(s)
  delete t.fast
  writeJSON('settings', t)
}

// ---------- layout / pagination ----------
// Every line is measured in characters, so text can never soft-wrap on device.
export function wrapText(text, cpl) {
  const src = String(text === undefined || text === null ? '' : text)
  const out = []
  const paras = src.split('\n')
  for (let p = 0; p < paras.length; p++) {
    let line = paras[p]
    while (line.length > cpl) {
      let cut = cpl
      // look back up to 8 chars for a break after punctuation
      for (let k = 0; k < 8; k++) {
        const ch = line.charAt(cpl - 1 - k)
        if ('，。！？；：、）」』…—'.indexOf(ch) >= 0) { cut = cpl - k; break }
      }
      if (cut <= 0) cut = cpl
      out.push(line.slice(0, cut))
      line = line.slice(cut)
    }
    out.push(line)
  }
  return out
}

export function paginateText(text, cpl, lpp) {
  const lines = wrapText(text, cpl)
  const pages = []
  for (let i = 0; i < lines.length; i += lpp) pages.push(lines.slice(i, i + lpp))
  if (!pages.length) pages.push([''])
  return pages
}

export function autoDelay(text, autoMs) {
  const len = String(text || '').length
  const d = 700 + len * autoMs
  return Math.max(1200, Math.min(12000, d))
}

// ---------- save slots ----------
export function loadSaves(done) {
  readJSON('saves', [], (list) => {
    const out = []
    for (let i = 0; i < SLOT_COUNT; i++) out.push(list[i] || null)
    done(out)
  })
}

export function saveSaves(list, done) {
  writeJSON('saves', list, done)
}
