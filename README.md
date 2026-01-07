# 🚀 AI Project Generator

Generate complete websites using AI with real-time streaming events.

## Features

- **🎯 Generate Websites** - Describe what you want, get complete code
- **✏️ Modify Projects** - Make changes with natural language
- **📡 Real-Time Events** - SSE streaming for engaging UX
- **💬 AI Chat** - Get help and guidance
- **🔍 Intent Detection** - Smart routing of user requests

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### 3. Run the API

```bash
uvicorn api.main:app --reload --port 8000
```

### 4. Open Documentation

Visit: http://localhost:8000/docs

## Project Structure

```
claude_v2_event/
├── api/                    # FastAPI Backend
│   ├── main.py             # App entry point
│   ├── schemas.py          # Request/Response models
│   └── routes/
│       ├── generate.py     # Generate/Modify endpoints
│       ├── projects.py     # Project management
│       └── chat.py         # Chat & classification
├── events/                 # Streaming Event System
│   └── stream_events.py    # Event definitions
├── models/                 # AI/LLM Integration
│   └── gemini_client_qa.py # Claude API client
├── intent/                 # Intent Classification
│   ├── classifier.py
│   └── greeting_generator.py
├── streamlit_backup/       # Streamlit Demo (backup)
├── output/                 # Generated projects
├── modified_output/        # Modified projects
├── API_GUIDE.md            # Complete API documentation
└── requirements.txt
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/generate` | Generate new project |
| `GET /api/generate/stream` | Generate with SSE streaming |
| `POST /api/modify` | Modify existing project |
| `POST /api/modify/stream` | Modify with SSE streaming |
| `GET /api/projects` | List all projects |
| `GET /api/projects/{id}` | Get specific project |
| `POST /api/chat` | Chat with AI |
| `POST /api/classify` | Classify user intent |

## Streaming Events

Connect via EventSource for real-time updates:

```javascript
const eventSource = new EventSource('/api/generate/stream?prompt=Create+a+blog');

eventSource.onmessage = (e) => {
  const event = JSON.parse(e.data);
  console.log(event.event_type, event.payload);
};
```

Event types: `thinking.start`, `progress.update`, `chat.message`, `fs.write`, `project.saved`, etc.

## Documentation

📖 **Complete Guide:** See [API_GUIDE.md](./API_GUIDE.md)

## Streamlit Demo

A Streamlit demo is available in `streamlit_backup/`:

```bash
cd streamlit_backup
streamlit run app_qa.py
```

## License

MIT

