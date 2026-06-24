from datetime import datetime

from pwdlib import PasswordHash
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base

password_hash = PasswordHash.recommended()


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(50), default="admin")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = kwargs.pop("password", None)
        if password:
            self.password = password

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.password_hash = password_hash.hash(password)

    def check_password(self, password):
        return password_hash.verify(password, self.password_hash)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    action_type: Mapped[str] = mapped_column(String(50), index=True)
    target_field: Mapped[str] = mapped_column(String(50), default="")
    before_value: Mapped[str] = mapped_column(Text, default="")
    after_value: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
