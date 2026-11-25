// Render the deck: dashboard screenshot for slide 8, one PNG per slide, and a PDF.
//   node render.cjs [--skip-dashboard]
// Needs the local server: python -m http.server 3590 in flagged-accounts-q3-2026.
const path = require('path'), fs = require('fs')
const { chromium } = require('C:/Users/arjun/Music/Documents/Desktop/Website/mathboard/node_modules/playwright-core')
const BASE = 'http://localhost:3590'
const OUT = path.resolve(__dirname, 'slides')

;(async () => {
  fs.mkdirSync(OUT, { recursive: true })
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, args: ['--hide-scrollbars'] })
  const errors = []

  if (!process.argv.includes('--skip-dashboard')) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 780 }, deviceScaleFactor: 2 })
    const page = await ctx.newPage()
    await page.goto(BASE + '/dashboard/', { waitUntil: 'networkidle' })
    await page.getByText('every row has a score and a reason').waitFor()
    await page.evaluate(() => {
      const i = document.getElementById('account-input'); i.value = 'ACC-10832'
      document.getElementById('lookup-form').requestSubmit(); i.blur(); window.scrollTo(0, 0)
    })
    await page.waitForTimeout(400)
    await page.screenshot({ path: path.join(__dirname, 'dashboard.png') })
    console.log('dashboard.png saved')
    await ctx.close()
  }

  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 })
  const page = await ctx.newPage()
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 200)) })
  page.on('pageerror', e => errors.push(e.message))
  await page.goto(BASE + '/deck/?print', { waitUntil: 'networkidle' })
  await page.evaluate(() => document.fonts.ready)
  await page.waitForTimeout(600)
  const stages = page.locator('.stage')
  const n = await stages.count()
  for (let k = 0; k < n; k++) {
    await stages.nth(k).screenshot({ path: path.join(OUT, `slide-${String(k + 1).padStart(2, '0')}.png`) })
  }
  // clipping probe: vertical overflow anywhere inside a slide
  const clipped = await page.evaluate(() => [...document.querySelectorAll('.stage')].map((st, k) => {
    const pad = st.querySelector('.pad'); const r = pad.getBoundingClientRect()
    const foot = pad.querySelector('.foot'), body = pad.querySelector('.body')
    const limit = foot && body ? foot.getBoundingClientRect().top - 4 : r.bottom
    const scope = body || pad
    const out = [...scope.querySelectorAll('*')].filter(el => { const b = el.getBoundingClientRect(); return b.height && (b.bottom > limit + 1 || b.right > r.right + 1) })
    return out.length ? `slide ${k + 1}: ${out.slice(0, 3).map(e => e.tagName + '.' + e.className).join(', ')}` : null
  }).filter(Boolean))
  await page.pdf({ path: path.join(__dirname, 'q3-call-list-deck.pdf'), width: '1600px', height: '900px', printBackground: true })
  console.log(`${n} slides + PDF saved`, clipped.length ? 'OVERFLOW: ' + clipped.join(' | ') : 'no overflow', errors.length ? 'ERRORS: ' + errors.join(' | ') : '')
  await browser.close()
})().catch(e => { console.error('FAILED', e.message); process.exit(1) })
