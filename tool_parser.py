"""
Tool call detection and parsing for Ollama responses.

Handles both:
1. Structured tool calls (OpenAI format)
2. Tool calls embedded in text responses
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple


def detect_tool_calls_in_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse tool calls from plain text responses.
    
    Looks for patterns like:
    - {"name": "read_file", "arguments": {"path": "prd.json"}}
    - {"name": "git_status", "arguments": {}}
    - Tool: read_file
      Arguments: {"path": "prd.json"}
    
    Returns list of tool calls in format:
    [
        {"name": "read_file", "arguments": {"path": "prd.json"}},
        ...
    ]
    """
    tool_calls = []
    
    # Pattern 1: JSON objects with name and arguments
    # Match complete JSON objects that have "name" and "arguments" keys
    # More lenient pattern that handles nested braces
    json_pattern = r'\{[^{}]*"name"[^{}]*"arguments"[^{}]*(?:\{[^{}]*\}[^{}]*)?\}'
    
    for match in re.finditer(json_pattern, text, re.DOTALL):
        try:
            # Try to extract a valid JSON object
            json_str = match.group()
            obj = json.loads(json_str)
            if "name" in obj and "arguments" in obj:
                tool_calls.append({
                    "name": obj["name"],
                    "arguments": obj.get("arguments", {})
                })
        except json.JSONDecodeError:
            # Try to find JSON by brace matching
            continue
    
    # Pattern 1b: More aggressive JSON matching with nested braces
    if not tool_calls:
        # Find all potential JSON objects (balanced braces)
        brace_depth = 0
        start_idx = None
        
        for i, char in enumerate(text):
            if char == '{':
                if brace_depth == 0:
                    start_idx = i
                brace_depth += 1
            elif char == '}':
                brace_depth -= 1
                if brace_depth == 0 and start_idx is not None:
                    json_str = text[start_idx:i+1]
                    try:
                        obj = json.loads(json_str)
                        if "name" in obj and "arguments" in obj:
                            tool_calls.append({
                                "name": obj["name"],
                                "arguments": obj.get("arguments", {})
                            })
                    except json.JSONDecodeError:
                        pass
                    start_idx = None
    
    # Pattern 2: Multi-line format
    # Tool: tool_name
    # Arguments: {json}
    multiline_pattern = r'Tool:\s*(\w+)\s+Arguments:\s*(\{[^}]*\})'
    
    for match in re.finditer(multiline_pattern, text, re.IGNORECASE):
        tool_name = match.group(1)
        try:
            arguments = json.loads(match.group(2))
            tool_calls.append({
                "name": tool_name,
                "arguments": arguments
            })
        except json.JSONDecodeError:
            continue
    
    # Pattern 3: Function call style
    # read_file({"path": "prd.json"})
    func_call_pattern = r'(\w+)\(\s*(\{[^}]*\})\s*\)'
    
    for match in re.finditer(func_call_pattern, text):
        tool_name = match.group(1)
        # Check if it's likely a tool name (common tool names)
        common_tools = [
            'read_file', 'write_file', 'list_dir', 'grep',
            'git_status', 'git_diff', 'git_commit_all', 'git_current_branch',
            'git_checkout', 'git_create_branch',
            'run_cmd', 'mkdir', 'remove', 'apply_patch',
            'run_tests', 'update_prd', 'append_progress', 'get_next_story',
            'docker_build', 'docker_compose_up', 'docker_compose_down',
            'docker_exec', 'docker_logs', 'docker_ps', 'docker_test'
        ]
        
        if tool_name in common_tools:
            try:
                arguments = json.loads(match.group(2))
                tool_calls.append({
                    "name": tool_name,
                    "arguments": arguments
                })
            except json.JSONDecodeError:
                continue
    
    return tool_calls


def extract_tool_calls(response_message, response_text: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Extract tool calls from a response.
    
    First checks for structured tool_calls (OpenAI format).
    Falls back to parsing text content if needed.
    
    Returns:
        (tool_calls, reasoning_text)
        - tool_calls: List of {"name": ..., "arguments": ...} dicts
        - reasoning_text: The text content minus tool call JSON
    """
    tool_calls = []
    reasoning_text = response_text
    
    # Check for structured tool calls first (OpenAI/Ollama format)
    if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
        for tc in response_message.tool_calls:
            tool_calls.append({
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments,
                "id": tc.id
            })
        return tool_calls, reasoning_text
    
    # Fall back to text parsing
    if response_text:
        detected_calls = detect_tool_calls_in_text(response_text)
        if detected_calls:
            # Remove the JSON tool calls from reasoning text
            cleaned_text = response_text
            for call in detected_calls:
                # Try to remove the JSON representation
                json_str = json.dumps({"name": call["name"], "arguments": call["arguments"]})
                cleaned_text = cleaned_text.replace(json_str, "")
            
            reasoning_text = cleaned_text.strip()
            
            # Add synthetic IDs for text-parsed calls
            for i, call in enumerate(detected_calls):
                if "id" not in call:
                    call["id"] = f"text_tool_{i}"
                tool_calls.extend([call])
    
    return tool_calls, reasoning_text


def deduplicate_tool_calls(
    tool_calls: List[Dict[str, Any]],
    recent_calls: List[Tuple[str, Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Remove duplicate tool calls that were just executed.
    
    Args:
        tool_calls: New tool calls to execute
        recent_calls: List of (tool_name, arguments) tuples from recent history
    
    Returns:
        Filtered list with duplicates removed
    """
    unique_calls = []
    
    for call in tool_calls:
        # Check if this exact call was just executed
        is_duplicate = False
        for recent_name, recent_args in recent_calls:
            if call["name"] == recent_name and call["arguments"] == recent_args:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_calls.append(call)
    
    return unique_calls


def has_progress_markers(messages: List[Dict], since_step: int = -3) -> bool:
    """
    Detect if real progress was made in recent steps.
    
    Checks for indicators like:
    - File was written
    - Commit was made
    - PRD was updated
    - Tests passed
    
    Args:
        messages: Conversation history
        since_step: How many steps back to check (negative = recent)
    
    Returns:
        True if progress indicators found
    """
    # Look at recent tool results
    recent_messages = messages[since_step:] if since_step < 0 else messages[-3:]
    
    progress_indicators = [
        "successfully wrote to",
        "committed:",
        "patch applied successfully",
        "created directory:",
        "✓", "✅", "success",
        '"passes": true',
        "test passed",
        "all tests passed"
    ]
    
    for msg in recent_messages:
        if msg.get("role") == "tool":
            content = msg.get("content", "").lower()
            for indicator in progress_indicators:
                if indicator.lower() in content:
                    return True
    
    return False
