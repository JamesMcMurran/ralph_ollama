# Ralph Agent Instructions

## Overview

Ralph is an autonomous AI agent loop that runs Ollama repeatedly until all PRD items are complete. Each iteration is a fresh model invocation with clean context.

## Commands

```bash
# Run the flowchart dev server
cd flowchart && npm run dev

# Build the flowchart
cd flowchart && npm run build

# Run Ralph (from your project that has prd.json)
./ralph.sh [max_iterations]

# Run health check
python3 ralph_ollama.py --health

# Use remote Ollama host
export OLLAMA_HOST=http://your-server:11434
./ralph.sh

# Or configure in .env file
echo "OLLAMA_HOST=http://your-server:11434" >> .env
./ralph.sh

# Test Ollama connectivity
python3 ralph_ollama.py --help
```

## Key Files

- `ralph.sh` - The bash loop that spawns fresh Ollama runner instances
- `ralph_ollama.py` - Python runner that calls Ollama with tool support
- `tools.py` - Tool definitions and executors
- `tool_parser.py` - Detects and parses tool calls from model responses
- `prompt.md` - Instructions given to each model invocation
- `prd.json` - Current PRD (copy from prd_todo_app.json for a fresh run)
- `prd.json.example` - Example PRD format
- `prd_todo_app.json` - Complete Todo web app PRD (6 user stories)
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `flowchart/` - Interactive React Flow diagram explaining how Ralph works

## Setup

1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Pull a tool-capable model: `ollama pull llama3.1`
3. Install Python deps: `pip install -r requirements.txt`
4. Optionally set env vars: `export RALPH_MODEL=llama3.1`

## Running the Todo App Example

```bash
# 1. Setup for Docker Todo app
./setup_todo_run.sh

# 2. Run Ralph (10-15 iterations should be enough)
./ralph.sh 15
```

This will build custom Docker images (Nginx, PHP-FPM, MySQL) and deploy a complete Todo web app running in Docker-in-Docker.

After completion, access the app at: http://localhost:8080

## Flowchart

The `flowchart/` directory contains an interactive visualization built with React Flow. It's designed for presentations - click through to reveal each step with animations.

To run locally:
```bash
cd flowchart
npm install
npm run dev
```

## Patterns

- Each iteration spawns a fresh model invocation with clean context
- Memory persists via git history, `progress.txt`, and `prd.json`
- Stories should be small enough to complete in one context window
- Always update AGENTS.md with discovered patterns for future iterations
- Tool calling requires a compatible model (llama3.1, qwen2.5, mistral, etc.)

### Tool Execution Flow

Ralph implements robust tool execution:

1. **Detection**: Extracts tool calls from model responses (structured or text-embedded)
2. **Deduplication**: Prevents infinite loops by filtering recently executed calls
3. **Execution**: Runs tools via `ToolExecutor` and returns results
4. **Injection**: Adds tool results back to conversation with `TOOL RESULT` prefix
5. **Progress tracking**: Monitors for real progress (commits, file writes, etc.)

This allows Ollama models (which lack native tool-call channels) to effectively use tools.

### Available Tools

**File & Directory:**
- `read_file(path)` - Read file contents
- `write_file(path, content)` - Write/create files
- `list_dir(path)` - List directory contents
- `mkdir(path)` - Create directories
- `remove(path)` - Remove files/directories

**Git:**
- `git_status()` - Get git status
- `git_diff(cached)` - Get git diff
- `git_current_branch()` - Get current branch name
- `git_checkout(branch)` - Checkout branch
- `git_create_branch(branch, from_ref)` - Create new branch
- `git_commit_all(message)` - Stage all and commit

**Docker (DinD):**
- `docker_build(tag, context, dockerfile)` - Build Docker image
- `docker_compose_up(compose_file, detach, build)` - Start services
- `docker_compose_down(compose_file, volumes)` - Stop services
- `docker_exec(container, command)` - Run command in container
- `docker_logs(container, tail)` - Get container logs
- `docker_ps(all)` - List containers
- `docker_test(test_command, container)` - Run test in DinD

**Progress:**
- `get_next_story` - Get highest-priority incomplete story from prd.json
- `run_cmd(command, cwd)` - Run shell commands
- `run_tests(command)` - Run tests with longer timeout
- `update_prd(story_id, passes, notes)` - Mark story complete
- `append_progress(story_id, summary, files_changed, learnings)` - Log progress

### Real-World Validation (Jan 15, 2026)

Tested with actual run on task priority system PRD:
- ✅ **30+ tool calls executed** across 6 iterations
- ✅ **Files created** (migrations/01_add_tasks_table.sql)
- ✅ **Branches created** (ralph/task-priority)
- ✅ **Commits made** (feat: US-001 - Add priority field to database)
- ✅ **Deduplication working** (filtered 1 duplicate call)
- ✅ **Progress tracking** (detected when stuck without progress)

**Key Learning**: Always run from within Python virtual environment:
```bash
source .venv/bin/activate
./ralph.sh
```

See [RUN_ANALYSIS.md](RUN_ANALYSIS.md) for detailed analysis of the test run.
