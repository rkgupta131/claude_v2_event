# Postman Testing Guide - Simplified Payloads

## 🎯 Quick Reference

**Base URL:** `http://localhost:8000`

**Endpoints:**
- **Generate/Modify:** `POST /api/stream` (SSE streaming)
- **Chat:** `POST /api/chat` (regular JSON response)
- **Classify Intent:** `POST /api/classify` (regular JSON response)

---

## 📦 Simplified Payloads (Only Required Fields)

### 1️⃣ **Generate Project** (POST)

**Endpoint:** `POST http://localhost:8000/api/stream`

**Headers:**
```
Content-Type: application/json
Accept: text/event-stream
```

**Body (JSON):**
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
  "prompt": "Create a portfolio website for a photographer",
  "model_family": "OpenAI",
  "model_name": "gpt-4"
}
```

**With OpenAI GPT-5.2:**
```json
{
  "prompt": "Create a modern e-commerce store",
  "model_family": "OpenAI",
  "model_name": "gpt-5.2"
}
```

---

### 2️⃣ **Modify Project** (POST)

**Endpoint:** `POST http://localhost:8000/api/stream`

**Headers:**
```
Content-Type: application/json
Accept: text/event-stream
```

**Body (JSON):**
```json
{
  "prompt": "Change the hero text to Welcome and make buttons blue",
  "project_id": "project_v13_20260108_104713",
  "event_type": "modify",
  "model_family": "OpenAI",
  "model_name": "gpt-4"
}
```

**With Claude:**
```json
{
  "prompt": "Add a contact form section",
  "project_id": "project_v13_20260108_104713",
  "event_type": "modify",
  "model_family": "Anthropic",
  "model_name": "claude-opus-4-5-20251101"
}
```

**Note:** If `project_id` is not provided, it will use the latest project.

---

### 3️⃣ **Chat with AI** (POST)

**Endpoint:** `POST http://localhost:8000/api/chat`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON) - Simple:**
```json
{
  "message": "What frameworks do you support?"
}
```

**Body (JSON) - With Conversation History:**
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

---

### 4️⃣ **Classify Intent** (POST)

**Endpoint:** `POST http://localhost:8000/api/classify`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "text": "Hello! Can you create a website for my bakery?"
}
```

---

## 🔧 Postman Setup Instructions

### **For Generate/Modify (SSE Streaming)**

#### Step 1: Create New Request
1. Click **New** → **HTTP Request**
2. Set method to **POST**
3. Enter URL: `http://localhost:8000/api/stream`

#### Step 2: Set Headers
Go to **Headers** tab:
```
Key: Content-Type
Value: application/json

Key: Accept
Value: text/event-stream
```

#### Step 3: Set Body
1. Go to **Body** tab
2. Select **raw**
3. Select **JSON** from dropdown
4. Paste one of the payloads above

#### Step 4: Send Request
1. Click **Send**
2. **Important:** You'll see streaming data in the **Response** section
3. Events will appear as they arrive (SSE format)

#### Step 5: View Streaming Response
Postman will show the response like:
```
data: {"event_type":"thinking.start","payload":{}}

data: {"event_type":"chat.message","payload":{"content":"🧠 Using Anthropic claude-opus-4-5-20251101..."}}

data: {"event_type":"fs.write","payload":{"path":"index.html","language":"html"}}

data: {"event_type":"project.saved","payload":{"project_id":"project_v14_...","model_used":"Anthropic/claude-opus-4-5-20251101"}}
```

**💡 Tip:** Each line starting with `data: ` is a separate event. Parse the JSON after `data: ` to get the event object.

---

### **For Chat (Regular JSON Response)**

#### Step 1: Create New Request
1. Click **New** → **HTTP Request**
2. Set method to **POST**
3. Enter URL: `http://localhost:8000/api/chat`

#### Step 2: Set Headers
Go to **Headers** tab:
```
Key: Content-Type
Value: application/json
```

#### Step 3: Set Body
1. Go to **Body** tab
2. Select **raw**
3. Select **JSON** from dropdown
4. Paste chat payload:
```json
{
  "message": "What frameworks do you support?"
}
```

