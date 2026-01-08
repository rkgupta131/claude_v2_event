# Postman Test Payloads - Unified API

## 🎯 Quick Setup

### Base URL
```
http://localhost:8000
```

Or from other devices on your network:
```
http://YOUR_LOCAL_IP:8000
```

### Important: For SSE Streaming
In Postman, SSE events will appear in the response body as they stream in real-time.

---

## 📦 Scenario 1: GENERATE (Create New Project)

### 1.1 Generate with Anthropic Claude (POST)

**Method:** `POST`  
**URL:** `{{BASE_URL}}/api/stream`  
**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "prompt": "Create a landing page for a coffee shop called Bean Dreams",
  "event_type": "generate",
  "model_family": "Anthropic",
  "model_name": "claude-opus-4-5-20251101",
  "business_name": "Bean Dreams",
  "tagline": "Where every cup tells a story",
  "website_type": "Landing Page",
  "color_scheme": "Modern Dark",
  "key_features": [
    "Artisan Coffee",
    "Fresh Pastries",
    "Cozy Atmosphere"
  ],
  "sections": [
    "Hero",
    "About Us",
    "Products",
    "Contact"
  ],
  "email": "hello@beandreams.com",
  "phone": "+1-555-0123"
}
```

---

### 1.2 Generate with OpenAI GPT-4 (POST)

**Method:** `POST`  
**URL:** `{{BASE_URL}}/api/stream`  
**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "prompt": "Create a modern portfolio website for a photographer",
  "event_type": "generate",
  "model_family": "OpenAI",
  "model_name": "gpt-4",
  "business_name": "John Doe Photography",
  "tagline": "Capturing moments that matter",
  "website_type": "Portfolio",
  "color_scheme": "Clean Light",
  "key_features": [
    "Photo Gallery",
    "About Me",
    "Client Testimonials",
    "Contact Form"
  ],
  "email": "contact@johndoe.com"
}
```

---

### 1.3 Generate with OpenAI GPT-5.2 (POST)

**Method:** `POST`  
**URL:** `{{BASE_URL}}/api/stream`  
**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "prompt": "Create a restaurant website with online menu",
  "event_type": "generate",
  "model_family": "OpenAI",
  "model_name": "gpt-5.2",
  "business_name": "Tasty Bites Restaurant",
  "tagline": "Delicious food, memorable experience",
  "website_type": "Landing Page",
  "color_scheme": "Vibrant & Colorful",
  "key_features": [
    "Menu Showcase",
    "Reservation System",
    "Chef's Specials",
    "Location Map"
  ],
  "sections": [
    "Hero",
    "Menu",
    "About",
    "Reservations",
    "Contact"
  ],
  "email": "info@tastybites.com",
  "phone": "+1-555-9876"
}
```

---

### 1.4 Generate - Simple (Minimal Payload)

**Method:** `POST`  
**URL:** `{{BASE_URL}}/api/stream`  
**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "prompt": "Create a simple blog website",
  "event_type": "generate",
  "model_family": "Anthropic",
  "model_name": "claude-sonnet-4-20250514"
}
```

---

### 1.5 Generate with GET Request

**Method:** `GET`  
**URL:** 
```
{{BASE_URL}}/api/stream?prompt=Create a bakery website&event_type=generate&model_family=Anthropic&model_name=claude-opus-4-5-20251101&business_name=Sweet Treats Bakery&website_type=Landing Page&color_scheme=Clean Light
```

**Headers:**
```
Accept: text/event-stream
```

---

## 🔧 Scenario 2: MODIFY (Modify Existing Project)

### 2.1 Modify with Anthropic Claude (POST)

**Method:** `POST`  
**URL:** `{{BASE_URL}}/api/stream`  
**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "prompt": "Change the hero section text to 'Welcome to Paradise' and make the buttons blue",
  "project_id": "project_v1_20250108_120000",
  "event_type": "modify",
  "model_family": "Anthropic",
  "model_name": "claude-sonnet-4-20250514"
}
```

**Note:** Replace `project_v1_20250108_120000` with an actual project ID from your first generate request.

---

### 2.2 Modify with OpenAI GPT-4 (POST)

**Method:** `POST`  
**URL:** `{{BASE_URL}}/api/stream`  
**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "prompt": "Update the color scheme to dark mode with purple accents",
  "project_id": "project_v1_20250108_120000",
  "event_type": "modify",
  "model_family": "OpenAI",
  "model_name": "gpt-4"
}
```

---

### 2.3 Modify with OpenAI GPT-5.2 (POST)

**Method:** `POST`  
**URL:** `{{BASE_URL}}/api/stream`  
**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "prompt": "Add a new 'Testimonials' section with three customer reviews",
  "project_id": "project_v1_20250108_120000",
  "event_type": "modify",
  "model_family": "OpenAI",
  "model_name": "gpt-5.2"
}
```

---

### 2.4 Modify Latest Project (No project_id)

**Method:** `POST`  
**URL:** `{{BASE_URL}}/api/stream`  
**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "prompt": "Change the main heading to 'Experience Excellence' and update the tagline",
  "event_type": "modify",
  "model_family": "Anthropic",
  "model_name": "claude-opus-4-5-20251101"
}
```

