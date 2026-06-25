from fastapi import FastAPI, Depends
from fastapi_mail import FastMail, MessageSchema, MessageType
from dependencies import get_email
from routers.auth_router import router as auth_router
from routers.name_router import router as name_router
from routers.rag_router import router as knowledge_router
from routers.admin import router as admin_router
from routers.admin_open_platform import router as admin_open_platform_router
from routers.brand_visual import router as brand_visual_router
from routers.expert import router as expert_router
from routers.expert_center import router as expert_center_router
from routers.community import router as community_router
from routers.developer import router as developer_router
from routers.openapi import router as openapi_router
from routers.user_center import router as user_center_router
from routers.growth import router as growth_router
from contextlib import asynccontextmanager
from core.workflow import init_workflow_graph, close_workflow_graph
from services.admin_service import init_super_admin
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动时，安全地初始化带记忆的工作流
    await init_workflow_graph()
    await init_super_admin()
    yield
    # 服务停止时，清理数据库连接
    await close_workflow_graph()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # 允许请求的源列表
    allow_credentials=True,    # 允许携带 Cookie/凭证
    allow_methods=["*"],       # 允许的请求方法（"GET", "POST", "PUT", "DELETE" 等，"*" 表示全部允许）
    allow_headers=["*"],       # 允许的请求头（"*" 表示全部允许）
)


app.include_router(auth_router)
app.include_router(name_router)
app.include_router(knowledge_router)
app.include_router(admin_router)
app.include_router(admin_open_platform_router)
app.include_router(brand_visual_router)
app.include_router(expert_router)
app.include_router(user_center_router)
app.include_router(expert_center_router)
app.include_router(community_router)
app.include_router(developer_router)
app.include_router(openapi_router)
app.include_router(growth_router)
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/email/text")
# GET请求接口
# 访问：
# http://127.0.0.1:8000/email/text?email=xxx@qq.com
async def mail_email(
        # 收件人邮箱
        # FastAPI自动从Query参数获取
        email: str,
        # FastAPI依赖注入
        # 自动调用 get_email()
        # 获取 FastMail 实例
        mail:FastMail=Depends(get_email)
):
    message = MessageSchema(
        # 邮件主题
        subject="ainame验证码",

        # 收件人列表
        # 即使只有一个收件人
        # 也必须是列表格式
        recipients=[email],

        # 邮件正文
        body=f"Hello {email}",

        # 邮件格式
        # plain = 纯文本
        subtype=MessageType.plain
    )
    # 异步发送邮件
    await mail.send_message(message)
    # 返回响应
    return {"message": "邮件发送成功"}
'''
浏览器请求
      ↓
/email/text?email=test@qq.com
      ↓
FastAPI路由
      ↓
Depends(get_email)
      ↓
创建FastMail实例
      ↓
构建MessageSchema
      ↓
SMTP服务器
      ↓
发送邮件
      ↓
QQ邮箱/Gmail
      ↓
用户收到邮件
      ↓
返回JSON
'''
