# AIName 项目开发文档

> 审查日期：2026-06-24  
> 适用范围：本仓库当前代码结构、后端接口、前端页面、业务流程与后续开发维护。

## 1. 项目定位

AIName 是一个围绕“AI 起名”的多端应用，当前代码已经从单一智能起名扩展为综合平台：

- C 端用户：注册登录、AI 起名、起名反馈微调、知识库上传、品牌视觉生成、专家服务购买、个人中心、钱包、会员、订单、发票。
- 专家端：专家申请、接单、提交报告、订单结算、收入与提现、评价回复、售后查看。
- B 端开放平台：开发者申请、API Key 管理、开放 API 调用、调用日志、计费统计、套餐与限流规则。
- 管理后台：用户管理、命名记录、专家审核、开放平台审核、支付/退款/提现/发票/售后/对账管理。
- AI 能力：DeepSeek 结构化命名、LangGraph 多节点工作流、PostgreSQL 记忆检查点、Chroma 私有知识库、阿里百炼文本与图片生成。

整体架构是“FastAPI 后端 + uni-app/Vue 前端 + MySQL 业务库 + PostgreSQL LangGraph 记忆库 + Chroma 向量库 + RabbitMQ 异步知识库任务”。

## 2. 仓库结构

```text
AiNameCode/
├─ AInameProject/                 # 后端 FastAPI 项目
│  ├─ main.py                      # FastAPI 应用入口，注册中间件、生命周期、路由、静态资源
│  ├─ run.py                       # Windows 兼容启动入口，设置 SelectorEventLoop 后启动 uvicorn
│  ├─ settings/__init__.py         # 环境变量与全局配置
│  ├─ dependencies.py              # FastAPI 依赖注入：数据库 Session、邮件实例
│  ├─ models/                      # SQLAlchemy ORM 模型
│  ├─ schemas/                     # Pydantic 请求/响应模型
│  ├─ routers/                     # API 路由层
│  ├─ core/                        # AI 工作流、RAG、认证、Key、邮件、工具函数
│  ├─ services/                    # 第三方 AI 服务、后台初始化等服务层
│  ├─ repository/                  # 仓储层，封装部分数据库访问
│  ├─ alembictable/                # Alembic 数据库迁移目录
│  ├─ chroma_rag_db/               # Chroma 向量库本地数据
│  ├─ uploads/                     # 用户上传文件
│  ├─ reports/                     # 专家报告示例/生成文件
│  └─ docs/                        # 后端局部设计文档
├─ AInameVue/                      # 前端 uni-app/Vue 项目
│  ├─ pages.json                   # 页面注册与导航配置
│  ├─ App.vue                      # 前端应用入口
│  ├─ main.js                      # Vue/uni 初始化入口
│  ├─ api/                         # 前端 API 封装
│  ├─ utils/                       # 请求、路由、配置工具
│  ├─ pages/                       # 业务页面
│  ├─ components/                  # 通用组件
│  ├─ styles/                      # 全局样式
│  └─ static/                      # 静态资源
├─ docs/                           # 仓库级文档
├─ scripts/                        # 编码/环境辅助脚本
└─ PROJECT_DEVELOPMENT_DOC.md      # 当前开发文档
```

## 3. 技术栈

### 3.1 后端

- Python `>=3.13`
- FastAPI + Uvicorn
- SQLAlchemy Async ORM
- Alembic 数据库迁移
- MySQL：主业务数据库，默认连接为 `mysql+aiomysql://root:123456@127.0.0.1:3306/ainame?charset=utf8`
- PostgreSQL：LangGraph checkpoint 记忆库，默认连接为 `postgresql://postgres:123456@127.0.0.1:5432/ainame`
- Redis：预留/配置于 `core/redisconfig.py`
- RabbitMQ：知识库文件解析异步队列
- Chroma：本地向量库
- LangChain / LangGraph：命名工作流
- DeepSeek：核心起名大模型
- DashScope/阿里百炼：品牌视觉文本与图片生成
- FastAPI-Mail：验证码邮件
- PyJWT + pwdlib[argon2]：用户认证与密码哈希

### 3.2 前端

- uni-app
- Vue 3
- Vite
- Sass
- H5 / 微信小程序 / App 多端构建脚本

## 4. 环境变量

