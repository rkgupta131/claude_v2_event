# API Quick Reference Card

## Base URL
```
http://localhost:8000
```

## Most Used Endpoints

### Generate Website (with streaming)
```bash
curl "http://localhost:8000/api/generate/stream?prompt=Create+a+landing+page"
```

### Generate Website (simple POST)
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a landing page for a coffee shop"}'
```

### Modify Project
```bash
curl -X POST http://localhost:8000/api/modify \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Change the hero background to blue"}'
```

### List Projects
```bash
curl http://localhost:8000/api/projects
```

### Get Project
```bash
curl http://localhost:8000/api/projects/{project_id}
```

### Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What can you build?"}'
```

### Classify Intent
```bash
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello! Create a website for me"}'
```

---

## SSE Event Handling (JavaScript)

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/generate/stream?prompt=' + encodeURIComponent(prompt)
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.event_type, data.payload);
  
  if (data.event_type === 'project.saved') {
    console.log('Done!', data.payload.project_id);
    eventSource.close();
  }
};

eventSource.onerror = () => eventSource.close();
```

---

## Key Event Types

| Event | Meaning |
|-------|---------|
| `thinking.start` | AI thinking |
| `progress.update` | Step status changed |
| `chat.message` | Status message |
| `fs.write` | File created |
| `project.saved` | Done - close stream |
| `error` | Error occurred |

---

## Intent Types

| Intent | Action |
|--------|--------|
| `greeting_only` | Show greeting |
| `chat` | Call /api/chat |
| `webpage_build` | Call /api/generate |
| `webpage_modify` | Call /api/modify |
| `illegal` | Block request |



