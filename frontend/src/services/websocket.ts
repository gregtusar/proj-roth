import { io, Socket } from 'socket.io-client';
import { store } from '../store';
import {
  addMessage,
  setStreamingMessage,
  updateStreamingMessage,
  finalizeStreamingMessage,
} from '../store/chatSlice';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(): void {
    const token = localStorage.getItem('access_token');
    const wsUrl = process.env.REACT_APP_WS_URL || 'http://localhost:8000';

    this.socket = io(wsUrl, {
      auth: {
        token,
      },
      transports: ['websocket'],
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
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
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
    if (!this.socket || !this.socket.connected) {
      console.error('WebSocket not connected');
      return;
    }

    this.socket.emit('send_message', {
      message,
      session_id: sessionId,
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const wsService = new WebSocketService();
export default wsService;