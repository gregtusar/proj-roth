import { io, Socket } from 'socket.io-client';
import { store } from '../store';
import {
  addMessage,
  setStreamingMessage,
  updateStreamingMessage,
  finalizeStreamingMessage,
  setCurrentSession,
  updateSession,
  replaceMessage,
  addReasoningEvent,
} from '../store/chatSlice';
import { MessageQueue, QueuedMessage } from './messageQueue';

// WebSocket configuration constants - using arithmetic to prevent minification issues
const PING_INTERVAL_MS = 20000;  // 20 seconds - do not change format
const PING_TIMEOUT_MS = 40000;   // 40 seconds - do not change format
const CONNECTION_TIMEOUT_MS = 600000; // 10 minutes - do not change format

class WebSocketService {
  private socket: Socket | null = null;
  private _reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private isConnecting = false;
  private activeSessionId: string | null = null;
  private messageQueue: MessageQueue;

  constructor() {
    // Initialize message queue with handlers
    this.messageQueue = new MessageQueue({
      maxRetries: 3,
      retryDelay: 500,
      maxQueueSize: 100,
      processingDelay: 10
    });
    
    this.setupMessageHandlers();
  }

  private setupMessageHandlers(): void {
    // Register handlers for different message types
    this.messageQueue.registerHandler('message', async (data) => {
      await this.handleMessage(data);
    });
    
    this.messageQueue.registerHandler('message_confirmed', async (data) => {
      await this.handleMessageConfirmed(data);
    });
    
    this.messageQueue.registerHandler('session_created', async (data) => {
      await this.handleSessionCreated(data);
    });
    
    this.messageQueue.registerHandler('session_updated', async (data) => {
      await this.handleSessionUpdated(data);
    });
  }

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
      wsUrl = 'https://nj-voter-chat-app-169579073940.us-central1.run.app';
    } else {
      // Cloud Run URL or other production - use same origin
      wsUrl = window.location.origin;
    }

    console.log('[WebSocket] Attempting to connect to:', wsUrl);

    // Build options object to prevent minification issues
    const socketOptions: any = {
      auth: {
        token,
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      // Force new connection on reconnect to avoid stale connections
      forceNew: false,
    };
    
    // Add ping settings - these are engine.io options
    // Using bracket notation to prevent minification
    socketOptions['pingInterval'] = PING_INTERVAL_MS;
    socketOptions['pingTimeout'] = PING_TIMEOUT_MS;
    socketOptions['timeout'] = CONNECTION_TIMEOUT_MS;
    
    this.socket = io(wsUrl, socketOptions);

    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this._reconnectAttempts = 0;
      this.isConnecting = false;
      
      // Check if we need to recover any incomplete messages
      const state = store.getState();
      if (state.chat.currentSessionId && state.chat.streamingMessage) {
        console.log('[WebSocket] Reconnected during streaming, requesting recovery');
        const lastMessage = state.chat.messages[state.chat.messages.length - 1];
        this.socket?.emit('recover_message', {
          session_id: state.chat.currentSessionId,
          last_message_id: lastMessage?.message_id
        });
      }
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
      // Don't clear reasoning events - keep them for debugging
      // store.dispatch(clearReasoningEvents());
    });
    
    // Handle reasoning events for verbose mode
    this.socket.on('reasoning_event', (event: any) => {
      store.dispatch(addReasoningEvent(event));
    });

    this.socket.on('message', (message: any) => {
      // Queue message for processing instead of handling directly
      const queuedMessage: QueuedMessage = {
        id: message.message_id || `msg_${Date.now()}`,
        type: 'message',
        data: message,
        timestamp: Date.now(),
        retryCount: 0,
        sessionId: message.session_id
      };
      
      this.messageQueue.enqueue(queuedMessage);
    });

    this.socket.on('message_confirmed', (message: any) => {
      // Queue for processing
      const queuedMessage: QueuedMessage = {
        id: `confirm_${message.message_id || Date.now()}`,
        type: 'message_confirmed',
        data: message,
        timestamp: Date.now(),
        retryCount: 0,
        sessionId: message.session_id
      };
      
      this.messageQueue.enqueue(queuedMessage);
    });

    this.socket.on('session_created', (data: { session_id: string; session_name: string }) => {
      // Queue for processing
      const queuedMessage: QueuedMessage = {
        id: `session_${data.session_id}`,
        type: 'session_created',
        data: data,
        timestamp: Date.now(),
        retryCount: 0,
        sessionId: data.session_id
      };
      
      this.messageQueue.enqueue(queuedMessage);
    });

    this.socket.on('session_updated', (session: any) => {
      // Queue for processing
      const queuedMessage: QueuedMessage = {
        id: `update_${session.session_id}_${Date.now()}`,
        type: 'session_updated',
        data: session,
        timestamp: Date.now(),
        retryCount: 0,
        sessionId: session.session_id
      };
      
      this.messageQueue.enqueue(queuedMessage);
    });

    this.socket.on('message_recovery', (data: any) => {
      console.log('[WebSocket] Message recovery received:', data);
      if (data.recovered_text) {
        // Update the streaming message with recovered content
        store.dispatch(setStreamingMessage(data.recovered_text));
        if (data.is_complete) {
          // If the message was complete, finalize it
          store.dispatch(finalizeStreamingMessage());
        }
      }
    });

    this.socket.on('error', (error: any) => {
      console.error('WebSocket error:', error);
    });

    this.socket.on('reconnect_attempt', (attemptNumber: number) => {
      this._reconnectAttempts = attemptNumber;
      console.log(`Reconnection attempt ${attemptNumber}`);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('Failed to reconnect after maximum attempts');
    });
  }

  sendMessage(message: string, sessionId?: string, modelId?: string): void {
    const state = store.getState();
    // Use the provided sessionId or fall back to current session
    const effectiveSessionId = sessionId || state.chat.currentSessionId;
    
    console.log('[WebSocket] sendMessage called:', { 
      message, 
      sessionId,
      effectiveSessionId,
      currentSessionId: state.chat.currentSessionId,
      modelId
    });
    console.log('[WebSocket] Socket state:', { 
      exists: !!this.socket, 
      connected: this.socket?.connected 
    });
    
    if (!this.socket) {
      console.error('WebSocket not initialized, attempting to connect...');
      this.connect();
      // Wait a bit for connection then retry
      setTimeout(() => this.sendMessage(message, sessionId, modelId), 1000);
      return;
    }
    
    if (!this.socket.connected) {
      console.error('WebSocket not connected, waiting for connection...');
      // Wait for connection event then send
      this.socket.once('connect', () => {
        console.log('[WebSocket] Connected, now sending message');
        this.sendMessage(message, sessionId, modelId);
      });
      return;
    }

    const user = state.auth.user;

    const payload = {
      message,
      session_id: effectiveSessionId,
      user_id: user?.id || 'anonymous',
      user_email: user?.email || 'anonymous@example.com',
      model_id: modelId,
    };
    
    console.log('[WebSocket] Emitting send_message with payload:', payload);
    this.socket.emit('send_message', payload);
    console.log('[WebSocket] Message emitted');
  }

  updateSessionModel(sessionId: string, modelId: string): void {
    if (!this.socket?.connected) {
      console.error('WebSocket not connected');
      return;
    }
    
    const payload = {
      session_id: sessionId,
      model_id: modelId,
    };
    
    console.log('[WebSocket] Updating session model:', payload);
    this.socket.emit('update_session_model', payload);
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

  setLoadingSession(loading: boolean): void {
    this.messageQueue.setSessionLoading(loading);
    console.log('[WebSocket] Session loading state:', loading);
  }

  setActiveSession(sessionId: string | null): void {
    this.activeSessionId = sessionId;
    this.messageQueue.setCurrentSession(sessionId);
    console.log('[WebSocket] Active session set to:', sessionId);
  }

  clearMessageQueue(): void {
    this.messageQueue.clear();
    console.log('[WebSocket] Message queue cleared');
  }

  // Handler methods for different message types
  private async handleMessage(message: any): Promise<void> {
    const state = store.getState();
    
    // Allow messages for new sessions being created
    if (state.chat.currentSessionId && message.session_id !== state.chat.currentSessionId) {
      console.log('[WebSocket] Ignoring message - different session');
      return;
    }
    
    // Check for duplicate before adding
    const exists = state.chat.messages.some(
      (msg: any) => msg.message_id === message.message_id
    );
    if (!exists) {
      store.dispatch(addMessage(message));
    } else {
      console.log('[WebSocket] Ignoring duplicate message:', message.message_id);
    }
  }

  private async handleMessageConfirmed(message: any): Promise<void> {
    const state = store.getState();
    
    console.log('[WebSocket] Message confirmed:', message);
    
    // Find the temp message to replace
    const tempMessage = state.chat.messages.find(
      (msg: any) => msg.message_id.startsWith('temp-') && 
                    msg.message_text === message.message_text &&
                    msg.message_type === 'user'
    );
    
    if (tempMessage) {
      // Replace the temp message with the confirmed one
      store.dispatch(replaceMessage({
        oldId: tempMessage.message_id,
        newMessage: message
      }));
    } else {
      // Check if message already exists before adding
      const exists = state.chat.messages.some(
        (msg: any) => msg.message_id === message.message_id
      );
      if (!exists) {
        store.dispatch(addMessage(message));
      }
    }
  }

  private async handleSessionCreated(data: { session_id: string; session_name: string }): Promise<void> {
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
      is_public: false,
      message_count: 1,
      metadata: {}
    };
    store.dispatch(updateSession(newSession));
    
    // Update any pending messages with the correct session_id
    const state = store.getState();
    state.chat.messages.forEach((msg: any) => {
      if (msg.session_id === 'pending') {
        // Replace the message with updated session_id
        store.dispatch(replaceMessage({
          oldId: msg.message_id,
          newMessage: { ...msg, session_id: data.session_id }
        }));
      }
    });
    
    // Set the active session
    this.activeSessionId = data.session_id;
    this.messageQueue.setCurrentSession(data.session_id);
  }

  private async handleSessionUpdated(session: any): Promise<void> {
    store.dispatch(updateSession(session));
  }

  getQueueStats() {
    return this.messageQueue.getStats();
  }
}

export const wsService = new WebSocketService();
export default wsService;