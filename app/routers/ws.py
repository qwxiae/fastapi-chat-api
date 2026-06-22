import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection_manager import manager
from app.core.constants import MESSAGE_HISTORY
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.message import Message
from app.models.room_member import RoomMember
from app.models.user import User

router = APIRouter(tags=["websocket"])


async def _authenticate_ws(token: str, db: AsyncSession) -> User | None:
    """
    WebSockets can't use Depends(get_current_user) the same way
    HTTP routes do, since there's no Authorization header mechanism
    in the WebSocket handshake
    """
    user_id = decode_access_token(token)
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


@router.websocket("/ws/rooms/{room_id}")
async def room_websocket(
    websocket: WebSocket,
    room_id: str,
):
    from app.core.database import AsyncSessionLocal

    await websocket.accept()

    async with AsyncSessionLocal() as db:
        user = None
        try:
            # 1) First message must be auth
            raw_auth = await websocket.receive_text()
            auth_data = json.loads(raw_auth)

            if auth_data.get("type") != "auth" or "token" not in auth_data:
                await websocket.close(code=4401)
                return

            user = await _authenticate_ws(auth_data["token"], db)
            if not user:
                # custom code, "unauthorized"
                await websocket.close(code=4401)
                return

            result = await db.execute(
                select(RoomMember).where(
                    RoomMember.room_id == room_id,
                    RoomMember.user_id == user.id,
                )
            )

            if not result.scalar_one_or_none():
                # "forbidden"
                await websocket.close(code=4403)
                return

            manager.connect(websocket, room_id, user.id)
            print(
                f"[DEBUG] {user.username} ({user.id}) just connected to room {room_id}"
            )
            # announce user
            await manager.broadcast(
                room_id,
                {"type": "user_joined", "user_id": user.id, "username": user.username},
                exclude=websocket,
            )
            # 2) Send recent history to the newly connected client
            result = await db.execute(
                select(Message)
                .where(Message.room_id == room_id)
                .order_by(Message.created_at.desc())
                .limit(MESSAGE_HISTORY)
            )

            history = list(reversed(result.scalars().all()))

            await websocket.send_json(
                {
                    "type": "history",
                    "messages": [
                        {
                            "id": m.id,
                            "content": m.content,
                            "user_id": m.user_id,
                            "created_at": m.created_at.isoformat(),
                        }
                        for m in history
                    ],
                }
            )

            # 3) Wait for new messages or write a new message in connection
            while True:
                raw_data = await websocket.receive_text()
                data = json.loads(raw_data)
                msg_type = data.get("type")

                if msg_type == "message":
                    message = Message(
                        content=data["content"],
                        user_id=user.id,
                        room_id=room_id,
                    )
                    db.add(message)
                    await db.commit()
                    await db.refresh(message)

                    await manager.broadcast(
                        room_id,
                        {
                            "type": "message",
                            "id": message.id,
                            "content": message.content,
                            "user_id": user.id,
                            "created_at": message.created_at.isoformat(),
                        },
                    )

                elif msg_type == "typing":
                    await manager.broadcast(
                        room_id,
                        {
                            "type": "typing",
                            "user_id": user.id,
                            "username": user.username,
                        },
                        exclude=websocket,
                    )
        except WebSocketDisconnect:
            pass
        finally:
            if user:
                manager.disconnect(websocket, room_id)
                await manager.broadcast(
                    room_id,
                    {
                        "type": "user_left",
                        "user_id": user.id,
                        "username": user.username,
                    },
                )
