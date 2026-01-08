# Unified API Documentation

## 🎯 Overview

The **Unified API** provides a single endpoint (`/api/stream`) that supports:
- ✅ Multiple AI providers (Anthropic, OpenAI, Google, Mistral)
- ✅ Dynamic model selection
- ✅ Both generation and modification operations
- ✅ GET and POST methods
- ✅ Real-time SSE streaming

---

## 📍 Endpoint

### Base URL
```
http://localhost:8000/api/stream
```

Or your local network IP (accessible from other devices):
```
http://YOUR_LOCAL_IP:8000/api/stream
```

### Methods
- **GET**: Query parameters
- **POST**: JSON request body

---

## 🔑 Request Parameters

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `prompt` | string | What you want to create/modify | `"Create a coffee shop landing page"` |
| `model_family` | string | AI provider | `"Anthropic"`, `"OpenAI"`, `"Google"`, `"Mistral"` |
| `model_name` | string | Specific model | `"claude-opus-4-5-20251101"`, `"gpt-5.2"` |

### Optional Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `project_id` | string | Project ID (for modify) | `null` (uses latest) |
| `event_type` | string | Operation type | `"generate"` or `"modify"` |
| `business_name` | string | Business name | `null` |
| `website_type` | string | Type of website | `null` |
| `color_scheme` | string | Color preference | `null` |
| `key_features` | array | Features list | `[]` |
| `sections` | array | Sections to include | `[]` |

---

## 🤖 Supported Models

### Anthropic (Claude)
```javascript
{
  "model_family": "Anthropic",
  "model_name": "claude-opus-4-5-20251101"  // or "claude-sonnet-4-20250514"
}
```

**Available Models:**
- `claude-opus-4-5-20251101` (most powerful)
- `claude-sonnet-4-20250514` (balanced)
- `claude-3-5-sonnet-20241022`

**Required Environment Variable:**
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

---

### OpenAI (GPT)
```javascript
{
  "model_family": "OpenAI",
  "model_name": "gpt-5.2"  // or "gpt-4", "gpt-3.5-turbo"
}
```

**Available Models:**
- `gpt-5.2` (when available)
- `gpt-4` (most capable currently)
- `gpt-4-turbo`
- `gpt-3.5-turbo`

**Required Environment Variable:**
```bash
OPENAI_API_KEY=sk-...
```

---

### Google Gemini (Coming Soon)
```javascript
{
  "model_family": "Google",
  "model_name": "gemini-pro"
}
```

**Status:** Not yet implemented

---

### Mistral (Coming Soon)
```javascript
{
  "model_family": "Mistral",
  "model_name": "mistral-large-latest"
}
```

**Status:** Not yet implemented

---

## 📡 Usage Examples

### Example 1: Generate with Claude (GET Request)

```javascript
const url = 'http://localhost:8000/api/stream?' + new URLSearchParams({
    prompt: 'Create a landing page for a coffee shop',
    event_type: 'generate',
    model_family: 'Anthropic',
    model_name: 'claude-opus-4-5-20251101',
    business_name: 'Bean Dreams',
    website_type: 'Landing Page'
});

const eventSource = new EventSource(url);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.event_type) {
        case 'thinking.start':
            console.log('🧠 AI is thinking...');
            break;
        case 'chat.message':
            console.log('💬', data.payload.content);
            break;
        case 'fs.write':
            console.log('📝 Writing file:', data.payload.path);
            break;
        case 'project.saved':
            console.log('✅ Project saved:', data.payload.project_id);
            console.log('🤖 Model used:', data.payload.model_used);
            break;
        case 'stream.complete':
            console.log('🎉 Done!');
            eventSource.close();
            break;
    }
};

eventSource.onerror = (error) => {
    console.error('❌ Error:', error);
    eventSource.close();
};
```

---

### Example 2: Generate with OpenAI GPT-5.2 (POST Request)

```javascript
const response = await fetch('http://localhost:8000/api/stream', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        prompt: 'Create a portfolio website for a photographer',
        event_type: 'generate',
        model_family: 'OpenAI',
        model_name: 'gpt-5.2',
        business_name: 'John Doe Photography',
        website_type: 'Portfolio',
        color_scheme: 'Modern Dark'
    })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const {value, done} = await reader.read();
    if (done) break;
    
    const text = decoder.decode(value);
    const lines = text.split('\n\n');
    
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const event = JSON.parse(line.slice(6));
            console.log(event.event_type, event.payload);
        }
    }
}
```

