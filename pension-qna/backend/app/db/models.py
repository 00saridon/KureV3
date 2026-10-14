from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .session import Base


class Room(Base):
    __tablename__ = 'rooms'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text)
    capacity: Mapped[int] = mapped_column(Integer)
    base_price: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="room")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(30))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    guest_name: Mapped[str] = mapped_column(String(100))
    guest_phone: Mapped[str] = mapped_column(String(30), index=True)
    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    guest_count: Mapped[int] = mapped_column(Integer)
    total_price: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="confirmed", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    room: Mapped[Room] = relationship(back_populates="reservations")
    user: Mapped[User | None] = relationship(back_populates="reservations")


class FaqEntry(Base):
    __tablename__ = 'faq_entries'
    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(String(300))
    answer: Mapped[str] = mapped_column(Text)
    source_text: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
