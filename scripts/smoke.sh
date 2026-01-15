#!/bin/bash
# Smoke test for Ralph Ollama setup
# Verifies that Ollama is running and the model is available

set -e

OLLAMA_HOST=${OLLAMA_HOST:-http://localhost:11434}
RALPH_MODEL=${RALPH_MODEL:-llama3.1}

echo "🔍 Ralph Ollama Smoke Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check 1: Ollama connectivity
echo "1️⃣  Checking Ollama connectivity ($OLLAMA_HOST)..."
if curl -s -f "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; then
    echo "   ✅ Ollama is reachable"
else
    echo "   ❌ Ollama is not reachable at $OLLAMA_HOST"
    echo ""
    echo "   Ensure Ollama is running:"
    echo "   - Install: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   - Start: ollama serve"
    exit 1
fi
echo ""

# Check 2: Model availability
echo "2️⃣  Checking for model '$RALPH_MODEL'..."
MODELS=$(curl -s "$OLLAMA_HOST/api/tags" | jq -r '.models[]?.name // empty' 2>/dev/null || echo "")

if echo "$MODELS" | grep -q "^$RALPH_MODEL"; then
    echo "   ✅ Model '$RALPH_MODEL' is available"
else
    echo "   ❌ Model '$RALPH_MODEL' not found"
    echo ""
    echo "   Available models:"
    if [ -n "$MODELS" ]; then
        echo "$MODELS" | sed 's/^/   - /'
    else
        echo "   (none)"
    fi
    echo ""
    echo "   Pull the model with:"
    echo "   ollama pull $RALPH_MODEL"
    exit 1
fi
echo ""

# Check 3: Python dependencies
echo "3️⃣  Checking Python dependencies..."
if python3 -c "import openai; from dotenv import load_dotenv" 2>/dev/null; then
    echo "   ✅ Python dependencies installed"
else
    echo "   ❌ Python dependencies missing"
    echo ""
    echo "   Install with:"
    echo "   pip install -r requirements.txt"
    exit 1
fi
echo ""

# Check 4: Tool parser functionality
echo "4️⃣  Testing tool parser..."
TEST_OUTPUT=$(python3 -c "
from tool_parser import detect_tool_calls_in_text
calls = detect_tool_calls_in_text('{\"name\": \"read_file\", \"arguments\": {\"path\": \"test.txt\"}}')
assert len(calls) == 1
assert calls[0]['name'] == 'read_file'
print('OK')
" 2>&1)

if [ "$TEST_OUTPUT" = "OK" ]; then
    echo "   ✅ Tool parser working"
else
    echo "   ❌ Tool parser test failed"
    echo "   Output: $TEST_OUTPUT"
    exit 1
fi
echo ""
echo "3️⃣  Checking Python dependencies..."
if python3 -c "import openai; import dotenv" 2>/dev/null; then
    echo "   ✅ Python dependencies installed"
else
    echo "   ❌ Python dependencies missing"
    echo ""
    echo "   Install with:"
    echo "   pip install -r requirements.txt"
    exit 1
fi
echo ""

# Check 4: Simple chat test
echo "4️⃣  Testing basic chat completion..."
RESPONSE=$(curl -s "$OLLAMA_HOST/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$RALPH_MODEL\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Say 'test' and nothing else\"}],
    \"max_tokens\": 10
  }" 2>&1)

if echo "$RESPONSE" | grep -q '"choices"'; then
    echo "   ✅ Chat completion successful"
else
    echo "   ❌ Chat completion failed"
    echo "   Response: $RESPONSE"
    exit 1
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All checks passed! Ralph is ready to run."
echo ""
echo "Run Ralph with:"
echo "  ./ralph.sh [max_iterations]"
echo ""
