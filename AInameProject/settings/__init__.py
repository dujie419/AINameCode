import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


DB_URI = os.getenv("DB_URI", "mysql+aiomysql://root:123456@127.0.0.1:3306/ainame?charset=utf8")
LANGGRAPH_DB_URI = os.getenv("LANGGRAPH_DB_URI", "postgresql://postgres:123456@127.0.0.1:5432/ainame")

MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)
MAIL_PORT = get_int("MAIL_PORT", 587)
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.qq.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "ainameapp")
MAIL_STARTTLS = get_bool("MAIL_STARTTLS", True)
MAIL_SSL_TLS = get_bool("MAIL_SSL_TLS", False)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "please-change-this-secret")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=get_int("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 15))
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=get_int("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 30))
PAYMENT_CALLBACK_SECRET = os.getenv("PAYMENT_CALLBACK_SECRET", JWT_SECRET_KEY)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-plus")
DASHSCOPE_API_URL = os.getenv(
    "DASHSCOPE_API_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
)
DASHSCOPE_IMAGE_MODEL = os.getenv("DASHSCOPE_IMAGE_MODEL", "wanx2.1-t2i-turbo")
DASHSCOPE_IMAGE_API_URL = os.getenv(
    "DASHSCOPE_IMAGE_API_URL",
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
)
DASHSCOPE_TASK_API_URL = os.getenv(
    "DASHSCOPE_TASK_API_URL",
    "https://dashscope.aliyuncs.com/api/v1/tasks",
)
