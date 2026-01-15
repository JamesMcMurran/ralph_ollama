# Tool Execution Implementation Guide

This document explains how Ralph handles tool execution for Ollama models.

## The Problem

Ollama models don't have the same tool-calling infrastructure as OpenAI:

- ❌ Don't enforce JSON schema strictly
- ❌ Don't have dedicated tool-call channels
- ❌ Don't auto-invoke tools
- ❌ May embed tool calls in plain text responses

This means Ralph must:
1. ✅ Detect tool calls in both structured and text formats
2. ✅ Execute the tools
3. ✅ Inject results back into the conversation
4. ✅ Prevent infinite loops

## Architecture

### 1. Tool Call Detection (`tool_parser.py`)

The `detect_tool_calls_in_text()` function looks for multiple patterns:

**Pattern 1: JSON embedded in text**
```
Let me read the file:
{"name": "read_file", "arguments": {"path": "prd.json"}}
```

**Pattern 2: Multi-line format**
```
Tool: read_file
Arguments: {"path": "prd.json"}
```

**Pattern 3: Function call style**
```
read_file({"path": "prd.json"})
```

The parser uses:
- Balanced brace matching for nested JSON
- Regex patterns for each format
- Validation that tool names are recognized

### 2. Tool Execution (`tools.py`)

The `ToolExecutor` class maps tool names to actual functions:

| Tool Name | Action |
|-----------|--------|
| `read_file` | Read file contents |
| `write_file` | Write to disk |
| `list_dir` | List directory contents |
| `git_status` | Run `git status --porcelain` |
| `git_diff` | Run `git diff` |
| `git_current_branch` | Get current branch name |
| `git_commit_all` | Stage all and commit |
| `run_cmd` | Execute shell command (with safety checks) |
| `grep` | Search files for pattern |
| `mkdir` | Create directory |
| `remove` | Remove file or directory |

All tools return string results that get injected back into the conversation.

### 3. Result Injection (`ralph_ollama.py`)

After executing a tool, Ralph adds a message to the conversation:

```python
{
    "role": "tool",
    "tool_call_id": "call_123",
    "content": "TOOL RESULT (read_file):\n<actual file contents>"
}
```

This is **critical** - without this, the model is blind to tool results and will keep asking.

### 4. Loop Prevention

Ralph prevents infinite loops through:

**Deduplication**: Tracks the last 10 tool calls and filters duplicates
```python
recent_tool_calls = [
    ("read_file", {"path": "prd.json"}),
    ("git_status", {}),
    ...
]

# Filter out exact duplicates
unique_calls = deduplicate_tool_calls(new_calls, recent_tool_calls[-3:])
```

**Progress Detection**: Monitors for actual work being done
```python
def has_progress_markers(messages):
    # Check for indicators like:
    # - "Successfully wrote to"
    # - "Committed:"
    # - "Tests passed"
    # - File changes, etc.
```

If no progress is detected after several steps, Ralph warns the user.

### 5. Conversation Flow

```
User: "Begin. Follow the system instructions."
  ↓
Assistant: "I'll read the PRD. {"name": "read_file", "arguments": {"path": "prd.json"}}"
  ↓
[Detection] Found tool call: read_file
  ↓
[Execution] Tool returns: "{...prd contents...}"
  ↓
[Injection] Add to messages: "TOOL RESULT (read_file): {...}"
  ↓
Assistant: "I see the PRD has 3 stories. Let me check the current branch..."
  ↓
... (continue until done)
```

## Implementation Chunks

### ✅ Chunk 1: Detect tool calls in model output

**File**: `tool_parser.py`  
**Function**: `detect_tool_calls_in_text()`

Parses text responses looking for:
- JSON objects with `name` and `arguments` keys
- Multi-line tool format
- Function call syntax

### ✅ Chunk 2: Execute the tool

**File**: `tools.py`  
**Class**: `ToolExecutor`

Maps tool names to Python functions. Each tool:
- Validates arguments
- Executes the operation
- Returns a string result

### ✅ Chunk 3: Inject tool result back

**File**: `ralph_ollama.py`  
**Location**: Main loop after tool execution

Adds tool results as messages with role="tool":
```python
messages.append({
    "role": "tool",
    "tool_call_id": tool_id,
    "content": f"TOOL RESULT ({tool_name}):\n{result}"
})
```

### ✅ Chunk 4: Stop re-asking once tool result is provided

**File**: `tool_parser.py`  
**Function**: `deduplicate_tool_calls()`

Prevents infinite loops by:
- Tracking recent tool calls (last 10)
- Filtering out exact duplicates
- Warning when duplicates are detected

### ✅ Chunk 5: Add a hard "progress made" detector

**File**: `tool_parser.py`  
**Function**: `has_progress_markers()`

Detects real progress by looking for:
- File writes ("Successfully wrote to")
- Commits ("Committed:")
- Test passes ("Tests passed")
- PRD updates (`"passes": true`)

## Testing

Run the test suite:

```bash
python3 test_tool_parser.py
```

Tests cover:
- JSON detection in text
- Multiple tool calls
- Various formats
- Deduplication logic
- Progress detection

## Debugging

### Enable verbose logging

```bash
# In ralph_ollama.py, uncomment debug prints
# Or run with stderr redirected
./ralph.sh 2>&1 | tee ralph.log
```

### Check what's being detected

```python
from tool_parser import detect_tool_calls_in_text

text = """Your model output here"""
calls = detect_tool_calls_in_text(text)
print(calls)
```

### Verify tools are executing

Look for this in stderr output:
```
[Step 1] Executing 1 tool call(s)...
  → read_file({"path": "prd.json"})
     ✓ {...200 chars preview...}
```

If you see:
- ❌ Model keeps requesting the same tool → Check deduplication
- ❌ Tool results not visible to model → Check message injection
- ❌ No tools detected → Model output format issue (check parsing)
- ❌ Infinite loop of reads → No progress being made (check step 5)

## Why This Is Necessary

OpenAI models have native tool calling:
- Structured `tool_calls` array in response
- Dedicated message channel for tool results
- Schema validation

Ollama models may:
- Embed tool calls in text
- Not use structured format consistently
- Require text-based result injection

Ralph bridges this gap, allowing local Ollama models to use tools effectively.

## Performance Considerations

- Tool detection adds ~1-2ms per response
- Deduplication is O(n) where n = recent calls (max 10)
- Progress detection is O(m) where m = recent messages (max 3)

Total overhead: negligible compared to LLM inference time.

## Future Improvements

- [ ] Support more tool formats (YAML, etc.)
- [ ] Smarter progress detection (git log parsing)
- [ ] Parallel tool execution for independent calls
- [ ] Tool result summarization for long outputs
- [ ] Dynamic tool schema generation from docstrings
