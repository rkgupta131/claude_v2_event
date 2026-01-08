# AI Project Generator - Unified API

A powerful API for generating and modifying web projects using multiple AI providers (Anthropic Claude, OpenAI GPT) with real-time Server-Sent Events (SSE) streaming.

---

## 🎯 Features

- ✅ **Single Unified Endpoint** - `/api/stream` for all operations
- ✅ **Multiple AI Providers** - Anthropic (Claude), OpenAI (GPT)
- ✅ **Dynamic Model Selection** - Choose any model at runtime
- ✅ **Real-Time Streaming** - SSE events for live progress updates
- ✅ **Generate & Modify** - Create new projects or modify existing ones
- ✅ **GET & POST Support** - Flexible request methods

---

## 🚀 Quick Start

### 1. Start the Server

```bash
cd /Users/rkguptayotta.com/Desktop/codes/api_approach/claude_v2_event_api
source event_api/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access the API

- **Local**: `http://localhost:8000`
- **Network**: `http://YOUR_LOCAL_IP:8000`
- **API Docs**: `http://localhost:8000/docs`

### 3. Test

```bash
curl http://localhost:8000/health
```

---

## 📡 Usage Example

### Generate a Project with OpenAI GPT

```javascript
const url = 'http://localhost:8000/api/stream?' + new URLSearchParams({
    prompt: 'Create a coffee shop landing page',
    event_type: 'generate',
    model_family: 'OpenAI',
    model_name: 'gpt-4',
    business_name: 'Bean Dreams'
});

const eventSource = new EventSource(url);

eventSource.onmessage = (e) => {
    const event = JSON.parse(e.data);
    console.log(event.event_type, event.payload);
    
    if (event.event_type === 'project.saved') {
        console.log('✅ Project ID:', event.payload.project_id);
        console.log('🤖 Model used:', event.payload.model_used);
    }
};
```

---

## 🤖 Supported AI Models

### Anthropic (Claude)
- `claude-opus-4-5-20251101`
- `claude-sonnet-4-20250514`
- `claude-3-5-sonnet-20241022`

**Environment Variable:**
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

### OpenAI (GPT)
- `gpt-4`
- `gpt-5.2` (when available)
- `gpt-3.5-turbo`

**Environment Variable:**
```bash
export OPENAI_API_KEY=sk-...
```

---

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stream` | GET, POST | Unified endpoint for generate/modify |
| `/api/models` | GET | List supported AI providers and models |
| `/api/projects` | GET | List all generated projects |
| `/api/projects/{id}` | GET | Get specific project details |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API documentation |

---

## 🔑 Request Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `prompt` | ✅ Yes | What to create/modify | `"Create a website"` |
| `model_family` | ✅ Yes | AI provider | `"OpenAI"`, `"Anthropic"` |
| `model_name` | ✅ Yes | Specific model | `"gpt-4"`, `"claude-opus-4-5-20251101"` |
| `event_type` | No | Operation type | `"generate"` or `"modify"` |
| `project_id` | No | Project to modify | `"project_v1_..."` |

---

## 📚 Documentation

| File | Description |
|------|-------------|
| **LOCAL_SERVER_SETUP.md** | Complete local server setup guide |
| **UNIFIED_API_DOCS.md** | Full API reference with examples |
| **POSTMAN_TEST_PAYLOADS.md** | Ready-to-use Postman test cases |
| **SYSTEM_PROMPTS.md** | All AI system prompts used |
| **IMPLEMENTATION_SUMMARY.md** | Technical implementation details |

---

## 🧪 Quick Test with cURL

```bash
# Health check
curl http://localhost:8000/health

# List models
curl http://localhost:8000/api/models

# Generate project with Claude
curl -N 'http://localhost:8000/api/stream?prompt=Create+a+bakery+website&event_type=generate&model_family=Anthropic&model_name=claude-opus-4-5-20251101'

