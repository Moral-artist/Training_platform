const UUID_PATTERN = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
const PREFIX_PATTERN = new RegExp(`^videos/hls/(${UUID_PATTERN})/(${UUID_PATTERN})/$`)
const encoder = new TextEncoder()

function fail(status, message) {
  throw Object.assign(new Error(message), { status })
}
function decodeBase64url(value) {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) fail(401, 'Invalid token')
  try {
    const encoded = value.replace(/-/g, '+').replace(/_/g, '/')
    return Uint8Array.from(atob(encoded + '='.repeat((4 - encoded.length % 4) % 4)), c => c.charCodeAt(0))
  } catch { fail(401, 'Invalid token') }
}

export async function verifyToken(token, secret, now = Math.floor(Date.now() / 1000)) {
  if (!secret || encoder.encode(secret).length < 32) fail(503, 'Playback not configured')
  if (!token || token.length > 4096) fail(401, 'Token required')
  const parts = token.split('.')
  if (parts.length !== 3) fail(401, 'Invalid token')
  let header, claims
  try {
    header = JSON.parse(new TextDecoder().decode(decodeBase64url(parts[0])))
    claims = JSON.parse(new TextDecoder().decode(decodeBase64url(parts[1])))
  } catch { fail(401, 'Invalid token') }
  if (header?.alg !== 'HS256' || header?.typ !== 'JWT') fail(401, 'Invalid token algorithm')
  const key = await crypto.subtle.importKey('raw', encoder.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['verify'])
  const ok = await crypto.subtle.verify('HMAC', key, decodeBase64url(parts[2]), encoder.encode(`${parts[0]}.${parts[1]}`))
  if (!ok) fail(401, 'Invalid signature')
  if (!claims || claims.iss !== 'training-api' || claims.aud !== 'training-video' ||
      !Number.isInteger(claims.iat) || !Number.isInteger(claims.exp) ||
      claims.exp <= now || claims.iat > now + 15 || claims.exp <= claims.iat || claims.exp - claims.iat > 600 ||
      typeof claims.sub !== 'string' || !claims.sub || typeof claims.jti !== 'string' || !claims.jti ||
      typeof claims.prefix !== 'string' || !PREFIX_PATTERN.test(claims.prefix) ||
      claims.prefix.split('/')[2] !== claims.asset) fail(401, 'Invalid or expired token')
  return claims
}

