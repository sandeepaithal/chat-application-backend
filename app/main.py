# app/main.py

from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.database import Base
from app.database import get_db
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from app.websocket_manager import manager
from app.models import User, Friend
from app.schemas import UserCreate, UserLogin, MessageCreate, FriendRequestCreate,UserProfileUpdate
from app.auth import hash_password, verify_password
from app.models import Room, DirectChat
from app.schemas import RoomCreate,RoomUpdate
from app.models import Message, Friend
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File
import shutil
import uuid
import os

# Create all tables in MySQL
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI()

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://chatsphere-ivory-nine.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Chat Application API Running"
    }


@app.post("/register")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    # Check if username already exists
    existing_user = (
        db.query(User)
        .filter(User.username == user.username)
        .first()
    )

    if existing_user:
        return {
            "message": "Username already exists"
        }

    # Check if email already exists
    existing_email = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_email:
        return {
            "message": "Email already exists"
        }

    # Hash password
    hashed_pw = hash_password(user.password)

    # Create user object
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw
    )

    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "username": new_user.username,
        "email": new_user.email
    }
@app.post("/rooms")
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db)
):
    existing_room = (
        db.query(Room)
        .filter(Room.name == room.name)
        .first()
    )

    if existing_room:
        return {"message": "Room already exists"}

    new_room = Room(name=room.name)

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return {
        "id": new_room.id,
        "name": new_room.name
    }
@app.get("/rooms")
def get_rooms(
    db: Session = Depends(get_db)
):
    return db.query(Room).all()

@app.post("/rooms/{room_id}/messages")
def send_message(
    room_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db)
):
    room = None
    if room_id not in (None, 0):
        room = (
            db.query(Room)
            .filter(Room.id == room_id)
            .first()
        )

        if not room:
            return {
                "message": "Room not found"
            }

    user = (
        db.query(User)
        .filter(User.id == data.user_id)
        .first()
    )

    if not user:
        return {
            "message": "User not found"
        }

    new_message = Message(
        content=data.content,
        message_type=data.message_type,

        file_name=data.file_name,
        file_url=data.file_url,
        file_size=data.file_size,
        mime_type=data.mime_type,

        user_id=data.user_id,

        room_id=room_id,
        direct_chat_id=data.direct_chat_id,
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return {
        "message_id": new_message.id,
        "content": new_message.content,

        "message_type": new_message.message_type,
        "file_name": new_message.file_name,
        "file_url": new_message.file_url,
        "file_size": new_message.file_size,
        "mime_type": new_message.mime_type,

        "room_id": room_id,
        "direct_chat_id": data.direct_chat_id,

        "user_id": data.user_id,
        "username": user.username
    }
@app.get("/rooms/{room_id}/messages")
def get_room_messages(
    room_id: int,
    db: Session = Depends(get_db)
):

    room = (
        db.query(Room)
        .filter(Room.id == room_id)
        .first()
    )

    if not room:
        return {
            "message": "Room not found"
        }
    messages = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .all()
    )

    result = []

    for message in messages:
        user = (
            db.query(User)
            .filter(User.id == message.user_id)
            .first()
        )

        result.append({
            "id": message.id,
            "content": message.content,
            "message_type": message.message_type,

            "file_name": message.file_name,
            "file_url": message.file_url,
            "file_size": message.file_size,
            "mime_type": message.mime_type,

            "created_at": message.created_at,
            "room_id": message.room_id,
            "user_id": message.user_id,
            "username": user.username if user else "Unknown",
            "profile_picture": (
                user.profile_picture if user else None
            )
        })

    return result
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
@app.post("/login")
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    db_user = (
        db.query(User)
        .filter(User.username == user.username)
        .first()
    )

    if not db_user:
        return {
            "message": "Invalid username or password"
        }

    if not verify_password(
        user.password,
        db_user.hashed_password
    ):
        return {
            "message": "Invalid username or password"
        }

    return {
        "message": "Login successful",
        "user_id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "profile_picture": db_user.profile_picture
    }
