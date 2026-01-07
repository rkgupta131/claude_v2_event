# 🚀 Frontend API Handover Document

## Quick Summary for Frontend Team

**Base URL:** `http://localhost:8000` (or your deployed server URL)

**Interactive API Docs:** `http://localhost:8000/docs`

---

## 📋 API Endpoints at a Glance

| Endpoint | Method | Description | Response Type |
|----------|--------|-------------|---------------|
| `/api/generate` | POST | Generate new website (blocking) | JSON |
| `/api/generate/stream` | GET/POST | Generate with real-time events | SSE Stream |
| `/api/modify` | POST | Modify existing project (blocking) | JSON |
| `/api/modify/stream` | POST | Modify with real-time events | SSE Stream |
| `/api/projects` | GET | List all projects | JSON |
| `/api/projects/latest` | GET | Get most recent project | JSON |
| `/api/projects/{id}` | GET | Get specific project | JSON |
| `/api/projects/{id}/files` | GET | List files in project | JSON |
| `/api/projects/{id}/files/{path}` | GET | Get specific file content | JSON |
| `/api/chat` | POST | Chat with AI | JSON |
| `/api/classify` | POST | Classify user intent | JSON |
| `/health` | GET | Health check | JSON |

---

## 🔥 Core Endpoints

### 1. Generate Website (Simple - Blocking)

**Use this for simple requests where you just need the result.**

```
POST /api/generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "Create a landing page for a coffee shop called Bean Dreams"
}
```

**Full Request (with all options):**
```json
{
  "prompt": "Create a landing page for my business",
  "business_name": "Bean Dreams Coffee",
  "tagline": "Where every cup tells a story",
  "website_type": "Landing Page",
  "color_scheme": "Modern Dark",
  "key_features": ["Artisan Coffee", "Fresh Pastries", "Cozy Atmosphere"],
  "sections": ["About Us", "Products/Services", "Contact Form"],
  "email": "hello@beandreams.com",
  "phone": "+1-555-1234",
  "additional_info": "Use warm colors and include a hero image"
}
```

**Response:**
```json
{
  "success": true,
  "project_id": "project_v1_20260105_143022",
  "path": "output/project_v1_20260105_143022.json",
  "files": [
    "index.html",
    "src/App.tsx",
    "src/main.tsx",
    "src/index.css",
    "package.json",
    "vite.config.ts"
  ],
  "metadata": {
    "version": 1,
    "timestamp": "20260105_143022",
    "is_modification": false,
    "created_at": "2026-01-05T14:30:22"
  }
}
```

**JavaScript Example:**
```javascript
const response = await fetch('http://localhost:8000/api/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'Create a portfolio website for a photographer'
  })
});

const result = await response.json();
console.log('Project created:', result.project_id);
```

---

### 2. Generate Website (SSE Stream - Recommended)

**Use this for the best user experience with real-time progress updates.**

```
GET /api/generate/stream?prompt=Create+a+landing+page
```

**Query Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `prompt` | Yes | Description of website to create |
| `business_name` | No | Business name |
| `website_type` | No | Type of website |
| `color_scheme` | No | Color preference |

**JavaScript Example (EventSource):**
```javascript
function generateWebsite(prompt) {
  const url = new URL('http://localhost:8000/api/generate/stream');
  url.searchParams.set('prompt', prompt);
  
  const eventSource = new EventSource(url);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch (data.event_type) {
      case 'thinking.start':
        showSpinner('AI is thinking...');
        break;
        
      case 'thinking.end':
        hideSpinner();
        showMessage(`Thought for ${data.payload.duration_ms / 1000}s`);
        break;
        
      case 'progress.init':
        initProgressBar(data.payload.steps);
        break;
        
      case 'progress.update':
        updateStep(data.payload.step_id, data.payload.status);
        break;
        
      case 'chat.message':
        addMessage(data.payload.content);
        break;
        
      case 'fs.write':
        showFileCreated(data.payload.path);
        break;
        
      case 'edit.start':
        showFileEditing(data.payload.path);
        break;
        
      case 'edit.end':
        showFileComplete(data.payload.path, data.payload.duration_ms);
        break;
        
      case 'project.saved':
        showSuccess(data.payload.project_id, data.payload.files);
        eventSource.close();
        break;
        
      case 'error':
      case 'stream.failed':
        showError(data.payload.message || data.payload.error);
        eventSource.close();
        break;
    }
  };
  
  eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    showError('Connection lost');
    eventSource.close();
  };
  
  return eventSource; // Return so caller can close if needed
}

// Usage
const stream = generateWebsite('Create a blog website');

// To cancel
// stream.close();
```

