import socketio
from typing import Optional
import json
import asyncio
from core.config import settings

# Create Socket.IO server with extended timeout settings for Cloud Run
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS,
    logger=settings.DEBUG,
    engineio_logger=settings.DEBUG,
    # Extended ping/pong settings to prevent disconnections
    ping_interval=20,  # Send ping every 20 seconds (well under Cloud Run's 60s timeout)
    ping_timeout=40,  # Wait 40 seconds for pong response
    max_http_buffer_size=10 * 1024 * 1024  # 10MB buffer for large messages
)

# Create Socket.IO ASGI app
sio_app = socketio.ASGIApp(
    sio,
    socketio_path='/socket.io'
)

# Store active connections and in-flight messages
connections = {}
in_flight_messages = {}  # Track messages being streamed per session

@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    print(f"Client {sid} connected")
    connections[sid] = {
        'authenticated': False,
        'user_id': None,
        'user_email': None
    }
    
    # Verify authentication token if provided
    if auth and 'token' in auth:
        try:
            from jose import jwt, JWTError
            from core.config import settings
            
            payload = jwt.decode(auth['token'], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            user_email = payload.get("email")
            
            if user_id:
                connections[sid]['authenticated'] = True
                connections[sid]['user_id'] = user_id
                connections[sid]['user_email'] = user_email
                print(f"Client {sid} authenticated as {user_email}")
        except (JWTError, KeyError) as e:
            print(f"Failed to authenticate client {sid}: {e}")
    
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
    print(f"[WebSocket] Received send_message event from {sid}: {data}")
    try:
        message = data.get('message', '')
        session_id = data.get('session_id', None)
        
        print(f"[WebSocket] Processing - Message: '{message}', Session: {session_id}")
        
        # Get user info from authenticated connection
        conn_info = connections.get(sid, {})
        user_id = conn_info.get('user_id') or data.get('user_id') or 'anonymous'
        user_email = conn_info.get('user_email') or data.get('user_email') or 'anonymous@example.com'
        
        print(f"[WebSocket] User info - ID: {user_id}, Email: {user_email}")
        
        # Import Firestore session service
        from services.firestore_chat_service import get_firestore_chat_service
        session_service = get_firestore_chat_service()
        
        if not session_service.connected:
            print("[WebSocket] Warning: Firestore chat service not connected. Session persistence may not work.")
            # Continue anyway - allow chat to work without persistence
        
        # Create or use existing session
        if not session_id:
            try:
                print(f"[WebSocket] Creating new session for user {user_id}...")
                # Create new session with first message as name
                session = await session_service.create_session(
                    user_id=user_id or 'anonymous',
                    user_email=user_email or 'anonymous@example.com',
                    first_message=message
                )
                session_id = session.session_id
                print(f"[WebSocket] Successfully created new session: {session_id}")
                
                # Notify client of new session BEFORE processing the message
                # This ensures the frontend has the session_id for tracking
                await sio.emit('session_created', {
                    'session_id': session_id,
                    'session_name': session.session_name
                }, room=sid)
                print(f"[WebSocket] Emitted session_created event for session: {session_id}")
                
                # Small delay to ensure frontend processes the session_created event
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[WebSocket] ERROR creating session: {e}")
                import traceback
                traceback.print_exc()
                await sio.emit('error', {'error': f'Failed to create session: {str(e)}'}, room=sid)
                return
        
        # Save user message to session
        try:
            print(f"[WebSocket] Saving user message to session {session_id}...")
            user_msg = await session_service.add_message(
                session_id=session_id,
                user_id=user_id or 'anonymous',
                message_type='user',
                message_text=message
            )
            print(f"[WebSocket] User message saved with ID: {user_msg.message_id}")
            
            # Emit the saved user message back to confirm it was stored
            # This replaces any temporary message in the frontend
            await sio.emit('message_confirmed', {
                'message_id': user_msg.message_id,
                'session_id': session_id,
                'message_type': 'user',
                'message_text': message,
                'timestamp': user_msg.timestamp.isoformat(),
                'sequence_number': user_msg.sequence_number
            }, room=sid)
        except Exception as e:
            print(f"[WebSocket] ERROR saving user message: {e}")
            import traceback
            traceback.print_exc()
        
        # Import agent and process message
        from services.agent_service import process_message_stream
        from agents.nj_voter_chat_adk.agent import _set_websocket
        
        # Set the websocket reference for reasoning events
        # Create a wrapper to emit to specific sid
        class WebSocketWrapper:
            def __init__(self, sio_instance, sid_target):
                self.sio = sio_instance
                self.sid = sid_target
            
            async def emit(self, event, data):
                await self.sio.emit(event, data, room=self.sid)
        
        wrapper = WebSocketWrapper(sio, sid)
        _set_websocket(wrapper)
        
        # Start streaming response
        await sio.emit('message_start', room=sid)
        
        # Track this message as in-flight for recovery purposes
        message_key = f"{session_id}:{user_msg.message_id if 'user_msg' in locals() else 'unknown'}"
        in_flight_messages[message_key] = {
            'sid': sid,
            'session_id': session_id,
            'user_message': message,
            'partial_response': '',
            'timestamp': asyncio.get_event_loop().time()
        }
        
        # Collect full response for saving
        full_response = ""
        print(f"[WebSocket] Starting to stream response for message: {message[:50]}...")
        try:
            async for chunk in process_message_stream(message, session_id, user_id, user_email):
                full_response += chunk
                # Update in-flight tracking
                if message_key in in_flight_messages:
                    in_flight_messages[message_key]['partial_response'] = full_response
                print(f"[WebSocket] Emitting chunk: {chunk[:20]}...")
                # Check if client is still connected before emitting
                if sid in connections:
                    await sio.emit('message_chunk', chunk, room=sid)
                    await asyncio.sleep(0.01)  # Small delay for smoother streaming
                else:
                    print(f"[WebSocket] Client {sid} disconnected during streaming, stopping")
                    break
            print(f"[WebSocket] Finished streaming. Total response: {len(full_response)} chars")
        finally:
            # Clean up in-flight tracking
            if message_key in in_flight_messages:
                del in_flight_messages[message_key]
        
        # Save assistant response to session
        await session_service.add_message(
            session_id=session_id,
            user_id=user_id or 'anonymous',
            message_type='assistant',
            message_text=full_response
        )
        
        # End streaming
        await sio.emit('message_end', room=sid)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        await sio.emit('error', {'error': str(e)}, room=sid)

@sio.event
async def recover_message(sid, data):
    """Recover an incomplete message after reconnection"""
    session_id = data.get('session_id')
    last_message_id = data.get('last_message_id')
    
    print(f"[WebSocket] Recovery requested for session {session_id}, last message {last_message_id}")
    
    # Check if we have any in-flight messages for this session
    for key, msg_data in list(in_flight_messages.items()):
        if msg_data['session_id'] == session_id:
            # Found an incomplete message, resume sending the remaining part
            partial_response = msg_data.get('partial_response', '')
            if partial_response:
                print(f"[WebSocket] Recovering {len(partial_response)} chars of response")
                await sio.emit('message_recovery', {
                    'session_id': session_id,
                    'recovered_text': partial_response,
                    'is_complete': False  # We don't know if it was fully generated
                }, room=sid)
            break
    else:
        # No in-flight message found, client has all messages
        await sio.emit('message_recovery', {
            'session_id': session_id,
            'recovered_text': '',
            'is_complete': True
        }, room=sid)

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