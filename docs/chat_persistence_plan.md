# Chat Persistence Implementation Plan

## Overview
This document outlines the required changes to add chat persistence and resumption capabilities to the NJ Voter Chat ADK agent. Currently, all chat sessions are stored in memory and lost when the application restarts. This plan details how to implement persistent storage for chat histories, allowing users to list, resume, and manage multiple conversations.

## Current Architecture Analysis

### Existing Implementation
- **Session Management**: Uses `InMemorySessionService` from ADK
- **Memory Service**: Uses `InMemoryMemoryService` from ADK  
- **Session IDs**: Generated with timestamp pattern `session_{int(time.time())}`
- **User Management**: Hardcoded as "streamlit_user"
- **Chat History**: 
  - CLI: No history preservation
  - Streamlit: Stored in `st.session_state.history` (session-only)

### Key Files Affected
- `agents/nj_voter_chat_adk/agent.py` - Core agent with session management
- `agents/nj_voter_chat_adk/app_cli.py` - CLI interface
- `agents/nj_voter_chat_adk/app_streamlit.py` - Streamlit web interface

## Implementation Options

### Option A: SQLite Database (Recommended for Quick Implementation)

**Pros:**
- No external dependencies
- File-based storage
- Simple to implement and deploy
- Good for single-user or low-concurrency scenarios

**Cons:**
- Not suitable for high concurrency
- Limited scalability

**Implementation:**
```python
from google.adk.sessions import DatabaseSessionService

# In agent.py __init__
db_url = "sqlite:///data/chats.db"
self._session_service = DatabaseSessionService(db_url=db_url)
```

### Option B: PostgreSQL Database (Recommended for Production)

**Pros:**
- Handles concurrent users well
- Scalable and reliable
- Production-ready
- Supports complex queries

**Cons:**
- Requires PostgreSQL server setup
- Additional dependency management

**Implementation:**
```python
from google.adk.sessions import DatabaseSessionService
import os

# In agent.py __init__
db_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/voter_chat")
self._session_service = DatabaseSessionService(db_url=db_url)
```

### Option C: Google Cloud Vertex AI (Recommended for GCP Integration)

**Pros:**
- Fully managed by Google Cloud
- Integrates with existing GCP infrastructure
- Automatic scaling and reliability
- No database management needed

**Cons:**
- Requires GCP bucket and Vertex AI setup
- May incur additional costs
- More complex initial configuration

**Implementation:**
```python
from google.adk.sessions import VertexAiSessionService

# In agent.py __init__
self._session_service = VertexAiSessionService(
    bucket_name="proj-roth-chats",
    reasoning_engine_id="nj-voter-chat-engine"
)
```

## Required Database Schema

### For Options A & B (Database-backed):

```sql
-- Users table (optional, for multi-user support)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chats table
CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_archived BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);

-- Chat messages table (for custom storage beyond ADK)
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    tool_calls JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_chats_updated_at ON chats(updated_at);
CREATE INDEX idx_messages_chat_id ON chat_messages(chat_id);
CREATE INDEX idx_messages_created_at ON chat_messages(created_at);
```

## New Components Required

### 1. Chat Manager Module (`chat_manager.py`)

```python
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Chat:
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    message_count: int = 0
    
class ChatManager:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def create_chat(self, user_id: str, title: Optional[str] = None) -> Chat:
        """Create a new chat session"""
        pass
    
    def list_chats(self, user_id: str, limit: int = 50) -> List[Chat]:
        """List all chats for a user"""
        pass
    
    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get a specific chat by ID"""
        pass
    
    def update_chat_title(self, chat_id: str, title: str) -> bool:
        """Update the title of a chat"""
        pass
    
    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat and all its messages"""
        pass
    
    def archive_chat(self, chat_id: str) -> bool:
        """Archive a chat (soft delete)"""
        pass
    
    def generate_title_from_first_message(self, message: str) -> str:
        """Auto-generate a title from the first user message"""
        pass
```

### 2. Session Store Module (`session_store.py`)

