from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # room_id -> list of (websocket, user_id) currently connected
        self.active_connections: dict[str, list[tuple[WebSocket, str]]] = {}

    def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        # endpoint accepts
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append((websocket, user_id))

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                (ws, uid)
                for ws, uid in self.active_connections[room_id]
                if ws != websocket
            ]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(
        self, room_id: str, message: dict, exclude: WebSocket | None = None
    ):
        if room_id not in self.active_connections:
            return
        for ws, _ in self.active_connections[room_id]:
            if ws is exclude:
                continue
            await ws.send_json(message)

    def online_user_ids(self, room_id: str) -> set[str]:
        if room_id not in self.active_connections:
            return set()
        return {uid for _, uid in self.active_connections[room_id]}


manager = ConnectionManager()