---

### Example 3: Modify Existing Project with OpenAI

```javascript
const url = 'http://localhost:8000/api/stream?' + new URLSearchParams({
    prompt: 'Change the hero section text to "Welcome to Paradise"',
    project_id: 'project_v1_20250108_120000',
    event_type: 'modify',
    model_family: 'OpenAI',
    model_name: 'gpt-4'
});

const eventSource = new EventSource(url);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.event_type === 'project.saved') {
        console.log('Modified files:', data.payload.files_modified);
        console.log('Sections changed:', data.payload.sections_changed);
        console.log('Model used:', data.payload.model_used);
    }
};
```

---

### Example 4: Using cURL (GET)

```bash
curl -N 'https://your-api.com/api/stream?prompt=Create%20a%20bakery%20website&event_type=generate&model_family=OpenAI&model_name=gpt-5.2'
```

---

### Example 5: Using cURL (POST)

```bash
curl -X POST http://localhost:8000/api/stream \
  -H "Content-Type: application/json" \
  -N \
  -d '{
    "prompt": "Create a restaurant website",
    "event_type": "generate",
    "model_family": "Anthropic",
    "model_name": "claude-opus-4-5-20251101",
    "business_name": "Tasty Bites",
    "website_type": "Landing Page"
  }'
```

---

## 📊 SSE Event Types

The API streams events in real-time. Here are all event types:

| Event Type | Description | Payload |
|------------|-------------|---------|
| `thinking.start` | AI started processing | `{}` |
| `thinking.end` | AI finished thinking | `{}` |
| `progress.init` | Initialize progress bar | `{ mode, steps }` |
| `progress.update` | Update progress step | `{ step_id, status }` |
| `chat.message` | Narration message | `{ content }` |
| `fs.create` | File/folder created | `{ path, type }` |
| `fs.write` | File written | `{ path, content, language }` |
| `edit.start` | Started editing file | `{ path }` |
| `edit.end` | Finished editing file | `{ path, duration_ms }` |
| `build.start` | Build started | `{}` |
| `build.log` | Build log message | `{ message, level }` |
| `project.saved` | Project saved successfully | `{ project_id, path, model_used }` |
| `stream.complete` | Generation complete | `{}` |
| `error` | Error occurred | `{ message, details }` |

---

## 🔍 List Available Models

Get all supported providers and models:

```javascript
fetch('http://localhost:8000/api/models')
    .then(res => res.json())
    .then(data => {
        console.log('Providers:', data.providers);
        console.log('Examples:', data.examples);
    });
```

**Response:**
```json
{
  "providers": {
    "Anthropic": "claude-opus-4-5-20251101",
    "OpenAI": "gpt-4",
    "Google": "gemini-pro",
    "Mistral": "mistral-large-latest"
  },
  "examples": {
    "Anthropic": [
      "claude-opus-4-5-20251101",
      "claude-sonnet-4-20250514"
    ],
    "OpenAI": [
      "gpt-4",
      "gpt-5.2",
      "gpt-3.5-turbo"
    ]
  }
}
```

---

## ⚙️ Environment Variables

### Required

```bash
# For Anthropic models
ANTHROPIC_API_KEY=sk-ant-api03-...

# For OpenAI models
OPENAI_API_KEY=sk-...
```

### Optional

```bash
# For Google models (coming soon)
GOOGLE_API_KEY=...

# For Mistral models (coming soon)
MISTRAL_API_KEY=...
```

---

## 🚀 Local Server Setup

### 1. Install Dependencies

```bash
cd /Users/rkguptayotta.com/Desktop/codes/api_approach/claude_v2_event_api
source event_api/bin/activate
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
export OPENAI_API_KEY=sk-...
```

Or create/update `.env` file:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
```

### 3. Start Server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Server will be available at:**
- Local: `http://localhost:8000`
- Network: `http://YOUR_LOCAL_IP:8000` (accessible from other devices on same network)

### 4. Test

