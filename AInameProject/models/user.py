from datetime import datetime
from decimal import Decimal

from pwdlib import PasswordHash
from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base

password_hash = PasswordHash.recommended()


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    _password: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="active")
    user_level: Mapped[str] = mapped_column(String(30), default="normal")
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    frozen_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    is_expert: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = kwargs.pop("password", None)
        if password:
            self.password = password

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = password_hash.hash(password)

    def check_password(self, password):
        return password_hash.verify(password, self._password)


class EmailCode(Base):
    __tablename__ = "email_code"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(100))
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