#### Step 4: Send Request
1. Click **Send**
2. You'll get a regular JSON response:
```json
{
  "message": "I support React with Vite and TypeScript...",
  "conversation_id": null
}
```

---

## 📋 Complete Test Collection

### **Test 1: Generate with Anthropic Claude**
```json
POST http://localhost:8000/api/stream
Content-Type: application/json
Accept: text/event-stream

{
  "prompt": "Create a landing page for a coffee shop",
  "model_family": "Anthropic",
  "model_name": "claude-opus-4-5-20251101"
}
```

---

### **Test 2: Generate with OpenAI GPT-4**
```json
POST http://localhost:8000/api/stream
Content-Type: application/json
Accept: text/event-stream

{
  "prompt": "Create a portfolio website",
  "model_family": "OpenAI",
  "model_name": "gpt-4"
}
```

---

### **Test 3: Generate with OpenAI GPT-5.2**
```json
POST http://localhost:8000/api/stream
Content-Type: application/json
Accept: text/event-stream

{
  "prompt": "Create an e-commerce store",
  "model_family": "OpenAI",
  "model_name": "gpt-5.2"
}
```

---

### **Test 4: Modify Project (Latest)**
```json
POST http://localhost:8000/api/stream
Content-Type: application/json
Accept: text/event-stream

{
  "prompt": "Change hero text to Welcome",
  "event_type": "modify",
  "model_family": "OpenAI",
  "model_name": "gpt-4"
}
```

---

### **Test 5: Modify Specific Project**
```json
POST http://localhost:8000/api/stream
Content-Type: application/json
Accept: text/event-stream

{
  "prompt": "Add a contact form",
  "project_id": "project_v13_20260108_104713",
  "event_type": "modify",
  "model_family": "Anthropic",
  "model_name": "claude-opus-4-5-20251101"
}
```

---

### **Test 6: Chat - Simple Question**
```json
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "What frameworks do you support?"
}
```

---

### **Test 7: Chat - With History**
```json
POST http://localhost:8000/api/chat
Content-Type: application/json

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
      "content": "I support React with Vite and TypeScript for building modern web applications."
    }
  ]
}
```

---

### **Test 8: Classify Intent**
```json
POST http://localhost:8000/api/classify
Content-Type: application/json

{
  "text": "Hello! Can you create a website for my bakery?"
}
```

---

## 🎯 How to Handle Chat in Postman

### **Understanding Chat Endpoint**

The `/api/chat` endpoint is **NOT** a streaming endpoint. It returns a regular JSON response immediately.

**Key Differences:**

| Feature | Generate/Modify (`/api/stream`) | Chat (`/api/chat`) |
|---------|--------------------------------|-------------------|
| **Response Type** | SSE Streaming (text/event-stream) | Regular JSON |
| **Response Time** | Real-time events over time | Single response |
| **Use Case** | Building/modifying projects | Asking questions |
| **Headers** | `Accept: text/event-stream` | `Content-Type: application/json` |

---

### **Chat Request Structure**

**Minimal (Required Only):**
```json
{
  "message": "Your question here"
}
```

**Full (With Context):**
```json
{
  "message": "Follow-up question",
  "conversation_id": "conv_123",
  "history": [
    {
      "role": "user",
      "content": "First message"
    },
    {
      "role": "assistant",
      "content": "AI response"
    }
  ]
}
```

---

### **Chat Response Structure**

**Success Response:**
```json
{
  "message": "AI's response text here...",
  "conversation_id": "conv_123"  // or null if not provided
}
```

**Error Response:**
```json
{
  "detail": "Chat error: ..."
}
```

---

### **Testing Chat Workflow**

#### **Step 1: Simple Chat**
```json
POST http://localhost:8000/api/chat

{
  "message": "What can you build for me?"
}
```

**Expected Response:**
```json
{
  "message": "I can build various types of websites including landing pages, portfolios, e-commerce stores, blogs, and corporate websites. I use React with Vite and TypeScript...",
  "conversation_id": null
}
```

---

#### **Step 2: Follow-up with History**
Use the `conversation_id` and `history` from previous response:

