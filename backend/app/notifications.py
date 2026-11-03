
import os
import jwt

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


class NotificationManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


notification_manager = NotificationManager()


@router.websocket("/ws")
async def notification_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token")
    secret = os.getenv("JWT_SECRET_KEY")

    if not token or not secret:
        await websocket.close(code=1008, reason="Authentication required")
        return

    db: Session = SessionLocal()

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = int(payload.get("sub", ""))

        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active or user.role != "owner":
            await websocket.close(code=1008, reason="Owner access required")
            return

        await notification_manager.connect(websocket)

        while True:
            # Keep the connection alive while waiting for messages.
            await websocket.receive_text()

    except (jwt.InvalidTokenError, ValueError, TypeError):
        await websocket.close(code=1008, reason="Invalid token")
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)
    finally:
        notification_manager.disconnect(websocket)
        db.close()
