from pydantic import BaseModel
from typing import Optional
from typing import Optional
from datetime import date


class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class MessageCreate(BaseModel):
    user_id: int

    # Text message
    content: Optional[str] = None
    room_id: Optional[int] = None
    direct_chat_id: Optional[int] = None

    # Message type
    message_type: str = "text"

    # File details
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
class RoomCreate(BaseModel):
    name: str
class UserLogin(BaseModel):
    username: str
    password: str
class RoomUpdate(BaseModel):
    name: str
class FriendRequestCreate(BaseModel):
    sender_id: int
    receiver_id: int
class FriendRequestAction(BaseModel):
    status: str
class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None