```python
class SessionStore:
    """Manages session persistence and retrieval"""
    
    def save_session(self, session_id: str, data: Dict[str, Any]):
        """Save session data to persistent storage"""
        pass
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from storage"""
        pass
    
    def delete_session(self, session_id: str):
        """Delete session data"""
        pass
```

## UI Changes Required

### CLI Interface (`app_cli.py`)

Add new commands:
- `/list` - Show all previous chats
- `/new [title]` - Start a new chat with optional title
- `/resume <chat_id>` - Resume a previous chat
- `/delete <chat_id>` - Delete a chat
- `/export <chat_id>` - Export chat to JSON/Markdown
- `/title <new_title>` - Update current chat title
- `/help` - Show available commands

```python
def handle_command(command: str, agent: NJVoterChatAgent, chat_manager: ChatManager):
    """Process special commands"""
    if command.startswith("/list"):
        chats = chat_manager.list_chats(user_id)
        for chat in chats:
            print(f"[{chat.id[:8]}] {chat.title} - {chat.updated_at}")
    elif command.startswith("/resume"):
        chat_id = command.split()[1]
        # Resume the specified chat
    # ... other commands
```

### Streamlit Interface (`app_streamlit.py`)

Add sidebar components:
```python
# Sidebar for chat management
with st.sidebar:
    st.header("Chat History")
    
    # New chat button
    if st.button("➕ New Chat"):
        new_chat = chat_manager.create_chat(st.session_state.user_id)
        st.session_state.current_chat_id = new_chat.id
        st.session_state.history = []
    
    # List existing chats
    chats = chat_manager.list_chats(st.session_state.user_id)
    for chat in chats:
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(f"💬 {chat.title[:30]}", key=f"chat_{chat.id}"):
                st.session_state.current_chat_id = chat.id
                # Load chat history
                st.session_state.history = load_chat_history(chat.id)
        with col2:
            if st.button("🗑️", key=f"del_{chat.id}"):
                chat_manager.delete_chat(chat.id)
                st.rerun()
```

## Implementation Steps

### Phase 1: Basic Persistence (Minimal Changes)
1. Switch from `InMemorySessionService` to `DatabaseSessionService` with SQLite
2. Add basic chat listing and selection to CLI
3. Store session IDs in a simple file or database table
4. Test session persistence and resumption

**Estimated effort:** 2-3 hours

### Phase 2: Full Chat Management
1. Implement `ChatManager` class
2. Add database schema and migrations
3. Update CLI with all commands
4. Update Streamlit with sidebar navigation
5. Add chat title generation from first message

**Estimated effort:** 4-6 hours

### Phase 3: Production Features
1. Add user authentication (optional)
2. Implement PostgreSQL or Vertex AI backend
3. Add chat export functionality
4. Add search within chat history
5. Implement chat sharing (read-only links)

**Estimated effort:** 6-8 hours

## Configuration Changes

### Environment Variables
```bash
# Option A: SQLite
CHAT_DB_PATH=/path/to/chats.db

# Option B: PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/voter_chat

# Option C: Vertex AI
VERTEX_AI_BUCKET=proj-roth-chats
VERTEX_AI_ENGINE_ID=nj-voter-chat-engine

# Common
ENABLE_CHAT_PERSISTENCE=true
MAX_CHATS_PER_USER=100
CHAT_RETENTION_DAYS=90
```

### Requirements Updates
```txt
# Add to requirements.txt for database support
sqlalchemy>=2.0.0
alembic>=1.13.0  # For database migrations
psycopg2-binary>=2.9.0  # For PostgreSQL (Option B)
```

## Testing Plan

### Unit Tests
- Test chat CRUD operations
- Test session persistence and retrieval
- Test message history management
- Test title generation

### Integration Tests
- Test full conversation flow with persistence
- Test resuming chats after restart
- Test concurrent user scenarios
- Test database connection failures

### Manual Testing
- Create multiple chats
- Resume old chats
- Delete chats
- Export chat history
- Test with both CLI and Streamlit

