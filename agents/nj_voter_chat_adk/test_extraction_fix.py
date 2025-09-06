#!/usr/bin/env python3
"""
Test script to verify the improved ADK response extraction logic.
This tests various response formats that ADK might return.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)
os.chdir(project_root)  # Change to project root for imports

from agents.nj_voter_chat_adk.agent import extract_response_text

# Mock classes to simulate ADK response structures
class MockPart:
    def __init__(self, text=None):
        if text is not None:
            self.text = text

class MockContent:
    def __init__(self, parts):
        self.parts = parts

class MockResponse:
    def __init__(self, content=None, text=None):
        if content:
            self.content = content
        if text is not None:
            self.text = text

def test_extraction():
    """Test various ADK response formats"""
    print("Testing ADK Response Extraction Improvements")
    print("=" * 50)
    
    # Test 1: Standard ADK response with content.parts
    print("\nTest 1: Standard ADK response with content.parts")
    response1 = MockResponse(
        content=MockContent([
            MockPart("This is the response text from ADK.")
        ])
    )
    result1 = extract_response_text(response1)
    assert result1 == "This is the response text from ADK."
    print(f"✓ Extracted: {result1[:50]}...")
    
    # Test 2: Empty response from ADK
    print("\nTest 2: Empty response from ADK")
    response2 = MockResponse(
        content=MockContent([
            MockPart("")  # Empty string indicates ADK returned no content
        ])
    )
    result2 = extract_response_text(response2)
    assert result2 and "couldn't generate" in result2.lower()
    print(f"✓ Handled empty response: {result2[:50]}...")
    
    # Test 3: Multiple parts in response
    print("\nTest 3: Multiple parts in response")
    response3 = MockResponse(
        content=MockContent([
            MockPart("Part 1 of the response."),
            MockPart("Part 2 of the response.")
        ])
    )
    result3 = extract_response_text(response3)
    assert "Part 1" in result3 and "Part 2" in result3
    print(f"✓ Combined multiple parts: {result3[:50]}...")
    
    # Test 4: Direct text attribute
    print("\nTest 4: Direct text attribute")
    response4 = MockResponse(text="Direct text response from ADK")
    result4 = extract_response_text(response4)
    assert result4 == "Direct text response from ADK"
    print(f"✓ Extracted direct text: {result4[:50]}...")
    
    # Test 5: Dict response
    print("\nTest 5: Dict response")
    response5 = {
        "text": "Response from dict format",
        "metadata": {"tokens": 10}
    }
    result5 = extract_response_text(response5)
    assert result5 == "Response from dict format"
    print(f"✓ Extracted from dict: {result5[:50]}...")
    
    # Test 6: List of responses
    print("\nTest 6: List of responses")
    response6 = [
        "First response chunk",
        "Second response chunk"
    ]
    result6 = extract_response_text(response6)
    assert "First response chunk" in result6 and "Second response chunk" in result6
    print(f"✓ Combined list responses: {result6[:50]}...")
    
    # Test 7: None text (different from empty)
    print("\nTest 7: None text response")
    response7 = MockResponse(
        content=MockContent([
            MockPart(None)  # None indicates no text field
        ])
    )
    result7 = extract_response_text(response7)
    assert result7 is None
    print(f"✓ Handled None response correctly: {result7}")
    
    # Test 8: Mixed content with empty and valid parts
    print("\nTest 8: Mixed content with empty and valid parts")
    response8 = MockResponse(
        content=MockContent([
            MockPart(""),  # Empty
            MockPart("Valid response text"),  # Valid
            MockPart("")   # Empty again
        ])
    )
    result8 = extract_response_text(response8)
    assert result8 == "Valid response text"
    print(f"✓ Extracted valid text from mixed parts: {result8[:50]}...")
    
    # Test 9: Nested response structure
    print("\nTest 9: Nested response structure")
    response9 = {
        "response": MockResponse(
            content=MockContent([
                MockPart("Nested response text")
            ])
        )
    }
    result9 = extract_response_text(response9)
    assert result9 == "Nested response text"
    print(f"✓ Extracted from nested structure: {result9[:50]}...")
    
    # Test 10: Duplicate responses (ADK streaming behavior)
    print("\nTest 10: Duplicate responses in list")
    response10 = [
        "Same response text",
        "Same response text",
        "Same response text"
    ]
    result10 = extract_response_text(response10)
    assert result10 == "Same response text"
    print(f"✓ Deduplicated responses: {result10[:50]}...")
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! ADK response extraction is working correctly.")
    print("\nThe improved extraction handles:")
    print("- Standard ADK responses with content.parts")
    print("- Empty responses (returns user-friendly message)")
    print("- Multiple parts in responses")
    print("- Direct text attributes")
    print("- Dict and list responses")
    print("- Nested response structures")
    print("- Duplicate/streaming responses")
    print("- Mixed valid and empty parts")

if __name__ == "__main__":
    try:
        test_extraction()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)