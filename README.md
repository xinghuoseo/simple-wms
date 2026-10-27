# 简易仓库管理系统 (Simple WMS)

轻量级仓库管理系统：围绕 **采购单（入库）** 和 **出库单（生产申领/非工单申领）** 维护物料库存，支持退料、供应商管理、用户管理。适合小团队（3~5 人）使用。

## 技术栈

- 后端：FastAPI + SQLAlchemy 2.0 + MySQL (PyMySQL)，JWT 登录鉴权
- 前端：Vue3 + Vite + Element Plus
- 部署：单进程部署（FastAPI 同时托管 API 与前端静态文件），Nginx 纯反代

## 核心功能

- **单据审核流程**：采购单、出库单均为「待审核 → 已审核」；待审核单据不参与库存计算，审核通过后才扣减/计入库存
- **FIFO 出库**：出库审核时按入库日期从老到新扣减，不足可负数结转（欠账）
- **负数结转**：新采购入库自动归零上一笔欠账行，欠账转移到新行
- **退料**：退料单必须对应一张已审核出库单，LIFO 反向回补库存
- **单号自动生成**：`CG_`（采购）/ `CK_`（生产出库）/ `FQ_`（非工单出库）/ `TL_`（退料）+ 日期 + 当日序号
- **UI**：全表格分页（默认 25）、联想下拉搜索、库存 Excel 导出、单据打印

## 快速开始

### 方式一：Docker 一键部署（推荐，无需克隆源码）

装好 [Docker](https://docs.docker.com/get-docker/) 后，任意目录执行：

```bash
curl -O https://raw.githubusercontent.com/xinghuoseo/simple-wms/main/docker-compose.standalone.yml
docker compose -f docker-compose.standalone.yml up -d
docker compose -f docker-compose.standalone.yml exec app python seed_admin.py   # 一路回车 = admin/admin123
```

打开 http://localhost:39800 即可使用。数据存在 docker 卷中，重启/升级不丢（升级：重新执行 `up -d` 拉取最新镜像）。

镜像地址：`ghcr.io/xinghuoseo/simple-wms:latest`（由 GitHub Actions 自动构建，公开可直接拉取）。

> Windows 用户把 `curl -O` 换成浏览器下载该 yml 文件即可。
> 生产环境请修改 yml 里的 `MYSQL_PASSWORD` 和 `SECRET_KEY`。

### 方式二：克隆源码构建

```bash
git clone https://github.com/xinghuoseo/simple-wms.git
cd simple-wms
docker compose up -d --build
docker compose exec app python seed_admin.py
```

### 方式三：手动部署（开发模式）

#### 0. 准备

```bash
# 需要：Python 3.11+，Node.js 18+，MySQL 8
```

### 1. 数据库

```sql
CREATE DATABASE ifungoo_erp DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wms'@'%' IDENTIFIED BY '你的密码';
GRANT ALL ON ifungoo_erp.* TO 'wms'@'%';
FLUSH PRIVILEGES;
```

### 2. 后端

```bash
python -m venv venv
# Windows: venv\Scripts\activate  /  Linux: source venv/bin/activate
pip install -r requirements.txt

copy .env.example .env   # Linux 用 cp
# 编辑 .env：填入数据库账号密码，SECRET_KEY 换成随机长字符串

python main.py           # 开发模式，http://127.0.0.1:39800
```

首次启动自动建表。需要一个初始用户，用下面脚本创建管理员：

```bash
python seed_admin.py     # 默认创建 admin/admin123，登录后请修改
```

### 3. 前端

```bash
cd frontend
npm install
npm run build            # 产物输出到 frontend/dist，由后端自动托管
```

重新打开 http://127.0.0.1:39800 即是完整系统。

### 4. 生产部署（可选，Ubuntu + Nginx）

参考 [docs/开发文档.md](docs/开发文档.md) 第 7 节：uvicorn 跑 39800 端口，Nginx 一条反代规则即可，HTTPS 用宝塔或 certbot 均可。

## 目录结构

```
├── main.py               # 入口：uvicorn main:app
├── requirements.txt
├── .env.example          # 环境变量模板
├── seed_admin.py         # 创建初始管理员
├── app/
│   ├── main.py           # FastAPI 实例 + SPA 托管
│   ├── models.py         # ORM（表头+明细两级结构）
│   ├── schemas.py
│   ├── auth.py           # JWT
│   └── routers/          # auth/users/materials/issues/purchases/suppliers
├── frontend/
│   └── src/
│       ├── views/        # 8 个页面
│       ├── components/   # IssueDialog / ReturnDialog / TablePager
│       └── usePaging.js
├── migrations/           # 已有库的加列迁移 SQL
└── docs/开发文档.md       # 详细设计与业务规则
```

## 业务规则速览

详见 [docs/开发文档.md](docs/开发文档.md)，要点：

| 规则 | 说明 |
|---|---|
| 库存 | 物料所有已审核采购明细行的 `purchase_qty - claimed_qty + return_qty` 之和 |
| 出库审核 | 待审核不扣库存；审核时 FIFO 扣减；扣穿允许负数（欠账记在最新一行） |
| 待审核出库单 | 不能退料；可直接删除 |
| 已审核出库单 | 删除会反向回补库存；有退料记录的需先删退料单 |
| 采购单 | 待审核可修改（复用新增接口）；审核后才计入库存 |
| 退料单 | 只能对应已审核出库单；出库量锁定，只能填回退量 |

## 给 AI Agent 的说明

如果你是 AI agent，被要求部署或二次开发本项目，请按以下顺序：

1. 读 `docs/开发文档.md` —— 完整的数据表结构、业务规则（FIFO/负数结转/审核流程）、API 清单都在这里
2. 本地跑通：MySQL 建库 → `.env` 配置 → `pip install -r requirements.txt` → `python seed_admin.py` → `python main.py` → `cd frontend && npm install && npm run build`
3. 改后端代码后重启 uvicorn；改前端代码后 `npm run build`
4. 表结构变更时：新表靠 create_all 自动建；已有表加列需写迁移（参考 `migrations/`）

## License

MIT
