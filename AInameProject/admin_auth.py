import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

import settings
from dependencies import get_session
from repository.admin_repo import AdminRepository
from schemas.admin import AdminTokenData

security = HTTPBearer()


def encode_admin_token(admin_id: int, role: str):
    from datetime import datetime

    payload = {
        "iss": str(admin_id),
        "sub": "admin_access",
        "role": role,
        "exp": datetime.now() + settings.JWT_ACCESS_TOKEN_EXPIRES,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


async def get_current_admin(
        auth: HTTPAuthorizationCredentials = Security(security),
        session: AsyncSession = Depends(get_session),
):
    try:
        payload = jwt.decode(auth.credentials, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("sub") != "admin_access":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="管理员Token类型错误")
        admin_id = int(payload.get("iss"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="管理员Token已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="管理员Token不可用")

    admin_repository = AdminRepository(session=session)
    admin = await admin_repository.get_admin_by_id(admin_id)
    if not admin:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="管理员不存在")
    if admin.status != "active":
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="管理员账号已禁用")
    return AdminTokenData(admin_id=admin.id, username=admin.username, role=admin.role, status=admin.status)
