// Сценарні знімки екрана веб-застосунку (puppeteer-core + chrome-headless-shell).
// usage: node shots.mjs steps.json outDir [width=720] [scale=3]
// steps: [{goto:"/path"}, {login:"obu1"}, {select:["css", "value"]}, {fill:["css", "text"]},
//         {clickText:"Текст кнопки"}, {click:"css"}, {shot:"name"}, {eval:"js", key}, {gotoVar:key}], base URL in steps[0].base
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import puppeteer from 'puppeteer-core';

const [, , stepsFile, outDir, wArg = '720', sArg = '3'] = process.argv;
const steps = JSON.parse(fs.readFileSync(stepsFile, 'utf8'));
const base = steps.shift().base;

function findChrome() {
  const b = path.join(os.homedir(), '.cache/puppeteer/chrome-headless-shell');
  for (const v of fs.readdirSync(b)) {
    const p = path.join(b, v, 'chrome-headless-shell-linux64/chrome-headless-shell');
    if (fs.existsSync(p)) return p;
  }
  throw new Error('chrome-headless-shell not found');
}

const browser = await puppeteer.launch({ executablePath: findChrome(), args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.setViewport({ width: Number(wArg), height: 600, deviceScaleFactor: Number(sArg) });
const nav = (fn) => Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), fn()]);
const out = {};
for (const s of steps) {
  if (s.goto) await page.goto(base + s.goto, { waitUntil: 'networkidle0' });
  else if (s.gotoVar) await page.goto(base + out[s.gotoVar], { waitUntil: 'networkidle0' });
  else if (s.login) {
    await page.goto(base + '/logout', { waitUntil: 'networkidle0' });
    await page.select('#login', s.login);
    await nav(() => page.click('form button'));
  } else if (s.select) await page.select(s.select[0], s.select[1]);
  else if (s.fill) { await page.$eval(s.fill[0], (e) => { e.value = ''; }); await page.type(s.fill[0], s.fill[1]); }
  else if (s.click) await nav(() => page.click(s.click));
  else if (s.clickText) {
    const h = await page.evaluateHandle((t) => [...document.querySelectorAll('button, a.btn, a')]
      .find((e) => e.textContent.trim() === t), s.clickText);
    if (!h.asElement()) throw new Error('no element with text ' + s.clickText);
    await nav(() => h.asElement().click());
  } else if (s.eval) out[s.key || 'eval'] = await page.evaluate(s.eval);
  else if (s.shot) {
    const h = await page.evaluate(() => Math.ceil((document.querySelector('main') || document.body).getBoundingClientRect().bottom));
    await page.setViewport({ width: Number(wArg), height: h, deviceScaleFactor: Number(sArg) });
    await page.screenshot({ path: path.join(outDir, s.shot + '.png'), clip: { x: 0, y: 0, width: Number(wArg), height: h } });
    out[s.shot] = { url: page.url().replace(base, ''), cssHeight: h };
    await page.setViewport({ width: Number(wArg), height: 600, deviceScaleFactor: Number(sArg) });
  }
}
console.log(JSON.stringify(out));
await browser.close();
