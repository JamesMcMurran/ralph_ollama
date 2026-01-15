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
- `prompt.md` - Instructions given to each model invocation
- `prd.json.example` - Example PRD format
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `flowchart/` - Interactive React Flow diagram explaining how Ralph works

## Setup

1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Pull a tool-capable model: `ollama pull llama3.1`
3. Install Python deps: `pip install -r requirements.txt`
4. Optionally set env vars: `export RALPH_MODEL=llama3.1`

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
