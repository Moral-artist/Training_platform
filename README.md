# Cloudflare 视频读取 Worker

负责验证每个 HLS 清单和分片的短时 JWT，从私有 R2 读取文件。它不负责转码，不允许源视频目录读取。完整操作见交付根目录 `小白操作手册.md` 第 9 节。

修改 wrangler.toml 的 Worker 名、真实 Bucket 名与前端来源，保留绑定变量 VIDEOS。

```bash
npm install
npx wrangler login
npx wrangler secret put PLAYBACK_TOKEN_SECRET
npx wrangler deploy
```

播放密钥与 FastAPI 完全相同，至少 32 字节。部署根域名回填后端 VIDEO_WORKER_BASE_URL，不包含文件路径。

```bash
npm test
```

Bucket 关闭 r2.dev 与公开直读域名；上传 CORS 示例为 r2-cors.json。播放域名绑定 Worker，不能绕过 Worker 直接读 Bucket。

清单和浏览器媒体响应均为 no-store。可选内部缓存仅用于不带个人 Token 的分片版本，仍先验证 Token 再查询缓存。默认关闭缓存，workers.dev 不提供实际 Cache API 缓存效果；绑定自定义 Worker 域名后再评估。

Worker 请求 URL 包含短时 Token，自动观测日志默认关闭，代理与分析日志也要脱敏。Bearer Token 在过期前仍能转发；本版本没有在线会话检查、并发设备限制或即时撤销。
