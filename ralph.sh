#!/bin/bash
# Ralph - Autonomous AI agent loop
# Usage: ./ralph.sh [max_iterations]

set -e

MAX_ITERATIONS=${1:-10}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRD_FILE="$SCRIPT_DIR/prd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
LOGS_DIR="$SCRIPT_DIR/logs"

# Activate virtual environment if it exists
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
  source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Create logs directory
mkdir -p "$LOGS_DIR"

# Create log file with timestamp
LOG_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOGS_DIR/ralph_run_${LOG_TIMESTAMP}.log"

# Log function
log() {
  echo "$@" | tee -a "$LOG_FILE"
}

log "Ralph run started at $(date)"
log "Log file: $LOG_FILE"
log "Python: $(which python3)"

log "Starting Ralph - Max iterations: $MAX_ITERATIONS"

for i in $(seq 1 $MAX_ITERATIONS); do
  log ""
  log "═══════════════════════════════════════════════════════"
  log "  Ralph Iteration $i of $MAX_ITERATIONS"
  log "═══════════════════════════════════════════════════════"
  
  # Run ralph_ollama.py
  OUTPUT=$(python3 "$SCRIPT_DIR/ralph_ollama.py" 2>&1 | tee -a "$LOG_FILE") || true
  
  # Check for completion signal
  if echo "$OUTPUT" | grep -qF "RALPH_DONE_ALL_STORIES_COMPLETE"; then
    log ""
    log "🎉 Ralph completed all tasks!"
    log "Completed at iteration $i of $MAX_ITERATIONS"
    exit 0
  fi
  
  log "Iteration $i complete. Continuing..."
  sleep 2
done

log ""
log "⚠️  Ralph reached max iterations ($MAX_ITERATIONS)"
exit 1
