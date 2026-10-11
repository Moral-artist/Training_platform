-- 取消会员等级：仅删除 accounts 的该列及随列删除的本表约束。
-- 用户已明确要求删除；先备份旧等级数据，停止旧应用后执行。
-- 由 tools.db_setup 的事务管理执行。重复运行不会重新创建该列。
-- 不使用 CASCADE；若外部视图等依赖该列，保留依赖并停止本次迁移。
ALTER TABLE accounts DROP COLUMN IF EXISTS membership_level;
