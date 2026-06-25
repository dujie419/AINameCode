"""
数据库初始化模块

作用：
1. 创建数据库连接引擎 Engine
2. 创建异步 Session 工厂
3. 定义所有 ORM 模型继承的 Base
4. 导入所有 Model，注册到 SQLAlchemy
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from settings import DB_URI # 数据库连接地址

# 创建异步数据库引擎
engine = create_async_engine(
DB_URI,
# 将输出所有执行SQL的日志（默认是关闭的）
echo=True,
# 连接池大小（默认是5个）
pool_size=10,
# 允许连接池最大的连接数（默认是10个）
max_overflow=20,
# 获得连接超时时间（默认是30s）
pool_timeout=10,
# 连接回收时间（默认是-1，代表永不回收）
pool_recycle=3600,
# 连接前是否预检查（默认是False）
pool_pre_ping=True,
)

# Session工厂
AsyncSessionFactory = async_sessionmaker(
    # 绑定数据库引擎
    bind=engine,

    # 自动刷新
    autoflush=True,

    # 提交事务后不让对象失效
    expire_on_commit=False
)

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# 定义命名约定的Base类
class Base(DeclarativeBase):
    metadata = MetaData(
        # 统一管理约束名称
        naming_convention={
            # ix: index，索引
            "ix": "ix_%(column_0_label)s",
            # un: unique，唯一约束
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            # ck: Check，检查约束
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            # fk: Foreign Key，外键约束
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            # pk: Primary Key，主键约束
            "pk": "pk_%(table_name)s"
    })

# 导入所有Model
from . import user
from . import admin
from . import brand_visual
from . import marketplace
from . import developer
from . import account
from . import name_record
from . import growth


'''
alembic init alembictable --template async

修改：
alembic.ini
注释第61行 # sqlalchemy.url = driver://user:pass@localhost/dbname
alembic.ini
alembic下env.py
import settings
from models import Base
# 添加连接数据库的配置
database_url = settings.DB_URI
if database_url is None:
raise ValueError("DB_URI没有设置!")
config.set_main_option("sqlalchemy.url", database_url)
# 修改第31行
target_metadata = Base.metadata

alembic revision --autogenerate -m "add user email_code model"
alembic upgrade head
'''
