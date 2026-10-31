// Run after build:web. Uses mock API responses, not a live backend.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright-core');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../dist');
const server = http.createServer((req, res) => {
  let file = path.resolve(root, '.' + new URL(req.url, 'http://localhost').pathname);
  if (!file.startsWith(root + path.sep) && file !== root) { res.writeHead(403).end(); return; }
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(root, 'index.html');
  res.setHeader('Content-Type', file.endsWith('.js') ? 'application/javascript' : file.endsWith('.html') ? 'text/html' : 'application/octet-stream');
  res.end(fs.readFileSync(file));
});
function wav() {
  const buffer = Buffer.alloc(44 + 8000);
  buffer.write('RIFF'); buffer.writeUInt32LE(buffer.length - 8, 4); buffer.write('WAVEfmt ', 8);
  buffer.writeUInt32LE(16, 16); buffer.writeUInt16LE(1, 20); buffer.writeUInt16LE(1, 22);
  buffer.writeUInt32LE(8000, 24); buffer.writeUInt32LE(16000, 28); buffer.writeUInt16LE(2, 32); buffer.writeUInt16LE(16, 34);
  buffer.write('data', 36); buffer.writeUInt32LE(8000, 40); return buffer;
}
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  let page;
  try {
    browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}) });
    page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    let reviews = []; let searchSeen = false; let localAudio = 0; let tts = 0; let failSave = false;
    const word = { id: 1, simplified: '你好', traditional: '你好', pinyin: 'nǐ hǎo', definitions: ['hello'], hsk_level: 'HSK1', audio_path: '/api/v1/audio/hsk1/你好.mp3' };
    await page.route('**/translate_tts?**', route => { tts++; return route.fulfill({ contentType: 'audio/wav', body: wav() }); });
    await page.route('http://localhost:8000/**', async route => {
      const request = route.request(); const url = new URL(request.url());
      const send = data => route.fulfill({ contentType: 'application/json', body: JSON.stringify(data) });
      if (url.pathname.includes('/audio/')) { localAudio++; return route.fulfill({ status: 404, body: '' }); }
      if (url.pathname.endsWith('/auth/me')) return send({ id: 1, username: 'Student', email: 'test@example.com', hsk_level: 'HSK1', xp: reviews.length * 5, streak_days: 2 });
      if (url.pathname.endsWith('/review') && request.method() === 'POST') {
        if (failSave) return route.fulfill({ status: 500, body: '{}' });
        reviews.push(request.postDataJSON()); return send({ word_id: 1, next_review: '2026-11-07T10:00:00Z', interval_days: 6, xp_gained: 5 });
      }
      if (url.pathname.endsWith('/review')) return send([word]);
      if (url.pathname.endsWith('/progress')) return send({ user_xp: 5, streak_days: 2, levels: { HSK1: { total: 150, learned: 42, due_for_review: 8 }, HSK2: { total: 0, learned: 0, due_for_review: 0 } } });
      if (url.pathname.endsWith('/words')) {
        const search = url.searchParams.get('search'); searchSeen ||= search === 'hello';
        const skip = Number(url.searchParams.get('skip'));
        const words = search === 'nothing' ? [] : skip ? [{ ...word, id: 21, simplified: '再见' }] : [{ ...word, audio_path: null }];
        return send({ total: search === 'nothing' ? 0 : 21, skip, limit: 20, words });
      }
      return route.fulfill({ status: 404, body: '{}' });
    });
    await page.addInitScript(() => { localStorage.setItem('access_token', 'test-access'); localStorage.setItem('refresh_token', 'test-refresh'); });
    const origin = `http://127.0.0.1:${server.address().port}`;
    await page.goto(origin);
    await page.getByText('Browse vocabulary', { exact: true }).waitFor();
    await page.getByText('Start review', { exact: true }).click();
    await page.getByRole('button', { name: 'Reveal answer for 你好' }).click();
    await page.getByText('nǐ hǎo', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Listen', exact: true }).click();
    await page.getByText('Synthetic pronunciation · Google TTS').waitFor();
    assert.equal(localAudio, 1); assert.equal(tts, 1);
    await page.getByRole('button', { name: '5 · Perfect recall', exact: true }).click();
    await page.getByText('Session complete', { exact: true }).waitFor();
    assert.deepEqual(reviews, [{ word_id: 1, quality: 5 }]);
    await page.goto(origin + '/progress');
    await page.getByText('42 / 150 words learned').waitFor();
    assert.equal(await page.getByRole('progressbar', { name: 'HSK1 words learned' }).getAttribute('aria-valuenow'), '28');
    assert.equal(await page.getByRole('progressbar', { name: 'HSK2 words learned' }).getAttribute('aria-valuenow'), '0');
    await page.goto(origin + '/vocabulary');
    await page.getByLabel('Search vocabulary').fill('hello');
    await page.waitForResponse(r => r.url().includes('search=hello'));
    await page.getByRole('button', { name: 'Next', exact: true }).click();
    await page.getByText('再见', { exact: true }).waitFor();
    assert.equal(searchSeen, true);
    await page.getByLabel('Search vocabulary').fill('nothing');
    await page.getByText('No matching words. Try another search or level.').waitFor();
    await page.getByLabel('Search vocabulary').fill('hello');
    await page.getByText('你好', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Listen', exact: true }).click();
    await page.getByText('Synthetic pronunciation · Google TTS').waitFor();
    assert.equal(tts, 2);
    fs.mkdirSync(path.resolve(__dirname, '../test-results'), { recursive: true });
    await page.screenshot({ path: path.resolve(__dirname, '../test-results/vocabulary-mobile.png'), fullPage: true });
    failSave = true;
    await page.goto(origin + '/flashcards');
    await page.getByRole('button', { name: 'Reveal answer for 你好' }).click();
    await page.getByRole('button', { name: '4 · Correct after hesitation', exact: true }).click();
    await page.getByText(/We could not confirm this rating/).waitFor();
    assert.equal(await page.getByRole('button', { name: '5 · Perfect recall', exact: true }).isDisabled(), true);
    failSave = false;
    await page.getByRole('button', { name: 'Try again', exact: true }).click();
    await page.getByRole('button', { name: 'Reveal answer for 你好' }).waitFor();
    assert.deepEqual(errors, []);
    console.log('PASS: navigation, review save/failure, pagination, search, empty state, progress, local-audio fallback and null-audio TTS (mock API).');
  } catch (error) {
    if (page) console.error('Browser state:', await page.locator('body').innerText());
    throw error;
  } finally { await browser?.close(); server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
