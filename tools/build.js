#!/usr/bin/env node
/**
 * Preflight checks + aiot build wrapper.
 *   node tools/build.js          -> debug rpk
 *   node tools/build.js release  -> release rpk (needs sign/)
 */
const fs = require('fs')
const path = require('path')
const { spawnSync } = require('child_process')

const PROJ = path.resolve(__dirname, '..')
const SRC = path.join(PROJ, 'src')
const DIST = path.join(PROJ, 'dist')
const mode = process.argv[2] === 'release' ? 'release' : 'build'
const problems = []
const warns = []

function walk(dir, out) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name)
    const st = fs.statSync(p)
    if (st.isDirectory()) walk(p, out)
    else out.push(p)
  }
  return out
}

function stripComments(text) {
  return text.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1')
}

function preflight() {
  const pages = walk(path.join(SRC, 'pages'), []).filter((f) => f.endsWith('.ux'))
  for (const p of pages) {
    const raw = fs.readFileSync(p, 'utf8')
    const code = stripComments(raw)
    const rel = path.relative(PROJ, p)
    const hasData = /\bdata\s*:\s*\{/.test(code)
    const hasVis = /\b(public|protected|private)\s*:\s*\{/.test(code)
    if (hasData && hasVis) problems.push(`${rel}: 'data' 与 public/protected/private 同时存在（页面 VM 会建不起来）`)
    const m = code.match(/export\s+default\s*\{([\s\S]*?)\n\s*(protected|public|private)\s*:/)
    if (m && /^\s{2}\w+\s*:/m.test(m[1])) warns.push(`${rel}: export default 顶层有字面量属性，运行时不保证存在`)
    if (/\.jpg|\.jpeg/i.test(code)) problems.push(`${rel}: 引用了 JPEG（9 Pro 真机解码不可靠）`)
  }

  // manifest <-> about version
  const manifest = JSON.parse(fs.readFileSync(path.join(SRC, 'manifest.json'), 'utf8'))
  const about = fs.readFileSync(path.join(SRC, 'pages', 'about', 'about.ux'), 'utf8')
  const av = about.match(/ver:\s*['"]([^'"]+)['"]/)
  if (av && av[1] !== manifest.versionName) {
    problems.push(`about.ux 的版本 ${av[1]} 与 manifest ${manifest.versionName} 不一致`)
  }

  // story assets present
  const idxPath = path.join(SRC, 'common', 'story', 'index.txt')
  if (!fs.existsSync(idxPath)) { problems.push('缺少 common/story/index.txt'); return manifest }
  const idx = JSON.parse(fs.readFileSync(idxPath, 'utf8'))
  for (const ch of idx.chunks) {
    if (!fs.existsSync(path.join(SRC, 'common', 'story', ch.f))) problems.push('缺分块 ' + ch.f)
  }

  // image budget
  let imgBytes = 0
  let imgCount = 0
  const imgRoot = path.join(SRC, 'common', 'img')
  if (fs.existsSync(imgRoot)) {
    for (const f of walk(imgRoot, [])) {
      if (f.endsWith('.png')) { imgBytes += fs.statSync(f).size; imgCount++ }
    }
  }
  const mb = imgBytes / 1e6
  console.log(`图片: ${imgCount} 张, ${mb.toFixed(2)} MB (预算 16 MB)`)
  if (mb > 16) problems.push(`图片总量 ${mb.toFixed(2)} MB 超过 16 MB 预算`)

  return manifest
}

function main() {
  console.log(`== preflight (${mode}) ==`)
  const manifest = preflight()
  for (const w of warns) console.log('  warn  ' + w)
  if (problems.length) {
    for (const p of problems) console.log('  FAIL  ' + p)
    process.exit(1)
  }
  console.log('  ok')

  const temp = path.join(PROJ, '..', '.temp_' + path.basename(PROJ))
  const clean = () => { try { spawnSync('cmd', ['/c', 'rmdir', '/s', '/q', temp], { stdio: 'ignore' }) } catch (e) {} }
  clean()

  const cli = path.join(PROJ, 'node_modules', 'aiot-toolkit', 'lib', 'bin.js')
  if (!fs.existsSync(cli)) {
    console.log('aiot-toolkit 未安装：npm install')
    process.exit(2)
  }
  const args = [cli, mode].concat(process.argv.slice(3))
  const r = spawnSync(process.execPath, args, { cwd: PROJ, stdio: 'inherit' })
  if (r.status !== 0) console.log(`aiot 退出码 ${r.status}（Windows 上常见于清理临时目录，先检查 dist/）`)
  clean()

  // verify product
  if (!fs.existsSync(DIST)) { console.log('dist/ 不存在'); process.exit(3) }
  const rpks = fs.readdirSync(DIST).filter((f) => f.endsWith('.rpk'))
  for (const f of rpks) {
    const size = fs.statSync(path.join(DIST, f)).size
    console.log(`产物 ${f}  ${(size / 1e6).toFixed(2)} MB`)
    if (size > 10e6) console.log('  warn 包体超过 10 MB')
  }
  if (!rpks.length) { console.log('没有生成 rpk'); process.exit(4) }
}

main()
