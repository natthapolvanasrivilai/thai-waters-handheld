const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright-core');

const root = path.resolve(__dirname, '../..');
const handbook = pathToFileURL(path.resolve(process.argv[2] || path.join(root, 'docs/index.html'))).href;
const legacy = process.argv.includes('--legacy');
const guide = 'R0014-PCB-assembly.html';
const record = fs.readFileSync(path.join(root, 'docs/wiki/Current-status.md'), 'utf8');
const project = 'natthapolvanasrivilai/thai-waters-handheld';
const github = 'https://github.com/' + project;
const mark = '<!-- current-handbook -->';
const a = 'a'.repeat(40);
const b = 'b'.repeat(40);
function review(number, sha, fullName = project) {
  return {number, body: 'Engineering review\n\n' + mark, head: {sha, repo: {full_name: fullName}}};
}

(async () => {
  const launch = {headless: true};
  if (process.env.BROWSER_PATH) launch.executablePath = process.env.BROWSER_PATH;
  else if (process.platform === 'win32') launch.channel = 'msedge';
  const browser = await chromium.launch(launch);
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    let pulls = [review(98, a), review(124, b, 'other/fork')];
    let markdown = record;
    let rawStatus = 200;
    let apiStatus = 200;
    let offline = false;
    let secondPage = [];
    const unexpected = [];
    await page.route(/^https?:/, async route => {
      const url = new URL(route.request().url());
      const headers = {'access-control-allow-origin': '*', 'access-control-expose-headers': 'Link'};
      if (offline) {
        if (route.request().frame().parentFrame()) unexpected.push(url.href);
        return route.abort();
      }
      if (url.hostname === 'api.github.com' && url.pathname === '/repos/' + project + '/pulls') {
        const first = url.searchParams.get('page') === '1';
        if (first && secondPage.length) headers.link = '<https://api.github.com/>; rel="next"';
        return route.fulfill({status: apiStatus, headers, json: first ? pulls : secondPage});
      }
      if (url.hostname === 'api.github.com' && url.pathname === '/repos/' + project + '/commits') {
        return route.fulfill({headers, json: [{sha: b}]});
      }
      if (url.hostname === 'raw.githubusercontent.com' && [a, b].some(sha =>
        url.pathname === '/' + project + '/' + sha + '/docs/wiki/Current-status.md')) {
        return route.fulfill({status: rawStatus, headers, contentType: 'text/plain', body: markdown});
      }
      unexpected.push(url.href);
      return route.abort();
    });
    const check = page.locator('#handbook-check');
    const panel = page.locator('#handbook-record');
    async function settled() {
      await page.waitForFunction(() => document.getElementById('handbook-refresh')?.disabled === false);
    }
    async function retry() {
      await page.locator('#handbook-refresh').click();
      await settled();
    }
    async function saved() {
      await retry();
      assert.match(await check.innerText(), /Could not verify current status.*saved .*release record/);
      assert.doesNotMatch(await panel.innerText(), /Later owner observation/);
    }
    await page.goto(handbook);
    await settled();
    assert.ok(await page.locator('#current').isVisible());
    assert.match(await check.innerText(), /Checked GitHub .*open review #98/);
    assert.equal(await page.getByRole('link', {name:'Open review #98'}).getAttribute('href'), github + '/pull/98');
    assert.ok((await panel.locator('a').all()).length >= 4);
    const guideLink = panel.getByRole('link', {name: 'Download the standalone 3D PCB assembly guide'});
    assert.ok((await guideLink.getAttribute('href')).startsWith(github + '/releases/download/'));
    assert.ok((await guideLink.getAttribute('href')).endsWith('/' + guide));
    for (const link of await panel.locator('a').all()) {
      const dest = await link.getAttribute('href');
      assert.ok(dest.startsWith(github + '/'), dest);
      if (dest.includes('/blob/')) assert.ok(dest.includes('/blob/' + a + '/'), dest);
    }
    // The same downloaded file follows a new designated PR, including one on a subsequent results page.
    pulls = [review(200, a, 'other/fork')];
    secondPage = [review(218, b)];
    markdown = record + '\nLater owner observation\n';
    await page.reload();
    await settled();
    assert.match(await check.innerText(), /open review #218/);
    assert.match(await panel.innerText(), /Later owner observation/);
    secondPage = [];
    await retry();
    assert.match(await check.innerText(), /default branch/);
    assert.ok((await page.locator('#handbook-source').getAttribute('href')).includes('/blob/' + b + '/'));
    // A source, permission or network failure must never leave a previous success onscreen.
    pulls = [review(1, a), review(2, b)];
    await saved();
    pulls = [];
    rawStatus = 404;
    await saved();
    rawStatus = 200;
    markdown = '# Incomplete record';
    await saved();
    markdown = record + '\n[Untrusted destination](https://example.org/unrelated)\n';
    await saved();
    apiStatus = 403;
    await saved();
    apiStatus = 404;
    await saved();
    apiStatus = 200;
    offline = true;
    await saved();
    const assemblyTab = page.getByRole('button', {name: 'PCB assembly', exact: true});
    if (legacy) {
      assert.equal(await assemblyTab.count(), 0);
    } else {
      const frame = page.locator('#pcb-assembly-frame');
      assert.equal(await frame.getAttribute('src'), null);
      await assemblyTab.click();
      const model = page.frameLocator('#pcb-assembly-frame');
      await model.locator('#model').waitFor({state: 'visible'});
      const steps = model.locator('#steps');
      const stage = await steps.inputValue();
      await model.locator('#next').click();
      assert.notEqual(await steps.inputValue(), stage);
      assert.ok(await page.locator('#archive-note').isHidden());
      const blob = await frame.getAttribute('src');
      assert.equal(await page.locator('#pcb-assembly-open').getAttribute('href'), blob);
      const digest = await page.evaluate(async url => {
        const file = await (await fetch(url)).arrayBuffer();
        const hash = await crypto.subtle.digest('SHA-256', file);
        return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('');
      }, blob);
      const standalone = fs.readFileSync(path.join(root, 'docs/models', guide));
      assert.equal(digest, createHash('sha256').update(standalone).digest('hex'));
    }
    await page.locator('[data-tab=business]').click();
    await page.locator('#archive-note').waitFor({state: 'visible'});
    assert.ok(await page.locator('#findPart').isVisible());
    await page.locator('[data-tab=assembly]').click();
    const archived = page.frameLocator('#viewer');
    await archived.locator('html[data-ready="true"]').waitFor({state: 'attached'});
    const archivedStep = await archived.locator('#stepTitle').innerText();
    await archived.getByRole('button', {name: 'Next assembly stage'}).click();
    await archived.locator('#stepTitle').filter({hasText: archivedStep}).waitFor({state: 'hidden'});
    await page.locator('#archive-note a').click();
    await page.locator('#archive-note').waitFor({state: 'hidden'});
    await page.setViewportSize({width: 390, height: 844});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 2));
    assert.deepEqual(unexpected, []);
    assert.deepEqual(errors, []);
    console.log('PASS live source selection, current assembly download, offline fallback, archive navigation and mobile width. ' +
      (legacy ? 'Verified previous reader.' : 'Verified interactive offline PCB tab and exact standalone bytes.'));
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
