"""
FastAPI Main Application
AI Project Generator with SSE Streaming Events

Run with: uvicorn api.main:app --reload --port 8000
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Import routes
from api.routes import generate, projects, chat, unified
from api.schemas import HealthResponse


# ==========================================================
# LIFESPAN (Startup/Shutdown)
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("🚀 Starting AI Project Generator API...")
    
    # Ensure output directories exist
    Path("output").mkdir(exist_ok=True)
    Path("modified_output").mkdir(exist_ok=True)
    
    # Check for API keys (optional - only needed if using that provider)
    if os.getenv("GOOGLE_API_KEY"):
        print("✅ Google Gemini API key configured")
    if os.getenv("ANTHROPIC_API_KEY"):
        print("✅ Anthropic Claude API key configured")
    if os.getenv("OPENAI_API_KEY"):
        print("✅ OpenAI API key configured")
    if not any([os.getenv("GOOGLE_API_KEY"), os.getenv("ANTHROPIC_API_KEY"), os.getenv("OPENAI_API_KEY")]):
        print("⚠️  WARNING: No AI provider API keys found! Set GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY")
    
    print(" API ready at http://localhost:8000")
    print("Docs at http://localhost:8000/docs")
    
    yield
    
    # Shutdown
    print(" Shutting down API...")


# ==========================================================
# CREATE APP
# ==========================================================

app = FastAPI(
    title="AI Project Generator API",
    description="""
## AI Project Generator with Real-Time Streaming Events

This API allows you to generate and modify web projects using AI, with real-time event streaming via SSE (Server-Sent Events).

### Features:
- **Generate Projects**: Create complete React/Vite projects from natural language descriptions
- **Modify Projects**: Make changes to existing projects with AI assistance
- **Real-Time Events**: Stream progress updates via SSE for engaging UX
- **Intent Detection**: Automatically classify user intent
- **Chat**: Have conversations with the AI

### Event Types (SSE):
- `thinking.start` / `thinking.end` - AI thinking indicator
- `progress.init` / `progress.update` - Build progress steps
- `chat.message` - Narration messages
- `fs.create` / `fs.write` - File operations
- `edit.start` / `edit.end` - File editing status
- `build.start` / `build.log` - Build process
- `stream.complete` - Generation finished

### Quick Start:
```javascript
// Connect to SSE stream
const eventSource = new EventSource('/api/generate/stream?prompt=Create a landing page');
eventSource.onmessage = (e) => {
    const event = JSON.parse(e.data);
    console.log(event.event_type, event.payload);
};
```
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ==========================================================
# CORS MIDDLEWARE
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# INCLUDE ROUTERS
# ==========================================================

# Unified API (recommended for new integrations)
app.include_router(unified.router, prefix="/api", tags=["Unified API"])

# Legacy endpoints (still supported)
app.include_router(generate.router, prefix="/api", tags=["Generation"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(chat.router, prefix="/api", tags=["Chat & Classification"])


# ==========================================================
# ROOT ENDPOINTS
# ==========================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "AI Project Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


# ==========================================================
# RUN DIRECTLY
# ==========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

