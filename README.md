# 培训平台前端

本次版本接入私有 R2 + HLS + Worker + 短时播放 Token。完整配置步骤见交付根目录 `小白操作手册.md`，函数修改见 `清单.md`。

```bash
npm install
cp .env.example .env
npm run dev
```

默认 API：`http://localhost:8000`。本地浏览器统一使用 `http://localhost:5173`。生产修改 `VITE_API_BASE_URL` 后重新构建。

- `/home`：访客可打开页面和专业入口；真实课程数据需要登录并获得授权。
- `/lessons/:major`：展示当前账号已授权课程，`major` 为 electrical/hvac/elv/fire。
- `/lessons/:major/:lessonId`：授权详情与正式视频播放器。
- `/lessons/lessoncreate`：管理员上传、确认、创建资产关联课程，显示转码状态。
- `/lessons/systemcreate`：保留管理员专业创建页。
- `/lessons/accessmanage`：管理员搜索学员、选择课程、授权或撤销。
- `/dashboard`：保留原工作台。

Safari/iOS 优先原生 HLS，其余支持的浏览器使用 hls.js。播放请求前检查登录、CSRF 和课程授权；长视频自动续期。前端 `.env` 只填写 API 地址，不放 R2 或签名密钥。

```bash
npm test
npm run build
```

前端测试模拟媒体对象，不代表真实浏览器解码验收。需要配合后端、独立 FFmpeg 转码进程和部署好的 Cloudflare Worker。
