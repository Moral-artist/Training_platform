# 数据库恢复

本目录说明如何根据当前 `data_model/data_model.py` 恢复一个全新的空 PostgreSQL 数据库。
项目不再包含或执行增量迁移 SQL，`data_model` 是数据库结构的唯一来源。

## 安全边界

- API 服务和转码 Worker 不导入 `tools.db_setup`。
- 生产 Docker 构建通过 `.dockerignore` 排除本目录和 `tools/db_setup.py`。
- 恢复程序拒绝任何已经存在业务表的数据库，不会更新、合并、删除或清空现有数据库。
- 未提供 `--apply` 时只显示目标和模型表名，不连接数据库。
- `IS_PRODUCTION=production` 时还必须提供额外的人工恢复授权参数。
- 程序只恢复表结构，不恢复账号、课程、计划、考试记录或 R2 视频文件。

## 空库结构恢复

先设置 `.env` 中的 `DATABASE_URL`，确认目标是一个全新的空数据库，然后执行只读检查：

```powershell
python -m tools.db_setup
```

确认数据库名称、主机和模型表清单无误后执行：

```powershell
python -m tools.db_setup --apply --confirm RESTORE_EMPTY_DATABASE
```

生产灾难恢复必须从受控的管理员代码副本执行，并额外提供：

```powershell
--allow-production-recovery
```

恢复结构后，再使用经过验证的 PostgreSQL 备份恢复业务数据，并单独恢复 R2 对象存储。不要把本工具当成业务数据备份。
