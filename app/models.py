# app/models.py

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Date

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )
    full_name = Column(String(100), nullable=True)

    phone = Column(String(20), nullable=True)

    dob = Column(Date, nullable=True)

    bio = Column(String(300), nullable=True)

    profile_picture = Column(String(300), nullable=True)
    messages = relationship(
        "Message",
        back_populates="user"
    )
    sent_requests = relationship(
        "Friend",
        foreign_keys="Friend.sender_id"
    )

    received_requests = relationship(
        "Friend",
        foreign_keys="Friend.receiver_id"
    )
class Message(Base):

    __tablename__ = "messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Text message (nullable because file messages won't have text)
    content = Column(
        String(1000),
        nullable=True
    )

    # "text" or "file"
    message_type = Column(
        String(20),
        default="text",
        nullable=False
    )

    # File details
    file_name = Column(
        String(255),
        nullable=True
    )

    file_url = Column(
        String(500),
        nullable=True
    )

    file_size = Column(
        Integer,
        nullable=True
    )

    mime_type = Column(
        String(255),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    room_id = Column(
        Integer,
        ForeignKey("rooms.id")
    )
    direct_chat_id = Column(
        Integer,
        ForeignKey("direct_chats.id"),
        nullable=True
    )

    user = relationship(
        "User",
        back_populates="messages"
    )

    room = relationship(
        "Room",
        back_populates="messages"
    )

class Room(Base):

    __tablename__ = "rooms"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False
    )

    messages = relationship(
        "Message",
        back_populates="room"
    )
class Friend(Base):

    __tablename__ = "friends"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    sender_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    receiver_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    status = Column(
        String(20),
        default="pending"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
class DirectChat(Base):

    __tablename__ = "direct_chats"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user1_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    user2_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )