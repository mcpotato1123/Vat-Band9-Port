// Design tokens — layout language borrowed from xuanyide01/steins-rw5,
// palette re-tinted to the original game's pink/beige.
export const C = {
  bg: '#141512',
  art: '#000000',
  panel: '#141512',
  card: '#292b23',
  slot: '#282921',
  slotEmpty: '#191a17',
  text: '#f0eee4',
  textStrong: '#ffffff',
  menu: '#e3e1cf',
  title: '#eeeadd',
  preview: '#d1cbb6',
  meta: '#b8ac8b',
  tag: '#a4a48e',
  muted: '#98aabd',
  disabled: '#64758a',
  accent: '#eb6877',
  accentSoft: '#f7dfce',
  goldBorder: '#b58132',
  slotBorder: '#a17c3b',
  optBorder: '#eb6877',
  divider: '#5a5949'
}

// 336 × 480, designWidth 336 → 1 css px = 1 physical px
export const W = 336
export const H = 480

export const TITLE_ART_H = 272
export const TITLE_ROW_H = 29
export const BTN_W = 116
export const BTN_H = 26

// scene area keeps the game's 16:9 framing: 336 x 189 centred in 252 px
export const PLAY_ART_H = 252
export const BG_W = 336
export const BG_H = 220
export const BG_TOP = 32

export const PANEL_TOP = 252
export const PANEL_H = 228
export const SPEAKER_TOP = 258
export const TEXT_TOP = 288
export const TEXT_W = 316
export const TEXT_PAD = 6
export const TEXT_H = 132
export const MAX_LINES = 6

export const LIST_TOP = 116
export const LIST_H = 300
export const SLOT_H = 84
export const SLOT_GAP = 8
export const SLOT_PER_PAGE = 4
