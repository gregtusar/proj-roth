import socketio
from typing import Optional
import json
import asyncio
from core.config import settings

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS,
    logger=settings.DEBUG,
    engineio_logger=settings.DEBUG
)

# Create Socket.IO ASGI app
sio_app = socketio.ASGIApp(
    sio,
    socketio_path='/socket.io'
)

# Store active connections
connections = {}

@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    print(f"Client {sid} connected")
    connections[sid] = {
        'authenticated': False,
        'user_id': None
    }
    
    # Verify authentication token if provided
    if auth and 'token' in auth:
        # TODO: Verify JWT token and get user info
        connections[sid]['authenticated'] = True
        connections[sid]['user_id'] = 'user_id_from_token'
    
    return True

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Client {sid} disconnected")
    if sid in connections:
        del connections[sid]

@sio.event
async def send_message(sid, data):
    """Handle incoming chat message"""
    try:
        message = data.get('message', '')
        session_id = data.get('session_id', None)
        
        # Start streaming response
        await sio.emit('message_start', room=sid)
        
        # Import agent and process message
        from services.agent_service import process_message_stream
        
        async for chunk in process_message_stream(message, session_id):
            await sio.emit('message_chunk', chunk, room=sid)
            await asyncio.sleep(0.01)  # Small delay for smoother streaming
        
        # End streaming
        await sio.emit('message_end', room=sid)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        await sio.emit('error', {'error': str(e)}, room=sid)

@sio.event
async def typing_start(sid, data):
    """Handle typing indicator start"""
    room = data.get('room', 'general')
    await sio.emit('user_typing', {'user': sid}, room=room, skip_sid=sid)

@sio.event
async def typing_stop(sid, data):
    """Handle typing indicator stop"""
    room = data.get('room', 'general')
    await sio.emit('user_stopped_typing', {'user': sid}, room=room, skip_sid=sid)