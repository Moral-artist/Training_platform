# 培训平台后端

本次版本使用原项目 Redis 会话登录，补齐课程授权、视频资产关联、R2 上传确认、HLS 转码队列和短时播放 JWT。完整步骤见交付根目录 `小白操作手册.md`。

1. 备份原库并建立测试库，核对真实表结构，再执行 `migrations/001_private_video.sql`。
2. 创建虚拟环境，安装 `requirements.txt`，复制 `.env.example` 为 `.env` 并填写真实测试配置。
3. 启动 PostgreSQL、Redis，安装 FFmpeg 和 FFprobe。
4. 在后端目录分别启动下面两个常驻进程。

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
python -m tools.transcode_worker
```

`--reload` 仅用于开发。生产配置 HTTPS、Secure Cookie、进程自动重启和数据库/R2备份。

代码模型已声明 video_assets/lesson_access，不保证原数据库已建表。create_all 不会修改已有表；只改模型不执行迁移不能正常接入新版本。

管理员角色名沿用 `administer`。manager 可管理自己资产，但播放课程仍需 lesson_access。加入学习计划不等于获得播放授权。没有视频资产的旧课按 migration_pending 处理，需逐门迁移。

```bash
python -m pytest tests -q
```

测试使用独立 SQLite 与假 R2，真实 PostgreSQL 迁移/并发锁、Redis、云端 SDK 和浏览器播放另行验收。单文件仍限制 300 MiB，没有 multipart、DRM或实时播放会话撤销。
