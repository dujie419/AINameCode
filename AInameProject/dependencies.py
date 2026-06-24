from core.mailtools import creat_mail_instance
from fastapi_mail import FastMail

async def get_email():
    """
       获取邮件发送实例

       返回:
           FastMail对象

       用途:
           FastAPI依赖注入(Depends)

       例如:

           @router.post("/send")
           async def send_email(
               mail: FastMail = Depends(get_email)
           ):
               ...

       """
    return creat_mail_instance()

from models import AsyncSessionFactory
from sqlalchemy.ext.asyncio import AsyncSession

async def get_session():
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()