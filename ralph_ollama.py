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


def load_prompt(script_dir: Path) -> str:
    """Load the prompt.md file."""
    prompt_path = script_dir / "prompt.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"prompt.md not found at {prompt_path}")
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
    
    args = parser.parse_args()
    
    # Run health check if requested
    if args.health:
        return health_check(args.host, args.model)
    
    # Get script directory (workspace root)
    script_dir = Path(__file__).parent.resolve()
    
    # Load prompt
    try:
        system_prompt = load_prompt(script_dir)
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
    
    # Tool calling loop
    step_count = 0
    
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
            
            # Add assistant message to conversation
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in (message.tool_calls or [])
                ]
            })
            
            # If no tool calls, we're done
            if not message.tool_calls:
                # Print final assistant message
                if message.content:
                    print(message.content)
                break
            
            # Execute tool calls
            print(f"\n[Step {step_count + 1}] Executing {len(message.tool_calls)} tool call(s)...", file=sys.stderr)
            
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"  → {tool_name}({json.dumps(arguments, indent=2)})", file=sys.stderr)
                
                # Execute the tool
                result = tool_executor.execute(tool_name, arguments)
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
                
                # Print abbreviated result
                result_preview = result[:200] + "..." if len(result) > 200 else result
                print(f"     Result: {result_preview}", file=sys.stderr)
            
            step_count += 1
            
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
