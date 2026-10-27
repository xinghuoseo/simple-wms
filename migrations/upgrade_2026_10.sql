-- 表结构变更迁移：仅当你的库是从旧版本升级时才需要执行
-- 全新部署不需要（首次启动 create_all 自动建全量表）

-- issue_orders 加申领类型与审核状态
ALTER TABLE issue_orders ADD COLUMN issue_type VARCHAR(20) NOT NULL DEFAULT '生产申领';
ALTER TABLE issue_orders ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'approved';

-- purchase_orders 加采购人与审核状态
ALTER TABLE purchase_orders ADD COLUMN purchaser VARCHAR(50) NOT NULL DEFAULT '';
ALTER TABLE purchase_orders ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'approved';

-- 退料单/物料加备注
ALTER TABLE return_orders ADD COLUMN remark VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE materials ADD COLUMN remark VARCHAR(255) NOT NULL DEFAULT '';
