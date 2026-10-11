# 后端

Python 3.10+；建议独立虚拟环境。安装 `pip install -r requirements.lock.txt`，配置 .env，启动 PostgreSQL 和 Redis。完整部署步骤见 ../docs/DEPLOYMENT.md。

应用：`uvicorn main:app --host 0.0.0.0 --port 8000`
转码独立进程：`python -m tools.transcode_worker`
只处理一个任务：`python -m tools.transcode_worker --once`
重试失败资产：`python -m tools.transcode_worker --retry ASSET_UUID`

数据库工具默认只显示目标，--apply 才执行：

- 空库：`python -m tools.db_setup init --apply`
- 旧库：`python -m tools.db_setup migrate --apply`
- 初始化管理员：`python -m tools.bootstrap_admin --email YOUR_EMAIL --apply`
- 待上传文件清理：`python -m tools.cleanup_uploads`，检查输出后加 --apply。
- 旧 HLS 版本清理：`python -m tools.cleanup_hls_versions --days 7`，检查输出后加 --apply。

测试：`pytest -q`。R2 使用替身，不调用真实存储。需要 FFmpeg/FFprobe 才能运行真实媒体测试。真实 PostgreSQL 迁移测试需要 TEST_POSTGRES_URL，且仅接受本地 video_patch_test 数据库。

公开目录 GET /api/lessons/catalog；其他详情、播放和管理接口由会话、数据库角色、课程授权及资产归属共同校验。新增字段与接口见 ../docs/API_MAP.md 和 migrations/002_platform_upgrade.sql。
