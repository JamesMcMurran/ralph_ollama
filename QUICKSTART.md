# Ralph Ollama - Quick Reference

## Installation

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull a tool-capable model
ollama pull llama3.1

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Verify setup
./scripts/smoke.sh
# or
python3 ralph_ollama.py --health
```

## Running Ralph

```bash
# Run with default settings (10 iterations max)
./ralph.sh

# Run with custom iteration limit
./ralph.sh 25

# Test the runner directly
python3 ralph_ollama.py --model llama3.1
```

## Environment Variables

```bash
# Optional configuration
export RALPH_MODEL=llama3.1              # Model to use
export OLLAMA_HOST=http://localhost:11434  # Ollama host
export RALPH_MAX_TOOL_STEPS=50           # Max tools per iteration

# Or create a .env file (copy from .env.example)
cp .env.example .env
# Edit .env with your preferences
```

## Available Tools (14 total)

### File Operations
- `read_file(path)` - Read file contents
- `write_file(path, content)` - Write/create files
- `list_dir(path)` - List directory contents
- `grep(pattern, path)` - Search files with grep
- `mkdir(path)` - Create directories
- `remove(path)` - Remove files/directories
- `apply_patch(patch)` - Apply unified diffs

### Git Operations
- `git_status()` - Get working tree status
- `git_diff(cached)` - Show changes
- `git_current_branch()` - Get current branch
- `git_checkout(branch)` - Switch branches
- `git_create_branch(branch, from_ref)` - Create new branch
- `git_commit_all(message)` - Stage and commit all

### System
- `run_cmd(command, cwd)` - Execute shell commands (with safety guards)

## PRD Format

See `prd.json.example` for full format. Key structure:

```json
{
  "branchName": "ralph/feature-name",
  "userStories": [
    {
      "id": "US-001",
      "title": "Story title",
      "description": "What to build",
      "acceptanceCriteria": ["Criterion 1", "Criterion 2"],
      "priority": 1,
      "passes": false
    }
  ]
}
```

## Workflow

1. **Create PRD**: Write `prd.json` with user stories
2. **Run Ralph**: `./ralph.sh [iterations]`
3. **Ralph executes**:
   - Creates/checks out branch from `branchName`
   - Picks highest priority story with `passes: false`
   - Uses tools to implement the story
   - Runs tests/quality checks
   - Commits if checks pass
   - Updates `prd.json` to set `passes: true`
   - Logs learnings to `progress.txt`
   - Repeats until all done or max iterations
4. **Completion**: When all stories pass, outputs `<promise>COMPLETE</promise>`

## Key Files

- `ralph.sh` - Main loop
- `ralph_ollama.py` - Python runner
- `tools.py` - Tool implementations
- `prompt.md` - Agent instructions
- `prd.json` - Task list (generated)
- `progress.txt` - Learnings log (generated)

## Debugging

```bash
# Check PRD status
cat prd.json | jq '.userStories[] | {id, title, passes}'

# View progress
cat progress.txt

# Check git history
git log --oneline -10

# Test Ollama connectivity
curl http://localhost:11434/api/tags

# List available models
ollama list
```

## Supported Models

Any Ollama model with tool/function calling support:
- ✅ llama3.1 (recommended)
- ✅ qwen2.5
- ✅ mistral
- ✅ mixtral
- ✅ command-r

## Troubleshooting

### Ollama not reachable
```bash
# Start Ollama
ollama serve

# Or check if it's running
ps aux | grep ollama
```

### Model not found
```bash
# List models
ollama list

# Pull model
ollama pull llama3.1
```

### Python dependencies missing
```bash
pip install -r requirements.txt
```

### Tool execution fails
Check `progress.txt` for error messages and learnings from previous iterations.

## Safety Features

- Maximum tool steps per iteration (prevents infinite loops)
- Command safety guards (blocks dangerous commands like `rm -rf /`)
- Read-only git operations (no force push, etc.)
- File operations restricted to workspace root

## Tips

1. **Keep stories small** - Should complete in one context window
2. **Update AGENTS.md** - Document patterns for future iterations
3. **Run quality checks** - Ensure tests pass before committing
4. **Monitor progress.txt** - Learn from previous iterations
5. **Use meaningful branch names** - `ralph/feature-description`

## References

- [Ollama Documentation](https://ollama.ai)
- [Function Calling Guide](https://ollama.ai/blog/tool-support)
- [Geoffrey Huntley's Ralph Pattern](https://ghuntley.com/ralph/)