**POST Version (for complex requests):**
```javascript
// For POST, you need to use fetch with streaming
async function generateWithDetails(requestBody) {
  const response = await fetch('http://localhost:8000/api/generate/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody)
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const text = decoder.decode(value);
    const lines = text.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        handleEvent(data);
      }
    }
  }
}
```

---

### 3. Modify Existing Project

```
POST /api/modify
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "Change the hero section background to blue and add a contact form",
  "project_id": "project_v1_20260105_143022"
}
```

> **Note:** If `project_id` is omitted, the API will modify the most recent project.

**Response:**
```json
{
  "success": true,
  "project_id": "project_v1_20260105_150000",
  "path": "modified_output/project_v1_20260105_150000.json",
  "base_project": "project_v1_20260105_143022",
  "files_modified": ["src/App.tsx", "src/index.css"],
  "sections_changed": ["hero", "contact"],
  "metadata": {
    "version": 1,
    "is_modification": true,
    "base_version": 1
  }
}
```

**Streaming Version:**
```
POST /api/modify/stream
```
Same request body, returns SSE stream with same event types as generate.

---

### 4. List Projects

```
GET /api/projects?type=original&limit=10&offset=0
```

**Query Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `type` | all | Filter: `original` or `modified` |
| `limit` | 50 | Max results (1-100) |
| `offset` | 0 | Pagination offset |

**Response:**
```json
{
  "total": 15,
  "projects": [
    {
      "id": "project_v3_20260105_150000",
      "version": 3,
      "is_modification": true,
      "created_at": "2026-01-05T15:00:00",
      "file_count": 6
    },
    {
      "id": "project_v2_20260105_143022",
      "version": 2,
      "is_modification": false,
      "created_at": "2026-01-05T14:30:22",
      "file_count": 6
    }
  ]
}
```

---

### 5. Get Project Details

```
GET /api/projects/{project_id}
```

**Response:**
```json
{
  "id": "project_v1_20260105_143022",
  "path": "output/project_v1_20260105_143022.json",
  "metadata": {
    "version": 1,
    "timestamp": "20260105_143022",
    "is_modification": false,
    "created_at": "2026-01-05T14:30:22"
  },
  "files": {
    "index.html": "<!DOCTYPE html>...",
    "src/App.tsx": "export function App() {...}",
    "src/main.tsx": "import React from 'react'...",
    "src/index.css": "body { margin: 0; ... }",
    "package.json": "{ \"name\": \"...",
    "vite.config.ts": "import { defineConfig }..."
  }
}
```

---

### 6. Get Latest Project

```
GET /api/projects/latest?type=original
```

Returns the most recent project with full file contents.

---

### 7. Chat with AI

```
POST /api/chat
Content-Type: application/json
```

**Request:**
```json
{
  "message": "What kind of websites can you create?",
  "conversation_id": "conv_123",
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ]
}
```

**Response:**
```json
{
  "message": "I can create various types of websites including landing pages, e-commerce shops, portfolios, blogs, and corporate websites. Just describe what you need!",
  "conversation_id": "conv_123"
}
```

---

### 8. Classify Intent

**Use this to determine what the user wants to do before calling other endpoints.**

```
POST /api/classify
Content-Type: application/json
```

**Request:**
```json
{
  "text": "Hello! Can you make a website for my bakery?"
}
```

**Response:**
```json
{
  "intent": "greeting_and_webpage",
  "confidence": 0.95,
  "explanation": "User greeted and requested a bakery website"
}
```

**Intent Types:**
| Intent | Description | Next Action |
|--------|-------------|-------------|
| `greeting_only` | Just a greeting | Show friendly response |
| `chat` | General question | Call `/api/chat` |
| `webpage_build` | Wants new website | Call `/api/generate` |
| `webpage_modify` | Wants to change existing | Call `/api/modify` |
| `greeting_and_webpage` | Greeting + build request | Call `/api/generate` |
| `illegal` | Harmful content | Show block message |

