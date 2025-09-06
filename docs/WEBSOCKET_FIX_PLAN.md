# WebSocket Message Loss Fix Implementation Plan

## Overview
This document outlines the implementation plan to fix WebSocket session management issues and prevent message loss in the NJ Voter Chat application.

## Priority 1: Critical Fixes (Immediate Impact)

### 1.1 Fix Agent Response Extraction (HIGH PRIORITY)
**Problem**: Agent returns complex ADK result structures that sometimes don't contain text in expected format.
**Files**: `agents/nj_voter_chat_adk/agent.py`

#### Implementation Steps:
1. Add comprehensive logging for all response types
2. Create robust response extraction function
3. Add fallback mechanisms for different result structures
4. Validate response content before returning

```python
# Proposed changes at lines 625-656
def extract_response_text(result):
    """Extract text from various ADK response formats"""
    # Try multiple extraction methods in order of preference
    extraction_methods = [
        lambda r: r.content.parts[0].text if hasattr(r, 'content') and r.content.parts else None,
        lambda r: r.text if hasattr(r, 'text') else None,
        lambda r: r.get('output') if isinstance(r, dict) else None,
        lambda r: r.get('response') if isinstance(r, dict) else None,
        lambda r: str(r) if r else None
    ]
    
    for method in extraction_methods:
        try:
            text = method(result)
            if text and text.strip():
                return text
        except Exception as e:
            continue
    
    return None
```

### 1.2 Add Response Validation Before Streaming
**Problem**: Streaming starts before validating agent response exists.
**Files**: `backend/services/agent_service.py`, `backend/core/websocket.py`

#### Implementation Steps:
1. Move `message_start` emission after response validation
2. Add timeout for agent response
3. Implement retry mechanism for empty responses
4. Send error event if no response after retries

```python
# Proposed changes at agent_service.py lines 91-116
async def process_message_stream(...):
    # First, get the full response from agent
    result = await get_agent_response_with_retry(message, max_retries=2)
    
    if not result:
        yield "I apologize, but I'm having trouble processing your request. Please try rephrasing your question."
        return
    
    # Only start streaming after we have a valid response
    # Stream the validated response in chunks
```

## Priority 2: Session Management Improvements

### 2.1 Fix In-Flight Message Tracking
**Problem**: In-flight messages deleted too early, preventing recovery.
**Files**: `backend/core/websocket.py`

#### Implementation Steps:
1. Keep in-flight messages for configurable duration (5 minutes)
2. Add timestamp-based cleanup
3. Implement proper message recovery on reconnect
4. Store partial responses in Redis/memory cache

```python
# Proposed changes at websocket.py lines 167-198
in_flight_messages = {}  # Change to include TTL
MESSAGE_RETENTION_SECONDS = 300  # 5 minutes

async def cleanup_old_messages():
    """Background task to clean up old in-flight messages"""
    current_time = asyncio.get_event_loop().time()
    for key in list(in_flight_messages.keys()):
        if current_time - in_flight_messages[key]['timestamp'] > MESSAGE_RETENTION_SECONDS:
            del in_flight_messages[key]
```

### 2.2 Simplify Frontend Message Reception Logic
**Problem**: Complex logic for handling different message types causes race conditions.
**Files**: `frontend/src/services/websocket.ts`

#### Implementation Steps:
1. Create single source of truth for message handling
2. Implement message queue with deduplication
3. Add sequence numbers for ordering
4. Simplify session loading state management

```typescript
// Proposed changes at websocket.ts lines 126-205
class MessageQueue {
  private queue: Map<string, Message> = new Map();
  private processed: Set<string> = new Set();
  
  add(message: Message): boolean {
    if (this.processed.has(message.message_id)) {
      return false;
    }
    this.queue.set(message.message_id, message);
    return true;
  }
  
  process(): Message[] {
    const messages = Array.from(this.queue.values())
      .sort((a, b) => a.sequence_number - b.sequence_number);
    messages.forEach(m => this.processed.add(m.message_id));
    this.queue.clear();
    return messages;
  }
}
```

## Priority 3: Reliability Enhancements

### 3.1 Implement Client-Side Message Retry
**Problem**: No retry mechanism for failed message sends.
**Files**: `frontend/src/services/websocket.ts`

#### Implementation Steps:
1. Add exponential backoff retry logic
2. Queue messages during disconnection
3. Implement optimistic UI updates with rollback
4. Add user notification for connection issues

### 3.2 Add Comprehensive Logging and Monitoring
**Problem**: Difficult to diagnose issues in production.
**Files**: All WebSocket-related files

