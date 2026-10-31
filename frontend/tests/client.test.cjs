const { test } = require('node:test');
const assert = require('node:assert/strict');
const ts = require('typescript');
const fs = require('node:fs');
require.extensions['.ts'] = (module, filename) => module._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, filename);
const { createClient, ApiError } = require('../services/client.ts');
const { audioUrl, ttsUrl } = require('../services/audio.ts');
const response = (data, status = 200) => new Response(JSON.stringify(data), { status });
function session() {
  let token = 'expired'; let cleared = 0;
  return { access: () => token, refresh: async () => 'refresh-token', save: async t => { token = t.access_token; }, clear: async () => { token = null; cleared++; }, cleared: () => cleared };
}
test('concurrent 401s share one refresh and retry with the new token', async () => {
  const state = session(); let refreshes = 0;
  const api = createClient('http://test/api/v1', state, async (url, init) => {
    if (url.endsWith('/auth/refresh')) { refreshes++; await new Promise(r => setTimeout(r, 10)); assert.deepEqual(JSON.parse(init.body), { refresh_token: 'refresh-token' }); return response({ access_token: 'fresh', refresh_token: 'rotated' }); }
    return init.headers.get('Authorization') === 'Bearer fresh' ? response({ ok: true }) : response({}, 401);
  });
  assert.deepEqual(await Promise.all([api('/one'), api('/two')]), [{ ok: true }, { ok: true }]);
  assert.equal(refreshes, 1);
});
test('an invalid refresh signs out without replaying the request', async () => {
  const state = session(); let calls = 0;
  const api = createClient('http://test', state, async () => { calls++; return response({ detail: 'Expired' }, 401); });
  await assert.rejects(api('/review'), e => e instanceof ApiError && e.status === 401);
  assert.equal(calls, 2); assert.equal(state.cleared(), 1);
});
test('a second 401 after refresh is not retried again', async () => {
  const state = session(); let calls = 0;
  const api = createClient('http://test', state, async url => { calls++; return url.endsWith('/auth/refresh') ? response({ access_token: 'fresh', refresh_token: 'new' }) : response({}, 401); });
  await assert.rejects(api('/review'), e => e.status === 401);
  assert.equal(calls, 3); assert.equal(state.cleared(), 1);
});
test('a network failure submitting a rating never causes an automatic duplicate', async () => {
  let calls = 0;
  const api = createClient('http://test', session(), async (url, init) => { calls++; assert.deepEqual(JSON.parse(init.body), { word_id: 7, quality: 4 }); throw new TypeError('Connection lost'); });
  await assert.rejects(api('/vocabulary/review', { method: 'POST', body: JSON.stringify({ word_id: 7, quality: 4 }) }));
  assert.equal(calls, 1);
});
test('public login does not attach tokens or attempt refresh', async () => {
  let calls = 0;
  const api = createClient('http://test', session(), async (url, init) => { calls++; assert.equal(init.headers.has('Authorization'), false); return response({}, 401); });
  await assert.rejects(api('/auth/login', { method: 'POST' }, false)); assert.equal(calls, 1);
});
test('logout during refresh cannot restore the old session', async () => {
  const state = session();
  const api = createClient('http://test', state, async url => {
    if (url.endsWith('/auth/refresh')) { await state.clear(); return response({ access_token: 'fresh', refresh_token: 'new' }); }
    return response({}, 401);
  });
  await assert.rejects(api('/review')); assert.equal(state.access(), null);
});
test('audio paths use exactly one API prefix and encode Chinese characters', () => {
  const base = 'http://localhost:8000/api/v1';
  const expected = 'http://localhost:8000/api/v1/audio/hsk1/%E4%BD%A0%E5%A5%BD.mp3';
  assert.equal(audioUrl(base, '/api/v1/audio/hsk1/你好.mp3'), expected);
  assert.equal(audioUrl(base, '/audio/hsk1/你好.mp3'), expected);
  assert.throws(() => audioUrl(base, 'https://external.test/file.mp3'));
  assert.equal(new URL(ttsUrl('你好')).searchParams.get('q'), '你好');
});