**Routing Example:**
```javascript
async function handleUserInput(userText) {
  // First, classify the intent
  const classifyRes = await fetch('http://localhost:8000/api/classify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: userText })
  });
  const { intent, confidence } = await classifyRes.json();
  
  // Route based on intent
  switch (intent) {
    case 'greeting_only':
      return showGreeting();
      
    case 'chat':
      return callChatEndpoint(userText);
      
    case 'webpage_build':
    case 'greeting_and_webpage':
      return startGenerateFlow(userText);
      
    case 'webpage_modify':
      return startModifyFlow(userText);
      
    case 'illegal':
      return showBlockedMessage();
  }
}
```

---

## 📡 SSE Event Types Reference

### Event Structure

All SSE events follow this format:
```json
{
  "event_id": "evt_abc123",
  "event_type": "progress.update",
  "timestamp": "2026-01-05T14:30:22Z",
  "project_id": "proj_123",
  "conversation_id": "conv_456",
  "payload": { ... }
}
```

### All Event Types

| Event Type | Payload | Description |
|------------|---------|-------------|
| `thinking.start` | `{}` | AI started thinking |
| `thinking.end` | `{ "duration_ms": 5000 }` | AI finished thinking |
| `progress.init` | `{ "steps": [...] }` | Build steps initialized |
| `progress.update` | `{ "step_id": "code", "status": "completed" }` | Step status changed |
| `chat.message` | `{ "content": "Setting up..." }` | Status message |
| `fs.create` | `{ "path": "src/", "kind": "folder" }` | Folder created |
| `fs.write` | `{ "path": "App.tsx", "language": "typescript" }` | File written |
| `edit.start` | `{ "path": "App.tsx" }` | File editing started |
| `edit.end` | `{ "path": "App.tsx", "duration_ms": 1200 }` | File editing done |
| `build.start` | `{ "container_id": "ctr_001" }` | Build started |
| `build.log` | `{ "level": "info", "message": "..." }` | Build log message |
| `project.saved` | `{ "project_id": "...", "files": [...] }` | Project saved |
| `stream.complete` | `{}` | Generation finished |
| `stream.failed` | `{ "error": "..." }` | Generation failed |
| `error` | `{ "scope": "llm", "message": "..." }` | Error occurred |

### Step Statuses

| Status | Icon Suggestion | Meaning |
|--------|-----------------|---------|
| `pending` | ⏳ | Not started |
| `in_progress` | 🔄 | Currently working |
| `completed` | ✅ | Done successfully |
| `failed` | ❌ | Failed |

---

## 💻 Complete React Integration Example

