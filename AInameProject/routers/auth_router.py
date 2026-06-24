import random

from fastapi import APIRouter, Query, Depends, HTTPException
import string

from fastapi_mail import MessageSchema, MessageType, FastMail
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from pydantic import EmailStr

from dependencies import get_email, get_session

from repository.user_repo import EmailCodeRepository

from core.redisconfig import get_redis_client

from redis.asyncio.client import Redis

router = APIRouter(prefix="/auth", tags=["auth"])
@router.get("/code",response_model=None)
async def get_email_code(
        email:Annotated[EmailStr,Query(...)],
        fastmail:FastMail=Depends(get_email),
        session:AsyncSession=Depends(get_session),
        redis:Redis=Depends(get_redis_client)
):

    # 1.生成验证码
    # 4位数验证码 0123456789012345678901234567890123456789
    source = string.digits*4

    # sample从source这个字符串中取出4位数
    code = "".join(random.sample(source,4))

    # 2.创建一个邮件
    message = MessageSchema(
        subject="【AI起名字APP】注册验证码",
        recipients=[email],
        body=f"您的验证码是：{code}，5分钟内有效",
        subtype=MessageType.plain
    )

    # 3.发送邮件
    await fastmail.send_message(message)

    # # 4.把发送的邮件信息保存起来
    # email_repository = EmailCodeRepository(session=session)
    # await email_repository.create_email_code(email,code)

    # redis存储的key和value是我们设计的，取值时要用同样的规则
    await redis.set(email,code,ex=300)
    return {"message":"验证码发送成功"}

from schemas.user_schemas import RegisterIn, UserCreateSchema, LoginIn,LoginOut
from repository.user_repo import UserRepository

@router.post("/register",response_model=None)
async def register(
        userinfo: RegisterIn,
        session: AsyncSession = Depends(get_session),
        redis:Redis=Depends(get_redis_client)
):
    # 向用户表插入数据
    userRepository = UserRepository(session=session)
    # 1.邮箱是否已被注册，请直接登录
    email_exist = await userRepository.email_is_exist(email=userinfo.email)
    if email_exist:
        raise HTTPException(status_code=400,detail="Email already exist")
    # 2.看验证码是否正确
    # emailCodeRepository = EmailCodeRepository(session=session)
    # email_code_bool = await emailCodeRepository.check_email_code(userinfo.email,userinfo.code)
    email_code = await redis.get(userinfo.email)
    # print(f"Redis中的验证码: {email_code}, 用户输入的验证码: {userinfo.code}")
    if (not email_code) or (userinfo.code !=  email_code):
        raise HTTPException(status_code=400,detail="Email Code does not exist")


    # 3.允许注册
    userCreateSchema = UserCreateSchema(
            email=userinfo.email,
            username=userinfo.username,
            password=userinfo.password
    )
    await userRepository.create_user(userCreateSchema)

    await redis.delete(userinfo.email)
    return {"message":"恭喜您注册成功"}

from models.user import User
from core.auth import AuthHandler


authHandler = AuthHandler()
import jwt
@router.post("/login",response_model=LoginOut)
async def login(
        userinfo:LoginIn,
        session: AsyncSession = Depends(get_session),
                ):
    # 获取你的信息，邮箱，根据
    # 1.登录需要确定是否为已注册用户
    userRepository = UserRepository(session=session)
    user:User|None = await userRepository.get_user_by_email(userinfo.email)
    if not user:
        raise HTTPException(status_code=400,detail="该用户不存在")
    if getattr(user, "status", "active") != "active":
        raise HTTPException(status_code=403,detail="账号已被禁用")
    # 2.看密码对不对，密码错误不让登录
    if not user.check_password(userinfo.password):
        raise HTTPException(status_code=400,detail="密码输入错误，请核对后输入")
    # 3.密码正确，允许登录
    tokens = authHandler.encode_login_token(user.id)
    return {
        "user":user,
        "token":tokens["access_token"],
    }
