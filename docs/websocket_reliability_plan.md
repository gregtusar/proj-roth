# WebSocket Reliability Improvements - Implementation Plan

## Overview
Plan for improving WebSocket chunk transmission reliability to prevent lost or duplicated chunks during streaming.

## Current Issues Identified

1. **No Sequence Tracking**: Chunks are sent without sequence numbers, making it impossible to detect missing chunks
2. **No Acknowledgments**: No confirmation that client received chunks
3. **No Retry Logic**: Failed chunk transmissions are lost forever
4. **No Buffering**: Can't retransmit chunks if client reconnects

## Planned Improvements

### 1. Chunk Sequencing
Add sequence numbers to each chunk for ordering and gap detection:

```python
# In websocket.py send_message handler
chunk_data = {
    'text': chunk,
    'sequence': chunk_sequence,
    'session_id': session_id,
    'timestamp': time.time()
}
await sio.emit('message_chunk', chunk_data, room=sid)
```

### 2. Chunk Buffer for Recovery
Maintain a buffer of recently sent chunks per session:

```python
class ChunkBuffer:
    - Store last N chunks per session
    - TTL of 5 minutes per chunk
    - Support querying missing chunks by sequence range
    - Clear on session completion
```

### 3. Client Acknowledgments
Implement optional ACK mechanism:

```python
# Every N chunks, request acknowledgment
if chunk_sequence % 10 == 0:
    await sio.emit('chunk_batch', {
        'sequences': [chunk_sequence-9, chunk_sequence],
        'require_ack': True
    })
    # Wait for client ACK or timeout
```

### 4. Recovery Endpoint
Add WebSocket event handler for chunk recovery:

```python
@sio.event
async def request_missing_chunks(sid, data):
    session_id = data.get('session_id')
    missing_sequences = data.get('missing_sequences', [])
    
    # Retransmit missing chunks from buffer
    for seq in missing_sequences:
        chunk = chunk_buffer.get(session_id, seq)
        if chunk:
            await sio.emit('message_chunk', chunk, room=sid)
```

### 5. Connection Recovery
Handle reconnection gracefully:

```python
@sio.event
async def recover_session(sid, data):
    session_id = data.get('session_id')
    last_received = data.get('last_sequence')
    
    # Send all chunks after last_received
    missing = chunk_buffer.get_after(session_id, last_received)
    for chunk in missing:
        await sio.emit('recovery_chunk', chunk, room=sid)
```

### 6. Metrics and Monitoring
Track reliability metrics:

```python
class ReliabilityMetrics:
    - chunks_sent: Total chunks transmitted
    - chunks_acknowledged: Chunks confirmed by client
    - chunks_retransmitted: Chunks sent again
    - recovery_requests: Number of recovery requests
    - failed_chunks: Chunks that failed after max retries
```

## Implementation Priority

1. **High Priority** (could implement now):
   - Chunk sequencing (simple, high value)
   - Basic chunk buffer (enables recovery)
   - Recovery endpoint (allows manual recovery)

2. **Medium Priority** (nice to have):
   - Client acknowledgments (adds complexity)
   - Automatic retry logic
   - Connection recovery

3. **Low Priority** (optimization):
   - Metrics dashboard
   - Adaptive buffering
   - Compression

## Frontend Changes Required

The frontend would need updates to:
1. Track received sequence numbers
2. Detect gaps in sequences
3. Request missing chunks
4. Send acknowledgments (if implemented)
5. Handle recovery chunks

## Configuration Options

```python
WEBSOCKET_RELIABILITY = {
    'enable_sequencing': True,
    'enable_acknowledgments': False,  # Start with False
    'buffer_size': 1000,  # Max chunks to buffer
    'buffer_ttl': 300,  # Seconds
    'ack_frequency': 10,  # Request ACK every N chunks
    'ack_timeout': 5,  # Seconds to wait for ACK
    'max_retries': 3,
    'retry_backoff': [0.5, 1, 2]  # Exponential backoff
}
```

## Testing Strategy

1. **Unit Tests**: Test ChunkBuffer, sequencing, recovery logic
2. **Integration Tests**: Test full streaming with simulated failures
3. **Load Tests**: Ensure buffering doesn't cause memory issues
4. **Chaos Tests**: Random disconnections, packet loss simulation

## Rollback Plan

All improvements should be behind feature flags:
- Can disable sequencing while keeping streaming
- Can disable ACKs while keeping sequencing
- Can clear buffers if memory issues

## Notes

- The ADK chunk handling fix (already implemented) is separate from and more critical than these WebSocket improvements
- These improvements are about network reliability, not ADK parsing
- Start simple (sequencing only) and add complexity gradually
- Monitor production metrics before adding more features