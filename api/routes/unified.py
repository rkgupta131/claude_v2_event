"""
Unified API Endpoint - Single endpoint for all AI operations
Supports multiple AI providers with GET and POST methods
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, AsyncGenerator
from queue import Queue
from threading import Thread

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from api.schemas import UnifiedRequest, ModelFamily, EventType, ErrorResponse

# Import model router
from models.model_router import create_provider

# Import helpers from generate.py
from api.routes.generate import (
    get_latest_project,
    get_next_version,
    validate_project,
    save_project,
    apply_patch,
    build_enhanced_prompt,
    OUTPUT_DIR,
    MODIFIED_DIR,
)

router = APIRouter()


# ==========================================================
# UNIFIED SSE EVENT GENERATOR
# ==========================================================

async def unified_sse_events(
    prompt: str,
    event_type: EventType,
    model_family: ModelFamily,
    model_name: str,
    project_id: Optional[str] = None,
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    Unified SSE event generator that works with any AI provider.
    
    Args:
        prompt: User prompt
        event_type: "generate" or "modify"
        model_family: AI provider (OpenAI, Google, Mistral)
        model_name: Specific model name
        project_id: Required for modify operations
        **kwargs: Additional parameters (business_name, website_type, etc.)
    """
    event_queue: Queue = Queue()
    result_holder = {"project": None, "error": None, "patch": None}
    
    def event_callback(event):
        """Callback that puts events in queue."""
        event_dict = event.to_dict()
        event_queue.put(event_dict)
    
    def run_generation():
        """Run generation in a separate thread."""
        try:
            # Import event emitter
            from events.stream_events import create_emitter
            emitter = create_emitter(callback=event_callback)
            
            # Create AI provider
            provider = create_provider(model_family, model_name)
            
            # Handle based on event type
            if event_type == EventType.MODIFY:
                # Load base project
                if not project_id:
                    # Get latest project
                    base_file = get_latest_project(MODIFIED_DIR) or get_latest_project(OUTPUT_DIR)
                    if not base_file:
                        raise ValueError("No existing project found to modify. Please provide project_id.")
                else:
                    # Find specific project
                    base_file = None
                    for folder in [MODIFIED_DIR, OUTPUT_DIR]:
                        matches = list(folder.glob(f"*{project_id}*.json"))
                        if matches:
                            base_file = matches[0]
                            break
                    if not base_file:
                        raise ValueError(f"Project not found: {project_id}")
                
                # Load project
                with open(base_file, "r") as f:
                    base_data = json.load(f)
                base_project = {"project": base_data["project"]}
                
                # Generate patch
                modification_prompt = f"Modify the existing project: {prompt}"
                patch = provider.generate_patch(modification_prompt, base_project, emitter=emitter)
                result_holder["patch"] = patch
                result_holder["base_project"] = base_project
                result_holder["base_file"] = base_file
                
            else:  # GENERATE
                project = provider.generate_project(prompt, emitter=emitter)
                result_holder["project"] = project
                
        except Exception as e:
            result_holder["error"] = str(e)
            # Emit error event
            error_event = {
                "event_id": "evt_error",
                "event_type": "error",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "project_id": "proj_current",
                "conversation_id": "conv_current",
                "payload": {
                    "scope": "llm",
                    "message": str(e),
                    "details": f"Model: {model_family}/{model_name}"
                }
            }
            event_queue.put(error_event)
        finally:
            event_queue.put(None)  # Signal completion
    
    # Start generation in background thread
    thread = Thread(target=run_generation)
    thread.start()
    
    # Yield events as they come
    while True:
        try:
            await asyncio.sleep(0.01)
            
            if not event_queue.empty():
                event = event_queue.get_nowait()
                
                if event is None:
                    break
                
                # Yield SSE formatted event
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            await asyncio.sleep(0.05)
    
    # Wait for thread
    thread.join(timeout=5.0)
    
    # Handle errors
    if result_holder["error"]:
        error_event = {
            "event_type": "stream.failed",
            "payload": {"error": result_holder["error"]}
        }
        yield f"data: {json.dumps(error_event)}\n\n"
        return
    
    # Save project
    try:
        if event_type == EventType.MODIFY and result_holder["patch"]:
            patch = result_holder["patch"]
            base_project = result_holder["base_project"]
            patched_project, modified_files = apply_patch(base_project, patch)
            validate_project(patched_project)
            
            path, saved_data = save_project(
                patched_project,
                is_modification=True,
                modified_files=modified_files
            )
            
            saved_event = {
                "event_type": "project.saved",
                "payload": {
                    "project_id": path.stem,
                    "path": str(path),
                    "is_modification": True,
                    "files_modified": modified_files,
                    "sections_changed": patch.get("sections_changed", []),
                    "model_used": f"{model_family}/{model_name}"
                }
            }
            yield f"data: {json.dumps(saved_event)}\n\n"
            
        elif result_holder["project"]:
            project = result_holder["project"]
            validate_project(project)
            path, saved_data = save_project(project, is_modification=False)
            
            saved_event = {
                "event_type": "project.saved",
                "payload": {
                    "project_id": path.stem,
                    "path": str(path),
                    "is_modification": False,
                    "files": list(project["project"]["files"].keys()),
                    "model_used": f"{model_family}/{model_name}"
                }
            }
            yield f"data: {json.dumps(saved_event)}\n\n"
            
    except Exception as e:
        error_event = {
            "event_type": "error",
            "payload": {"message": f"Failed to save: {str(e)}"}
        }
        yield f"data: {json.dumps(error_event)}\n\n"


# ==========================================================
# UNIFIED ENDPOINT (GET)
# ==========================================================

