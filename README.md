# 后端

Python 3.10+；建议独立虚拟环境。安装 `pip install -r requirements.lock.txt`，配置 .env，启动 PostgreSQL 和 Redis。完整部署步骤见 ../docs/DEPLOYMENT.md。

应用：`uvicorn main:app --host 0.0.0.0 --port 8000`
转码独立进程：`python -m tools.transcode_worker`
只处理一个任务：`python -m tools.transcode_worker --once`
重试失败资产：`python -m tools.transcode_worker --retry ASSET_UUID`

数据库结构以 `data_model/data_model.py` 为准。应用和转码 Worker 启动时不会自动建表或执行数据库恢复。
空库恢复工具默认只显示目标，只有显式确认后才执行，并且拒绝修改任何非空数据库：

- 检查恢复目标：`python -m tools.db_setup`
- 恢复空库结构：`python -m tools.db_setup --apply --confirm RESTORE_EMPTY_DATABASE`
- 生产环境还必须额外添加 `--allow-production-recovery`；恢复工具不包含在生产 Docker 构建中。
- 初始化管理员：`python -m tools.bootstrap_admin --email YOUR_EMAIL --apply`
- 待上传文件清理：`python -m tools.cleanup_uploads`，检查输出后加 --apply。
- 旧 HLS 版本清理：`python -m tools.cleanup_hls_versions --days 7`，检查输出后加 --apply。

测试：`pytest -q`。R2 使用替身，不调用真实存储。需要 FFmpeg/FFprobe 才能运行真实媒体测试。

公开目录 GET /api/lessons/catalog；其他详情、播放和管理接口由会话、数据库角色、课程授权及资产归属共同校验。接口说明见 ../docs/API_MAP.md，数据库恢复说明见 database_recovery/README.md。
