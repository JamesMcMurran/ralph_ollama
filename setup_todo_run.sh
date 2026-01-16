#!/bin/bash
# Setup script for running Ralph to build a Docker-based Todo app
# Usage: ./setup_todo_run.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🐳 Setting up Ralph Docker Todo App Run"
echo "========================================"

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "   Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker is available: $(docker --version)"

# Check Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running"
    echo "   Start Docker and try again"
    exit 1
fi

echo "✅ Docker daemon is running"

# 1. Copy the Todo app PRD
echo ""
echo "1. Copying prd_todo_app.json to prd.json..."
cp "$SCRIPT_DIR/prd_todo_app.json" "$SCRIPT_DIR/prd.json"

# 2. Reset progress file
echo "2. Resetting progress.txt..."
cat > "$SCRIPT_DIR/progress.txt" << 'PROGRESS'
# Ralph Progress Log
Started: $(date)
---
## Codebase Patterns
- Docker images are built with docker_build tool
- Test with docker_compose_up then docker_test
- MySQL container name: todoapp-mysql
- PHP container name: todoapp-php  
- Nginx container name: todoapp-nginx
- App runs on http://localhost:8080
---
PROGRESS

# 3. Create todo-app directory structure
echo "3. Creating todo-app directory structure..."
mkdir -p "$SCRIPT_DIR/todo-app/docker/mysql"
mkdir -p "$SCRIPT_DIR/todo-app/docker/php"
mkdir -p "$SCRIPT_DIR/todo-app/docker/nginx"
mkdir -p "$SCRIPT_DIR/todo-app/src"

# 4. Clean up any old containers
echo "4. Cleaning up old Docker containers..."
docker compose -f "$SCRIPT_DIR/todo-app/docker-compose.yml" down -v 2>/dev/null || true
docker rm -f todoapp-mysql todoapp-php todoapp-nginx 2>/dev/null || true

# 5. Initialize git if needed
if [ ! -d "$SCRIPT_DIR/.git" ]; then
    echo "5. Initializing git repository..."
    cd "$SCRIPT_DIR" && git init
else
    echo "5. Git repository already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run Ralph and build the Docker Todo app:"
echo "  ./ralph.sh 10"
echo ""
echo "The app will:"
echo "  - Build custom Docker images for MySQL, PHP-FPM, and Nginx"
echo "  - Create a PHP REST API backend"
echo "  - Create an HTML/CSS/JS frontend"
echo "  - Test everything in Docker-in-Docker"
echo ""
echo "After completion, access the app at: http://localhost:8080"
