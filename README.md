# Ralph

![Ralph](ralph.webp)

Ralph is an autonomous AI agent loop that runs Ollama repeatedly until all PRD items are complete. Each iteration is a fresh model invocation with clean context. Memory persists via git history, `progress.txt`, and `prd.json`.

Based on [Geoffrey Huntley's Ralph pattern](https://ghuntley.com/ralph/).

[Read the in-depth article on the Ralph pattern](https://x.com/ryancarson/status/2008548371712135632)

## Prerequisites

- [Ollama](https://ollama.ai) installed and running
- A tool-capable model (e.g., llama3.1, qwen2.5, mistral)
- Python 3.8+ with pip
- `jq` installed (`brew install jq` on macOS)
- A git repository for your project

## Setup

### 1. Install Ollama and pull a model

```bash
# Install Ollama (see https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a tool-capable model
ollama pull llama3.1
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment (optional)

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
# Edit .env to set your preferred model and settings
```

Or export environment variables:

```bash
export RALPH_MODEL=llama3.1
export OLLAMA_HOST=http://localhost:11434
export RALPH_MAX_TOOL_STEPS=50
```

**Using a remote Ollama host:**

To use a remote Ollama server, set the `OLLAMA_HOST` in your `.env` file:

```bash
# Local Ollama
OLLAMA_HOST=http://localhost:11434

# Remote Ollama (by IP)
OLLAMA_HOST=http://192.168.1.100:11434

# Remote Ollama (by domain)
OLLAMA_HOST=https://ollama.example.com
```

Make sure your remote Ollama server is accessible and has the required model pulled.

📖 **See [REMOTE_SETUP.md](REMOTE_SETUP.md) for detailed instructions on setting up and securing a remote Ollama server.**

### 4. Verify setup (optional but recommended)

```bash
# Run health check to verify Ollama connectivity and model availability
python3 ralph_ollama.py --health

# Or specify a custom host
python3 ralph_ollama.py --host http://your-server:11434 --health
```

### 5. Copy to your project (optional)

```bash
# From your project root
mkdir -p scripts/ralph
cp /path/to/ralph_ollama/*.{py,sh,md,txt,example} scripts/ralph/
chmod +x scripts/ralph/ralph.sh
```

## Workflow

### 1. Create a PRD

Create a `prd.json` file with your user stories (see `prd.json.example` for format).

### 2. Run Ralph

```bash
./ralph.sh [max_iterations]
```

Default is 10 iterations.

Ralph will:
1. Create a feature branch (from PRD `branchName`)
2. Pick the highest priority story where `passes: false`
3. Implement that single story using available tools
4. Run quality checks (typecheck, tests)
5. Commit if checks pass
6. Update `prd.json` to mark story as `passes: true`
7. Append learnings to `progress.txt`
8. Repeat until all stories pass or max iterations reached

## Key Files

| File | Purpose |
|------|---------|
| `ralph.sh` | The bash loop that spawns fresh Ollama runner instances |
| `ralph_ollama.py` | Python runner that calls Ollama with tool support |
| `tools.py` | Tool definitions and executors (read/write files, git, etc.) |
| `prompt.md` | Instructions given to each model invocation |
| `prd.json` | User stories with `passes` status (the task list) |
| `prd.json.example` | Example PRD format for reference |
| `progress.txt` | Append-only learnings for future iterations |
| `requirements.txt` | Python dependencies |
| `.env` / `.env.example` | Environment configuration (Ollama host, model, etc.) |
| `REMOTE_SETUP.md` | Guide for using Ralph with a remote Ollama server |
| `flowchart/` | Interactive visualization of how Ralph works |

## Flowchart

[![Ralph Flowchart](ralph-flowchart.png)](https://snarktank.github.io/ralph/)

**[View Interactive Flowchart](https://snarktank.github.io/ralph/)** - Click through to see each step with animations.

The `flowchart/` directory contains the source code. To run locally:

```bash
cd flowchart
npm install
npm run dev
```

## Critical Concepts

### Each Iteration = Fresh Context

Each iteration spawns a **new model invocation** with clean context. The only memory between iterations is:
- Git history (commits from previous iterations)
- `progress.txt` (learnings and context)
- `prd.json` (which stories are done)

### Tool-Capable Models Required

Ralph uses Ollama's function calling support to provide tools for file I/O, git operations, and command execution. You need a model that supports tool calling, such as:
- llama3.1 (recommended)
- qwen2.5
- mistral

### Small Tasks

Each PRD item should be small enough to complete in one context window. If a task is too big, the LLM runs out of context before finishing and produces poor code.

Right-sized stories:
- Add a database column and migration
- Add a UI component to an existing page
- Update a server action with new logic
- Add a filter dropdown to a list

Too big (split these):
- "Build the entire dashboard"
- "Add authentication"
- "Refactor the API"

### AGENTS.md Updates Are Critical

After each iteration, Ralph updates the relevant `AGENTS.md` files with learnings. Future iterations automatically reference these files to understand discovered patterns, gotchas, and conventions.

Examples of what to add to AGENTS.md:
- Patterns discovered ("this codebase uses X for Y")
- Gotchas ("do not forget to update Z when changing W")
- Useful context ("the settings panel is in component X")

### Feedback Loops

Ralph only works if there are feedback loops:
- Typecheck catches type errors
- Tests verify behavior
- CI must stay green (broken code compounds across iterations)

### Stop Condition

When all stories have `passes: true`, Ralph outputs `<promise>COMPLETE</promise>` and the loop exits.

## Debugging

Check current state:

```bash
# See which stories are done
cat prd.json | jq '.userStories[] | {id, title, passes}'

# See learnings from previous iterations
cat progress.txt

# Check git history
git log --oneline -10
```

## Customizing prompt.md

Edit `prompt.md` to customize Ralph's behavior for your project:
- Add project-specific quality check commands
- Include codebase conventions
- Add common gotchas for your stack

## Archiving

Ralph automatically archives previous runs when you start a new feature (different `branchName`). Archives are saved to `archive/YYYY-MM-DD-feature-name/`.

## References

- [Geoffrey Huntley's Ralph article](https://ghuntley.com/ralph/)
- [Ollama documentation](https://ollama.ai)
- [Ollama function calling](https://ollama.ai/blog/tool-support)
