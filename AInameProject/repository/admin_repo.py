from datetime import date

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin import AdminUser
from models.user import User


class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_admin_by_username(self, username: str):
        async with self.session.begin():
            result = await self.session.execute(select(AdminUser).where(AdminUser.username == username))
            return result.scalar_one_or_none()

    async def get_admin_by_id(self, admin_id: int):
        async with self.session.begin():
            result = await self.session.execute(select(AdminUser).where(AdminUser.id == admin_id))
            return result.scalar_one_or_none()

    async def admin_exists(self):
        async with self.session.begin():
            stmt = select(exists().where(AdminUser.id.is_not(None)))
            return await self.session.scalar(stmt)

    async def create_admin(self, username: str, password: str, role: str = "admin", status: str = "active"):
        async with self.session.begin():
            admin = AdminUser(username=username, password=password, role=role, status=status)
            self.session.add(admin)
            return admin

    async def count_admins(self):
        async with self.session.begin():
            return await self.session.scalar(select(func.count(AdminUser.id)))


class AdminUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_users(self, page: int = 1, page_size: int = 10, keyword: str | None = None):
        async with self.session.begin():
            stmt = select(User)
            count_stmt = select(func.count(User.id))
            if keyword:
                condition = or_(User.email.like(f"%{keyword}%"), User.username.like(f"%{keyword}%"))
                stmt = stmt.where(condition)
                count_stmt = count_stmt.where(condition)

            total = await self.session.scalar(count_stmt)
            result = await self.session.execute(
                stmt.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
            )
            return total or 0, result.scalars().all()

    async def get_user(self, user_id: int):
        async with self.session.begin():
            result = await self.session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    async def update_user_status(self, user_id: int, status: str):
        async with self.session.begin():
            result = await self.session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return None
            user.status = status
            return user

    async def count_users(self):
        async with self.session.begin():
            return await self.session.scalar(select(func.count(User.id)))

    async def count_today_users(self):
        async with self.session.begin():
            return await self.session.scalar(
                select(func.count(User.id)).where(func.date(User.created_at) == date.today())
            )
