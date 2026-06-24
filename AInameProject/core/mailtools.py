from fastapi_mail import FastMail,ConnectionConfig
from pydantic import EmailStr,SecretStr
import settings

def creat_mail_instance():
    """
        创建邮件发送实例

        返回:
            FastMail对象

        用于:
            - 用户注册验证码
            - 找回密码验证码
            - 邮箱验证
            - 系统通知邮件
        """
    # 邮件服务器配置
    config = ConnectionConfig(

        # 发件邮箱账号
        # 例如:
        # 123456@qq.com
        MAIL_USERNAME=settings.MAIL_USERNAME,

        # 邮箱授权码
        # 注意:
        # 不是邮箱登录密码
        MAIL_PASSWORD=settings.MAIL_PASSWORD,

        # 发件人邮箱
        MAIL_FROM=settings.MAIL_FROM,

        # SMTP服务器端口
        # QQ邮箱:
        # 465 或 587
        MAIL_PORT=settings.MAIL_PORT,

        # SMTP服务器地址
        # 例如:
        # smtp.qq.com
        MAIL_SERVER=settings.MAIL_SERVER,

        # 发件人名称
        # 用户收到邮件时显示
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,

        # STARTTLS加密
        MAIL_STARTTLS=settings.MAIL_STARTTLS,

        # SSL/TLS加密
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,

        # 是否使用用户名密码认证
        USE_CREDENTIALS=True,

        # 是否验证SSL证书
        VALIDATE_CERTS=True,
    )

    # 创建邮件发送器
    return FastMail(config)