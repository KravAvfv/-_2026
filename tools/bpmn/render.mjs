// Render a BPMN 2.0 file (with DI) to SVG + high-DPI PNG using the bpmn.io reference renderer (bpmn-js)
// inside the Chrome Headless Shell already installed for mermaid-cli.
// Usage: node tools/bpmn/render.mjs <in.bpmn> <out.svg> <out.png> [scale=3] [fontPx=16]
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const here = path.dirname(fileURLToPath(import.meta.url));
const [, , inFile, outSvg, outPng, scaleArg = '3', fontArg = '16'] = process.argv;
if (!inFile || !outSvg || !outPng) {
  console.error('usage: render.mjs in.bpmn out.svg out.png [scale] [fontPx]');
  process.exit(2);
}
const scale = Number(scaleArg);
const fontPx = Number(fontArg);

function findChrome() {
  const base = path.join(os.homedir(), '.cache/puppeteer/chrome-headless-shell');
  for (const v of fs.readdirSync(base)) {
    const p = path.join(base, v, 'chrome-headless-shell-linux64/chrome-headless-shell');
    if (fs.existsSync(p)) return p;
  }
  throw new Error('chrome-headless-shell not found in ' + base);
}

const xml = fs.readFileSync(inFile, 'utf8');
const dist = path.join(here, 'node_modules/bpmn-js/dist');
const css = ['assets/diagram-js.css', 'assets/bpmn-js.css']
  .map(f => fs.readFileSync(path.join(dist, f), 'utf8')).join('\n');
const viewerJs = fs.readFileSync(path.join(dist, 'bpmn-viewer.production.min.js'), 'utf8');

const html = `<!doctype html><html><head><meta charset="utf-8"><style>${css}
html,body{margin:0;padding:0;background:#fff}
#c{width:6000px;height:4000px}
</style></head><body><div id="c"></div></body></html>`;

const browser = await puppeteer.launch({ executablePath: findChrome(), args: ['--no-sandbox'] });
try {
  const page = await browser.newPage();
  await page.setContent(html);
  await page.addScriptTag({ content: viewerJs });
  const svg = await page.evaluate(async (xml, fontPx) => {
    const viewer = new BpmnJS({
      container: '#c',
      textRenderer: {
        defaultStyle: { fontFamily: 'Times New Roman', fontSize: fontPx, lineHeight: 1.15, fontWeight: 'normal' },
        externalStyle: { fontFamily: 'Times New Roman', fontSize: fontPx - 1, lineHeight: 1.15 },
      },
      bpmnRenderer: { defaultFillColor: '#ffffff', defaultStrokeColor: '#000000', defaultLabelColor: '#000000' },
    });
    const res = await viewer.importXML(xml);
    if (res.warnings && res.warnings.length) {
      console.warn('BPMN import warnings: ' + res.warnings.map(w => w.message).join(' | '));
    }
    const { svg } = await viewer.saveSVG();
    return svg;
  }, xml, fontPx);
  fs.writeFileSync(outSvg, svg);
  // rasterise the exported SVG at `scale` for print
  const m = svg.match(/viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"/);
  const w = Math.ceil(Number(m[3])), h = Math.ceil(Number(m[4]));
  const p2 = await browser.newPage();
  await p2.setViewport({ width: w, height: h, deviceScaleFactor: scale });
  await p2.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#fff}svg{display:block}</style></head><body>${svg}</body></html>`);
  await p2.screenshot({ path: outPng, clip: { x: 0, y: 0, width: w, height: h } });
  console.log(JSON.stringify({ width: w, height: h, scale }));
} finally {
  await browser.close();
}
