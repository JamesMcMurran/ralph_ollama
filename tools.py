"""
Tool definitions and executors for Ralph Ollama Runner.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List


# Tool schemas compatible with OpenAI function calling format
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file at the specified path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to read (relative to workspace root)"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List contents of a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to list (relative to workspace root, or '.' for current)"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search for a pattern in files using grep",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The search pattern (supports regex)"
                    },
                    "path": {
                        "type": "string",
                        "description": "The file or directory path to search in"
                    }
                },
                "required": ["pattern", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Get the current git status",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Get the git diff of current changes",
            "parameters": {
                "type": "object",
                "properties": {
                    "cached": {
                        "type": "boolean",
                        "description": "Show staged changes (--cached)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file (creates or overwrites)",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to write to (relative to workspace root)"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_patch",
            "description": "Apply a unified diff patch using git apply",
            "parameters": {
                "type": "object",
                "properties": {
                    "patch": {
                        "type": "string",
                        "description": "The unified diff patch to apply"
                    }
                },
                "required": ["patch"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_cmd",
            "description": "Run a shell command (use with caution)",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to run"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (relative to workspace root, default: '.')"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mkdir",
            "description": "Create a directory (including parent directories)",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to create"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove",
            "description": "Remove a file or directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file or directory path to remove"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_checkout",
            "description": "Checkout a git branch",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": "The branch name to checkout"
                    }
                },
                "required": ["branch"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_create_branch",
            "description": "Create and checkout a new git branch",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": "The new branch name"
                    },
                    "from_ref": {
                        "type": "string",
                        "description": "The ref to branch from (default: main)"
                    }
                },
                "required": ["branch"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit_all",
            "description": "Stage all changes and commit with a message",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The commit message"
                    }
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_current_branch",
            "description": "Get the current git branch name",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


class ToolExecutor:
    """Executes tool calls and returns results."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
    
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result as a string."""
        try:
            if tool_name == "read_file":
                return self._read_file(arguments["path"])
            elif tool_name == "list_dir":
                return self._list_dir(arguments["path"])
            elif tool_name == "grep":
                return self._grep(arguments["pattern"], arguments["path"])
            elif tool_name == "git_status":
                return self._git_status()
            elif tool_name == "git_diff":
                return self._git_diff(arguments.get("cached", False))
            elif tool_name == "write_file":
                return self._write_file(arguments["path"], arguments["content"])
            elif tool_name == "apply_patch":
                return self._apply_patch(arguments["patch"])
            elif tool_name == "run_cmd":
                return self._run_cmd(arguments["command"], arguments.get("cwd", "."))
            elif tool_name == "mkdir":
                return self._mkdir(arguments["path"])
            elif tool_name == "remove":
                return self._remove(arguments["path"])
            elif tool_name == "git_checkout":
                return self._git_checkout(arguments["branch"])
            elif tool_name == "git_create_branch":
                return self._git_create_branch(arguments["branch"], arguments.get("from_ref", "main"))
            elif tool_name == "git_commit_all":
                return self._git_commit_all(arguments["message"])
            elif tool_name == "git_current_branch":
                return self._git_current_branch()
            else:
                return f"Error: Unknown tool '{tool_name}'"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def _read_file(self, path: str) -> str:
        """Read a file's contents."""
        file_path = self.workspace_root / path
        if not file_path.exists():
            return f"Error: File not found: {path}"
        if not file_path.is_file():
            return f"Error: Not a file: {path}"
        try:
            return file_path.read_text()
        except UnicodeDecodeError:
            return f"Error: Cannot read binary file: {path}"
    
    def _list_dir(self, path: str) -> str:
        """List directory contents."""
        dir_path = self.workspace_root / path
        if not dir_path.exists():
            return f"Error: Directory not found: {path}"
        if not dir_path.is_dir():
            return f"Error: Not a directory: {path}"
        
        items = []
        for item in sorted(dir_path.iterdir()):
            if item.is_dir():
                items.append(f"{item.name}/")
            else:
                items.append(item.name)
        
        return "\n".join(items) if items else "(empty directory)"
    
    def _grep(self, pattern: str, path: str) -> str:
        """Search for pattern in files."""
        search_path = self.workspace_root / path
        if not search_path.exists():
            return f"Error: Path not found: {path}"
        
        try:
            result = subprocess.run(
                ["grep", "-r", "-n", pattern, str(search_path)],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout
            elif result.returncode == 1:
                return f"No matches found for pattern: {pattern}"
            else:
                return f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Search timed out"
    
    def _git_status(self) -> str:
        """Get git status."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.workspace_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        if not result.stdout.strip():
            return "Working tree clean"
        
        return result.stdout
    
    def _git_diff(self, cached: bool = False) -> str:
        """Get git diff."""
        cmd = ["git", "diff"]
        if cached:
            cmd.append("--cached")
        
        result = subprocess.run(
            cmd,
            cwd=self.workspace_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        if not result.stdout.strip():
            return "No changes" if not cached else "No staged changes"
        
        return result.stdout
    
    def _write_file(self, path: str, content: str) -> str:
        """Write content to a file."""
        file_path = self.workspace_root / path
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            file_path.write_text(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    def _apply_patch(self, patch: str) -> str:
        """Apply a unified diff patch."""
        try:
            result = subprocess.run(
                ["git", "apply"],
                input=patch,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return "Patch applied successfully"
            else:
                return f"Error applying patch: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Patch application timed out"
    
    def _run_cmd(self, command: str, cwd: str = ".") -> str:
        """Run a shell command with safety guardrails."""
        # Safety: Block obviously dangerous commands
        dangerous_patterns = ["rm -rf /", "dd if=", "mkfs", "> /dev/"]
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return f"Error: Command blocked for safety: {pattern}"
        
        work_dir = self.workspace_root / cwd
        if not work_dir.exists():
            return f"Error: Directory not found: {cwd}"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            
            if result.returncode != 0:
                output = f"Command exited with code {result.returncode}\n{output}"
            
            return output if output else f"Command completed (exit code: {result.returncode})"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 60 seconds"
    
    def _mkdir(self, path: str) -> str:
        """Create a directory."""
        dir_path = self.workspace_root / path
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return f"Created directory: {path}"
        except Exception as e:
            return f"Error creating directory: {str(e)}"
    
    def _remove(self, path: str) -> str:
        """Remove a file or directory."""
        target_path = self.workspace_root / path
        
        if not target_path.exists():
            return f"Error: Path does not exist: {path}"
        
        try:
            if target_path.is_file():
                target_path.unlink()
                return f"Removed file: {path}"
            elif target_path.is_dir():
                import shutil
                shutil.rmtree(target_path)
                return f"Removed directory: {path}"
        except Exception as e:
            return f"Error removing path: {str(e)}"
    
    def _git_checkout(self, branch: str) -> str:
        """Checkout a git branch."""
        result = subprocess.run(
            ["git", "checkout", branch],
            cwd=self.workspace_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return f"Checked out branch: {branch}"
        else:
            return f"Error checking out branch: {result.stderr}"
    
    def _git_create_branch(self, branch: str, from_ref: str = "main") -> str:
        """Create and checkout a new git branch."""
        # First ensure we're on the from_ref
        result = subprocess.run(
            ["git", "checkout", from_ref],
            cwd=self.workspace_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return f"Error checking out {from_ref}: {result.stderr}"
        
        # Create and checkout new branch
        result = subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=self.workspace_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return f"Created and checked out new branch: {branch} (from {from_ref})"
        else:
            return f"Error creating branch: {result.stderr}"
    
    def _git_commit_all(self, message: str) -> str:
        """Stage all changes and commit."""
        # Stage all changes
        result = subprocess.run(
            ["git", "add", "-A"],
            cwd=self.workspace_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return f"Error staging changes: {result.stderr}"
        
        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.workspace_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return f"Committed: {message}"
        else:
            # Check if there were no changes to commit
            if "nothing to commit" in result.stdout.lower():
                return "No changes to commit"
            return f"Error committing: {result.stderr}"
    
    def _git_current_branch(self) -> str:
        """Get the current git branch."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.workspace_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error getting current branch: {result.stderr}"