**Note:** When `project_id` is `null` or omitted, it automatically uses the latest generated project.

---

### 2.5 Modify with GET Request

**Method:** `GET`  
**URL:** 
```
{{BASE_URL}}/api/stream?prompt=Make all buttons green&project_id=project_v1_20250108_120000&event_type=modify&model_family=OpenAI&model_name=gpt-4
```

**Headers:**
```
Accept: text/event-stream
```

---

## 📋 Complete Postman Collection (JSON Import)

Save this as `unified-api-collection.json` and import into Postman:

```json
{
  "info": {
    "name": "Unified API - Multi-Provider",
    "description": "Test collection for unified streaming API with multiple AI providers",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "BASE_URL",
      "value": "http://localhost:8000",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "GENERATE Scenarios",
      "item": [
        {
          "name": "1. Generate with Claude Opus",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"prompt\": \"Create a landing page for a coffee shop called Bean Dreams\",\n  \"event_type\": \"generate\",\n  \"model_family\": \"Anthropic\",\n  \"model_name\": \"claude-opus-4-5-20251101\",\n  \"business_name\": \"Bean Dreams\",\n  \"tagline\": \"Where every cup tells a story\",\n  \"website_type\": \"Landing Page\",\n  \"color_scheme\": \"Modern Dark\",\n  \"key_features\": [\n    \"Artisan Coffee\",\n    \"Fresh Pastries\",\n    \"Cozy Atmosphere\"\n  ],\n  \"email\": \"hello@beandreams.com\"\n}"
            },
            "url": {
              "raw": "{{BASE_URL}}/api/stream",
              "host": ["{{BASE_URL}}"],
              "path": ["api", "stream"]
            }
          }
        },
        {
          "name": "2. Generate with OpenAI GPT-4",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"prompt\": \"Create a modern portfolio website for a photographer\",\n  \"event_type\": \"generate\",\n  \"model_family\": \"OpenAI\",\n  \"model_name\": \"gpt-4\",\n  \"business_name\": \"John Doe Photography\",\n  \"tagline\": \"Capturing moments that matter\",\n  \"website_type\": \"Portfolio\",\n  \"color_scheme\": \"Clean Light\"\n}"
            },
            "url": {
              "raw": "{{BASE_URL}}/api/stream",
              "host": ["{{BASE_URL}}"],
              "path": ["api", "stream"]
            }
          }
        },
        {
          "name": "3. Generate with OpenAI GPT-5.2",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"prompt\": \"Create a restaurant website with online menu\",\n  \"event_type\": \"generate\",\n  \"model_family\": \"OpenAI\",\n  \"model_name\": \"gpt-5.2\",\n  \"business_name\": \"Tasty Bites Restaurant\",\n  \"website_type\": \"Landing Page\",\n  \"color_scheme\": \"Vibrant & Colorful\"\n}"
            },
            "url": {
              "raw": "{{BASE_URL}}/api/stream",
              "host": ["{{BASE_URL}}"],
              "path": ["api", "stream"]
            }
          }
        },
        {
          "name": "4. Generate - Simple (GET)",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Accept",
                "value": "text/event-stream"
              }
            ],
            "url": {
              "raw": "{{BASE_URL}}/api/stream?prompt=Create a bakery website&event_type=generate&model_family=Anthropic&model_name=claude-opus-4-5-20251101",
              "host": ["{{BASE_URL}}"],
              "path": ["api", "stream"],
              "query": [
                {
                  "key": "prompt",
                  "value": "Create a bakery website"
                },
                {
                  "key": "event_type",
                  "value": "generate"
                },
                {
                  "key": "model_family",
                  "value": "Anthropic"
                },
                {
                  "key": "model_name",
                  "value": "claude-opus-4-5-20251101"
                }
              ]
            }
          }
        }
      ]
    },
    {
      "name": "MODIFY Scenarios",
      "item": [
        {
          "name": "1. Modify with Claude",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"prompt\": \"Change the hero section text to 'Welcome to Paradise' and make the buttons blue\",\n  \"project_id\": \"project_v1_20250108_120000\",\n  \"event_type\": \"modify\",\n  \"model_family\": \"Anthropic\",\n  \"model_name\": \"claude-sonnet-4-20250514\"\n}"
            },
            "url": {
              "raw": "{{BASE_URL}}/api/stream",
              "host": ["{{BASE_URL}}"],
              "path": ["api", "stream"]
            }
          }
        },
        {
          "name": "2. Modify with OpenAI GPT-4",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"prompt\": \"Update the color scheme to dark mode with purple accents\",\n  \"project_id\": \"project_v1_20250108_120000\",\n  \"event_type\": \"modify\",\n  \"model_family\": \"OpenAI\",\n  \"model_name\": \"gpt-4\"\n}"
            },
            "url": {
              "raw": "{{BASE_URL}}/api/stream",
              "host": ["{{BASE_URL}}"],
              "path": ["api", "stream"]
            }
          }
        },
        {
          "name": "3. Modify Latest Project (No ID)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"prompt\": \"Change the main heading to 'Experience Excellence'\",\n  \"event_type\": \"modify\",\n  \"model_family\": \"Anthropic\",\n  \"model_name\": \"claude-opus-4-5-20251101\"\n}"
            },
            "url": {
              "raw": "{{BASE_URL}}/api/stream",
              "host": ["{{BASE_URL}}"],
              "path": ["api", "stream"]
            }
          }
        }
      ]
    },
    {
      "name": "Utilities",
      "item": [
        {
          "name": "List Supported Models",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{BASE_URL}}/api/models",
              "host": ["{{BASE_URL}}"],
              "path": ["api", "models"]
            }
          }
        },
        {
          "name": "Health Check",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{BASE_URL}}/health",
              "host": ["{{BASE_URL}}"],
              "path": ["health"]
            }
          }
        },
        {
          "name": "List All Projects",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{BASE_URL}}/api/projects",
              "host": ["{{BASE_URL}}"],
              "path": ["api", "projects"]
            }
          }
        }
      ]
    }
  ]
}
```

