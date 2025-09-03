/**
 * Message queue implementation for proper WebSocket message handling.
 * Replaces the unreliable isLoadingSession flag with a robust queue system.
 */

export interface QueuedMessage {
  id: string;
  type: 'message' | 'message_confirmed' | 'session_created' | 'session_updated';
  data: any;
  timestamp: number;
  retryCount: number;
  sessionId?: string;
}

export interface MessageQueueConfig {
  maxRetries: number;
  retryDelay: number;
  maxQueueSize: number;
  processingDelay: number;
}

export class MessageQueue {
  private queue: QueuedMessage[] = [];
  private processing = false;
  private sessionLoading = false;
  private currentSessionId: string | null = null;
  private config: MessageQueueConfig;
  private processedMessageIds = new Set<string>();
  private messageHandlers: Map<string, (data: any) => Promise<void>> = new Map();

  constructor(config: Partial<MessageQueueConfig> = {}) {
    this.config = {
      maxRetries: 3,
      retryDelay: 1000,
      maxQueueSize: 100,
      processingDelay: 10,
      ...config
    };
  }

  /**
   * Register a handler for a specific message type
   */
  registerHandler(type: string, handler: (data: any) => Promise<void>): void {
    this.messageHandlers.set(type, handler);
  }

  /**
   * Add a message to the queue
   */
  async enqueue(message: QueuedMessage): Promise<void> {
    // Check for duplicates
    if (this.processedMessageIds.has(message.id)) {
      console.log('[MessageQueue] Ignoring duplicate message:', message.id);
      return;
    }

    // Check queue size limit
    if (this.queue.length >= this.config.maxQueueSize) {
      console.warn('[MessageQueue] Queue full, dropping oldest message');
      const dropped = this.queue.shift();
      if (dropped) {
        this.processedMessageIds.delete(dropped.id);
      }
    }

    // Add to queue
    this.queue.push(message);
    console.log(`[MessageQueue] Enqueued message ${message.id} (queue size: ${this.queue.length})`);

    // Start processing if not already running
    if (!this.processing) {
      await this.processQueue();
    }
  }

  /**
   * Process messages in the queue
   */
  private async processQueue(): Promise<void> {
    if (this.processing) {
      return;
    }

    this.processing = true;
    console.log('[MessageQueue] Starting queue processing');

    while (this.queue.length > 0) {
      // Check if we should pause for session loading
      if (this.sessionLoading) {
        console.log('[MessageQueue] Pausing for session load');
        await this.waitForSessionLoad();
      }

      const message = this.queue[0];
      
      // Check if message is for current session
      if (message.sessionId && this.currentSessionId && 
          message.sessionId !== this.currentSessionId) {
        console.log(`[MessageQueue] Skipping message for different session: ${message.sessionId}`);
        this.queue.shift();
        continue;
      }

      try {
        await this.processMessage(message);
        this.queue.shift(); // Remove from queue after successful processing
        this.processedMessageIds.add(message.id);
        
        // Keep processed IDs limited to prevent memory leak
        if (this.processedMessageIds.size > 1000) {
          const idsArray = Array.from(this.processedMessageIds);
          this.processedMessageIds = new Set(idsArray.slice(-500));
        }
      } catch (error) {
        console.error('[MessageQueue] Error processing message:', error);
        message.retryCount++;
        
        if (message.retryCount >= this.config.maxRetries) {
          console.error(`[MessageQueue] Max retries reached for message ${message.id}, dropping`);
          this.queue.shift();
        } else {
          // Move to end of queue for retry
          this.queue.shift();
          this.queue.push(message);
          await this.delay(this.config.retryDelay);
        }
      }

      // Small delay between messages for smooth processing
      if (this.queue.length > 0) {
        await this.delay(this.config.processingDelay);
      }
    }

    this.processing = false;
    console.log('[MessageQueue] Queue processing completed');
  }

  /**
   * Process a single message
   */
  private async processMessage(message: QueuedMessage): Promise<void> {
    console.log(`[MessageQueue] Processing message ${message.id} of type ${message.type}`);
    
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      await handler(message.data);
    } else {
      console.warn(`[MessageQueue] No handler registered for message type: ${message.type}`);
    }
  }

  /**
   * Set session loading state
   */
  setSessionLoading(loading: boolean): void {
    console.log(`[MessageQueue] Session loading state: ${loading}`);
    this.sessionLoading = loading;
    
    // Resume processing if loading completed
    if (!loading && !this.processing && this.queue.length > 0) {
      this.processQueue();
    }
  }

  /**
   * Set current session ID for filtering
   */
  setCurrentSession(sessionId: string | null): void {
    console.log(`[MessageQueue] Current session set to: ${sessionId}`);
    this.currentSessionId = sessionId;
    
    // Clear queue of messages for other sessions
    if (sessionId) {
      const initialSize = this.queue.length;
      this.queue = this.queue.filter(msg => 
        !msg.sessionId || msg.sessionId === sessionId
      );
      const removed = initialSize - this.queue.length;
      if (removed > 0) {
        console.log(`[MessageQueue] Removed ${removed} messages for other sessions`);
      }
    }
  }

  /**
   * Clear the queue
   */
  clear(): void {
    const count = this.queue.length;
    this.queue = [];
    this.processedMessageIds.clear();
    console.log(`[MessageQueue] Cleared ${count} messages from queue`);
  }

  /**
   * Get queue statistics
   */
  getStats(): {
    queueSize: number;
    processing: boolean;
    sessionLoading: boolean;
    currentSessionId: string | null;
    processedCount: number;
  } {
    return {
      queueSize: this.queue.length,
      processing: this.processing,
      sessionLoading: this.sessionLoading,
      currentSessionId: this.currentSessionId,
      processedCount: this.processedMessageIds.size
    };
  }

  /**
   * Wait for session to finish loading
   */
  private async waitForSessionLoad(): Promise<void> {
    const maxWait = 10000; // 10 seconds max wait
    const checkInterval = 100;
    let waited = 0;

    while (this.sessionLoading && waited < maxWait) {
      await this.delay(checkInterval);
      waited += checkInterval;
    }

    if (this.sessionLoading) {
      console.warn('[MessageQueue] Session load timeout, continuing anyway');
      this.sessionLoading = false;
    }
  }

  /**
   * Utility delay function
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Check if a message has been processed
   */
  hasProcessed(messageId: string): boolean {
    return this.processedMessageIds.has(messageId);
  }

  /**
   * Get pending messages for current session
   */
  getPendingMessages(): QueuedMessage[] {
    return this.queue.filter(msg => 
      !msg.sessionId || msg.sessionId === this.currentSessionId
    );
  }
}