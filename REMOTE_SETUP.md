# Remote Ollama Setup Guide

This guide shows you how to use Ralph with a remote Ollama server instead of running Ollama locally.

## Why Use a Remote Ollama Server?

- Run Ralph from a lightweight machine (laptop, tablet, etc.)
- Use a powerful GPU server for model inference
- Share Ollama resources across multiple projects/users
- Separate concerns: development machine vs inference machine

## Prerequisites

- A remote server with Ollama installed
- Network access to the remote server
- The `openai` Python package installed locally (`pip install -r requirements.txt`)

## Option 1: Environment Variables

Export the `OLLAMA_HOST` environment variable before running Ralph:

```bash
export OLLAMA_HOST=http://your-server-ip:11434
./ralph.sh
```

## Option 2: .env File (Recommended)

Create or edit the `.env` file in the Ralph directory:

```bash
# .env
RALPH_MODEL=llama3.1
OLLAMA_HOST=http://192.168.1.100:11434
RALPH_MAX_TOOL_STEPS=50
```

Then run Ralph normally:

```bash
./ralph.sh
```

## Option 3: Command Line Arguments

Pass the host directly to the Python script:

```bash
python3 ralph_ollama.py --host http://your-server:11434 --model llama3.1
```

## Remote Server Setup

### 1. Install Ollama on the remote server

```bash
# On your remote server
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Configure Ollama to accept remote connections

By default, Ollama only listens on localhost. To accept remote connections:

**Option A: Environment variable (recommended)**

```bash
# On the remote server
export OLLAMA_HOST=0.0.0.0:11434
ollama serve
```

**Option B: Systemd service (persistent)**

Edit the Ollama systemd service:

```bash
sudo systemctl edit ollama
```

Add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Restart the service:

```bash
sudo systemctl restart ollama
```

### 3. Pull the required model

```bash
# On the remote server
ollama pull llama3.1
```

### 4. Verify the server is accessible

From your local machine:

```bash
curl http://your-server-ip:11434/api/tags
```

You should see a JSON response with available models.

## Security Considerations

⚠️ **Important**: By default, Ollama has no authentication. When exposing it to the network:

### Option 1: Firewall Rules

Only allow connections from specific IPs:

```bash
# On the remote server (example for ufw)
sudo ufw allow from 192.168.1.0/24 to any port 11434
```

### Option 2: SSH Tunnel (Most Secure)

Instead of exposing Ollama directly, use an SSH tunnel:

```bash
# On your local machine
ssh -L 11434:localhost:11434 user@your-server

# Then use localhost in Ralph
export OLLAMA_HOST=http://localhost:11434
./ralph.sh
```

This keeps Ollama listening only on localhost while securely forwarding traffic.

### Option 3: Reverse Proxy with Authentication

Use nginx or caddy with basic auth:

```nginx
# nginx example
server {
    listen 11434 ssl;
    server_name ollama.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        auth_basic "Ollama Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://localhost:11434;
    }
}
```

## Verification

After setup, verify the connection:

```bash
# From your local machine
python3 ralph_ollama.py --host http://your-server:11434 --health
```

You should see:

```
🔍 Ralph Ollama Health Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  Checking Ollama connectivity (http://your-server:11434)...
   ✅ Ollama is reachable

2️⃣  Checking for model 'llama3.1'...
   ✅ Model 'llama3.1' is available

3️⃣  Testing basic chat completion...
   ✅ Chat completion successful

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All checks passed! Ralph is ready to run.
```

## Troubleshooting

### Error: "Cannot reach Ollama"

- Verify Ollama is running: `systemctl status ollama` (on server)
- Check firewall rules
- Verify the port is correct (default: 11434)
- Try `curl http://your-server:11434/api/tags` from your local machine

### Error: "Model not found"

- Pull the model on the remote server: `ollama pull llama3.1`
- Verify with: `ollama list`

### Error: "Connection refused"

- Ensure Ollama is listening on `0.0.0.0`, not just `127.0.0.1`
- Check `OLLAMA_HOST` environment variable on the server

### Error: "openai package not installed"

- Install dependencies: `pip install -r requirements.txt`
- Verify: `pip list | grep openai`

## Performance Considerations

- Network latency affects response time
- Large context windows may be slower over network
- Consider using SSH tunnel compression: `ssh -C -L ...`
- Use a model size appropriate for your GPU (7B, 13B, 70B, etc.)

## Example: Complete Workflow

```bash
# 1. On remote server
ssh user@gpu-server
curl -fsSL https://ollama.ai/install.sh | sh
export OLLAMA_HOST=0.0.0.0:11434
ollama serve &
ollama pull llama3.1

# 2. On local machine
cd /path/to/your/project
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
RALPH_MODEL=llama3.1
OLLAMA_HOST=http://gpu-server:11434
RALPH_MAX_TOOL_STEPS=50
EOF

# Verify connectivity
python3 ralph_ollama.py --health

# Run Ralph
./ralph.sh 10
```

## Tips

- Use environment-specific `.env` files (`.env.local`, `.env.production`)
- Keep `.env` files in `.gitignore` to avoid committing credentials
- Document your remote setup in your project's README
- Monitor GPU usage on the remote server during runs
- Consider using tmux/screen on the remote server to keep Ollama running