## Migration Strategy

1. **Backup Current State**: Document any important conversations
2. **Deploy Database**: Set up chosen database option
3. **Update Code**: Deploy new agent code with persistence
4. **Test Migration**: Verify existing functionality still works
5. **Enable Persistence**: Switch to persistent session service
6. **Monitor**: Watch for any issues in production

## Rollback Plan

If issues arise:
1. Switch back to `InMemorySessionService` in config
2. Redeploy previous version
3. Investigate and fix issues
4. Retry deployment with fixes

## Security Considerations

- Ensure database credentials are stored securely (use Secret Manager)
- Implement proper user authentication before production deployment
- Add rate limiting to prevent abuse
- Sanitize chat titles and content to prevent injection attacks
- Consider encrypting sensitive chat content at rest
- Implement proper access controls (users can only see their own chats)

## Performance Considerations

- Add database connection pooling for PostgreSQL
- Implement pagination for chat lists
- Consider caching recent chats in memory
- Add indexes on frequently queried fields
- Monitor database size and implement retention policies

## Future Enhancements

1. **Chat Templates**: Save common query patterns as templates
2. **Collaborative Chats**: Allow multiple users to share a chat session
3. **Chat Analytics**: Track usage patterns and popular queries
4. **Smart Suggestions**: Suggest follow-up questions based on context
5. **Bookmark Messages**: Mark important messages within a chat
6. **Chat Folders**: Organize chats into folders/categories
7. **Full-Text Search**: Search across all chat histories
8. **Export Formats**: Support PDF, Word, and HTML exports

## Decision Matrix

| Criteria | SQLite | PostgreSQL | Vertex AI |
|----------|---------|------------|-----------|
| Setup Complexity | Low | Medium | High |
| Scalability | Low | High | Very High |
| Cost | Free | Low | Medium |
| Maintenance | Low | Medium | Low |
| Performance | Good | Excellent | Excellent |
| Multi-user Support | Limited | Excellent | Excellent |
| Backup/Recovery | Manual | Good | Automatic |

## Recommended Approach

For immediate implementation with minimal changes:
1. **Start with SQLite** (Option A) for rapid prototyping
2. **Implement basic chat management** (Phase 1)
3. **Test with real users** to validate the approach
4. **Upgrade to PostgreSQL or Vertex AI** when scaling is needed

This incremental approach allows you to add persistence quickly while maintaining flexibility for future enhancements.

## Code Examples

### Quick Start: Minimal SQLite Implementation

```python
# agent.py modifications
from google.adk.sessions import DatabaseSessionService
import os

class NJVoterChatAgent(Agent):
    def __init__(self, chat_id: Optional[str] = None):
        # ... existing init code ...
        
        # Replace InMemorySessionService
        db_path = os.getenv("CHAT_DB_PATH", "data/chats.db")
        self._session_service = DatabaseSessionService(f"sqlite:///{db_path}")
        
        # Use provided chat_id or create new one
        self._session_id = chat_id or str(uuid.uuid4())
```

### CLI with Basic Commands

```python
# app_cli.py modifications
def main():
    agent = None
    current_chat_id = None
    
    print("NJ Voter Chat (ADK) - type 'exit' to quit, '/help' for commands")
    
    while True:
        try:
            q = input("\n> ").strip()
        except EOFError:
            break
            
        if q.startswith("/"):
            # Handle commands
            if q == "/new":
                current_chat_id = str(uuid.uuid4())
                agent = NJVoterChatAgent(chat_id=current_chat_id)
                print(f"Started new chat: {current_chat_id[:8]}")
            elif q == "/list":
                # List available chats from database
                pass
            continue
            
        if not agent:
            agent = NJVoterChatAgent()
            
        # Regular chat interaction
        resp = _agent_invoke(agent, q)
        print("\nAssistant:\n" + str(resp))
```

This plan provides a clear path forward for implementing chat persistence while maintaining flexibility in choosing the appropriate storage backend for your needs.