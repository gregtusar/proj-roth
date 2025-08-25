import { io, Socket } from 'socket.io-client';
import { store } from '../store';
import {
  addMessage,
  setStreamingMessage,
  updateStreamingMessage,
  finalizeStreamingMessage,
  setCurrentSession,
  updateSession,
} from '../store/chatSlice';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private isConnecting = false;

  connect(): void {
    // Prevent multiple connection attempts
    if (this.isConnecting || (this.socket && this.socket.connected)) {
      console.log('[WebSocket] Already connected or connecting');
      return;
    }

    this.isConnecting = true;
    const token = localStorage.getItem('access_token');
    
    // Determine WebSocket URL based on environment
    let wsUrl: string;
    if (window.location.hostname === 'localhost') {
      // Local development
      wsUrl = process.env.REACT_APP_WS_URL || 'http://localhost:8080';
    } else if (window.location.hostname === 'gwanalytica.ai') {
      // Custom domain - use the actual Cloud Run backend
      wsUrl = 'https://nj-voter-chat-app-nwv4o72vjq-uc.a.run.app';
    } else {
      // Cloud Run URL or other production - use same origin
      wsUrl = window.location.origin;
    }

    console.log('[WebSocket] Attempting to connect to:', wsUrl);

    this.socket = io(wsUrl, {
      auth: {
        token,
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.isConnecting = false;
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.isConnecting = false;
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
    });

    this.socket.on('message_start', () => {
      store.dispatch(setStreamingMessage(''));
    });

    this.socket.on('message_chunk', (chunk: string) => {
      store.dispatch(updateStreamingMessage(chunk));
    });

    this.socket.on('message_end', () => {
      store.dispatch(finalizeStreamingMessage());
    });

    this.socket.on('message', (message: any) => {
      store.dispatch(addMessage(message));
    });

    this.socket.on('message_confirmed', (message: any) => {
      // Replace the temporary message with the confirmed one from backend
      console.log('[WebSocket] Message confirmed:', message);
      // We could update the message here if needed
    });

    this.socket.on('session_created', (data: { session_id: string; session_name: string }) => {
      console.log('[WebSocket] Session created:', data);
      
      // Update current session ID immediately
      store.dispatch(setCurrentSession(data.session_id));
      
      // Create a session object and update the store
      const newSession = {
        session_id: data.session_id,
        session_name: data.session_name,
        user_id: store.getState().auth.user?.id || 'anonymous',
        user_email: store.getState().auth.user?.email || 'anonymous@example.com',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_active: true,
        message_count: 1,
        metadata: {}
      };
      store.dispatch(updateSession(newSession));
      
      // Update any pending messages with the correct session_id
      const state = store.getState();
      state.chat.messages.forEach((msg: any) => {
        if (msg.session_id === 'pending') {
          msg.session_id = data.session_id;
        }
      });
    });

    this.socket.on('session_updated', (session: any) => {
      store.dispatch(updateSession(session));
    });

    this.socket.on('error', (error: any) => {
      console.error('WebSocket error:', error);
    });

    this.socket.on('reconnect_attempt', (attemptNumber: number) => {
      this.reconnectAttempts = attemptNumber;
      console.log(`Reconnection attempt ${attemptNumber}`);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('Failed to reconnect after maximum attempts');
    });
  }

  sendMessage(message: string, sessionId?: string): void {
    console.log('[WebSocket] sendMessage called:', { message, sessionId });
    console.log('[WebSocket] Socket state:', { 
      exists: !!this.socket, 
      connected: this.socket?.connected 
    });
    
    if (!this.socket) {
      console.error('WebSocket not initialized, attempting to connect...');
      this.connect();
      // Wait a bit for connection then retry
      setTimeout(() => this.sendMessage(message, sessionId), 1000);
      return;
    }
    
    if (!this.socket.connected) {
      console.error('WebSocket not connected, waiting for connection...');
      // Wait for connection event then send
      this.socket.once('connect', () => {
        console.log('[WebSocket] Connected, now sending message');
        this.sendMessage(message, sessionId);
      });
      return;
    }

    const state = store.getState();
    const user = state.auth.user;

    const payload = {
      message,
      session_id: sessionId || state.chat.currentSessionId,
      user_id: user?.id || 'anonymous',
      user_email: user?.email || 'anonymous@example.com',
    };
    
    console.log('[WebSocket] Emitting send_message with payload:', payload);
    this.socket.emit('send_message', payload);
    console.log('[WebSocket] Message emitted');
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.isConnecting = false;
  }

  reconnect(): void {
    console.log('[WebSocket] Force reconnecting...');
    this.disconnect();
    setTimeout(() => {
      this.connect();
    }, 100);
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getConnectionStatus(): { connected: boolean; connecting: boolean } {
    return {
      connected: this.socket?.connected || false,
      connecting: this.isConnecting
    };
  }
}

export const wsService = new WebSocketService();
export default wsService;