后端配置集中在 `AInameProject/settings/__init__.py`，从 `AInameProject/.env` 读取。

| 变量 | 用途 | 默认值/说明 |
| --- | --- | --- |
| `DB_URI` | MySQL 主业务库 | `mysql+aiomysql://root:123456@127.0.0.1:3306/ainame?charset=utf8` |
| `LANGGRAPH_DB_URI` | LangGraph checkpoint PostgreSQL 库 | `postgresql://postgres:123456@127.0.0.1:5432/ainame` |
| `MAIL_USERNAME` | SMTP 用户名 | 空 |
| `MAIL_PASSWORD` | SMTP 密码/授权码 | 空 |
| `MAIL_FROM` | 发件人邮箱 | 默认同 `MAIL_USERNAME` |
| `MAIL_PORT` | SMTP 端口 | `587` |
| `MAIL_SERVER` | SMTP 服务 | `smtp.qq.com` |
| `MAIL_STARTTLS` | 是否启用 STARTTLS | `true` |
| `MAIL_SSL_TLS` | 是否启用 SSL/TLS | `false` |
| `JWT_SECRET_KEY` | JWT 签名与 API Key HMAC 密钥 | `please-change-this-secret`，生产必须修改 |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | Access Token 有效期 | `15` |
| `JWT_REFRESH_TOKEN_EXPIRES_DAYS` | Refresh Token 有效期 | `30` |
| `PAYMENT_CALLBACK_SECRET` | 支付回调签名密钥 | 默认同 `JWT_SECRET_KEY` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 空 |
| `DEEPSEEK_MODEL` | DeepSeek 模型 | `deepseek-chat` |
| `DASHSCOPE_API_KEY` | 阿里百炼 API Key | 空 |
| `DASHSCOPE_MODEL` | 阿里百炼文本模型 | `qwen-plus` |
| `DASHSCOPE_IMAGE_MODEL` | 阿里百炼图片模型 | `wanx2.1-t2i-turbo` |

前端接口地址在 `AInameVue/utils/config.js`：

- H5 运行在 `localhost` 或 `127.0.0.1` 时，默认请求 `http://127.0.0.1:8000`。
- H5 局域网访问时，使用当前页面 host + `8000` 端口。
- 非 H5 环境默认使用 `http://192.168.0.105:8000`，也可通过 `VUE_APP_API_BASE_URL` 覆盖。

## 5. 启动与开发

### 5.1 后端启动

```bash
cd AInameProject
uv sync
alembic upgrade head
python run.py
```

Windows 环境建议使用 `python run.py`，因为该入口会在 uvicorn 创建事件循环前设置 `WindowsSelectorEventLoopPolicy`，避免 psycopg 异步模式与 Windows 默认 ProactorEventLoop 冲突。

后端启动后访问：

```text
http://127.0.0.1:8000/docs
```

### 5.2 前端启动

```bash
cd AInameVue
npm install
npm run dev:h5
```

其他构建目标：

```bash
npm run build:h5
npm run dev:mp-weixin
npm run build:mp-weixin
npm run dev:app
npm run build:app
```

### 5.3 知识库 Worker

知识库上传接口会把文件任务投递到 RabbitMQ 队列，实际解析与向量化由 `AInameProject/rag_worker.py` 处理。

```bash
cd AInameProject
python rag_worker.py
```

默认 RabbitMQ：

```text
amqp://admin:admin123456@127.0.0.1:5672/
queue: rag_document_queue
```

## 6. 后端架构

### 6.1 应用生命周期

`AInameProject/main.py` 使用 FastAPI lifespan：

1. 服务启动时调用 `init_workflow_graph()` 初始化 LangGraph 图与 PostgreSQL checkpoint 连接池。
2. 服务启动时调用 `init_super_admin()` 初始化超级管理员。
3. 服务关闭时调用 `close_workflow_graph()` 释放 LangGraph PostgreSQL 连接池。

当前应用开启 CORS：