@app.put("/rooms/{room_id}")
def update_room(
    room_id: int,
    room: RoomUpdate,
    db: Session = Depends(get_db)
):
    db_room = (
        db.query(Room)
        .filter(Room.id == room_id)
        .first()
    )

    if not db_room:
        return {
            "message": "Room not found"
        }

    existing_room = (
        db.query(Room)
        .filter(
            Room.name == room.name,
            Room.id != room_id
        )
        .first()
    )

    if existing_room:
        return {
            "message": "Room name already exists"
        }

    db_room.name = room.name

    db.commit()
    db.refresh(db_room)

    return {
        "id": db_room.id,
        "name": db_room.name
    }
@app.delete("/rooms/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db)
):
    room = (
        db.query(Room)
        .filter(Room.id == room_id)
        .first()
    )

    if not room:
        return {
            "message": "Room not found"
        }

    # Delete all messages in the room
    (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .delete()
    )

    # Delete the room
    db.delete(room)

    db.commit()

    return {
        "message": "Room deleted successfully"
    }
@app.delete("/rooms/{room_id}/messages")
def clear_room_messages(
    room_id: int,
    db: Session = Depends(get_db)
):
    room = (
        db.query(Room)
        .filter(Room.id == room_id)
        .first()
    )

    if not room:
        return {
            "message": "Room not found"
        }

    (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .delete()
    )

    db.commit()

    return {
        "message": "Messages cleared successfully"
    }
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    # Generate unique filename
    extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{extension}"

    filepath = os.path.join("uploads", filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": filename,
        "url": f"http://127.0.0.1:8000/uploads/{filename}"
    }
@app.get("/users/search")
def search_users(
    username: str = Query(...),
    db: Session = Depends(get_db)
):
    users = (
        db.query(User)
        .filter(User.username.ilike(f"%{username}%"))
        .all()
    )

    result = []

    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })

    return result
@app.post("/friends/request")
def send_friend_request(
    request: FriendRequestCreate,
    db: Session = Depends(get_db)
):
    # Cannot send request to yourself
    if request.sender_id == request.receiver_id:
        return {
            "message": "You cannot send a friend request to yourself."
        }

    # Check sender
    sender = (
        db.query(User)
        .filter(User.id == request.sender_id)
        .first()
    )

    if not sender:
        return {
            "message": "Sender not found"
        }

    # Check receiver
    receiver = (
        db.query(User)
        .filter(User.id == request.receiver_id)
        .first()
    )

    if not receiver:
        return {
            "message": "Receiver not found"
        }

    # Check if request already exists
    existing_request = (
        db.query(Friend)
        .filter(
            (
                (Friend.sender_id == request.sender_id) &
                (Friend.receiver_id == request.receiver_id)
            ) |
            (
                (Friend.sender_id == request.receiver_id) &
                (Friend.receiver_id == request.sender_id)
            )
        )
        .first()
    )

    if existing_request:
        return {
            "message": "Friend request already exists."
        }

    friend_request = Friend(
        sender_id=request.sender_id,
        receiver_id=request.receiver_id,
        status="pending"
    )

    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)

    return {
        "message": "Friend request sent successfully.",
        "request_id": friend_request.id
    }
@app.put("/friends/{request_id}/accept")
def accept_friend_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    friend_request = (
        db.query(Friend)
        .filter(Friend.id == request_id)
        .first()
    )

    if not friend_request:
        return {
            "message": "Friend request not found"
        }

    friend_request.status = "accepted"

    db.commit()
    db.refresh(friend_request)

    return {
        "message": "Friend request accepted successfully."
    }
@app.put("/friends/{request_id}/reject")
def reject_friend_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    friend_request = (
        db.query(Friend)
        .filter(Friend.id == request_id)
        .first()
    )

    if not friend_request:
        return {
            "message": "Friend request not found"
        }

    friend_request.status = "rejected"

    db.commit()
    db.refresh(friend_request)

    return {
        "message": "Friend request rejected successfully."
    }
