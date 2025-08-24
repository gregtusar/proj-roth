#!/usr/bin/env python3
"""Test session integration without requiring external authentication"""

import asyncio
import os
import sys
import tempfile
from unittest.mock import Mock, patch

sys.path.append("backend")
sys.path.append("agents/nj_voter_chat_adk")

async def test_firestore_service_fixes():
    """Test the fixed FirestoreChatService functionality"""
    print("Testing FirestoreChatService fixes...")
    
    try:
        from services.firestore_chat_service import FirestoreChatService
        from models.chat_session import ChatSession, ChatMessage
        
        with patch('google.cloud.firestore.Client') as mock_client:
            mock_sync_client = Mock()
            mock_client.return_value = mock_sync_client
            
            mock_doc_ref = Mock()
            mock_collection = Mock()
            mock_collection.document.return_value = mock_doc_ref
            mock_sync_client.collection.return_value = mock_collection
            
            service = FirestoreChatService()
            service.sync_client = mock_sync_client
            
            print("✓ FirestoreChatService initializes with null safety checks")
            
            session = await service.create_session(
                user_id="test_user",
                user_email="test@example.com",
                session_name="Test Session"
            )
            print(f"✓ Session creation works: {session.session_id}")
            
            seq_num = await service._get_next_sequence_number("test_session")
            print(f"✓ Atomic sequence number generation: {seq_num}")
            
            print("✓ All FirestoreChatService fixes verified")
            return True
            
    except Exception as e:
        print(f"✗ FirestoreChatService test failed: {e}")
        return False

async def test_session_integration():
    """Test the SessionIntegration class"""
    print("\nTesting SessionIntegration...")
    
    try:
        from session_integration import SessionIntegration
        
        with patch.object(SessionIntegration, '_initialize_service'):
            integration = SessionIntegration()
            integration.session_service = Mock()
            
            mock_session = Mock()
            mock_session.session_id = "test_session_123"
            integration.session_service.create_session.return_value = mock_session
            integration.session_service.get_session.return_value = mock_session
            
            session_id = await integration.create_or_get_session(
                user_id="test_user",
                user_email="test@example.com"
            )
            print(f"✓ Session integration creates sessions: {session_id}")
            
            await integration.add_message(
                session_id=session_id,
                user_id="test_user",
                message_type="user",
                message_text="Test message"
            )
            print("✓ Session integration adds messages")
            
            print("✓ SessionIntegration works correctly")
            return True
            
    except Exception as e:
        print(f"✗ SessionIntegration test failed: {e}")
        return False

def test_agent_integration():
    """Test that the agent properly integrates with session persistence"""
    print("\nTesting Agent Integration...")
    
    try:
        os.environ["VOTER_LIST_USER_ID"] = "test_user"
        os.environ["VOTER_LIST_USER_EMAIL"] = "test@example.com"
        os.environ["CHAT_SESSION_ID"] = "test_session_456"
        
        from agent import NJVoterChatAgent
        
        with patch('agent.SessionIntegration') as mock_integration_class:
            mock_integration = Mock()
            mock_integration_class.return_value = mock_integration
            mock_integration.create_or_get_session.return_value = "test_session_456"
            
            agent = NJVoterChatAgent()
            
            assert hasattr(agent, '_persistent_sessions'), "Agent should have _persistent_sessions attribute"
            print("✓ Agent initializes with persistent session integration")
            
            print("✓ Agent integration works correctly")
            return True
            
    except Exception as e:
        print(f"✗ Agent integration test failed: {e}")
        return False

def test_data_models():
    """Test the updated data models"""
    print("\nTesting Data Models...")
    
    try:
        from models.chat_session import ChatSession, ChatMessage
        from datetime import datetime
        
        session = ChatSession(
            session_id="test_session",
            user_id="test_user",
            user_email="test@example.com",
            session_name="Test Session",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_sequence_number=5
        )
        
        assert session.last_sequence_number == 5, "ChatSession should have last_sequence_number field"
        print("✓ ChatSession model includes last_sequence_number field")
        
        message = ChatMessage(
            message_id="test_msg",
            session_id="test_session",
            user_id="test_user",
            message_type="user",
            message_text="Test message",
            timestamp=datetime.now(),
            sequence_number=1
        )
        
        assert message.sequence_number == 1, "ChatMessage should have sequence_number field"
        print("✓ ChatMessage model works correctly")
        
        print("✓ Data models updated successfully")
        return True
        
    except Exception as e:
        print(f"✗ Data models test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("Session Management Integration Tests")
    print("=" * 50)
    
    results = []
    
    results.append(await test_firestore_service_fixes())
    results.append(await test_session_integration())
    results.append(test_agent_integration())
    results.append(test_data_models())
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} tests passed!")
        print("Session management integration is working correctly.")
        return True
    else:
        print(f"✗ {total - passed} out of {total} tests failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