#### Implementation Steps:
1. Add structured logging with correlation IDs
2. Implement WebSocket event tracking
3. Add performance metrics (message latency, drop rate)
4. Create debug mode for verbose logging

### 3.3 Implement Heartbeat Beyond Ping/Pong
**Problem**: Connection may appear alive but be non-functional.
**Files**: `backend/core/websocket.py`, `frontend/src/services/websocket.ts`

#### Implementation Steps:
1. Add application-level heartbeat
2. Implement message acknowledgment system
3. Add connection quality monitoring
4. Auto-reconnect on degraded connection

## Priority 4: ADK Session Management Simplification

### 4.1 Refactor ADK Session Handling
**Problem**: Overly complex session management with multiple retry patterns.
**Files**: `agents/nj_voter_chat_adk/agent.py`

#### Implementation Steps:
1. Create single session manager class
2. Implement clear session lifecycle
3. Add session state persistence
4. Simplify error handling and recovery

```python
class ADKSessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = asyncio.Lock()
    
    async def get_or_create_session(self, chat_session_id: str):
        async with self.lock:
            if chat_session_id not in self.sessions:
                self.sessions[chat_session_id] = await self._create_session(chat_session_id)
            return self.sessions[chat_session_id]
    
    async def _create_session(self, chat_session_id: str):
        # Single place for session creation logic
        pass
```

## Implementation Schedule

### Phase 1: Critical Fixes (Day 1-2)
- [ ] Fix agent response extraction (1.1)
- [ ] Add response validation before streaming (1.2)
- [ ] Test with various query types

### Phase 2: Session Management (Day 3-4)
- [ ] Fix in-flight message tracking (2.1)
- [ ] Simplify frontend message reception (2.2)
- [ ] Add comprehensive testing

### Phase 3: Reliability (Day 5-6)
- [ ] Implement client-side retry (3.1)
- [ ] Add logging and monitoring (3.2)
- [ ] Implement heartbeat (3.3)

### Phase 4: Optimization (Day 7-8)
- [ ] Refactor ADK session handling (4.1)
- [ ] Performance testing
- [ ] Documentation update

## Testing Plan

### Unit Tests
- Response extraction with various formats
- Message queue and deduplication
- Session management state transitions
- Retry logic with different failure scenarios

### Integration Tests
- Full message flow from input to display
- Reconnection scenarios
- Concurrent message handling
- Session switching

### Load Tests
- Multiple concurrent users
- Rapid message sending
- Network interruption simulation
- Long-running sessions

### Manual Testing Checklist
- [ ] Send message, get response
- [ ]. Send message, disconnect, reconnect
- [ ] Send multiple messages rapidly
- [ ] Switch between sessions
- [ ] Test with slow network
- [ ] Test with agent timeouts
- [ ] Verify no message duplication
- [ ] Verify no message loss

## Rollback Plan

If issues arise after deployment:
1. Revert to previous Git commit
2. Deploy previous Docker image
3. Restore previous Cloud Run revision
4. Monitor logs for 30 minutes

## Success Metrics

- **Zero message loss rate** (primary metric)
- **< 100ms message delivery latency** (p99)
- **< 1% WebSocket disconnection rate**
- **100% message recovery on reconnection**
- **No duplicate messages**

## Risk Mitigation

### Risk 1: Breaking Changes
- **Mitigation**: Feature flag for gradual rollout
- **Testing**: Extensive QA in staging environment

### Risk 2: Performance Degradation
- **Mitigation**: Load testing before deployment
- **Monitoring**: Real-time performance metrics

### Risk 3: Compatibility Issues
- **Mitigation**: Test with various browsers/devices
- **Fallback**: Maintain backward compatibility

## Documentation Updates Required

1. Update CLAUDE.md with new debugging commands
2. Add WebSocket troubleshooting guide
3. Document new logging format
4. Update API documentation
5. Add monitoring dashboard setup guide

## Code Review Checklist

- [ ] All error paths handled
- [ ] No race conditions
- [ ] Memory leaks prevented
- [ ] Proper cleanup on disconnection
- [ ] Security considerations addressed
- [ ] Performance impact assessed
- [ ] Tests cover edge cases
- [ ] Documentation complete

## Notes

- Consider using Socket.IO's built-in acknowledgment feature
- Evaluate switching to Server-Sent Events (SSE) for one-way streaming
- Consider implementing GraphQL subscriptions as alternative
- May need to increase Cloud Run timeout settings
- Monitor Cloud Run cold start impact on WebSocket connections