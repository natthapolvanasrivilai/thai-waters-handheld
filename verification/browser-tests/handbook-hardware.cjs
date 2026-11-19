const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright-core');

const root = path.resolve(__dirname, '../..');
const handbook = path.resolve(process.argv[2] || path.join(root, 'docs/index.html'));
const getRows = String.raw`import csv,json,sys
with open(sys.argv[1], encoding="utf-8-sig", newline="") as stream:
    print(json.dumps(list(csv.DictReader(stream)), ensure_ascii=True))`;
const expected = JSON.parse(execFileSync(process.env.PYTHON || 'python', [
  '-c', getRows, path.join(root, 'sourcing/production-intent/R0009-prototype-budget.csv'),
], { encoding: 'utf8' }));
const expectedByRef = new Map(expected.map(part => [part.Ref, part]));
const repo = 'https://github.com/natthapolvanasrivilai/thai-waters-handheld/blob/';

function checkDestination(url, source, ref) {
  if (source.startsWith('https://')) {
    assert.equal(url, new URL(source).href, ref);
    return;
  }
  assert.ok(url.startsWith(repo), ref + ' should link to the private source tree');
  const [pathname, fragment] = source.split('#');
  const target = new URL(url);
  assert.ok(decodeURIComponent(target.pathname).endsWith('/' + pathname), ref);
  assert.equal(target.hash, fragment ? '#' + fragment : '', ref);
}

async function verifyTable(page) {
  const search = page.locator('#findPart');
  const select = page.locator('#partVariant');
  const table = page.locator('#bomGrid tbody tr');
  await page.locator('[data-tab=business]').click();
  await page.getByRole('heading', {name: 'One full R0009 prototype'}).waitFor();
  await search.waitFor({state:'visible'});
  assert.ok(await select.isVisible());
  assert.equal(await table.count(), expected.length);
  const visible = await table.evaluateAll(rows => rows.map(row => {
    const anchor = row.querySelector('a');
    return {
      ref: row.cells[0].textContent.split(' · ')[0],
      quantity: row.cells[2].textContent,
      text: anchor?.textContent.trim(),
      href: anchor?.href,
      visible: !!anchor?.getClientRects().length && getComputedStyle(anchor).visibility === 'visible',
      anchors: row.querySelectorAll('a').length,
    };
  }));
  assert.equal(new Set(visible.map(row => row.ref)).size, expected.length);
  for (const row of visible) {
    const part = expectedByRef.get(row.ref);
    assert.ok(part, row.ref);
    assert.equal(row.anchors, 1, row.ref);
    assert.ok(row.visible, row.ref);
    assert.ok(row.text.includes(part.mpn), row.ref + ' link should identify its exact part or process');
    assert.equal(row.quantity, part.qty + ' ' + part.UOM, row.ref);
    checkDestination(row.href, part.url, row.ref);
  }
  const groups = [...new Set(expected.map(row => row.group))];
  assert.deepEqual((await select.locator('option').allTextContents()).sort(), ['All', ...groups].sort());
  for (const group of groups) {
    await select.selectOption({label: group});
    const refs = expected.filter(row => row.group === group).map(row => row.Ref);
    assert.deepEqual(await table.evaluateAll(rows => rows.map(row => row.cells[0].textContent.split(' · ')[0])), refs);
    assert.equal(await page.locator('#partCount').textContent(), refs.length + ' lines');
  }
  await select.selectOption({label: 'All'});
  for (const [term, refs] of [['SDSQUNR-032-GN3MA', ['SD1']], ['W1/W4', ['C8']], ['BT2', ['BT2']], ['RC0603FR-072K7L', ['USB-R1']], ['no-such-part-12345', []]]) {
    await search.fill(term);
    assert.deepEqual(await table.evaluateAll(rows => rows.map(row => row.cells[0].textContent.split(' · ')[0])), refs, term);
  }
  await search.fill('3922');
  assert.deepEqual(await table.evaluateAll(rows => rows.map(row => row.cells[0].textContent.split(' · ')[0])), ['W2-B', 'W5']);
  await search.fill('');
  assert.equal(await table.count(), expected.length);
}

async function verifyElectrical(page) {
  const record = require(path.join(root, 'hardware/electronics/integration-r0004/verification.json'));
  await page.locator('[data-tab=circuits]').click();
  await page.getByRole('heading', {name: 'R0004 circuit verification'}).waitFor();
  const wave = page.locator('details').filter({has:page.getByText('Inspect the simulated USB recovery waveform', {exact:true})});
  await wave.locator('summary').click();
  assert.equal(await wave.locator('svg:visible polyline').count(), 2);
  await wave.locator('summary').click();
  const rows = page.locator('#gateRows tr:visible');
  assert.equal(await rows.count(), Object.values(record.candidate_metrics).reduce((a,b) => a+b, 0));
  await page.locator('#gateStatus').selectOption('OUTSIDE');
  assert.equal(await rows.count(), record.candidate_metrics.OUTSIDE);
  await page.locator('#gateStatus').selectOption('All');
  await page.locator('#gateSearch').fill('no_cell');
  assert.ok(await rows.count() > 0);
  assert.ok((await rows.allTextContents()).every(value => value.includes('no_cell')));
  await page.locator('#gateSearch').fill('');
}

(async () => {
  const launch = {headless: true};
  if (process.env.BROWSER_PATH) launch.executablePath = process.env.BROWSER_PATH;
  else if (process.platform === 'win32') launch.channel = 'msedge';
  const browser = await chromium.launch(launch);
  try {
    const page = await browser.newPage({viewport: {width: 1280, height: 800}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(pathToFileURL(handbook).href);
    await verifyTable(page);
    await verifyElectrical(page);
    await page.setViewportSize({width: 390, height: 844});
    await verifyTable(page);
    await verifyElectrical(page);
    assert.deepEqual(errors, []);
    console.log(`PASS ${expected.length} distinct BOM references, source labels, destinations, group filters, part search and visible links at desktop and phone widths, circuit dispositions, search and both recovery waveforms.`);
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
