from sqlalchemy.ext.asyncio.session import AsyncSession
from models.user import User,EmailCode
from sqlalchemy import select,update,delete,exists
from datetime import datetime,timedelta

from schemas.user_schemas import UserCreateSchema


class EmailCodeRepository():

    def __init__(self,session: AsyncSession):
        self.session = session

    # 把一条email_code数据插入到数据库
    async def create_email_code(self,email:str,code:str):
        async with self.session.begin():
            # 准备与email_code表对应的一个对象
            email_code = EmailCode(email=email,code=code)
            self.session.add(email_code)

            return email_code

    async def check_email_code(self,email:str,code:str):
        async with (self.session.begin()):
            email_code= await self.session.scalar(select(EmailCode).filter(EmailCode.email==email,EmailCode.code==code))

            if not email_code:
                return False
            if(datetime.now() - email_code.created_time) >= timedelta(minutes=5):
                return False
            return True

class UserRepository():
    def __init__(self,session: AsyncSession):
        self.session = session

    # 判断传过来的邮箱收被他人注册
    async def get_user_by_email(self,email:str):
        async with self.session.begin():
            result = await self.session.execute(select(User).where(User.email==email))
            return result.scalar_one_or_none()
    # 插入一条数据
    async def create_user(self,user:UserCreateSchema):
        async with self.session.begin():
            user = User(**user.model_dump())
            self.session.add(user)
            return user
    # 判断传过来的邮箱是否已经存在于数据库中
    async def email_is_exist(self, email: str) -> bool | None:
        async with self.session.begin():
            stmt = select(exists().where(User.email==email))
            return await self.session.scalar(stmt)