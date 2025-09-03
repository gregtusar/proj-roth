"""
Integration tests for the complete session management flow.
Tests the entire stack from WebSocket through to ADK agent.
"""
import pytest
import asyncio
import uuid
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import components to test
from core.session_manager import get_session_manager, UnifiedSession
from core.request_context import set_request_context, get_current_request_context
from core.circuit_breaker import get_circuit_manager, CircuitBreakerError
from services.firestore_chat_service import FirestoreChatService
from services.agent_service import process_message_stream, clear_session_agent_cache


@pytest.fixture
def session_manager():
    """Get a fresh session manager for testing"""
    mgr = get_session_manager()
    # Clear any existing sessions
    mgr._sessions.clear()
    mgr._sid_to_session.clear()
    mgr._user_sessions.clear()
    return mgr


@pytest.fixture
def circuit_manager():
    """Get a fresh circuit breaker manager"""
    mgr = get_circuit_manager()
    mgr.reset_all()
    return mgr


@pytest.fixture
async def firestore_service():
    """Mock Firestore service for testing"""
    with patch('services.firestore_chat_service.firestore.Client') as mock_client:
        service = FirestoreChatService()
        service.connected = True
        service.client = mock_client.return_value
        return service


class TestUnifiedSessionManagement:
    """Test the unified session management system"""
    
    def test_unified_session_creation(self, session_manager):
        """Test creating a unified session"""
        chat_id = str(uuid.uuid4())
        user_id = "test_user"
        model_id = "gemini-2.0-flash-exp"
        
        session = session_manager.create_session(chat_id, user_id, model_id)
        
        assert session.chat_id == chat_id
        assert session.user_id == user_id
        assert session.model_id == model_id
        assert session.get_adk_session_id() == f"adk_{chat_id}"
        assert session.get_agent_cache_key() == f"{user_id}:{chat_id}:{model_id}:{session.created_at.date().isoformat()}"
    
    def test_session_websocket_registration(self, session_manager):
        """Test registering WebSocket connections with sessions"""
        chat_id = str(uuid.uuid4())
        user_id = "test_user"
        ws_sid = "websocket_123"
        
        session = session_manager.create_session(chat_id, user_id)
        session_manager.register_websocket(chat_id, ws_sid)
        
        # Check WebSocket is registered
        assert session.has_active_connections()
        assert ws_sid in session._websocket_sids
        
        # Check reverse lookup works
        retrieved_session = session_manager.get_session_by_websocket(ws_sid)
        assert retrieved_session == session
        
        # Unregister and verify
        session_manager.unregister_websocket(ws_sid)
        assert not session.has_active_connections()
        assert session_manager.get_session_by_websocket(ws_sid) is None
    
    def test_session_model_update(self, session_manager):
        """Test updating session model and cache key changes"""
        chat_id = str(uuid.uuid4())
        user_id = "test_user"
        initial_model = "gemini-2.0-flash-exp"
        new_model = "gemini-2.0-pro"
        
        session = session_manager.create_session(chat_id, user_id, initial_model)
        initial_cache_key = session.get_agent_cache_key()
        
        # Update model
        new_cache_key = session_manager.update_session_model(chat_id, new_model)
        
        assert session.model_id == new_model
        assert new_cache_key != initial_cache_key
        assert new_model in new_cache_key
    
    def test_user_sessions_retrieval(self, session_manager):
        """Test getting all sessions for a user"""
        user_id = "test_user"
        
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            chat_id = str(uuid.uuid4())
            session = session_manager.create_session(chat_id, user_id)
            session_ids.append(chat_id)
            # Add small delay to ensure different last_accessed times
            asyncio.sleep(0.01)
        
        # Get user sessions
        user_sessions = session_manager.get_user_sessions(user_id)
        
        assert len(user_sessions) == 3
        # Check they're sorted by last_accessed (most recent first)
        for i in range(len(user_sessions) - 1):
            assert user_sessions[i].last_accessed >= user_sessions[i + 1].last_accessed