```bash
curl -N 'http://localhost:8000/api/stream?prompt=Create%20a%20test%20website&event_type=generate&model_family=Anthropic&model_name=claude-opus-4-5-20251101'
```

### 5. Access API Documentation

Open in browser:
- Interactive Docs: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

---

## 📝 Response Format

### Success Response (SSE Stream)

```
data: {"event_type": "thinking.start", "payload": {}}

data: {"event_type": "chat.message", "payload": {"content": "🧠 Analyzing your request..."}}

data: {"event_type": "progress.init", "payload": {"mode": "modal", "steps": [...]}}

data: {"event_type": "fs.write", "payload": {"path": "src/App.tsx", "language": "typescript"}}

data: {"event_type": "project.saved", "payload": {"project_id": "project_v1_20250108", "model_used": "OpenAI/gpt-5.2"}}

data: {"event_type": "stream.complete", "payload": {}}
```

### Error Response

```
data: {"event_type": "error", "payload": {"message": "OpenAI API key not configured", "details": "Set OPENAI_API_KEY environment variable"}}
```

---

## 🆚 Comparison: Old vs New API

### Old API (Deprecated)

```javascript
// Separate endpoints for generate and modify
const generateUrl = '/api/generate/stream?prompt=...';
const modifyUrl = '/api/modify/stream';

// Only Claude models
// Fixed model selection
```

### New Unified API (Recommended)

```javascript
// Single endpoint for all operations
const url = '/api/stream?prompt=...&event_type=generate&model_family=OpenAI&model_name=gpt-5.2';

// Multiple AI providers
// Dynamic model selection
// Same interface for all providers
```

---

## 🔐 Security Notes

1. **API Keys**: Never expose API keys in frontend code
2. **Environment Variables**: Use server-side environment variables
3. **CORS**: Configure CORS properly for production
4. **Rate Limiting**: Implement rate limiting for production use

---

## 🐛 Troubleshooting

### Error: "Unsupported model_family"

**Solution:** Check that `model_family` is one of: `Anthropic`, `OpenAI`, `Google`, `Mistral`

---

### Error: "OPENAI_API_KEY not set"

**Solution:** Set the environment variable:
```bash
export OPENAI_API_KEY=sk-...
```

---

### Error: "Project not found"

**Solution:** 
- For modifications, ensure `project_id` is valid
- Or omit `project_id` to use the latest project

---

### Error: "Google/Mistral provider not yet implemented"

**Solution:** Use `Anthropic` or `OpenAI` providers (fully supported)

---

## 📚 Additional Resources

- [Full API Documentation](./FRONTEND_API_HANDOVER.md)
- [System Prompts](./SYSTEM_PROMPTS.md)
- [Interactive API Docs](http://localhost:8000/docs)

---

## 💡 Best Practices

1. **Model Selection**:
   - Use `claude-opus-4-5-20251101` for highest quality
   - Use `gpt-4` for OpenAI
   - Test different models for your use case

2. **Error Handling**:
   ```javascript
   eventSource.onerror = (error) => {
       console.error('Connection error:', error);
       eventSource.close();
       // Implement retry logic
   };
   ```

3. **Connection Management**:
   - Always close EventSource when done
   - Implement reconnection logic
   - Handle network timeouts

4. **Event Processing**:
   - Handle all event types
   - Update UI based on events
   - Show progress indicators

---

## 🎉 Quick Start Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Unified API Test</title>
</head>
<body>
    <h1>Unified API Test</h1>
    <button onclick="testAPI()">Generate with GPT-5.2</button>
    <div id="output"></div>
    
    <script>
        function testAPI() {
            const url = '/api/stream?' + new URLSearchParams({
                prompt: 'Create a simple landing page',
                event_type: 'generate',
                model_family: 'OpenAI',
                model_name: 'gpt-5.2'
            });
            
            const eventSource = new EventSource(url);
            const output = document.getElementById('output');
            
            eventSource.onmessage = (e) => {
                const event = JSON.parse(e.data);
                output.innerHTML += `<p>${event.event_type}: ${JSON.stringify(event.payload)}</p>`;
                
                if (event.event_type === 'stream.complete') {
                    eventSource.close();
                }
            };
        }
    </script>
</body>
</html>
```

---

**Version:** 1.0  
**Last Updated:** January 8, 2026  
**Contact:** Backend Team

