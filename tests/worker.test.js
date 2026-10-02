import test from 'node:test'
import assert from 'node:assert/strict'
import { createHmac, webcrypto } from 'node:crypto'
import worker, { verifyToken, safeObjectKey, rewriteManifest, parseRange } from '../src/index.js'
globalThis.crypto ||= webcrypto
const secret = 'test-only-secret-32-bytes-0123456789'
const asset = '11111111-1111-4111-8111-111111111111'
const prefix = `videos/hls/${asset}/22222222-2222-4222-8222-222222222222/`
function sign(overrides = {}, signingSecret = secret, algorithm = 'HS256') {
  const now = Math.floor(Date.now() / 1000)
  const body = { iss: 'training-api', aud: 'training-video', sub: 'student-a', asset, prefix, iat: now, exp: now + 300, jti: 'test-session', ...overrides }
  const message = [Buffer.from(JSON.stringify({ alg: algorithm, typ: 'JWT' })).toString('base64url'), Buffer.from(JSON.stringify(body)).toString('base64url')].join('.')
  return `${message}.${createHmac('sha256', signingSecret).update(message).digest('base64url')}`
}
const env = { PLAYBACK_TOKEN_SECRET: secret, ALLOWED_ORIGINS: 'https://training.example.com', CACHE_SEGMENTS: 'false' }
const request = (path, token = sign(), opts = {}) => new Request(`https://media.example.com/${path}${token ? '?token=' + token : ''}`, opts)

test('valid, expired, wrong key, algorithm, audience, excessive lifetime', async () => {
  assert.equal((await verifyToken(sign(), secret)).asset, asset)
  for (const token of [sign({ exp: 1 }), sign({}, 'wrong'), sign({}, secret, 'none'), sign({ aud: 'other' }), sign({ exp: Math.floor(Date.now() / 1000) + 999 })]) {
    await assert.rejects(verifyToken(token, secret))
  }
})
test('token is scoped to one asset and version and rejects encoded traversal', () => {
  assert.equal(safeObjectKey('/' + prefix + '360p/segment_00000.ts', prefix), prefix + '360p/segment_00000.ts')
  for (const path of ['videos/source/private.mp4', prefix + '../source.mp4', prefix + '%2e%2e/source.mp4', prefix + '%252e%252e/a.ts', prefix + 'a\\b.ts', prefix + 'key.bin', prefix.replace(asset, '33333333-3333-4333-8333-333333333333') + 'a.ts']) {
    assert.throws(() => safeObjectKey('/' + path, prefix))
  }
})
test('nested playlists, TS and URI tags all retain authorization', () => {
  const base = `https://media.example.com/${prefix}master.m3u8?token=old`
  const master = rewriteManifest('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1200000\n360p/index.m3u8\n', base, prefix, 'fresh')
  assert.match(master, /360p\/index\.m3u8\?token=fresh/)
  const media = rewriteManifest('#EXTM3U\n#EXT-X-MAP:URI="init.mp4"\nsegment_00000.ts\n', base.replace('master', '360p/index'), prefix, 'fresh')
  assert.match(media, /init\.mp4\?token=fresh/)
  assert.match(media, /360p\/segment_00000\.ts\?token=fresh/)
  for (const uri of ['https://evil.example/a.ts', '//evil.example/a.ts', '../secret.ts', '/videos/source/a.mp4']) {
    assert.throws(() => rewriteManifest('#EXTM3U\n' + uri, base, prefix, 'fresh'))
  }
})
test('HTTP byte ranges including suffix and unsatisfiable requests', () => {
  assert.deepEqual(parseRange('bytes=2-5', 10), { offset: 2, length: 4 })
  assert.deepEqual(parseRange('bytes=-3', 10), { offset: 7, length: 3 })
  assert.deepEqual(parseRange('bytes=5-', 10), { offset: 5, length: 5 })
  for (const value of ['bytes=50-', 'bytes=4-1', 'bytes=-0', 'bytes=0-1,3-4', 'nonsense']) assert.throws(() => parseRange(value, 10))
})
test('missing and expired token, cross-asset path denied before R2 read', async () => {
  let reads = 0
  const runtime = { ...env, VIDEOS: { get() { reads++; return null } } }
  assert.equal((await worker.fetch(request(prefix + 'master.m3u8', null), runtime, {})).status, 401)
  assert.equal((await worker.fetch(request(prefix + 'master.m3u8', sign({ exp: 1 })), runtime, {})).status, 401)
  assert.equal((await worker.fetch(request('videos/source/a.mp4'), runtime, {})).status, 403)
  assert.equal(reads, 0)
})
test('manifest response is private, rewritten and has precise CORS', async () => {
  const runtime = { ...env, VIDEOS: { async get() { return { size: 30, text: async () => '#EXTM3U\n360p/index.m3u8\n' } } } }
  const response = await worker.fetch(request(prefix + 'master.m3u8', sign(), { headers: { Origin: 'https://training.example.com' } }), runtime, {})
  assert.equal(response.status, 200)
  assert.equal(response.headers.get('Cache-Control'), 'no-store')
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), 'https://training.example.com')
  assert.match(await response.text(), /token=/)
  assert.equal((await worker.fetch(request(prefix + 'master.m3u8', sign(), { headers: { Origin: 'https://evil.example' } }), runtime, {})).status, 403)
})
test('binary range body, HEAD and not-found', async () => {
  const runtime = { ...env, VIDEOS: {
    head: async () => ({ size: 10, httpEtag: '"etag"' }),
    get: async (_, options) => ({ size: 10, httpEtag: '"etag"', body: new Uint8Array(options?.range?.length || 10) })
  } }
  const response = await worker.fetch(request(prefix + 'a.ts', sign(), { headers: { Range: 'bytes=2-5' } }), runtime, {})
  assert.equal(response.status, 206)
  assert.equal(response.headers.get('Content-Range'), 'bytes 2-5/10')
  assert.equal((await response.arrayBuffer()).byteLength, 4)
  assert.equal((await worker.fetch(request(prefix + 'a.ts', sign(), { method: 'HEAD' }), runtime, {})).status, 200)
  const bad = await worker.fetch(request(prefix + 'a.ts', sign(), { headers: { Range: 'bytes=20-' } }), runtime, {})
  assert.equal(bad.status, 416)
  assert.equal(bad.headers.get('Content-Range'), 'bytes */10')
  assert.equal((await worker.fetch(request(prefix + 'a.ts'), { ...env, VIDEOS: { get: async () => null } }, {})).status, 404)
})
test('cached segments are still checked on every request', async () => {
  let checks = 0
  globalThis.caches = { default: { async match() { checks++; return new Response('cached', { headers: { 'Content-Type': 'video/mp2t' } }) } } }
  const runtime = { ...env, CACHE_SEGMENTS: 'true' }
  assert.equal((await worker.fetch(request(prefix + 'a.ts', null), runtime, {})).status, 401)
  assert.equal(checks, 0)
  const response = await worker.fetch(request(prefix + 'a.ts'), runtime, {})
  assert.equal(await response.text(), 'cached')
  assert.equal(response.headers.get('Cache-Control'), 'no-store')
  assert.equal(checks, 1)
  delete globalThis.caches
})
