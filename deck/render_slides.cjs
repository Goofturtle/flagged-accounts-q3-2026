// Render each 1920x1080 section of slides.html to deck/out/slide-NN.png at 2560x1440, plus notes.json.
const path = require('path'), fs = require('fs')
const { chromium } = require('C:/Users/arjun/Music/Documents/Desktop/Website/mathboard/node_modules/playwright-core')
const OUT = path.resolve(__dirname, 'out')

;(async () => {
  fs.mkdirSync(OUT, { recursive: true })
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, args: ['--hide-scrollbars'] })
  const page = await (await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 4 / 3 })).newPage()
  const errors = []
  page.on('pageerror', e => errors.push(e.message))
  page.on('requestfailed', r => errors.push('failed ' + r.url()))
  await page.goto('http://localhost:3590/deck/slides.html', { waitUntil: 'networkidle' })
  await page.evaluate(() => document.fonts.ready)
  await page.waitForTimeout(500)
  const secs = page.locator('section.s')
  const n = await secs.count(), notes = []
  for (let k = 0; k < n; k++) {
    const s = secs.nth(k)
    await s.screenshot({ path: path.join(OUT, `slide-${String(k + 1).padStart(2, '0')}.png`) })
    notes.push(await s.getAttribute('data-notes'))
  }
  // text that runs past the slide edge or into the footer line (images and windows may bleed on purpose)
  const issues = await page.evaluate(() => [...document.querySelectorAll('section.s')].map((s, k) => {
    const r = s.getBoundingClientRect(), src = s.querySelector('.src, .pg'), lim = src ? src.getBoundingClientRect().top - 6 : r.bottom
    const bad = [...s.querySelectorAll('h1,h2,.sub,.big,.feat,.lc,.stepc,.legend,.sig,.callout')].filter(e => {
      const b = e.getBoundingClientRect(); return b.right > r.right + 1 || b.bottom > lim || b.left < r.left - 1 })
    return bad.length ? `slide ${k + 1}: ${bad.slice(0, 4).map(e => e.tagName + '.' + e.className).join(', ')}` : null
  }).filter(Boolean))
  fs.writeFileSync(path.join(OUT, 'notes.json'), JSON.stringify(notes, null, 1))
  console.log(`${n} slides`, issues.length ? 'ISSUES: ' + issues.join(' | ') : 'no text collisions', errors.length ? 'ERRORS: ' + errors.join(' | ') : '')
  await browser.close()
})().catch(e => { console.error('FAILED', e.message); process.exit(1) })
