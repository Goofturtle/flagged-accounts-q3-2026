// Capture the real product shots used in the deck.
//   node shots.cjs            -> deck/shots/*.png
// Needs the local server (python -m http.server 3590 in flagged-accounts-q3-2026).
const path = require('path'), fs = require('fs')
const { chromium } = require('C:/Users/arjun/Music/Documents/Desktop/Website/mathboard/node_modules/playwright-core')
const OUT = path.resolve(__dirname, 'shots')
const SHEET = 'https://docs.google.com/spreadsheets/d/1iGSvshfq0duZX7YIIByxbNwJYSdMqWXHZJoRLZ7vsmw/edit?gid=0'

async function dash(browser, name, js, w = 1440, h = 900) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2 })
  const page = await ctx.newPage()
  await page.goto('http://localhost:3590/dashboard/', { waitUntil: 'networkidle' })
  await page.getByText('every row has a score and a reason').waitFor()
  await page.evaluate(js)
  await page.waitForTimeout(500)
  await page.screenshot({ path: path.join(OUT, name + '.png') })
  console.log(name, 'saved')
  await ctx.close()
}

;(async () => {
  fs.mkdirSync(OUT, { recursive: true })
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, args: ['--hide-scrollbars'] })
  const lookup = id => `(() => { const i = document.getElementById('account-input'); i.value = '${id}'; document.getElementById('lookup-form').requestSubmit(); i.blur(); window.scrollTo(0, 0) })()`
  await dash(browser, 'dash-free', lookup('ACC-10832'))
  await dash(browser, 'dash-paying', lookup('ACC-10070'))
  await dash(browser, 'dash-list', `(() => { const s = document.getElementById('f-band'); s.value = 'Call now'; s.dispatchEvent(new Event('change')); document.querySelector('.panel + .panel').scrollIntoView(); window.scrollBy(0, -24) })()`)

  // the real Google Sheet, opened anonymously through its view link
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2, locale: 'en-US' })
  const page = await ctx.newPage()
  await page.goto(SHEET, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(7000)
  await page.keyboard.press('Escape'); await page.keyboard.press('ArrowDown'); await page.keyboard.press('ArrowDown')
  await page.mouse.move(5, 880); await page.waitForTimeout(800)
  await page.screenshot({ path: path.join(OUT, 'sheet.png') })
  console.log('sheet saved; title:', await page.title())
  await browser.close()
})().catch(e => { console.error('FAILED', e.message); process.exit(1) })
