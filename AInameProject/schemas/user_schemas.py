from pydantic import BaseModel, EmailStr, Field, model_validator,ValidationError
from typing import Annotated

RawPasswordStr = Annotated[str,Field(...,min_length=4,max_length=50)]
RawUsernameStr = Annotated[str,Field(...,min_length=4,max_length=50)]
class RegisterIn(BaseModel):
    email: EmailStr
    username: RawUsernameStr
    password: RawPasswordStr
    confirm_password: RawPasswordStr
    # 验证用户的有效性
    code:Annotated[str,Field(...,min_length=4,max_length=4)]
    invite_code: Annotated[str | None, Field(None, max_length=32)] = None
    partner_code: Annotated[str | None, Field(None, max_length=32)] = None

    # 完成确认密码的校验
    @model_validator(mode="after")
    def password_is_valid(self) -> bool:
        password = self.password
        confirm_password = self.confirm_password
        if password != confirm_password:
            return ValidationError("Passwords don't match")
        return self

class UserCreateSchema(BaseModel):
    email: EmailStr
    username:RawUsernameStr
    password:RawPasswordStr


# 开发对象，接受用户登录信息
class LoginIn(BaseModel):
    email: EmailStr
    password: RawPasswordStr

class UserSchema(BaseModel):
    id: Annotated[int,Field(...)]
    username: RawUsernameStr
    email: EmailStr


class LoginOut(BaseModel):
    user: UserSchema
    token: str