@router.get("/stream", tags=["Unified API"])
async def unified_stream_get(
    prompt: str = Query(..., description="Request prompt", min_length=1),
    project_id: Optional[str] = Query(None, description="Project ID (for modify)"),
    event_type: EventType = Query(EventType.GENERATE, description="Operation: generate or modify"),
    model_family: ModelFamily = Query(ModelFamily.GOOGLE, description="AI provider"),
    model_name: str = Query("gemini-1.5-flash", description="Specific model name"),
    business_name: Optional[str] = Query(None, description="Business name"),
    website_type: Optional[str] = Query(None, description="Website type"),
    color_scheme: Optional[str] = Query(None, description="Color scheme"),
):
    """
    **🎯 Unified Streaming Endpoint (GET)**
    
    Single endpoint for all AI operations with real-time SSE streaming.
    
    **Parameters:**
    - `prompt`: What you want to create or modify
    - `project_id`: Project to modify (optional, uses latest if not provided)
    - `event_type`: "generate" (new project) or "modify" (existing project)
    - `model_family`: AI provider - "OpenAI", "Google", "Mistral"
    - `model_name`: Specific model (e.g., "gpt-4", "gemini-1.5-flash")
    
    **Examples:**
    
    ```javascript
    // Generate with Google Gemini
    const url = '/api/stream?' + new URLSearchParams({
        prompt: 'Create a coffee shop landing page',
        event_type: 'generate',
        model_family: 'Google',
        model_name: 'gemini-1.5-flash'
    });
    
    // Generate with OpenAI GPT-4
    const url2 = '/api/stream?' + new URLSearchParams({
        prompt: 'Create a portfolio website',
        event_type: 'generate',
        model_family: 'OpenAI',
        model_name: 'gpt-4'
    });
    
    // Modify with OpenAI GPT-5.2
    const url3 = '/api/stream?' + new URLSearchParams({
        prompt: 'Change hero text to Welcome',
        project_id: 'project_v1_20250101',
        event_type: 'modify',
        model_family: 'OpenAI',
        model_name: 'gpt-5.2'
    });
    
    const eventSource = new EventSource(url);
    eventSource.onmessage = (e) => {
        const event = JSON.parse(e.data);
        console.log(event.event_type, event.payload);
    };
    ```
    
    **Supported Models:**
    - **OpenAI**: gpt-3.5-turbo, gpt-4, gpt-5.2 (when available)
    - **Google**: gemini-1.5-flash, gemini-1.5-pro, gemini-pro
    - **Mistral**: mistral-large-latest (coming soon)
    """
    # Build enhanced prompt if business details provided
    if business_name or website_type or color_scheme:
        # Create a pseudo-request object
        from api.schemas import GenerateRequest
        request_obj = GenerateRequest(
            prompt=prompt,
            business_name=business_name,
            website_type=website_type,
            color_scheme=color_scheme
        )
        full_prompt = build_enhanced_prompt(request_obj)
    else:
        full_prompt = prompt
    
    return StreamingResponse(
        unified_sse_events(
            prompt=full_prompt,
            event_type=event_type,
            model_family=model_family,
            model_name=model_name,
            project_id=project_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ==========================================================
# UNIFIED ENDPOINT (POST)
# ==========================================================

@router.post("/stream", tags=["Unified API"])
async def unified_stream_post(request: UnifiedRequest):
    """
    **🎯 Unified Streaming Endpoint (POST)**
    
    Single endpoint for all AI operations (POST version with full request body).
    
    **Request Body:**
    ```json
    {
        "prompt": "Create a landing page",
        "project_id": null,
        "event_type": "generate",
        "model_family": "OpenAI",
        "model_name": "gpt-5.2",
        "business_name": "Bean Dreams",
        "website_type": "Landing Page",
        "color_scheme": "Modern Dark"
    }
    ```
    
    **Model Examples:**
    - OpenAI: `gpt-4`, `gpt-5.2`, `gpt-3.5-turbo`
    - Google: `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-pro`
    - Mistral: `mistral-large-latest` (coming soon)
    
    **Usage:**
    ```javascript
    const response = await fetch('/api/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: 'Create a bakery website',
            event_type: 'generate',
            model_family: 'OpenAI',
            model_name: 'gpt-5.2'
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value);
        const lines = text.split('\\n\\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const event = JSON.parse(line.slice(6));
                console.log(event.event_type, event.payload);
            }
        }
    }
    ```
    """
    # Build enhanced prompt
    full_prompt = build_enhanced_prompt(request)
    
    return StreamingResponse(
        unified_sse_events(
            prompt=full_prompt,
            event_type=request.event_type,
            model_family=request.model_family,
            model_name=request.model_name,
            project_id=request.project_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ==========================================================
# MODEL INFO ENDPOINT
# ==========================================================

@router.get("/models", tags=["Unified API"])
async def list_supported_models():
    """
    List all supported AI providers and their default models.
    
    **Response:**
    ```json
    {
        "providers": {
            "OpenAI": "gpt-4",
            "Google": "gemini-1.5-flash",
            "Mistral": "mistral-large-latest"
        },
        "examples": {
            "OpenAI": ["gpt-4", "gpt-5.2", "gpt-3.5-turbo"],
            "Google": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        }
    }
    ```
    """
    from models.model_router import get_supported_providers
    
    providers = get_supported_providers()
    
    return {
        "providers": providers,
        "examples": {
            "OpenAI": [
                "gpt-4",
                "gpt-5.2",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ],
            "Google": [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro"
            ],
            "Mistral": [
                "mistral-large-latest",
                "mistral-medium-latest"
            ]
        },
        "note": "Google Gemini is fully supported via Vertex AI. OpenAI is fully supported. Mistral is coming soon."
    }