```json
POST http://localhost:8000/api/chat

{
  "message": "Can you explain React components?",
  "conversation_id": "conv_123",
  "history": [
    {
      "role": "user",
      "content": "What can you build for me?"
    },
    {
      "role": "assistant",
      "content": "I can build various types of websites..."
    }
  ]
}
```

---

#### **Step 3: Multi-turn Conversation**
Keep adding to history:

```json
POST http://localhost:8000/api/chat

{
  "message": "Show me an example",
  "conversation_id": "conv_123",
  "history": [
    {
      "role": "user",
      "content": "What can you build for me?"
    },
    {
      "role": "assistant",
      "content": "I can build various types of websites..."
    },
    {
      "role": "user",
      "content": "Can you explain React components?"
    },
    {
      "role": "assistant",
      "content": "React components are reusable pieces of UI..."
    }
  ]
}
```

---

## 🔍 Understanding SSE Response Format

When you call `/api/stream`, Postman will show the response like this:

```
data: {"event_type":"thinking.start","payload":{}}

data: {"event_type":"chat.message","payload":{"content":"🧠 Using Anthropic claude-opus-4-5-20251101..."}}

data: {"event_type":"fs.write","payload":{"path":"index.html","language":"html"}}

data: {"event_type":"fs.write","payload":{"path":"src/main.tsx","language":"typescript"}}

data: {"event_type":"project.saved","payload":{"project_id":"project_v14_20260108_120000","model_used":"Anthropic/claude-opus-4-5-20251101"}}

data: {"event_type":"stream.complete","payload":{}}
```

**How to Parse:**
1. Each line starts with `data: `
2. Everything after `data: ` is JSON
3. Parse the JSON to get:
   - `event_type`: Type of event
   - `payload`: Event data

**Example Parsed Event:**
```json
{
  "event_type": "project.saved",
  "payload": {
    "project_id": "project_v14_20260108_120000",
    "model_used": "Anthropic/claude-opus-4-5-20251101",
    "files": ["index.html", "src/main.tsx", "src/App.tsx"]
  }
}
```

---

## 📝 Quick Copy-Paste Payloads

### **Generate (Claude)**
```json
{"prompt":"Create a coffee shop landing page","model_family":"Anthropic","model_name":"claude-opus-4-5-20251101"}
```

### **Generate (GPT-4)**
```json
{"prompt":"Create a portfolio website","model_family":"OpenAI","model_name":"gpt-4"}
```

### **Generate (GPT-5.2)**
```json
{"prompt":"Create an e-commerce store","model_family":"OpenAI","model_name":"gpt-5.2"}
```

### **Modify**
```json
{"prompt":"Change hero text to Welcome","project_id":"project_v13_20260108_104713","event_type":"modify","model_family":"OpenAI","model_name":"gpt-4"}
```

### **Chat**
```json
{"message":"What frameworks do you support?"}
```

### **Classify**
```json
{"text":"Hello! Can you create a website for my bakery?"}
```

---

## ✅ Checklist for Testing

- [ ] Server is running (`uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload`)
- [ ] Health check works: `GET http://localhost:8000/health`
- [ ] Generate with Claude works
- [ ] Generate with OpenAI GPT-4 works
- [ ] Generate with OpenAI GPT-5.2 works
- [ ] Modify project works
- [ ] Chat endpoint works
- [ ] Classify endpoint works

---

## 🚨 Common Issues

### **Issue 1: No Response in Postman**
**Solution:** Make sure you set `Accept: text/event-stream` header for `/api/stream` endpoint.

### **Issue 2: Chat Returns Error**
**Solution:** Check that `message` field is not empty and is a string.

### **Issue 3: Modify Fails with "Project not found"**
**Solution:** 
1. First generate a project to get a `project_id`
2. Use that `project_id` in modify request
3. Or omit `project_id` to use latest project

### **Issue 4: SSE Events Not Streaming**
**Solution:** 
- Make sure server is running
- Check network tab in Postman
- Try with `curl` to verify:
  ```bash
  curl -N 'http://localhost:8000/api/stream?prompt=test&model_family=Anthropic&model_name=claude-opus-4-5-20251101'
  ```

---

## 🎉 You're Ready!

Copy any payload above, paste into Postman, and start testing! 🚀