```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

生产环境应收敛允许来源。

### 6.2 数据访问

`models/__init__.py` 创建全局异步引擎：

- `create_async_engine(DB_URI, echo=True, pool_size=10, max_overflow=20, pool_timeout=10, pool_recycle=3600, pool_pre_ping=True)`
- `AsyncSessionFactory` 由 `dependencies.get_session()` 注入到路由。
- ORM 基类 `Base` 设置统一命名约定，便于 Alembic 迁移生成稳定约束名。

### 6.3 认证

用户认证逻辑在 `core/auth.py`：

- 登录后生成 access token 与 refresh token。
- 前端把 token 存入 `uni` storage，并通过 `Authorization: Bearer <token>` 调用普通用户接口。
- 需要登录的接口通过 `AuthHandler().auth_access_dependency` 获取当前用户 ID。

管理员认证独立在 `admin_auth.py` 与后台路由中使用，前端通过 `admin_token` 调用后台接口。

开放平台 API Key 认证在 `core/api_key.py` 与 `repository/developer_repo.py`：

- API Key 明文只在创建时返回。
- 数据库存储 prefix 与 HMAC hash。
- 开放 API 调用使用 `Authorization: Bearer ak_xxx`。

## 7. 核心业务模块

### 7.1 用户注册登录

相关文件：

- 后端：`routers/auth_router.py`、`models/user.py`、`schemas/user_schemas.py`
- 前端：`pages/login/login.vue`、`pages/register/register.vue`、`api/auth.js`

业务流程：

1. 用户输入邮箱，请求 `GET /auth/code` 获取验证码。
2. 后端生成邮件验证码并通过 SMTP 发送。
3. 用户请求 `POST /auth/register` 完成注册。
4. 用户请求 `POST /auth/login` 登录，后端返回 token 与用户信息。
5. 前端存储 token，后续普通接口自动附带 Bearer Token。

### 7.2 AI 智能起名

相关文件：

- 后端：`routers/name_router.py`、`core/workflow.py`、`core/nametools.py`、`models/name_record.py`、`schemas/name_schemas.py`
- 前端：`pages/index/index.vue`、`api/name.js`

主要接口：

| 接口 | 说明 |
| --- | --- |
| `POST /name/get_names` | 旧版/直接命名接口 |
| `POST /name/generate` | LangGraph 带 thread_id 的智能起名 |
| `POST /name/feedback` | 基于上一轮 thread_id 的反馈微调 |

LangGraph 工作流：

```text
supervisor_node
  ├─ human_naming_node    # 人名
  ├─ company_naming_node  # 企业/品牌名
  └─ pet_naming_node      # 宠物名
