from models import AsyncSessionFactory
from repository.admin_repo import AdminRepository


async def init_super_admin():
    session = AsyncSessionFactory()
    try:
        admin_repository = AdminRepository(session=session)
        exists = await admin_repository.admin_exists()
        if not exists:
            await admin_repository.create_admin(
                username="admin",
                password="admin123456",
                role="super_admin",
                status="active",
            )
    finally:
        await session.close()