```jsx
import { useState, useCallback } from 'react';

const API_BASE = 'http://localhost:8000';

function WebsiteGenerator() {
  const [prompt, setPrompt] = useState('');
  const [status, setStatus] = useState('idle'); // idle, generating, success, error
  const [progress, setProgress] = useState({});
  const [messages, setMessages] = useState([]);
  const [files, setFiles] = useState([]);
  const [projectId, setProjectId] = useState(null);
  const [error, setError] = useState(null);

  const generate = useCallback(() => {
    if (!prompt.trim()) return;
    
    setStatus('generating');
    setProgress({});
    setMessages([]);
    setFiles([]);
    setError(null);
    
    const url = new URL(`${API_BASE}/api/generate/stream`);
    url.searchParams.set('prompt', prompt);
    
    const eventSource = new EventSource(url);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.event_type) {
        case 'thinking.start':
          setStatus('thinking');
          break;
          
        case 'thinking.end':
          setStatus('generating');
          break;
          
        case 'progress.init':
          const steps = {};
          data.payload.steps.forEach(step => {
            steps[step.id] = { label: step.label, status: step.status };
          });
          setProgress(steps);
          break;
          
        case 'progress.update':
          setProgress(prev => ({
            ...prev,
            [data.payload.step_id]: {
              ...prev[data.payload.step_id],
              status: data.payload.status
            }
          }));
          break;
          
        case 'chat.message':
          setMessages(prev => [...prev, data.payload.content]);
          break;
          
        case 'fs.write':
        case 'edit.start':
          setFiles(prev => {
            const path = data.payload.path;
            if (!prev.find(f => f.path === path)) {
              return [...prev, { path, status: 'editing' }];
            }
            return prev;
          });
          break;
          
        case 'edit.end':
          setFiles(prev => 
            prev.map(f => 
              f.path === data.payload.path 
                ? { ...f, status: 'complete', duration: data.payload.duration_ms }
                : f
            )
          );
          break;
          
        case 'project.saved':
          setProjectId(data.payload.project_id);
          setStatus('success');
          eventSource.close();
          break;
          
        case 'error':
        case 'stream.failed':
          setError(data.payload.message || data.payload.error);
          setStatus('error');
          eventSource.close();
          break;
      }
    };
    
    eventSource.onerror = () => {
      setError('Connection lost. Please try again.');
      setStatus('error');
      eventSource.close();
    };
  }, [prompt]);

  return (
    <div className="generator">
      <div className="input-section">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe your website..."
          disabled={status === 'generating' || status === 'thinking'}
        />
        <button 
          onClick={generate}
          disabled={status === 'generating' || status === 'thinking'}
        >
          {status === 'thinking' ? '🤔 Thinking...' : 
           status === 'generating' ? '⚡ Generating...' : 
           '🚀 Generate Website'}
        </button>
      </div>
      
      {/* Progress Steps */}
      {Object.keys(progress).length > 0 && (
        <div className="progress">
          <h3>Progress</h3>
          {Object.entries(progress).map(([id, step]) => (
            <div key={id} className={`step ${step.status}`}>
              {step.status === 'completed' ? '✅' : 
               step.status === 'in_progress' ? '🔄' : '⏳'}
              {step.label || id}
            </div>
          ))}
        </div>
      )}
      
      {/* Activity Messages */}
      {messages.length > 0 && (
        <div className="messages">
          <h3>Activity</h3>
          {messages.map((msg, i) => (
            <div key={i} className="message">💬 {msg}</div>
          ))}
        </div>
      )}
      
      {/* Files Being Created */}
      {files.length > 0 && (
        <div className="files">
          <h3>Files ({files.length})</h3>
          {files.map((file, i) => (
            <div key={i} className={`file ${file.status}`}>
              {file.status === 'complete' ? '✅' : '✏️'} {file.path}
              {file.duration && <span> ({file.duration}ms)</span>}
            </div>
          ))}
        </div>
      )}
      
      {/* Success */}
      {status === 'success' && (
        <div className="success">
          <h3>✨ Website Created!</h3>
          <p>Project ID: {projectId}</p>
          <button onClick={() => window.open(`${API_BASE}/api/projects/${projectId}`)}>
            View Project
          </button>
        </div>
      )}
      
      {/* Error */}
      {error && (
        <div className="error">
          <h3>❌ Error</h3>
          <p>{error}</p>
          <button onClick={() => setStatus('idle')}>Try Again</button>
        </div>
      )}
    </div>
  );
}

export default WebsiteGenerator;
```

---

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad request | Check request body |
| 404 | Not found | Check project ID |
| 500 | Server error | Check API key, retry |

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

### Handling Errors

```javascript
try {
  const response = await fetch(`${API_BASE}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: 'Create a website' })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }
  
  const data = await response.json();
  // Handle success
} catch (error) {
  console.error('API Error:', error.message);
  // Show error to user
}
```

---

## 🔧 CORS Configuration

The API allows all origins by default. If you need to restrict this in production, configure the backend's CORS settings in `api/main.py`.

---

## 📊 Typical Flow

```
1. User enters prompt
   ↓
2. Call /api/classify to detect intent
   ↓
3. If intent is "webpage_build" or "greeting_and_webpage":
   → Call /api/generate/stream (SSE)
   → Show progress UI as events arrive
   → On "project.saved" event, show success
   ↓
4. If intent is "webpage_modify":
   → Optionally call /api/projects to let user pick project
   → Call /api/modify/stream with project_id
   ↓
5. If intent is "chat":
   → Call /api/chat
   → Show response
   ↓
6. To view/download generated files:
   → Call /api/projects/{project_id}
   → Render files or provide download
```

---

## 🚀 Server Startup (for Testing)

```bash
# Navigate to project folder
cd claude_v2_event_api

# Activate virtual environment
source event_api/bin/activate  # or claude_v2_event/bin/activate

# Set API key (if not in .env)
export ANTHROPIC_API_KEY="your-key-here"

# Start server
uvicorn api.main:app --reload --port 8000

# Server will be available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

---

## 📞 Contact

For any questions or issues, please reach out to the backend team.

---

**Happy Building! 🎉**