```

命名输出使用 `NameResultSchema` 约束结构化结果。企业起名节点还会：

- 检索用户私有知识库上下文。
- 读取上一轮命名结果与用户反馈。
- 并发检查候选域名 `.com` 状态。
- 将 thread_id 绑定到 PostgreSQL checkpoint，实现连续微调。

### 7.3 企业知识库/RAG

相关文件：

- 后端：`routers/rag_router.py`、`core/rag_service.py`、`rag_worker.py`
- 前端：`api/knowledge.js`
- 数据目录：`AInameProject/chroma_rag_db/`

业务流程：

1. 用户上传文件到 `POST /knowledge/upload`。
2. 后端保存文件并将 `{user_id, file_path}` 投递到 RabbitMQ。
3. `rag_worker.py` 消费队列，解析 PDF/文本并写入 Chroma。
4. 企业起名时通过 `retrive_user_from_knowledge(user_id, search_query)` 检索私有知识，作为 Prompt 上下文。

### 7.4 品牌视觉生成

相关文件：

- 后端：`routers/brand_visual.py`、`services/bailian_service.py`、`models/brand_visual.py`、`schemas/brand_visual.py`
- 前端：`pages/brand/visual-generate.vue`、`pages/brand/visual-result.vue`、`api/brand.js`

主要接口：

| 接口 | 说明 |
| --- | --- |
| `POST /brand/visual/generate` | 生成品牌视觉方案、色彩、Logo Prompt、名片文案等 |
| `POST /brand/visual/image` | 根据 Logo Prompt 生成图片 |

外部能力：

- 文本生成：DashScope compatible chat completions。
- 图片生成：DashScope text2image task API。
- 当外部服务不可用时，`BailianService` 包含 fallback 方案生成逻辑。

### 7.5 专家市场

相关文件：

- 后端：`routers/expert.py`、`routers/expert_center.py`、`models/marketplace.py`、`models/account.py`、`schemas/marketplace.py`、`schemas/account.py`
- 前端：`pages/expert/*`、`pages/expert-center/*`、`api/expert.js`

用户侧能力：

- 申请成为专家：`POST /expert/apply`
- 浏览专家：`GET /experts`
- 查看专家详情：`GET /experts/{expert_id}`
- 创建专家订单：`POST /expert-orders`
- 查看/确认订单：`GET /expert-orders/{order_id}`、`POST /expert-orders/{order_id}/confirm`
- 提交评价：`POST /expert-orders/{order_id}/review`
- 创建售后：`POST /expert-orders/{order_id}/after-sales`

专家侧能力：

- 查看/更新专家资料：`GET/PUT /expert/profile`
- 查看统计：`GET /expert/center/statistics`
- 订单接单、完成、结算：`POST /expert/center/orders/{order_id}/accept|complete|settle`
- 收入与提现：`GET /expert/center/income`、`POST /expert/center/withdrawals`
- 评价回复与售后查看。

结算逻辑：

1. 用户创建专家订单，生成业务订单与支付流程。
2. 专家接单并提交报告。
3. 用户确认或专家中心触发到期结算。
4. 系统根据 `ExpertFeeRule` 拆分专家收入和平台抽佣。
5. 写入 `ExpertIncomeRecord`、`PlatformLedger` 等账务数据。

### 7.6 用户中心、钱包、会员、订单

相关文件：

- 后端：`routers/user_center.py`、`models/account.py`、`schemas/account.py`
- 前端：`pages/user/*`、`api/user.js`

主要能力：

- 个人资料：`GET/PUT /user/profile`
- 头像上传：`POST /user/avatar/upload`
- 余额查询：`GET /user/balance`
- 充值：`POST /user/recharge`
- 模拟支付：`POST /user/recharge/{order_id}/mock-pay`
- 会员套餐：`GET /user/membership/plans`
- 开通会员：`POST /user/membership/orders`
- 支付单查询与虚拟支付：`GET /user/payments/{payment_no}`、`POST /user/payments/{payment_no}/virtual-pay`
- 支付回调：`POST /user/payments/callback/{provider}`
- 订单列表与详情：`GET /user/orders`、`GET /user/orders/{order_id}`
- 余额支付、发起支付、退款、发票、钱包流水。

当前支付实现包含虚拟支付、模拟支付与回调签名校验，适合开发测试；接入真实支付时需要替换 `build_pay_url`、回调验签、交易查询与退款通道。

### 7.7 社区投票

相关文件：

- 后端：`routers/community.py`、`models/marketplace.py`、`schemas/marketplace.py`
- 前端：`pages/community/*`、`api/community.js`

能力：

- 创建投票帖：`POST /community/posts`
- 投票帖列表/详情：`GET /community/posts`、`GET /community/posts/{post_id}`
- 投票：`POST /community/posts/{post_id}/vote`
- 结果：`GET /community/posts/{post_id}/result`
- 排行：`GET /community/rank`

适用场景是让用户围绕候选名字发起投票，沉淀灵感与社区排行。

### 7.8 开放平台

相关文件：

- 后端：`routers/developer.py`、`routers/openapi.py`、`routers/admin_open_platform.py`、`models/developer.py`、`schemas/developer.py`、`repository/developer_repo.py`
- 前端：`pages/developer/*`、`api/developer.js`、后台开放平台页面

开发者侧：

- 申请开发者：`POST /developer/apply`
- 查看资料：`GET /developer/profile`
- Dashboard：`GET /developer/dashboard`
- API Key 创建/列表/禁用/删除。
- 调用日志：`GET /developer/logs`

开放 API：

| 接口 | 场景 |
| --- | --- |
| `POST /openapi/npc-name` | 游戏 NPC 命名 |
| `POST /openapi/novel-character` | 小说角色命名 |
| `POST /openapi/location-name` | 地名/组织名 |
| `POST /openapi/baby-name` | 宝宝起名 |
| `POST /openapi/company-name` | 企业品牌命名 |

调用链路：

1. 开发者申请并由后台审核通过。
2. 开发者创建 API Key。
3. 第三方使用 `Authorization: Bearer ak_xxx` 调用 `/openapi/*`。
4. 后端验证 Key 状态、额度、套餐/限流规则。
5. 调用 AI 生成名称。
6. 记录 `api_usage_logs` 与 `billing_records`，累加使用量。

后台开放平台：

- 开发者审核：`/admin/developers`
- API Key、调用日志、计费流水查看。
- 套餐创建/更新。
- 订阅、限流规则、计费汇总、对账记录。

### 7.9 管理后台

相关文件：

- 后端：`routers/admin.py`、`routers/admin_open_platform.py`、`models/admin.py`、`schemas/admin.py`
- 前端：`pages/admin/*`、`api/admin.js`

主要能力：

- 管理员登录：`POST /admin/login`
- 用户管理：用户列表、详情、状态更新。
- 命名记录：查询 AI 起名历史。
- 专家管理：专家审核、订单、评价、售后、收入、提现、抽佣规则。
- 财务管理：支付单、退款、发票、对账。
- 开放平台管理：开发者、API Key、日志、套餐、订阅、限流、账单、对账。

## 8. 数据模型概览

### 8.1 用户与认证

| 表 | ORM | 说明 |
| --- | --- | --- |
| `user` | `User` | 普通用户账号、密码、个人信息、状态等 |
| `email_code` | `EmailCode` | 邮箱验证码 |
| `admin_users` | `AdminUser` | 管理员账号 |

### 8.2 起名记录

| 表 | ORM | 说明 |
| --- | --- | --- |
| `name_records` | `NameRecord` | 用户起名主记录，保存类别、输入、thread_id 等 |
| `name_candidates` | `NameCandidate` | 候选名称、寓意、域名状态等 |

### 8.3 品牌视觉

| 表 | ORM | 说明 |
| --- | --- | --- |
| `brand_visual_records` | `BrandVisualRecord` | 品牌视觉生成记录 |

### 8.4 专家与社区

| 表 | ORM | 说明 |
| --- | --- | --- |
| `experts` | `Expert` | 专家资料、审核状态、评分等 |
| `expert_orders` | `ExpertOrder` | 专家服务订单 |
| `expert_reviews` | `ExpertReview` | 专家评价与回复 |
| `after_sale_requests` | `AfterSaleRequest` | 售后申请 |
| `community_posts` | `CommunityPost` | 投票帖 |
| `community_candidates` | `CommunityCandidate` | 投票候选项 |
| `community_votes` | `CommunityVote` | 用户投票记录 |

### 8.5 账户、订单与财务

| 表 | ORM | 说明 |
| --- | --- | --- |
| `recharge_orders` | `RechargeOrder` | 充值订单 |
| `membership_plans` | `MembershipPlan` | 会员套餐 |
| `membership_orders` | `MembershipOrder` | 会员购买订单 |
| `user_memberships` | `UserMembership` | 用户会员权益 |
| `orders` | `Order` | 统一业务订单 |
| `wallet_transactions` | `WalletTransaction` | 钱包流水 |
| `payment_orders` | `PaymentOrder` | 支付单 |
| `payment_transactions` | `PaymentTransaction` | 支付交易流水 |
| `payment_callback_events` | `PaymentCallbackEvent` | 支付回调记录 |
| `refund_orders` | `RefundOrder` | 退款单 |
| `reconciliation_records` | `ReconciliationRecord` | 对账记录 |
| `invoices` | `Invoice` | 发票记录 |
| `expert_income_records` | `ExpertIncomeRecord` | 专家收入记录 |
| `expert_fee_rules` | `ExpertFeeRule` | 专家抽佣规则 |
| `platform_ledgers` | `PlatformLedger` | 平台账本 |
| `expert_withdrawals` | `ExpertWithdrawal` | 专家提现 |

### 8.6 开放平台

| 表 | ORM | 说明 |
| --- | --- | --- |
| `developers` | `Developer` | 开发者申请与认证状态 |
| `api_keys` | `ApiKey` | API Key 元数据、哈希、额度、状态 |
| `api_usage_logs` | `ApiUsageLog` | 开放 API 调用日志 |
| `billing_records` | `BillingRecord` | Token/调用计费流水 |
| `plans` | `Plan` | 开放平台套餐 |
| `developer_subscriptions` | `DeveloperSubscription` | 开发者套餐订阅 |
| `api_rate_limit_rules` | `ApiRateLimitRule` | API 限流规则 |
| `api_billing_summaries` | `ApiBillingSummary` | 计费汇总 |
| `api_reconciliation_records` | `ApiReconciliationRecord` | API 对账记录 |

## 9. 前端结构与页面

### 9.1 请求封装

`AInameVue/utils/request.js` 提供三个核心函数：

- `request(url, options)`：普通用户接口，自动附带 `token`。
- `adminRequest(url, options)`：管理员接口，自动附带 `admin_token`。
- `uploadFile(url, filePath)`：文件上传，自动附带用户 token。

401/403 时会清理本地 token 并跳转登录页。

### 9.2 API 封装

| 文件 | 对应业务 |
| --- | --- |
| `api/auth.js` | 注册、登录、验证码 |
| `api/name.js` | 智能起名、反馈微调 |
| `api/knowledge.js` | 知识库上传 |
| `api/brand.js` | 品牌视觉生成 |
| `api/expert.js` | 专家市场与专家中心 |
| `api/user.js` | 用户中心、钱包、会员、订单 |
| `api/community.js` | 社区投票 |
| `api/developer.js` | 开发者中心 |
| `api/admin.js` | 管理后台 |

### 9.3 页面分组

| 目录 | 页面说明 |
| --- | --- |
| `pages/index` | 首页与 AI 起名主流程 |
| `pages/login`、`pages/register` | 登录注册 |
| `pages/brand` | 品牌视觉生成与结果页 |
| `pages/expert` | 专家列表、详情、购买、申请、工作台 |
| `pages/expert-center` | 专家资料、订单、收入、提现 |
| `pages/user` | 个人中心、资料、钱包、充值、会员、订单 |
| `pages/community` | 灵感投票帖列表、详情、创建 |
| `pages/developer` | 开发者中心、调用日志 |
| `pages/admin` | 后台登录、首页、用户、命名记录、专家、开放平台 |

## 10. 主要业务流程

### 10.1 普通用户起名闭环

```mermaid
flowchart TD
    A[用户登录] --> B[填写起名需求]
    B --> C[POST /name/generate]
    C --> D[LangGraph 按 category 路由]
    D --> E[DeepSeek 结构化生成]
    E --> F[企业名补充 RAG 与域名检查]
    F --> G[保存记录和候选名]
    G --> H[前端展示候选方案]
    H --> I{是否需要调整}
    I -->|是| J[POST /name/feedback]
    J --> D
    I -->|否| K[结束]
```

### 10.2 知识库增强企业起名

```mermaid
flowchart TD
    A[用户上传资料] --> B[POST /knowledge/upload]
    B --> C[保存文件]
    C --> D[投递 RabbitMQ]
    D --> E[rag_worker 消费]
    E --> F[解析与切分文档]
    F --> G[写入 Chroma]
    G --> H[企业起名检索私有知识]
    H --> I[补充到 Prompt]
```

### 10.3 专家服务交易

```mermaid
flowchart TD
    A[用户浏览专家] --> B[创建专家订单]
    B --> C[支付或余额扣款]
    C --> D[专家接单]
    D --> E[专家提交报告]
    E --> F[用户确认或到期结算]
    F --> G[计算专家收入与平台抽佣]
    G --> H[专家提现]
    F --> I[用户评价/售后]
```

### 10.4 开放平台调用

```mermaid
flowchart TD
    A[用户申请开发者] --> B[后台审核]
    B --> C[创建 API Key]
    C --> D[第三方调用 /openapi/*]
    D --> E[Bearer API Key 校验]
    E --> F[额度/状态/限流检查]
    F --> G[AI 生成]
    G --> H[写调用日志与计费流水]
    H --> I[开发者 Dashboard]
```

## 11. API 总览

### 11.1 用户认证

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/auth/code` | 获取邮箱验证码 |
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录 |

### 11.2 命名与知识库

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/name/get_names` | 旧版起名 |
| POST | `/name/generate` | 起名并创建 thread |
| POST | `/name/feedback` | 基于 thread 反馈微调 |
| POST | `/knowledge/upload` | 上传知识库文件 |

### 11.3 品牌视觉

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/brand/visual/generate` | 生成品牌视觉方案 |
| POST | `/brand/visual/image` | 生成 Logo 图片 |

### 11.4 专家与社区

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/expert/apply` | 申请专家 |
| GET | `/experts` | 专家列表 |
| GET | `/experts/{expert_id}` | 专家详情 |
| POST | `/expert-orders` | 创建专家订单 |
| GET | `/expert-orders/{order_id}` | 订单详情 |
| POST | `/expert-orders/{order_id}/confirm` | 用户确认订单 |
| POST | `/expert-orders/{order_id}/review` | 创建评价 |
| POST | `/expert-orders/{order_id}/after-sales` | 创建售后 |
| GET | `/expert/profile` | 专家中心资料 |
| PUT | `/expert/profile` | 更新专家资料 |
| GET | `/expert/center/statistics` | 专家统计 |
| GET | `/expert/center/orders` | 专家订单 |
| GET | `/expert/center/income` | 专家收入 |
| POST | `/expert/center/withdrawals` | 申请提现 |
| POST | `/community/posts` | 创建投票帖 |
| GET | `/community/posts` | 投票帖列表 |
| POST | `/community/posts/{post_id}/vote` | 投票 |
| GET | `/community/rank` | 排行 |

### 11.5 用户中心与财务

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET/PUT | `/user/profile` | 个人资料 |
| POST | `/user/avatar/upload` | 上传头像 |
| GET | `/user/balance` | 余额 |
| POST | `/user/recharge` | 创建充值订单 |
| GET | `/user/membership/plans` | 会员套餐 |
| POST | `/user/membership/orders` | 创建会员订单 |
| GET | `/user/payments/{payment_no}` | 支付单详情 |
| POST | `/user/payments/{payment_no}/virtual-pay` | 虚拟支付 |
| POST | `/user/payments/callback/{provider}` | 支付回调 |
| GET | `/user/orders` | 订单列表 |
| POST | `/user/orders/{order_id}/pay` | 余额支付 |
| POST | `/user/orders/{order_id}/refund` | 退款申请 |
| GET | `/user/wallet/transactions` | 钱包流水 |
| POST | `/user/invoices` | 申请发票 |

### 11.6 开放平台

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/developer/apply` | 申请开发者 |
| GET | `/developer/profile` | 开发者资料 |
| GET | `/developer/dashboard` | 开发者统计 |
| POST | `/developer/api-keys` | 创建 API Key |
| GET | `/developer/api-keys` | API Key 列表 |
| PUT | `/developer/api-keys/{key_id}/disable` | 禁用 API Key |
| DELETE | `/developer/api-keys/{key_id}` | 删除 API Key |
| GET | `/developer/logs` | 调用日志 |
| POST | `/openapi/npc-name` | NPC 命名 |
| POST | `/openapi/novel-character` | 小说角色命名 |
| POST | `/openapi/location-name` | 地名/组织名 |
| POST | `/openapi/baby-name` | 宝宝起名 |
| POST | `/openapi/company-name` | 企业命名 |

### 11.7 管理后台

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/admin/login` | 管理员登录 |
| GET | `/admin/dashboard/statistics` | 仪表盘统计 |
| GET | `/admin/users` | 用户列表 |
| PUT | `/admin/users/{user_id}/status` | 修改用户状态 |
| GET | `/admin/name-records` | 起名记录 |
| GET | `/admin/experts` | 专家列表 |
| PUT | `/admin/experts/{expert_id}/approve` | 通过专家 |
| PUT | `/admin/experts/{expert_id}/reject` | 拒绝专家 |
| GET | `/admin/expert-orders` | 专家订单 |
| GET | `/admin/payments` | 支付单 |
| GET | `/admin/refunds` | 退款单 |
| GET | `/admin/withdrawals` | 提现单 |
| GET | `/admin/invoices` | 发票 |
| POST | `/admin/reconciliations` | 创建对账 |
| GET | `/admin/after-sales` | 售后列表 |
| GET | `/admin/developers` | 开发者列表 |
| PUT | `/admin/developers/{developer_id}/approve` | 通过开发者 |
| PUT | `/admin/developers/{developer_id}/reject` | 拒绝开发者 |
| GET | `/admin/api-usage-logs` | API 调用日志 |
| GET/POST | `/admin/plans` | 套餐列表/创建 |
| POST/GET | `/admin/rate-limit-rules` | 限流规则 |

## 12. 开发规范建议

### 12.1 后端新增接口

建议按以下顺序开发：

1. 在 `schemas/` 定义请求和响应模型。
2. 在 `models/` 定义或扩展 ORM 模型。
3. 如涉及复杂查询，优先在 `repository/` 增加仓储方法。
4. 在 `routers/` 增加接口，使用 `Depends(get_session)` 获取会话。
5. 对写操作明确事务边界，成功后 `commit()`，失败时 `rollback()`。
6. 生成 Alembic 迁移并检查字段类型、索引、唯一约束。
7. 前端在 `api/*.js` 增加对应封装，再接页面。

### 12.2 前端新增页面

1. 在 `pages/` 下按业务域创建页面。
2. 在 `pages.json` 注册页面路径和导航标题。
3. 在 `api/` 增加接口封装，页面不要直接拼接复杂请求。
4. 通过 `utils/request.js` 统一处理 token、错误提示和登录跳转。
5. 对需要管理员权限的页面使用 `adminRequest`。

### 12.3 数据库迁移

```bash
cd AInameProject
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```

迁移前检查：

- 是否导入了新增模型到 `models/__init__.py`。
- 是否设置必要索引与唯一约束。
- 枚举/状态字段是否有默认值。
- 金额字段优先使用 Decimal 语义，避免 float 造成财务误差。

## 13. 审查发现与维护风险

本次代码审查主要聚焦项目结构、功能边界和业务链路，未执行完整测试。发现以下维护风险：

1. 中文编码显示异常  
   多个 `.py`、`.js`、`.json`、`.md` 文件中的中文注释、标题、提示文案出现 mojibake。建议统一确认文件实际编码，使用 UTF-8 保存，并避免编辑器按 GBK/ANSI 误写。

2. 配置默认值偏开发环境  
   数据库、RabbitMQ、局域网 IP、JWT 默认密钥等均带有本地默认值。生产部署必须通过 `.env` 覆盖，并避免提交真实密钥。

3. CORS 过宽  
   当前 `allow_origins=["*"]` 且允许 credentials，生产环境应收敛到可信域名。

4. 静态目录可能缺失  
   `main.py` 挂载 `StaticFiles(directory="static")`，但当前文件列表中未看到根级 `static/` 目录。如果运行目录下不存在该目录，应用启动可能报错。建议确认实际部署目录或改为显式创建/配置。

5. 支付仍偏模拟实现  
   目前存在 mock-pay、virtual-pay 与自定义回调签名，适合开发联调。接入真实支付时需要补齐交易查询、幂等、退款、对账和回调重放防护。

6. RAG Worker 配置硬编码  
   `rag_worker.py` 中 RabbitMQ 地址和队列名硬编码，建议迁移到 `settings`，与 `.env` 统一管理。

7. AI 外部调用需要降级策略  
   DeepSeek 和 DashScope 均依赖外部网络与 API Key。品牌视觉服务已有 fallback，命名主流程仍需明确外部服务失败时的错误提示、重试和限流策略。

8. 路由层承载业务较重  
   `routers/admin.py`、`routers/user_center.py`、`routers/expert.py` 包含较多财务和状态流转逻辑。后续建议逐步下沉到 service 层，降低路由文件复杂度。

9. 前端环境变量读取方式需确认  
   `utils/config.js` 使用 `process.env.VUE_APP_API_BASE_URL`，uni-app/Vite 项目中通常更推荐确认构建时环境变量注入方式，避免不同端构建时取不到值。

## 14. 推荐后续路线

短期：

- 修复编码问题，统一 UTF-8。
- 补齐 `.env.example`。
- 确认 `static/`、`uploads/`、`reports/` 目录创建策略。
- 为核心接口补充最小化测试：登录、起名、反馈、专家订单、支付虚拟回调、开发者 API Key。

中期：

- 将支付、专家结算、开放平台计费拆成 service 层。
- 为订单、支付、退款、提现增加状态机文档和幂等键。
- 为开放 API 增加限流中间件或统一依赖。
- 为 RAG Worker 增加任务状态表，前端可查看知识库处理进度。

长期：

- 完善真实支付渠道与对账闭环。
- 引入统一日志、链路追踪和异常监控。
- 为 AI 调用增加成本统计、缓存、熔断与降级。
- 将管理后台权限从单一角色扩展为 RBAC。

