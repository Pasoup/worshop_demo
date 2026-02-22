import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List



app = FastAPI()
clients = set()
room_states = {} #turn this to PostSQL later
class ConnectionManager:
    def __init__(self):
        
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
       
        await websocket.accept()
      
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
   
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str, exclude: WebSocket = None):
       
        for connection in self.active_connections:
            if connection != exclude:
                await connection.send_text(message)
manager = ConnectionManager()
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket)
    if room_id in room_states:
        initial_code = room_states[room_id]
        await websocket.send_text(initial_code)
    try:
        while True:
            data = await websocket.receive_text()
            room_states[room_id] = data
            await manager.broadcast(data, exclude=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for client in clients:
                if client != websocket:
                    await client.send_text(data)
    except WebSocketDisconnect:
        clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
    