# Generate project with OpenAI (POST)
curl -X POST http://localhost:8000/api/stream \
  -H "Content-Type: application/json" \
  -N \
  -d '{
    "prompt": "Create a portfolio website",
    "event_type": "generate",
    "model_family": "OpenAI",
    "model_name": "gpt-4"
  }'
```

---

## 🌐 Network Access

To access from other devices on your network:

### Find Your Local IP:

**macOS/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Or:**
```bash
ipconfig getifaddr en0  # macOS
hostname -I             # Linux
```

### Share with Team:
```
http://YOUR_LOCAL_IP:8000
http://YOUR_LOCAL_IP:8000/docs
```

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- Virtual environment activated

### Setup

```bash
# Navigate to project
cd /Users/rkguptayotta.com/Desktop/codes/api_approach/claude_v2_event_api

# Activate virtual environment
source event_api/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (already in .env)
export ANTHROPIC_API_KEY=sk-ant-api03-...
export OPENAI_API_KEY=sk-...

# Start server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔧 Configuration

Environment variables (in `.env` file):

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
```

---

## 📊 SSE Event Types

The API streams these events in real-time:

- `thinking.start` / `thinking.end` - AI processing status
- `progress.init` / `progress.update` - Build progress
- `chat.message` - Status messages
- `fs.create` / `fs.write` - File operations
- `edit.start` / `edit.end` - File editing
- `project.saved` - Project saved successfully
- `stream.complete` - Generation complete
- `error` - Error occurred

---

## 🛠️ Project Structure

```
claude_v2_event_api/
├── api/
│   ├── main.py              # FastAPI application
│   ├── schemas.py           # Request/response models
│   └── routes/
│       ├── unified.py       # Unified streaming endpoint
│       ├── generate.py      # Legacy generation endpoints
│       ├── projects.py      # Project management
│       └── chat.py          # Chat & classification
├── models/
│   ├── model_router.py      # AI provider routing
│   ├── gemini_client_qa.py  # Anthropic Claude client
│   └── openai_client.py     # OpenAI GPT client
├── events/
│   └── stream_events.py     # SSE event system
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in git)
└── *.md                     # Documentation files
```

---

## 🎉 Example Response

When you generate a project, you'll receive SSE events like:

```javascript
// Event 1
{
  "event_type": "thinking.start",
  "payload": {}
}

// Event 2
{
  "event_type": "chat.message",
  "payload": {
    "content": "🧠 Using OpenAI gpt-4 to generate your project..."
  }
}

// Event 3
{
  "event_type": "fs.write",
  "payload": {
    "path": "src/App.tsx",
    "language": "typescript"
  }
}

// Event 4
{
  "event_type": "project.saved",
  "payload": {
    "project_id": "project_v1_20250108_152030",
    "model_used": "OpenAI/gpt-4",
    "files": ["index.html", "src/main.tsx", "src/App.tsx", "src/index.css"]
  }
}

// Event 5
{
  "event_type": "stream.complete",
  "payload": {}
}
```

---

## 🔐 Security

- ✅ API keys stored in `.env` (excluded from git)
- ✅ Safe for local network use
- ⚠️ **Do not expose to public internet** without proper security (HTTPS, authentication, rate limiting)

---

## 📞 Support

For questions or issues, refer to:
- **LOCAL_SERVER_SETUP.md** - Setup and troubleshooting
- **UNIFIED_API_DOCS.md** - Complete API reference
- **POSTMAN_TEST_PAYLOADS.md** - Test examples

---

## 🎯 Key Benefits

1. **One Endpoint, All Operations** - No need for separate generate/modify endpoints
2. **Multi-Provider Support** - Switch between Claude, GPT, and more
3. **Dynamic Model Selection** - Choose any model at request time
4. **Real-Time Feedback** - SSE streaming for better UX
5. **Easy Integration** - Simple GET/POST requests
6. **Well Documented** - Comprehensive docs and examples

---

**Version**: 1.0  
**Last Updated**: January 8, 2026  
**Status**: ✅ Production Ready for Local Hosting

---

**🚀 Ready to use!** Start the server and explore the interactive docs at `http://localhost:8000/docs`
