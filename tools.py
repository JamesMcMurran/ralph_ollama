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
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run tests or quality checks for the project",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The test command to run (e.g., 'npm test', 'pytest', 'cargo test')"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_prd",
            "description": "Update a user story in prd.json to mark it as complete",
            "parameters": {
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "The ID of the user story to update (e.g., 'US-001')"
                    },
                    "passes": {
                        "type": "boolean",
                        "description": "Set to true when the story is complete"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the completion"
                    }
                },
                "required": ["story_id", "passes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_progress",
            "description": "Append a progress entry to progress.txt",
            "parameters": {
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "The user story ID"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Summary of what was implemented"
                    },
                    "files_changed": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of files that were changed"
                    },
                    "learnings": {
                        "type": "string",
                        "description": "Any learnings or patterns discovered"
                    }
                },
                "required": ["story_id", "summary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_next_story",
            "description": "Get the next user story to implement from prd.json (highest priority where passes=false)",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_build",
            "description": "Build a Docker image from a Dockerfile",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "The tag for the image (e.g., 'myapp-nginx:latest')"
                    },
                    "context": {
                        "type": "string",
                        "description": "Build context directory (relative to workspace root)"
                    },
                    "dockerfile": {
                        "type": "string",
                        "description": "Path to Dockerfile (relative to context, default: 'Dockerfile')"
                    }
                },
                "required": ["tag", "context"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_compose_up",
            "description": "Start services with docker-compose",
            "parameters": {
                "type": "object",
                "properties": {
                    "compose_file": {
                        "type": "string",
                        "description": "Path to docker-compose.yml (relative to workspace root)"
                    },
                    "detach": {
                        "type": "boolean",
                        "description": "Run in background (default: true)"
                    },
                    "build": {
                        "type": "boolean",
                        "description": "Build images before starting (default: false)"
                    }
                },
                "required": ["compose_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_compose_down",
            "description": "Stop and remove docker-compose services",
            "parameters": {
                "type": "object",
                "properties": {
                    "compose_file": {
                        "type": "string",
                        "description": "Path to docker-compose.yml (relative to workspace root)"
                    },
                    "volumes": {
                        "type": "boolean",
                        "description": "Remove volumes (default: false)"
                    }
                },
                "required": ["compose_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_exec",
            "description": "Execute a command in a running container",
            "parameters": {
                "type": "object",
                "properties": {
                    "container": {
                        "type": "string",
                        "description": "Container name or ID"
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to execute"
                    }
                },
                "required": ["container", "command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_logs",
            "description": "Get logs from a container",
            "parameters": {
                "type": "object",
                "properties": {
                    "container": {
                        "type": "string",
                        "description": "Container name or ID"
                    },
                    "tail": {
                        "type": "integer",
                        "description": "Number of lines to show (default: 100)"
                    }
                },
                "required": ["container"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_ps",
            "description": "List running containers",
            "parameters": {
                "type": "object",
                "properties": {
                    "all": {
                        "type": "boolean",
                        "description": "Show all containers including stopped (default: false)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_test",
            "description": "Run a test command inside the DinD environment against the running containers",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_command": {
                        "type": "string",
                        "description": "Test command to run (e.g., 'curl -s http://localhost:8080')"
                    },
                    "container": {
                        "type": "string",
                        "description": "Optional: run inside specific container, otherwise runs on host"
                    }
                },
                "required": ["test_command"]
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
            elif tool_name == "run_tests":
                return self._run_tests(arguments["command"])
            elif tool_name == "update_prd":
                return self._update_prd(
                    arguments["story_id"],
                    arguments["passes"],
                    arguments.get("notes", "")
                )
            elif tool_name == "append_progress":
                return self._append_progress(
                    arguments["story_id"],
                    arguments["summary"],
                    arguments.get("files_changed", []),
                    arguments.get("learnings", "")
                )
            elif tool_name == "get_next_story":
                return self._get_next_story()
            elif tool_name == "docker_build":
                return self._docker_build(
                    arguments["tag"],
                    arguments["context"],
                    arguments.get("dockerfile", "Dockerfile")
                )
            elif tool_name == "docker_compose_up":
                return self._docker_compose_up(
                    arguments["compose_file"],
                    arguments.get("detach", True),
                    arguments.get("build", False)
                )
            elif tool_name == "docker_compose_down":
                return self._docker_compose_down(
                    arguments["compose_file"],
                    arguments.get("volumes", False)
                )
            elif tool_name == "docker_exec":
                return self._docker_exec(
                    arguments["container"],
                    arguments["command"]
                )
            elif tool_name == "docker_logs":
                return self._docker_logs(
                    arguments["container"],
                    arguments.get("tail", 100)
                )
            elif tool_name == "docker_ps":
                return self._docker_ps(arguments.get("all", False))
            elif tool_name == "docker_test":
                return self._docker_test(
                    arguments["test_command"],
                    arguments.get("container")
                )
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

    def _run_tests(self, command: str) -> str:
        """Run tests or quality checks."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for tests
            )
            
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            
            if result.returncode == 0:
                return f"Tests passed!\n{output}"
            else:
                return f"Tests failed (exit code: {result.returncode})\n{output}"
        except subprocess.TimeoutExpired:
            return "Error: Tests timed out after 300 seconds"

    def _update_prd(self, story_id: str, passes: bool, notes: str = "") -> str:
        """Update a user story in prd.json."""
        prd_path = self.workspace_root / "prd.json"
        
        if not prd_path.exists():
            return "Error: prd.json not found"
        
        try:
            prd = json.loads(prd_path.read_text())
            
            # Find and update the story
            for story in prd.get("userStories", []):
                if story.get("id") == story_id:
                    story["passes"] = passes
                    if notes:
                        story["notes"] = notes
                    
                    # Write back
                    prd_path.write_text(json.dumps(prd, indent=2))
                    return f"Updated {story_id}: passes={passes}"
            
            return f"Error: Story {story_id} not found in prd.json"
        except json.JSONDecodeError:
            return "Error: Invalid JSON in prd.json"

    def _append_progress(self, story_id: str, summary: str, 
                         files_changed: List[str] = None, learnings: str = "") -> str:
        """Append progress entry to progress.txt."""
        from datetime import datetime
        
        progress_path = self.workspace_root / "progress.txt"
        
        entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} - {story_id}\n"
        entry += f"Thread: local\n"
        entry += f"- {summary}\n"
        
        if files_changed:
            entry += f"- Files changed: {', '.join(files_changed)}\n"
        
        if learnings:
            entry += f"**Learnings for future iterations:**\n"
            entry += f"  - {learnings}\n"
        
        entry += "---\n"
        
        try:
            with open(progress_path, "a") as f:
                f.write(entry)
            return f"Appended progress for {story_id}"
        except Exception as e:
            return f"Error appending progress: {str(e)}"

    def _get_next_story(self) -> str:
        """Get the next user story to implement."""
        prd_path = self.workspace_root / "prd.json"
        
        if not prd_path.exists():
            return "Error: prd.json not found"
        
        try:
            prd = json.loads(prd_path.read_text())
            
            # Find stories where passes=false, sorted by priority
            incomplete_stories = [
                s for s in prd.get("userStories", [])
                if not s.get("passes", False)
            ]
            
            if not incomplete_stories:
                return "ALL_STORIES_COMPLETE"
            
            # Sort by priority (lowest number = highest priority)
            incomplete_stories.sort(key=lambda s: s.get("priority", 999))
            
            next_story = incomplete_stories[0]
            
            return json.dumps({
                "id": next_story.get("id"),
                "title": next_story.get("title"),
                "description": next_story.get("description"),
                "acceptanceCriteria": next_story.get("acceptanceCriteria", []),
                "priority": next_story.get("priority"),
                "remaining_stories": len(incomplete_stories) - 1
            }, indent=2)
        except json.JSONDecodeError:
            return "Error: Invalid JSON in prd.json"

    # Docker tools for DinD environment
    def _docker_build(self, tag: str, context: str, dockerfile: str = "Dockerfile") -> str:
        """Build a Docker image."""
        context_path = self.workspace_root / context
        if not context_path.exists():
            return f"Error: Build context not found: {context}"
        
        dockerfile_path = context_path / dockerfile
        if not dockerfile_path.exists():
            return f"Error: Dockerfile not found: {context}/{dockerfile}"
        
        try:
            result = subprocess.run(
                ["docker", "build", "-t", tag, "-f", str(dockerfile_path), str(context_path)],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for builds
            )
            
            if result.returncode == 0:
                return f"Successfully built image: {tag}\n{result.stdout[-500:] if len(result.stdout) > 500 else result.stdout}"
            else:
                return f"Docker build failed:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Docker build timed out after 600 seconds"
        except FileNotFoundError:
            return "Error: Docker not found. Is Docker installed and in PATH?"

    def _docker_compose_up(self, compose_file: str, detach: bool = True, build: bool = False) -> str:
        """Start services with docker-compose."""
        compose_path = self.workspace_root / compose_file
        if not compose_path.exists():
            return f"Error: docker-compose file not found: {compose_file}"
        
        cmd = ["docker", "compose", "-f", str(compose_path), "up"]
        if detach:
            cmd.append("-d")
        if build:
            cmd.append("--build")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            output = result.stdout + result.stderr
            if result.returncode == 0:
                return f"Docker compose up successful\n{output[-1000:] if len(output) > 1000 else output}"
            else:
                return f"Docker compose up failed:\n{output}"
        except subprocess.TimeoutExpired:
            return "Error: Docker compose up timed out"
        except FileNotFoundError:
            return "Error: Docker not found. Is Docker installed?"

    def _docker_compose_down(self, compose_file: str, volumes: bool = False) -> str:
        """Stop docker-compose services."""
        compose_path = self.workspace_root / compose_file
        if not compose_path.exists():
            return f"Error: docker-compose file not found: {compose_file}"
        
        cmd = ["docker", "compose", "-f", str(compose_path), "down"]
        if volumes:
            cmd.append("-v")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return f"Docker compose down successful\n{result.stdout}"
            else:
                return f"Docker compose down failed:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Docker compose down timed out"

    def _docker_exec(self, container: str, command: str) -> str:
        """Execute command in a container."""
        try:
            result = subprocess.run(
                ["docker", "exec", container, "sh", "-c", command],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            
            if result.returncode == 0:
                return output if output else "Command completed successfully"
            else:
                return f"Command failed (exit {result.returncode}):\n{output}"
        except subprocess.TimeoutExpired:
            return "Error: Docker exec timed out"

    def _docker_logs(self, container: str, tail: int = 100) -> str:
        """Get container logs."""
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(tail), container],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            return output if output else "(no logs)"
        except subprocess.TimeoutExpired:
            return "Error: Docker logs timed out"

    def _docker_ps(self, all_containers: bool = False) -> str:
        """List containers."""
        cmd = ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"]
        if all_containers:
            cmd.insert(2, "-a")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.stdout if result.stdout else "No containers running"
        except subprocess.TimeoutExpired:
            return "Error: Docker ps timed out"

    def _docker_test(self, test_command: str, container: str = None) -> str:
        """Run a test command in DinD environment."""
        try:
            if container:
                # Run inside container
                result = subprocess.run(
                    ["docker", "exec", container, "sh", "-c", test_command],
                    cwd=self.workspace_root,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            else:
                # Run on host (for testing network connectivity to containers)
                result = subprocess.run(
                    test_command,
                    shell=True,
                    cwd=self.workspace_root,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            
            if result.returncode == 0:
                return f"TEST PASSED\n{output}"
            else:
                return f"TEST FAILED (exit {result.returncode})\n{output}"
        except subprocess.TimeoutExpired:
            return "Error: Test command timed out"
