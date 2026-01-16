#!/bin/bash
# Ralph Multi-Agent System
# Three agents: Project Manager, Worker, Tester
# Usage: ./ralph_agents.sh [max_iterations]

# Don't use set -e as we use return codes for flow control

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_ITERATIONS=${1:-50}
LOGS_DIR="$SCRIPT_DIR/logs"
STATE_DIR="$SCRIPT_DIR/state"

# Create directories
mkdir -p "$LOGS_DIR" "$STATE_DIR"

# Log file with timestamp
LOG_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOGS_DIR/ralph_run_${LOG_TIMESTAMP}.log"

log() {
    echo "$@" | tee -a "$LOG_FILE"
}

log "═══════════════════════════════════════════════════════════════"
log "  Ralph Multi-Agent System Started"
log "  Time: $(date)"
log "  Max Iterations: $MAX_ITERATIONS"
log "  Log: $LOG_FILE"
log "═══════════════════════════════════════════════════════════════"

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    log "✅ Activated virtual environment"
fi

# Initialize state if not exists
if [ ! -f "$STATE_DIR/current_state.json" ]; then
    echo '{"state": "start", "story_id": null}' > "$STATE_DIR/current_state.json"
    log "✅ Initialized state"
fi

# Copy PRD if needed
if [ ! -f "$SCRIPT_DIR/prd.json" ] && [ -f "$SCRIPT_DIR/prd_todo_app.json" ]; then
    cp "$SCRIPT_DIR/prd_todo_app.json" "$SCRIPT_DIR/prd.json"
    log "✅ Copied PRD"
fi

# Function to run an agent
run_agent() {
    local agent_name=$1
    local prompt_file=$2
    local max_tries=${3:-1}
    
    log ""
    log "───────────────────────────────────────────────────────────────"
    log "  🤖 Running: $agent_name"
    log "───────────────────────────────────────────────────────────────"
    
    for try in $(seq 1 $max_tries); do
        if [ $max_tries -gt 1 ]; then
            log "  Attempt $try of $max_tries"
        fi
        
        # Run the agent
        OUTPUT=$(python3 "$SCRIPT_DIR/ralph_ollama.py" --prompt "$prompt_file" 2>&1) || true
        echo "$OUTPUT" >> "$LOG_FILE"
        
        # Check for agent signals
        if echo "$OUTPUT" | grep -qF "RALPH_DONE_ALL_STORIES_COMPLETE"; then
            log "🎉 All stories complete!"
            return 0
        fi
        
        if echo "$OUTPUT" | grep -qF "PM_WORK_ASSIGNED"; then
            log "  ✓ PM assigned work"
            return 1  # Continue to worker
        fi
        
        if echo "$OUTPUT" | grep -qF "PM_NEXT_STORY"; then
            log "  ✓ PM moving to next story"
            return 1  # Continue loop
        fi
        
        if echo "$OUTPUT" | grep -qF "WORKER_DONE"; then
            log "  ✓ Worker completed task"
            return 2  # Continue to tester
        fi
        
        if echo "$OUTPUT" | grep -qF "WORKER_STUCK"; then
            log "  ⚠ Worker is stuck"
            if [ $try -eq $max_tries ]; then
                return 3  # Back to PM
            fi
            continue
        fi
        
        if echo "$OUTPUT" | grep -qF "TESTER_PASSED"; then
            log "  ✓ Tests passed!"
            return 4  # Back to PM for next story
        fi
        
        if echo "$OUTPUT" | grep -qF "TESTER_FAILED"; then
            log "  ✗ Tests failed"
            return 5  # Back to PM with failure
        fi
        
        # No signal detected - check if agent made progress
        log "  ⚠ No clear signal from $agent_name"
    done
    
    return 99  # Unknown state
}

# Main orchestration loop
iteration=0
while [ $iteration -lt $MAX_ITERATIONS ]; do
    iteration=$((iteration + 1))
    
    log ""
    log "═══════════════════════════════════════════════════════════════"
    log "  Iteration $iteration of $MAX_ITERATIONS"
    log "═══════════════════════════════════════════════════════════════"
    
    # Read current state
    STATE=$(cat "$STATE_DIR/current_state.json" 2>/dev/null || echo '{"state": "start"}')
    CURRENT_STATE=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('state', 'start'))")
    
    log "  Current state: $CURRENT_STATE"
    
    case "$CURRENT_STATE" in
        "start"|"idle"|"tests_passed"|"tests_failed"|"worker_stuck")
            # Project Manager decides what to do
            run_agent "Project Manager" "$SCRIPT_DIR/prompts/pm_prompt.md"
            result=$?
            
            if [ $result -eq 0 ]; then
                log ""
                log "🎉 Ralph completed all stories!"
                log "═══════════════════════════════════════════════════════════════"
                exit 0
            fi
            ;;
            
        "worker_assigned")
            # Worker implements the task (up to 4 tries)
            run_agent "Worker" "$SCRIPT_DIR/prompts/worker_prompt.md" 4
            result=$?
            
            if [ $result -eq 3 ]; then
                # Worker stuck after 4 tries, PM will see worker_stuck state
                log "  Worker exhausted attempts, escalating to PM"
            fi
            ;;
            
        "ready_for_test")
            # Tester verifies the work
            run_agent "Tester" "$SCRIPT_DIR/prompts/tester_prompt.md"
            ;;
            
        *)
            log "  Unknown state: $CURRENT_STATE, resetting to start"
            echo '{"state": "start", "story_id": null}' > "$STATE_DIR/current_state.json"
            ;;
    esac
    
    sleep 2
done

log ""
log "⚠️  Reached max iterations ($MAX_ITERATIONS)"
log "Check state: $STATE_DIR/current_state.json"
log "Check logs: $LOG_FILE"
exit 1
