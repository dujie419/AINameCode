# AINameCode

AINameCode 是一个围绕 AI 起名场景构建的多端应用，包含 FastAPI 后端与 uni-app/Vue 前端。项目覆盖用户注册登录、AI 起名、知识库上传、品牌视觉生成、专家服务、用户中心、开发者开放平台和管理后台等功能。

## 项目结构

```text
AINameCode/
├── AInameProject/              # 后端 FastAPI 项目
│   ├── main.py                 # FastAPI 应用入口
│   ├── run.py                  # Windows 兼容启动入口
│   ├── settings/               # 环境变量与全局配置
│   ├── models/                 # SQLAlchemy ORM 模型
│   ├── schemas/                # Pydantic 请求/响应模型
│   ├── routers/                # API 路由
│   ├── core/                   # AI 工作流、RAG、认证、工具函数
│   ├── services/               # 第三方服务与业务服务
│   ├── repository/             # 数据访问封装
│   ├── alembictable/           # Alembic 数据库迁移
│   └── docs/                   # 后端文档
├── AInameVue/                  # 前端 uni-app/Vue 项目
│   ├── pages/                  # 页面
│   ├── components/             # 通用组件
│   ├── api/                    # 前端 API 封装
│   ├── utils/                  # 请求、路由、配置工具
│   └── package.json
├── docs/                       # 仓库级文档
├── scripts/                    # 辅助脚本
└── PROJECT_DEVELOPMENT_DOC.md  # 项目开发文档
```

## 技术栈

- 后端：Python 3.13、FastAPI、Uvicorn、SQLAlchemy、Alembic、MySQL、PostgreSQL、Redis、RabbitMQ
- AI 能力：LangChain、LangGraph、Chroma、DeepSeek、DashScope/阿里百炼
- 前端：uni-app、Vue 3、Vite、Sass
- 认证与安全：PyJWT、pwdlib[argon2]、API Key HMAC 签名

## 后端启动

进入后端目录：

```bash
cd AInameProject
```

复制并配置环境变量：

```bash
cp .env.example .env
```

安装依赖并执行迁移：

```bash
uv sync
alembic upgrade head
```

启动服务：

```bash
python run.py
```

启动后可访问：

```text
http://127.0.0.1:8000/docs
```

## 前端启动

进入前端目录：

```bash
cd AInameVue
```

安装依赖并启动 H5：

```bash
npm install
npm run dev:h5
```

常用构建命令：

```bash
npm run build:h5
npm run dev:mp-weixin
npm run build:mp-weixin
npm run dev:app
npm run build:app
```

## 常用环境变量

后端配置位于 `AInameProject/settings/__init__.py`，默认从 `AInameProject/.env` 读取。

| 变量 | 说明 |
| --- | --- |
| `DB_URI` | MySQL 主业务数据库连接 |
| `LANGGRAPH_DB_URI` | LangGraph checkpoint PostgreSQL 连接 |
| `JWT_SECRET_KEY` | JWT 签名与 API Key HMAC 密钥 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_MODEL` | DeepSeek 模型名称 |
| `DASHSCOPE_API_KEY` | DashScope/阿里百炼 API Key |
| `MAIL_USERNAME` | SMTP 用户名 |
| `MAIL_PASSWORD` | SMTP 密码或授权码 |
| `MAIL_SERVER` | SMTP 服务器 |
| `MAIL_PORT` | SMTP 端口 |

## 知识库 Worker

知识库上传任务会通过 RabbitMQ 投递，解析与向量化由后端 Worker 处理：

```bash
cd AInameProject
python rag_worker.py
```

## 说明

- `.env`、虚拟环境、IDE 配置、本地 Chroma 数据库、上传文件和生成报告默认不会提交到 Git。
- `.env.example` 只保留配置项名称和脱敏占位符，实际 API Key、数据库密码、JWT 密钥等敏感信息请只写入本地 `.env` 或部署环境变量。
- 更完整的业务设计与接口说明见 `PROJECT_DEVELOPMENT_DOC.md` 和 `AInameProject/docs/`。
