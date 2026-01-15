# Ralph Ollama Migration - Complete ✅

This document summarizes the completed migration from Amp to Ollama.

## All 10 Chunks Completed

### ✅ Chunk 1: Ollama config + dependency skeleton
- Created `ralph_ollama.py` with CLI argument parsing
- Created `requirements.txt` using OpenAI-compatible approach
- Created `.env.example` with configuration options
- Supports `--model`, `--host`, and `--max-steps` arguments

### ✅ Chunk 2: Replace amp call site in ralph.sh
- Updated `ralph.sh` to call `ralph_ollama.py` instead of amp
- Preserved `<promise>COMPLETE</promise>` detection logic
- Loop continues to work as before

### ✅ Chunk 3: Update prompt.md for non-Amp environment
- Removed Amp-specific thread URL references
- Changed thread line to "Thread: local"
- Added instruction to use tools for file reading
- Removed browser skill references

### ✅ Chunk 4: Implement one Ollama call (no tools)
- Implemented basic Ollama chat completion
- Loads `prompt.md` as system message
- Uses OpenAI-compatible `/v1/chat/completions` endpoint
- Returns model response to stdout

### ✅ Chunk 5: Add tool schemas + dispatcher (read-only)
- Created `tools.py` with tool definitions and executor
- Implemented read-only tools:
  - `read_file(path)` - Read file contents
  - `list_dir(path)` - List directory contents
  - `grep(pattern, path)` - Search with grep
  - `git_status()` - Get git status
  - `git_diff(cached)` - Get git diff
- Integrated tools with ralph_ollama.py

### ✅ Chunk 6: Add write/mutate tools
- Added write operations:
  - `write_file(path, content)` - Write/overwrite files
  - `apply_patch(patch)` - Apply unified diffs with git apply
  - `run_cmd(command, cwd)` - Run shell commands with safety guards
  - `mkdir(path)` - Create directories
  - `remove(path)` - Remove files/directories
- Safety guardrails for dangerous commands

### ✅ Chunk 7: Add tool-call loop (multi-step)
- Implemented iterative tool calling loop
- Respects `RALPH_MAX_TOOL_STEPS` safety cap
- Properly formats tool call/response messages
- Prints progress to stderr, final output to stdout
- Handles both tool calls and text responses

### ✅ Chunk 8: Implement git workflow tools
- Added git operations:
  - `git_checkout(branch)` - Checkout branch
  - `git_create_branch(branch, from_ref)` - Create new branch
  - `git_commit_all(message)` - Stage and commit all changes
  - `git_current_branch()` - Get current branch name
- Enables full Ralph workflow automation

### ✅ Chunk 9: Update docs to remove Amp references
- Updated `README.md`:
  - Replaced Amp with Ollama throughout
  - Added setup instructions for Ollama
  - Documented tool-capable model requirement
  - Updated key files table
- Updated `AGENTS.md`:
  - Added Ollama setup commands
  - Updated file descriptions
  - Added tool calling note
- Updated `flowchart/src/App.tsx`:
  - Changed "Amp picks a story" → "Agent picks a story"
  - Changed title to "How Ralph Works with Ollama"

### ✅ Chunk 10: Add smoke test
- Created `scripts/smoke.sh`:
  - Checks Ollama connectivity
  - Verifies model availability
  - Tests Python dependencies
  - Runs simple chat completion test
- Added `--health` flag to `ralph_ollama.py`:
  - Python-based health check
  - Detailed error messages
  - Verifies full stack

## File Structure

```
ralph_ollama/
├── ralph.sh                 # Main loop (updated)
├── ralph_ollama.py         # Ollama runner with tool support (NEW)
├── tools.py                # Tool definitions and executors (NEW)
├── prompt.md               # Agent instructions (updated)
├── requirements.txt        # Python dependencies (NEW)
├── .env.example            # Environment template (NEW)
├── prd.json.example        # PRD format example
├── README.md               # User documentation (updated)
├── AGENTS.md               # Agent patterns (updated)
├── scripts/
│   └── smoke.sh            # Smoke test script (NEW)
├── flowchart/              # React Flow diagram (updated)
└── skills/                 # Legacy (can be removed)
```

## Usage

### Quick Start

```bash
# 1. Install Ollama and pull a model
ollama pull llama3.1

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run health check
python3 ralph_ollama.py --health
# or
./scripts/smoke.sh

# 4. Run Ralph
./ralph.sh 10
```

### Environment Variables

```bash
export RALPH_MODEL=llama3.1              # Model to use
export OLLAMA_HOST=http://localhost:11434  # Ollama API host
export RALPH_MAX_TOOL_STEPS=50           # Safety limit per iteration
```

## API Approach

**OpenAI-Compatible Endpoint**: Using the OpenAI Python client with `base_url` set to Ollama's `/v1` endpoint. This provides:
- Standard tool/function calling support
- Familiar API interface
- Easy migration path
- Wide model compatibility

## Tool Capabilities

Ralph can now:
- Read and write files
- Run shell commands (with safety guardrails)
- Execute git operations (checkout, commit, branch)
- Search codebases with grep
- Apply patches with git apply
- Create/remove directories

## Requirements

- **Ollama**: Running locally or remotely
- **Tool-capable model**: llama3.1, qwen2.5, mistral, etc.
- **Python 3.8+**: With openai and python-dotenv packages
- **Git**: For version control operations
- **jq**: For JSON parsing in bash scripts

## Testing Without Ollama

The implementation is complete but requires Ollama to be running to test end-to-end. To verify:

1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Start Ollama: `ollama serve` (or it may auto-start)
3. Pull a model: `ollama pull llama3.1`
4. Run health check: `./scripts/smoke.sh`
5. Test with a simple PRD: `./ralph.sh 1`

## Migration Complete

All 10 chunks have been implemented. The codebase is now fully Ollama-native with no Amp dependencies. Ralph can autonomously:

1. Read PRD from prd.json
2. Check/create git branches
3. Read/write files with tools
4. Run tests and quality checks
5. Commit changes with proper messages
6. Update prd.json to mark completion
7. Log progress for future iterations
8. Loop until all stories are complete

The implementation supports the full Ralph workflow using local Ollama models with function calling.
