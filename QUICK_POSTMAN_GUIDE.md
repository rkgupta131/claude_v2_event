# 🚀 Quick Postman Guide - Simplified Payloads

## 📦 Payloads (Only Required Fields)

### **1. Generate Project**

**Endpoint:** `POST http://localhost:8000/api/stream`

**Headers:**
- `Content-Type: application/json`
- `Accept: text/event-stream`

**Body:**
```json
{
  "prompt": "Create a coffee shop landing page",
  "model_family": "Anthropic",
  "model_name": "claude-opus-4-5-20251101"
}
```

**With OpenAI GPT-4:**
```json
{
  "prompt": "Create a portfolio website",
  "model_family": "OpenAI",
  "model_name": "gpt-4"
}
```

**With OpenAI GPT-5.2:**
```json
{
  "prompt": "Create an e-commerce store",
  "model_family": "OpenAI",
  "model_name": "gpt-5.2"
}
```

---

### **2. Modify Project**

**Endpoint:** `POST http://localhost:8000/api/stream`

**Headers:**
- `Content-Type: application/json`
- `Accept: text/event-stream`

**Body:**
```json
{
  "prompt": "Change hero text to Welcome",
  "project_id": "project_v13_20260108_104713",
  "event_type": "modify",
  "model_family": "OpenAI",
  "model_name": "gpt-4"
}
```

**Note:** Omit `project_id` to modify the latest project.

---

## 💬 How to Handle Chat in Postman

### **Key Difference:**

| Endpoint | Response Type | Use Case |
|----------|--------------|----------|
| `/api/stream` | **SSE Streaming** (real-time events) | Generate/Modify projects |
| `/api/chat` | **Regular JSON** (single response) | Ask questions |

---

### **Chat Endpoint**

**Endpoint:** `POST http://localhost:8000/api/chat`

**Headers:**
- `Content-Type: application/json`

**Body (Simple):**
```json
{
  "message": "What frameworks do you support?"
}
```

**Body (With History):**
```json
{
  "message": "Can you explain React components?",
  "conversation_id": "conv_123",
  "history": [
    {
      "role": "user",
      "content": "What frameworks do you support?"
    },
    {
      "role": "assistant",
      "content": "I support React with Vite and TypeScript..."
    }
  ]
}
```

**Response:**
```json
{
  "message": "AI's response here...",
  "conversation_id": "conv_123"
}
```

---

## 🎯 Postman Setup Steps

### **For Generate/Modify (SSE Streaming):**

1. **Create Request:**
   - Method: `POST`
   - URL: `http://localhost:8000/api/stream`

2. **Set Headers:**
   ```
   Content-Type: application/json
   Accept: text/event-stream
   ```

3. **Set Body:**
   - Select **Body** tab
   - Choose **raw**
   - Select **JSON**
   - Paste payload

4. **Send:**
   - Click **Send**
   - Watch streaming events in response

---

### **For Chat (Regular JSON):**

1. **Create Request:**
   - Method: `POST`
   - URL: `http://localhost:8000/api/chat`

2. **Set Headers:**
   ```
   Content-Type: application/json
   ```

3. **Set Body:**
   - Select **Body** tab
   - Choose **raw**
   - Select **JSON**
   - Paste chat payload

4. **Send:**
   - Click **Send**
   - Get immediate JSON response

---

## 📋 Quick Copy-Paste Payloads

### Generate (Claude)
```json
{"prompt":"Create a coffee shop landing page","model_family":"Anthropic","model_name":"claude-opus-4-5-20251101"}
```

### Generate (GPT-4)
```json
{"prompt":"Create a portfolio website","model_family":"OpenAI","model_name":"gpt-4"}
```

### Generate (GPT-5.2)
```json
{"prompt":"Create an e-commerce store","model_family":"OpenAI","model_name":"gpt-5.2"}
```

### Modify
```json
{"prompt":"Change hero text to Welcome","project_id":"project_v13_20260108_104713","event_type":"modify","model_family":"OpenAI","model_name":"gpt-4"}
```

### Chat
```json
{"message":"What frameworks do you support?"}
```

---

## 📥 Import Postman Collection

**Import the ready-made collection:**
1. Open Postman
2. Click **Import**
3. Select `postman_collection.json`
4. All requests are ready to use! ✅

---

## ✅ Testing Checklist

- [ ] Server running: `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload`
- [ ] Health check: `GET http://localhost:8000/health`
- [ ] Generate with Claude ✅
- [ ] Generate with GPT-4 ✅
- [ ] Generate with GPT-5.2 ✅
- [ ] Modify project ✅
- [ ] Chat endpoint ✅

---

**📚 Full Guide:** See `POSTMAN_SIMPLIFIED.md` for detailed instructions!

