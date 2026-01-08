# Local Server Setup Guide

## 🚀 Quick Start

### 1. Navigate to Project Directory

```bash
cd /Users/rkguptayotta.com/Desktop/codes/api_approach/claude_v2_event_api
```

### 2. Activate Virtual Environment

```bash
source event_api/bin/activate
```

### 3. Install Dependencies (First Time Only)

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

**Option A: Export in terminal** (temporary, for current session)
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
export OPENAI_API_KEY=sk-...
```

**Option B: Use .env file** (recommended, already configured)
Your `.env` file already contains:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Just add your OpenAI key if needed:
```
OPENAI_API_KEY=sk-...
```

### 5. Start the Server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Options explained:**
- `--host 0.0.0.0` - Makes server accessible from other devices on your network
- `--port 8000` - Server runs on port 8000
- `--reload` - Auto-restart on code changes (useful during development)

---

## ✅ Server is Running!

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 Starting AI Project Generator API...
✅ API key configured
✅ API ready at http://localhost:8000
📚 Docs at http://localhost:8000/docs
```

---

## 🌐 Access URLs

### From Your Machine:
```
http://localhost:8000
http://localhost:8000/docs  (Interactive API documentation)
```

### From Other Devices (same network):

First, find your local IP address:

**macOS/Linux:**
```bash
# Method 1
ifconfig | grep "inet " | grep -v 127.0.0.1

# Method 2 (macOS)
ipconfig getifaddr en0

# Method 3 (Linux)
hostname -I
```

**Windows:**
```bash
ipconfig
# Look for "IPv4 Address" under your active network adapter
```

Then share with your team:
```
http://YOUR_LOCAL_IP:8000
http://YOUR_LOCAL_IP:8000/docs
```

Example: `http://192.168.1.100:8000`

---

## 🧪 Test the API

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-08T..."
}
```

### Test 2: List Supported Models
```bash
curl http://localhost:8000/api/models
```

### Test 3: Generate a Project
```bash
curl -N 'http://localhost:8000/api/stream?prompt=Create+a+test+website&event_type=generate&model_family=Anthropic&model_name=claude-opus-4-5-20251101'
```

You should see SSE events streaming in real-time!

---

## 📦 For Your Team

### Share These Files:
1. **UNIFIED_API_DOCS.md** - Complete API documentation
2. **POSTMAN_TEST_PAYLOADS.md** - Ready-to-use Postman examples
3. **SYSTEM_PROMPTS.md** - All system prompts used by AI

### Share This URL:
```
http://YOUR_LOCAL_IP:8000
```

### Share API Docs URL:
```
http://YOUR_LOCAL_IP:8000/docs
```

---

## 🔧 Troubleshooting

### Port Already in Use?

**Error:**
```
ERROR: Address already in use
```

**Solution 1: Use a different port**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

**Solution 2: Kill process using port 8000**
```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9

# Or find and kill manually
lsof -i :8000
kill -9 <PID>
```

---

### Can't Access from Other Devices?

**Check:**
1. Firewall settings - allow port 8000
2. Make sure you're on the same network
3. Use correct local IP (not 127.0.0.1 or localhost)

**macOS Firewall:**
```bash
System Preferences → Security & Privacy → Firewall → Firewall Options
→ Add Python/uvicorn → Allow incoming connections
```

---

### API Key Not Working?

**Check .env file:**
```bash
cat .env
```

Should show:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
```

**Verify keys are loaded:**
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Anthropic:', 'Yes' if os.getenv('ANTHROPIC_API_KEY') else 'No'); print('OpenAI:', 'Yes' if os.getenv('OPENAI_API_KEY') else 'No')"
```

---

## 🛑 Stop the Server

Press `CTRL + C` in the terminal where server is running.

---

## 🔄 Restart the Server

Just run again:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📝 Useful Commands

### Check if server is running:
```bash
curl http://localhost:8000/health
```

### View server logs:
Server logs appear directly in the terminal where you started it.

### Test different endpoints:
```bash
# Health
curl http://localhost:8000/health

# Models
curl http://localhost:8000/api/models

# Projects list
curl http://localhost:8000/api/projects

# Interactive docs
open http://localhost:8000/docs  # macOS
xdg-open http://localhost:8000/docs  # Linux
```

---

## 🎯 Production Tips (Optional)

If you want to run this more permanently:

### 1. Run in Background
```bash
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

### 2. Check if Running
```bash
ps aux | grep uvicorn
```

### 3. Stop Background Server
```bash
pkill -f uvicorn
```

### 4. Use Screen/Tmux (Recommended)

**With screen:**
```bash
screen -S api_server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
# Press Ctrl+A then D to detach
# screen -r api_server to reattach
```

**With tmux:**
```bash
tmux new -s api_server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
# Press Ctrl+B then D to detach
# tmux attach -t api_server to reattach
```

---

## 🔐 Security Notes

1. **Local Network Only**: Current setup is safe for local network use
2. **Don't Expose to Internet**: Without proper security (HTTPS, auth, rate limiting)
3. **API Keys**: Never commit `.env` file to git (already in `.gitignore`)

---

## ✅ Summary

**Start Server:**
```bash
cd /Users/rkguptayotta.com/Desktop/codes/api_approach/claude_v2_event_api
source event_api/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Access:**
- Local: `http://localhost:8000`
- Network: `http://YOUR_LOCAL_IP:8000`
- Docs: `http://localhost:8000/docs`

**Test:**
```bash
curl http://localhost:8000/health
```

**Stop:**
`CTRL + C`

---

**That's it! Your API is ready to use!** 🎉


