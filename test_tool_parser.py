#!/usr/bin/env python3
"""
Tests for tool_parser.py
"""

import json
from tool_parser import detect_tool_calls_in_text, deduplicate_tool_calls, has_progress_markers


def test_json_embedded():
    """Test detecting JSON-formatted tool calls in text."""
    text = '''
    I need to read the PRD file.
    {"name": "read_file", "arguments": {"path": "prd.json"}}
    '''
    
    calls = detect_tool_calls_in_text(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "read_file"
    assert calls[0]["arguments"]["path"] == "prd.json"
    print("✓ JSON embedded test passed")


def test_multiple_calls():
    """Test detecting multiple tool calls."""
    text = '''
    First, let me check the current branch:
    {"name": "git_current_branch", "arguments": {}}
    
    Then read the PRD:
    {"name": "read_file", "arguments": {"path": "prd.json"}}
    '''
    
    calls = detect_tool_calls_in_text(text)
    assert len(calls) == 2
    assert calls[0]["name"] == "git_current_branch"
    assert calls[1]["name"] == "read_file"
    print("✓ Multiple calls test passed")


def test_function_call_style():
    """Test detecting function-call style tool invocations."""
    text = '''
    Let me read the file:
    read_file({"path": "prd.json"})
    '''
    
    calls = detect_tool_calls_in_text(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "read_file"
    print("✓ Function call style test passed")


def test_multiline_format():
    """Test detecting multi-line format."""
    text = '''
    Tool: read_file
    Arguments: {"path": "prd.json"}
    '''
    
    calls = detect_tool_calls_in_text(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "read_file"
    print("✓ Multi-line format test passed")


def test_deduplication():
    """Test tool call deduplication."""
    new_calls = [
        {"name": "read_file", "arguments": {"path": "prd.json"}},
        {"name": "git_status", "arguments": {}},
        {"name": "read_file", "arguments": {"path": "prd.json"}},  # duplicate
    ]
    
    recent = [
        ("read_file", {"path": "prd.json"}),
    ]
    
    unique = deduplicate_tool_calls(new_calls, recent)
    assert len(unique) == 1
    assert unique[0]["name"] == "git_status"
    print("✓ Deduplication test passed")


def test_progress_detection():
    """Test progress marker detection."""
    messages = [
        {"role": "tool", "content": "TOOL RESULT (write_file):\nSuccessfully wrote to prd.json"},
        {"role": "assistant", "content": "File updated"},
    ]
    
    assert has_progress_markers(messages)
    print("✓ Progress detection test passed")


def test_no_progress():
    """Test no progress detection."""
    messages = [
        {"role": "tool", "content": "TOOL RESULT (read_file):\n{...}"},
        {"role": "assistant", "content": "I see the file"},
    ]
    
    assert not has_progress_markers(messages)
    print("✓ No progress test passed")


if __name__ == "__main__":
    print("Running tool_parser tests...\n")
    
    test_json_embedded()
    test_multiple_calls()
    test_function_call_style()
    test_multiline_format()
    test_deduplication()
    test_progress_detection()
    test_no_progress()
    
    print("\n✅ All tests passed!")