class TestRequestContext:
    """Test the request context management"""
    
    def test_context_manager_basic(self):
        """Test basic context manager functionality"""
        user_id = "test_user"
        user_email = "test@example.com"
        session_id = str(uuid.uuid4())
        model_id = "gemini-2.0-flash-exp"
        request_id = str(uuid.uuid4())
        
        # Context should be None initially
        assert get_current_request_context() is None
        
        # Set context
        with set_request_context(
            user_id=user_id,
            user_email=user_email,
            session_id=session_id,
            model_id=model_id,
            request_id=request_id
        ) as ctx:
            # Context should be available
            current_ctx = get_current_request_context()
            assert current_ctx is not None
            assert current_ctx.user.user_id == user_id
            assert current_ctx.user.user_email == user_email
            assert current_ctx.session.session_id == session_id
            assert current_ctx.session.model_id == model_id
        
        # Context should be cleared after exiting
        assert get_current_request_context() is None
    
    def test_nested_contexts(self):
        """Test that nested contexts don't interfere"""
        user1_id = "user1"
        user2_id = "user2"
        
        with set_request_context(
            user_id=user1_id,
            user_email="user1@example.com",
            session_id="session1",
            model_id="model1",
            request_id="req1"
        ):
            ctx1 = get_current_request_context()
            assert ctx1.user.user_id == user1_id
            
            # Create nested context
            with set_request_context(
                user_id=user2_id,
                user_email="user2@example.com",
                session_id="session2",
                model_id="model2",
                request_id="req2"
            ):
                ctx2 = get_current_request_context()
                assert ctx2.user.user_id == user2_id
            
            # Original context should be restored
            ctx1_after = get_current_request_context()
            assert ctx1_after.user.user_id == user1_id
    
    async def test_context_in_async_tasks(self):
        """Test context isolation in async tasks"""
        results = []
        
        async def task_with_context(user_id: str, delay: float):
            with set_request_context(
                user_id=user_id,
                user_email=f"{user_id}@example.com",
                session_id=f"session_{user_id}",
                model_id="model",
                request_id=f"req_{user_id}"
            ):
                await asyncio.sleep(delay)
                ctx = get_current_request_context()
                results.append(ctx.user.user_id)
        
        # Run multiple tasks concurrently
        await asyncio.gather(
            task_with_context("user1", 0.01),
            task_with_context("user2", 0.005),
            task_with_context("user3", 0.015)
        )
        
        # Each task should have maintained its own context
        assert set(results) == {"user1", "user2", "user3"}


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    async def test_circuit_breaker_states(self, circuit_manager):
        """Test circuit breaker state transitions"""
        breaker = circuit_manager.get_or_create(
            "test_service",
            failure_threshold=2,
            recovery_timeout=1
        )
        
        # Mock function that can fail
        call_count = 0
        
        async def flaky_function(should_fail=False):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise Exception("Service error")
            return "success"
        
        # Initial state should be closed
        assert breaker.get_state() == "closed"
        
        # Successful call
        result = await breaker.call(flaky_function, should_fail=False)
        assert result == "success"
        assert breaker.get_state() == "closed"
        
        # First failure
        with pytest.raises(Exception):
            await breaker.call(flaky_function, should_fail=True)
        assert breaker.get_state() == "closed"  # Still closed (threshold=2)
        
        # Second failure - should open
        with pytest.raises(Exception):
            await breaker.call(flaky_function, should_fail=True)
        assert breaker.get_state() == "open"
        
        # Calls should be rejected while open
        with pytest.raises(CircuitBreakerError):
            await breaker.call(flaky_function, should_fail=False)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Next call should be allowed (half-open state)
        result = await breaker.call(flaky_function, should_fail=False)
        assert result == "success"
        
        # After success threshold, should be closed
        result = await breaker.call(flaky_function, should_fail=False)
        assert breaker.get_state() == "closed"
    
    def test_circuit_breaker_statistics(self, circuit_manager):
        """Test circuit breaker statistics tracking"""
        breaker = circuit_manager.get_or_create("stats_test")
        
        async def test_function():
            return "success"
        
        # Make some calls
        asyncio.run(breaker.call(test_function))
        asyncio.run(breaker.call(test_function))
        
        stats = breaker.get_stats()
        assert stats["total_calls"] == 2
        assert stats["total_successes"] == 2
        assert stats["total_failures"] == 0
        assert stats["success_rate"] == 100.0


