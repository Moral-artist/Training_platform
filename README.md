# 前端

测试运行环境为 Node 22.16。Vite 8 需要受支持的较新 Node；建议使用 Node 22.16 或更高版本。

```
npm ci
cp .env.example .env
npm run dev
npm test
npm run build
```

.env 中设置 VITE_API_BASE_URL。部署前重建 dist；默认 API 是 http://localhost:8000。生产 API 需使用 HTTPS。Web 服务器应将前端路由回退到 index.html，参考 ../deploy/nginx.example.conf。

src/components/AppLayout.vue 是统一页头、侧栏、登出、语言切换入口。界面文案只维护在 src/i18n/messages.json，三种语言的 key 必须一致。

首页读取公开课程目录；路由守卫保护登录后页面；后端再次验证课程权限。课程详情与播放器是两个路由。大文件上传使用分段签名，不向 R2 发送站点会话和 CSRF。

上传草稿仅保存表单、资产 ID 和文件校验值，按账号隔离。刷新之后浏览器需要重新选择原文件；已完成的分段从 R2 查询，转码由后台独立任务继续完成。

npm test 包含增量文件哈希、三语键完整性、HLS 续期/退出清理及 21 路由的 DOM 渲染检查。DOM 测试不代表真实浏览器画面或生产云端联调验收。
