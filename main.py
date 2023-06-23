import json
from typing import List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Response
from fastapi.templating import Jinja2Templates
from schemas import RegisterValidator

app = FastAPI()
templates = Jinja2Templates(directory="templates")


class SocketManager:
    """Connect users to websocket with the help of connect function.
    Disconnect/Remove users with disconnect function.
    Send messages to all the connected users with broadcast function"""
    def __init__(self):
        self.active_connections: List[(WebSocket, str)] = []

    async def connect(self, websocket: WebSocket, user: str):
        await websocket.accept()
        self.active_connections.append((websocket, user))

    def disconnect(self, websocket: WebSocket, user: str):
        self.active_connections.remove((websocket, user))

    async def broadcast(self, data):
        for connection in self.active_connections:
            await connection[0].send_json(data)


manager = SocketManager()


@app.websocket('/api/chat')
async def chat(websocket: WebSocket):
    """Check to see if user is registered/authenticated by reading from browser cookie.
    Connect user to websocket with SocketManager's connect(). Get data from connected user and broadcast it
    to all connected users with websocket.receive_json() and broadcast() respectively."""
    sender = websocket.cookies.get('X-Authorization')
    if sender:
        await manager.connect(websocket, sender)
        response = {
            'sender': sender,
            'message': 'connected'
        }
        await manager.broadcast(response)
        try:
            while True:
                data = await websocket.receive_json()
                await manager.broadcast(data)
        except WebSocketDisconnect:
            manager.disconnect(websocket, sender)
            response['message'] = 'left chat'
            await manager.broadcast(response)


@app.get('/api/current_user')
def get_user(request: Request):
    """Get user by reading browser cookie."""
    current_user = request.cookies.get('X-Authorization')
    return current_user


@app.post('/api/register')
def register_user(user: RegisterValidator, response: Response):
    """Get username from the frontend and validate it.
    Create a cookie on the browser with httponly set to True so that no script gets hold of it"""
    return response.set_cookie(key='X-Authorization', value=user.username, httponly=True)


@app.get('/')
async def get_home(request: Request):
    data = {'request': request}
    return templates.TemplateResponse('home.html', data)


@app.get('/chat')
async def get_chat(request: Request):
    data = {'request': request}
    return templates.TemplateResponse('chat.html', data)