---

## 🎯 Step-by-Step Testing Guide

### Step 1: Start the Server

```bash
cd /Users/rkguptayotta.com/Desktop/codes/api_approach/claude_v2_event_api
source event_api/bin/activate
uvicorn api.main:app --reload --port 8000
```

### Step 2: Open Postman

1. Create a new request
2. Set base URL: `http://localhost:8000`

### Step 3: Test GENERATE (Scenario 1)

1. **Method:** POST
2. **URL:** `http://localhost:8000/api/stream`
3. **Headers:** `Content-Type: application/json`
4. **Body:** Copy any "Generate" payload from above
5. **Send** - You'll see SSE events streaming in

### Step 4: Get Project ID

From the response, look for the `project.saved` event:
```json
{
  "event_type": "project.saved",
  "payload": {
    "project_id": "project_v1_20250108_120000",
    "model_used": "Anthropic/claude-opus-4-5-20251101"
  }
}
```

Copy the `project_id` value.

### Step 5: Test MODIFY (Scenario 2)

1. **Method:** POST
2. **URL:** `http://localhost:8000/api/stream`
3. **Headers:** `Content-Type: application/json`
4. **Body:** Use any "Modify" payload, but replace the `project_id` with your copied ID
5. **Send** - You'll see modification events streaming

---

## 📊 Expected Response Format

### SSE Stream Format:
```
data: {"event_type": "thinking.start", "payload": {}}

data: {"event_type": "chat.message", "payload": {"content": "🧠 Using OpenAI gpt-5.2..."}}

data: {"event_type": "progress.init", "payload": {"mode": "modal"}}

data: {"event_type": "fs.write", "payload": {"path": "src/App.tsx", "language": "typescript"}}

data: {"event_type": "project.saved", "payload": {"project_id": "project_v1_20250108_120000", "model_used": "OpenAI/gpt-5.2"}}

data: {"event_type": "stream.complete", "payload": {}}
```

---

## 🔍 Verify Model Used

In the `project.saved` event, check the `model_used` field:

```json
{
  "event_type": "project.saved",
  "payload": {
    "project_id": "project_v1_20250108_152030",
    "model_used": "OpenAI/gpt-5.2",  // ✅ Confirms which model was used
    "files": ["index.html", "src/main.tsx", "src/App.tsx", "src/index.css"]
  }
}
```

---

## ⚠️ Important Notes

### 1. Environment Variables
Make sure these are set:
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
export OPENAI_API_KEY=sk-...
```

### 2. Project IDs
- For MODIFY requests, use a valid `project_id` from a previous GENERATE
- Or omit `project_id` to use the latest project

### 3. Model Names
- **Anthropic**: `claude-opus-4-5-20251101`, `claude-sonnet-4-20250514`
- **OpenAI**: `gpt-4`, `gpt-5.2`, `gpt-3.5-turbo`

### 4. SSE in Postman
- Postman will show SSE events in the response body
- Events come in real-time as they're generated
- Look for `stream.complete` to know when done

---

## 🎉 Quick Copy-Paste Tests

### Test 1: Generate with Claude
```json
{
  "prompt": "Create a landing page for a tech startup",
  "event_type": "generate",
  "model_family": "Anthropic",
  "model_name": "claude-opus-4-5-20251101",
  "business_name": "TechFlow",
  "website_type": "Landing Page"
}
```

### Test 2: Generate with OpenAI
```json
{
  "prompt": "Create a blog website about travel",
  "event_type": "generate",
  "model_family": "OpenAI",
  "model_name": "gpt-4",
  "business_name": "Wanderlust Blog",
  "website_type": "Blog"
}
```

### Test 3: Modify with Any Model
```json
{
  "prompt": "Make the buttons bigger and change their color to green",
  "event_type": "modify",
  "model_family": "OpenAI",
  "model_name": "gpt-4"
}
```

---

**Ready to test!** 🚀 Just copy any payload above and paste into Postman!

