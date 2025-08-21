export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
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
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
  user_id: string;
}

export interface ChatState {
  messages: Message[];
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  streamingMessage: string | null;
  error: string | null;
}