#!/usr/bin/env python3
"""
Ralph Ollama Runner - Autonomous AI agent loop using Ollama models.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed.", file=sys.stderr)
    print("Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

from tools import TOOL_SCHEMAS, ToolExecutor
from tool_parser import extract_tool_calls, deduplicate_tool_calls, has_progress_markers


def load_prompt(script_dir: Path, prompt_file: str = None) -> str:
    """Load the prompt file."""
    if prompt_file:
        prompt_path = Path(prompt_file)
        if not prompt_path.is_absolute():
            prompt_path = script_dir / prompt_file
    else:
        prompt_path = script_dir / "prompt.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found at {prompt_path}")
    return prompt_path.read_text()


def health_check(host: str, model: str) -> int:
    """Run health check to verify Ollama setup."""
    print("🔍 Ralph Ollama Health Check")
    print("━" * 60)
    print()
    
    # Check 1: Ollama connectivity
    print(f"1️⃣  Checking Ollama connectivity ({host})...")
    try:
        import requests
        response = requests.get(f"{host}/api/tags", timeout=5)
        if response.status_code == 200:
            print("   ✅ Ollama is reachable")
        else:
            print(f"   ❌ Ollama returned status {response.status_code}")
            return 1
    except Exception as e:
        print(f"   ❌ Cannot reach Ollama: {e}")
        print()
        print("   Ensure Ollama is running:")
        print("   - Install: curl -fsSL https://ollama.ai/install.sh | sh")
        print("   - Start: ollama serve")
        return 1
    print()
    
    # Check 2: Model availability
    print(f"2️⃣  Checking for model '{model}'...")
    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        
        if model in models or any(m.startswith(model) for m in models):
            print(f"   ✅ Model '{model}' is available")
        else:
            print(f"   ❌ Model '{model}' not found")
            print()
            print("   Available models:")
            for m in models:
                print(f"   - {m}")
            print()
            print(f"   Pull the model with:")
            print(f"   ollama pull {model}")
            return 1
    except Exception as e:
        print(f"   ❌ Error checking models: {e}")
        return 1
    print()
    
    # Check 3: Simple chat test
    print("3️⃣  Testing basic chat completion...")
    try:
        client = OpenAI(base_url=f"{host}/v1", api_key="ollama")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'test' and nothing else"}],
            max_tokens=10
        )
        if response.choices:
            print("   ✅ Chat completion successful")
        else:
            print("   ❌ No response from model")
            return 1
    except Exception as e:
        print(f"   ❌ Chat completion failed: {e}")
        return 1
    print()
    
    print("━" * 60)
    print("✅ All checks passed! Ralph is ready to run.")
    print()
    print("Run Ralph with:")
    print("  ./ralph.sh [max_iterations]")
    print()
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Ralph Ollama Runner - Execute PRD tasks using Ollama models"
    )
    
    parser.add_argument(
        "--model",
        default=os.getenv("RALPH_MODEL", "llama3.1"),
        help="Ollama model to use (default: llama3.1 or RALPH_MODEL env var)"
    )
    
    parser.add_argument(
        "--host",
        default=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        help="Ollama host URL (default: http://localhost:11434 or OLLAMA_HOST env var)"
    )
    
    parser.add_argument(
        "--max-steps",
        type=int,
        default=int(os.getenv("RALPH_MAX_TOOL_STEPS", "50")),
        help="Maximum tool steps per iteration (default: 50 or RALPH_MAX_TOOL_STEPS env var)"
    )
    
    parser.add_argument(
        "--health",
        action="store_true",
        help="Run health check and exit"
    )
    
    parser.add_argument(
        "--prompt",
        default=None,
        help="Path to prompt file (default: prompt.md in script directory)"
    )
    
    args = parser.parse_args()
    
    # Run health check if requested
    if args.health:
        return health_check(args.host, args.model)
    
    # Get script directory (workspace root)
    script_dir = Path(__file__).parent.resolve()
    
    # Load prompt
    try:
        system_prompt = load_prompt(script_dir, args.prompt)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Initialize tool executor
    tool_executor = ToolExecutor(script_dir)
    
    # Initialize OpenAI client with Ollama base URL
    client = OpenAI(
        base_url=f"{args.host}/v1",
        api_key="ollama"  # Ollama doesn't require a real API key
    )
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Begin. Follow the system instructions."}
    ]
    
    # Tool calling loop with deduplication
    step_count = 0
    recent_tool_calls = []  # Track recent calls to prevent loops
    
    while step_count < args.max_steps:
        # Make the API call with tools
        try:
            response = client.chat.completions.create(
                model=args.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                temperature=0.7
            )
            
            message = response.choices[0].message
            response_text = message.content or ""
            
            # Extract tool calls (handles both structured and text-embedded)
            tool_calls, reasoning_text = extract_tool_calls(message, response_text)
            
            # Print reasoning if present
            if reasoning_text and reasoning_text.strip():
                print(f"\n💭 {reasoning_text}", file=sys.stderr)
            
            # Deduplicate tool calls against recent history
            if tool_calls:
                original_count = len(tool_calls)
                tool_calls = deduplicate_tool_calls(tool_calls, recent_tool_calls[-3:])
                
                if len(tool_calls) < original_count:
                    print(f"\n⚠️  Filtered {original_count - len(tool_calls)} duplicate tool call(s)", file=sys.stderr)
            
            # If no tool calls, we're done
            if not tool_calls:
                # Check if we're stuck asking for the same thing
                if not has_progress_markers(messages):
                    print("\n⚠️  No tool calls and no recent progress detected", file=sys.stderr)
                
                # Print final assistant message
                if response_text:
                    print(response_text)
                break
            
            # Execute tool calls
            print(f"\n[Step {step_count + 1}] Executing {len(tool_calls)} tool call(s)...", file=sys.stderr)
            
            # Build assistant message with tool calls for conversation history
            assistant_msg = {
                "role": "assistant",
                "content": reasoning_text
            }
            
            # Add tool_calls if using structured format
            if hasattr(message, 'tool_calls') and message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            messages.append(assistant_msg)
            
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                arguments = tool_call["arguments"]
                tool_id = tool_call.get("id", f"call_{step_count}")
                
                print(f"  → {tool_name}({json.dumps(arguments, indent=2)})", file=sys.stderr)
                
                # Execute the tool
                result = tool_executor.execute(tool_name, arguments)
                
                # Track this call to prevent duplicates
                recent_tool_calls.append((tool_name, arguments))
                
                # Add tool result to messages (visible to model)
                tool_result_msg = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": f"TOOL RESULT ({tool_name}):\n{result}"
                }
                messages.append(tool_result_msg)
                
                # Print abbreviated result
                result_preview = result[:200] + "..." if len(result) > 200 else result
                print(f"     ✓ {result_preview}", file=sys.stderr)
            
            step_count += 1
            
            # Keep only recent call history (prevent unbounded growth)
            if len(recent_tool_calls) > 10:
                recent_tool_calls = recent_tool_calls[-10:]
            
        except Exception as e:
            print(f"\nError during execution: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
    
    if step_count >= args.max_steps:
        print(f"\n⚠ Warning: Reached maximum tool steps ({args.max_steps})", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
