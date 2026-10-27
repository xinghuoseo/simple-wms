-- 出库单审核流程迁移
ALTER TABLE issue_orders ADD COLUMN issue_type VARCHAR(20) NOT NULL DEFAULT '生产申领';
ALTER TABLE issue_orders ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'approved';