class TestMessageQueueIntegration:
    """Test message queue functionality (frontend component)"""
    
    # Note: These would be JavaScript/TypeScript tests in practice
    # Included here for completeness of the test plan
    
    def test_message_queue_deduplication(self):
        """Test that duplicate messages are properly filtered"""
        # This would test the MessageQueue.enqueue() deduplication logic
        pass
    
    def test_message_queue_session_filtering(self):
        """Test that messages for different sessions are filtered"""
        # This would test MessageQueue.setCurrentSession() filtering
        pass
    
    def test_message_queue_retry_logic(self):
        """Test message retry on failure"""
        # This would test the retry mechanism in MessageQueue.processQueue()
        pass


class TestEndToEndFlow:
    """Test complete message flow from WebSocket to agent response"""
    
    @pytest.mark.asyncio
    async def test_full_message_flow(self, session_manager, firestore_service):
        """Test complete message flow through the system"""
        user_id = "test_user"
        user_email = "test@example.com"
        session_id = str(uuid.uuid4())
        message = "What is the weather?"
        
        # 1. Create unified session
        unified_session = session_manager.create_session(session_id, user_id)
        
        # 2. Register WebSocket connection
        ws_sid = "ws_123"
        session_manager.register_websocket(session_id, ws_sid)
        
        # 3. Mock agent response
        with patch('services.agent_service.NJVoterChatAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent.chat.return_value = Mock(
                content=Mock(parts=[Mock(text="The weather is sunny")])
            )
            mock_agent_class.return_value = mock_agent
            
            # 4. Process message with context
            with set_request_context(
                user_id=user_id,
                user_email=user_email,
                session_id=session_id,
                model_id="gemini-2.0-flash-exp",
                request_id=str(uuid.uuid4())
            ):
                response_chunks = []
                async for chunk in process_message_stream(
                    message=message,
                    session_id=session_id,
                    user_id=user_id,
                    user_email=user_email
                ):
                    response_chunks.append(chunk)
                
                # Verify response was streamed
                assert len(response_chunks) > 0
                full_response = "".join(response_chunks)
                assert len(full_response) > 0
        
        # 5. Verify session state
        retrieved_session = session_manager.get_session(session_id)
        assert retrieved_session is not None
        assert retrieved_session.has_active_connections()
        
        # 6. Clean up
        session_manager.unregister_websocket(ws_sid)
        clear_session_agent_cache(session_id)
    
    @pytest.mark.asyncio
    async def test_session_recovery_after_disconnect(self, session_manager):
        """Test session recovery after WebSocket disconnection"""
        user_id = "test_user"
        session_id = str(uuid.uuid4())
        
        # Create session and register connection
        session = session_manager.create_session(session_id, user_id)
        ws_sid1 = "ws_1"
        session_manager.register_websocket(session_id, ws_sid1)
        
        # Simulate disconnect
        session_manager.unregister_websocket(ws_sid1)
        assert not session.has_active_connections()
        
        # Simulate reconnect with new WebSocket
        ws_sid2 = "ws_2"
        session_manager.register_websocket(session_id, ws_sid2)
        
        # Session should be recovered
        assert session.has_active_connections()
        assert ws_sid2 in session._websocket_sids
        assert ws_sid1 not in session._websocket_sids
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, session_manager):
        """Test handling multiple concurrent sessions"""
        users = [f"user_{i}" for i in range(5)]
        sessions = []
        
        # Create multiple sessions concurrently
        async def create_session(user_id):
            session_id = str(uuid.uuid4())
            session = session_manager.create_session(session_id, user_id)
            return session
        
        sessions = await asyncio.gather(*[
            create_session(user_id) for user_id in users
        ])
        
        # Verify all sessions were created
        assert len(sessions) == 5
        
        # Verify each user has their session
        for i, user_id in enumerate(users):
            user_sessions = session_manager.get_user_sessions(user_id)
            assert len(user_sessions) == 1
            assert user_sessions[0].user_id == user_id


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])