export function safeObjectKey(pathname, prefix) {
  let key
  try { key = decodeURIComponent(pathname.replace(/^\//, '')) } catch { fail(403, 'Invalid path') }
  if (key.includes('\\') || key.includes('%') || key.includes('\0') ||
      key.split('/').some(p => !p || p === '.' || p === '..') || !key.startsWith(prefix) ||
      !/\.(m3u8|ts|m4s|mp4)$/.test(key)) fail(403, 'Resource not allowed')
  return key
}

export function rewriteManifest(text, requestUrl, prefix, token) {
  const base = new URL(requestUrl)
  const rewrite = uri => {
    if (/^[a-z][a-z\d+.-]*:/i.test(uri) || uri.startsWith('//') || uri.includes('\\') ||
        uri.split(/[/?#]/).some(part => part === '..' || part === '.')) fail(403, 'Unsafe playlist URI')
    const target = new URL(uri, base)
    if (target.origin !== base.origin || target.hash) fail(403, 'Unsafe playlist URI')
    safeObjectKey(target.pathname, prefix)
    target.search = ''
    target.searchParams.set('token', token)
    return target.href
  }
  if (!text.startsWith('#EXTM3U')) fail(502, 'Invalid playlist')
  return text.split(/\r?\n/).map(line => {
    if (!line || !line.trim()) return line
    if (!line.startsWith('#')) return rewrite(line.trim())
    return line.replace(/URI="([^"]+)"/g, (_, uri) => `URI="${rewrite(uri)}"`)
  }).join('\n')
}

export function parseRange(value, size) {
  const match = /^bytes=(\d*)-(\d*)$/.exec(value || '')
  if (!match || (!match[1] && !match[2]) || size <= 0) fail(416, 'Invalid range')
  let start, end
  if (!match[1]) {
    const suffix = Number(match[2])
    if (!Number.isSafeInteger(suffix) || suffix <= 0) fail(416, 'Invalid range')
    start = Math.max(0, size - suffix); end = size - 1
  } else {
    start = Number(match[1]); end = match[2] ? Number(match[2]) : size - 1
    if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start >= size || end < start) fail(416, 'Invalid range')
    end = Math.min(end, size - 1)
  }
  return { offset: start, length: end - start + 1 }
}

function corsHeaders(request, env) {
  const headers = new Headers({ 'Vary': 'Origin', 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff' })
  const origin = request.headers.get('Origin')
  const allowed = (env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean)
  if (origin && !allowed.includes(origin)) fail(403, 'Origin not allowed')
  if (origin) headers.set('Access-Control-Allow-Origin', origin)
  headers.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
  headers.set('Access-Control-Allow-Headers', 'Range')
  headers.set('Access-Control-Expose-Headers', 'Content-Length, Content-Range, Accept-Ranges, ETag')
  return headers
}

export default {
  async fetch(request, env, ctx) {
    let headers = new Headers({ 'Cache-Control': 'no-store', 'Vary': 'Origin' })
    try {
      headers = corsHeaders(request, env)
      if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers })
      if (!['GET', 'HEAD'].includes(request.method)) fail(405, 'Method not allowed')
      const url = new URL(request.url)
      const token = url.searchParams.get('token')
      const claims = await verifyToken(token, env.PLAYBACK_TOKEN_SECRET)
      const key = safeObjectKey(url.pathname, claims.prefix)
      const playlist = key.endsWith('.m3u8')
      // 必须先鉴权，再查询缓存。清单含个人 Token，绝不共享缓存。
      const rangeValue = request.headers.get('Range')
      const useCache = !playlist && !rangeValue && request.method === 'GET' && env.CACHE_SEGMENTS === 'true'
      const cacheKey = new Request(`${url.origin}/${key}`)
      const cache = typeof caches !== 'undefined' ? caches.default : null
      if (useCache && cache) {
        const cached = await cache.match(cacheKey)
        if (cached) {
          for (const name of ['Content-Type', 'Content-Length', 'ETag', 'Accept-Ranges']) {
            const value = cached.headers.get(name)
            if (value) headers.set(name, value)
          }
          return new Response(cached.body, { headers })
        }
      }
      if (playlist) {
        const object = await env.VIDEOS.get(key)
        if (!object) fail(404, 'Video object not found')
        if (object.size > 1024 * 1024) fail(502, 'Playlist too large')
        const manifest = rewriteManifest(await object.text(), url.href, claims.prefix, token)
        headers.set('Content-Type', 'application/vnd.apple.mpegurl')
        return new Response(request.method === 'HEAD' ? null : manifest, { headers })
      }
      let range = null, total = null
      if (rangeValue) {
        const meta = await env.VIDEOS.head(key)
        if (!meta) fail(404, 'Video object not found')
        total = meta.size
        try { range = parseRange(rangeValue, total) }
        catch (e) { headers.set('Content-Range', `bytes */${total}`); throw e }
      }
      const object = request.method === 'HEAD' ? await env.VIDEOS.head(key) : await env.VIDEOS.get(key, range ? { range } : undefined)
      if (!object) fail(404, 'Video object not found')
      headers.set('Content-Type', key.endsWith('.ts') ? 'video/mp2t' : 'video/mp4')
      headers.set('Accept-Ranges', 'bytes')
      headers.set('ETag', object.httpEtag)
      headers.set('Content-Length', String(range ? range.length : object.size))
      if (range) headers.set('Content-Range', `bytes ${range.offset}-${range.offset + range.length - 1}/${total}`)
      const response = new Response(request.method === 'HEAD' ? null : object.body, { status: range ? 206 : 200, headers })
      if (useCache && cache) {
        const stored = response.clone()
        stored.headers.set('Cache-Control', 'public, max-age=86400')
        stored.headers.delete('Access-Control-Allow-Origin')
        stored.headers.delete('Vary')
        ctx.waitUntil(cache.put(cacheKey, stored))
      }
      return response
    } catch (error) {
      const status = error.status || 502
      // 不打印 request.url，避免日志暴露 token；不透出 R2 错误详情。
      return new Response(JSON.stringify({ error: error.status ? error.message : 'Media unavailable' }), {
        status, headers: new Headers([...headers, ['Content-Type', 'application/json']])
      })
    }
  }
}