@app.get("/friends/requests/{user_id}")
def get_friend_requests(
    user_id: int,
    db: Session = Depends(get_db)
):
    requests = (
        db.query(Friend)
        .filter(
            Friend.receiver_id == user_id,
            Friend.status == "pending"
        )
        .all()
    )

    result = []

    for request in requests:
        sender = (
            db.query(User)
            .filter(User.id == request.sender_id)
            .first()
        )

        result.append({
            "request_id": request.id,
            "sender_id": sender.id,
            "username": sender.username,
            "email": sender.email,
            "status": request.status
        })

    return result
@app.get("/friends/{user_id}")
def get_friends(
    user_id: int,
    db: Session = Depends(get_db)
):
    friendships = (
        db.query(Friend)
        .filter(
            Friend.status == "accepted",
            (
                (Friend.sender_id == user_id) |
                (Friend.receiver_id == user_id)
            )
        )
        .all()
    )

    friends = []

    for friendship in friendships:

        # Find the other user
        friend_id = (
            friendship.receiver_id
            if friendship.sender_id == user_id
            else friendship.sender_id
        )

        friend = (
            db.query(User)
            .filter(User.id == friend_id)
            .first()
        )

        if friend:
            friends.append({
                "id": friend.id,
                "username": friend.username,
                "email": friend.email
            })

    return friends
@app.post("/direct-chats")
def create_or_get_direct_chat(
    sender_id: int,
    receiver_id: int,
    db: Session = Depends(get_db)
):
    # Look for an existing chat in either direction
    chat = (
        db.query(DirectChat)
        .filter(
            (
                (DirectChat.user1_id == sender_id) &
                (DirectChat.user2_id == receiver_id)
            ) |
            (
                (DirectChat.user1_id == receiver_id) &
                (DirectChat.user2_id == sender_id)
            )
        )
        .first()
    )

    # Return existing chat
    if chat:
        return {
            "id": chat.id,
            "user1_id": chat.user1_id,
            "user2_id": chat.user2_id
        }

    # Create new chat
    chat = DirectChat(
        user1_id=sender_id,
        user2_id=receiver_id
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return {
        "id": chat.id,
        "user1_id": chat.user1_id,
        "user2_id": chat.user2_id
    }
@app.get("/direct-chats/{chat_id}/messages")
def get_direct_messages(
    chat_id: int,
    db: Session = Depends(get_db)
):
    chat = (
        db.query(DirectChat)
        .filter(DirectChat.id == chat_id)
        .first()
    )

    if not chat:
        return {
            "message": "Direct chat not found"
        }

    messages = (
        db.query(Message)
        .filter(Message.direct_chat_id == chat_id)
        .all()
    )

    result = []

    for message in messages:
        user = (
            db.query(User)
            .filter(User.id == message.user_id)
            .first()
        )

        result.append({
            "id": message.id,
            "content": message.content,
            "created_at": message.created_at,
            "user_id": message.user_id,
            "username": user.username if user else "Unknown",
            "profile_picture": (
                user.profile_picture if user else None
            ),
            "message_type": message.message_type,
            "file_name": message.file_name,
            "file_url": message.file_url,
            "file_size": message.file_size,
            "mime_type": message.mime_type,
        })

    return result
@app.post("/direct-chats/{chat_id}/messages")
def send_direct_message(
    chat_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == data.user_id)
        .first()
    )

    if not user:
        return {"message": "User not found"}

    new_message = Message(
        content=data.content,
        user_id=data.user_id,
        direct_chat_id=chat_id,
        message_type=data.message_type,
        file_name=data.file_name,
        file_url=data.file_url,
        file_size=data.file_size,
        mime_type=data.mime_type,
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return {"message": "Sent"}
@app.get("/users/{user_id}")
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        return {
            "message": "User not found"
        }

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "dob": user.dob,
        "bio": user.bio,
        "profile_picture": user.profile_picture
    }
@app.put("/users/{user_id}")
def update_user_profile(
    user_id: int,
    profile: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        return {
            "message": "User not found"
        }

    user.full_name = profile.full_name
    user.phone = profile.phone
    user.dob = profile.dob
    user.bio = profile.bio
    user.profile_picture = profile.profile_picture

    db.commit()
    db.refresh(user)

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "dob": user.dob,
            "bio": user.bio,
            "profile_picture": user.profile_picture,
        }
    }