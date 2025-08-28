export interface Message {
  message_id: string;
  session_id: string;
  user_id: string;
  message_type: 'user' | 'assistant';
  message_text: string;
  timestamp: string;
  sequence_number: number;
  metadata?: {
    tool_calls?: ToolCall[];
    query?: string;
    results_count?: number;
  };
}

export interface ToolCall {
  tool: string;
  args: Record<string, any>;
  result?: any;
}

export interface ChatSession {
  session_id: string;
  user_id: string;
  user_email: string;
  session_name: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count: number;
  metadata?: Record<string, any>;
}

export interface ReasoningEvent {
  type: string;
  data: Record<string, any>;
  timestamp: number;
}

export interface ChatState {
  messages: Message[];
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  streamingMessage: string | null;
  error: string | null;
  verboseMode: boolean;
  reasoningEvents: ReasoningEvent[];
  currentReasoning: ReasoningEvent | null;
}