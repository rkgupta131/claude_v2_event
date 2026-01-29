"""
Generation Routes with SSE Streaming
Handles project generation and modification with real-time events
"""

import json
import asyncio
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, AsyncGenerator
from queue import Queue
from threading import Thread

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from api.schemas import GenerateRequest, ModifyRequest, ErrorResponse

# Import core modules
from events.stream_events import StreamEventEmitter, create_emitter
from models.model_router import ModelRouter

router = APIRouter()

# Directories
OUTPUT_DIR = Path("output")
MODIFIED_DIR = Path("modified_output")


# ==========================================================
# HELPERS
# ==========================================================

def get_latest_project(folder: Path):
    """Get the most recent project file from a folder."""
    files = sorted(folder.glob("project_v*.json"))
    return files[-1] if files else None


def get_next_version(folder: Path):
    """Get the next version number for a project."""
    versions = []
    for f in folder.glob("project_v*.json"):
        try:
            versions.append(int(f.stem.split("_v")[1].split("_")[0]))
        except:
            pass
    return max(versions, default=0) + 1


def validate_project(project: dict):
    """Validate project structure."""
    if "project" not in project:
        raise ValueError("Missing project key")
    files = project["project"]["files"]
    if "index.html" not in files:
        raise ValueError("Missing index.html")
    for f in ["src/main.tsx", "src/App.tsx"]:
        if f not in files:
            raise ValueError(f"Missing required file {f}")


def save_project(project: dict, is_modification: bool, base_version=None, modified_files=None):
    """Save project to disk."""
    folder = MODIFIED_DIR if is_modification else OUTPUT_DIR
    folder.mkdir(exist_ok=True)
    
    version = get_next_version(folder)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    final_data = {
        "metadata": {
            "version": version,
            "timestamp": timestamp,
            "is_modification": is_modification,
            "base_version": base_version,
            "modified_files": modified_files or [],
            "created_at": datetime.now().isoformat()
        },
        **project
    }

    path = folder / f"project_v{version}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)

    return path, final_data


def apply_patch(base_project: dict, patch: dict):
    """Apply a patch to a base project."""
    files = base_project["project"]["files"]
    modified = []

    for path, content in patch.get("modified_files", {}).items():
        if path not in files:
            files[path] = {"content": content}
        else:
            if isinstance(files[path], dict):
                files[path]["content"] = content
            else:
                files[path] = {"content": content}
        modified.append(path)

    for path, content in patch.get("new_files", {}).items():
        files[path] = {"content": content}
        modified.append(path)

    for path in patch.get("deleted_files", []):
        if path in files:
            files.pop(path)
            modified.append(path)

    return base_project, modified


def build_enhanced_prompt(request: GenerateRequest) -> str:
    """Build an enhanced prompt from request parameters."""
    if not any([request.business_name, request.website_type, request.key_features]):
        return request.prompt
    
    parts = [f"Create a {request.website_type or 'landing page'} website"]
    
    if request.business_name:
        parts.append(f"for: {request.business_name}")
    
    if request.tagline:
        parts.append(f"\nTagline: {request.tagline}")
    
    if request.key_features:
        parts.append("\n\nKey Features/Products:")
        for feature in request.key_features:
            parts.append(f"- {feature}")
    
    if request.sections:
        parts.append(f"\n\nRequired Sections: {', '.join(request.sections)}")
    
    if request.color_scheme:
        parts.append(f"\n\nDesign Style: {request.color_scheme}")
    
    if request.email or request.phone:
        parts.append("\n\nContact Info:")
        if request.email:
            parts.append(f"- Email: {request.email}")
        if request.phone:
            parts.append(f"- Phone: {request.phone}")
    
    if request.additional_info:
        parts.append(f"\n\nAdditional Requirements: {request.additional_info}")
    
    parts.append(f"\n\nOriginal request: {request.prompt}")
    parts.append("\n\nPlease create a modern, professional, and visually appealing website with smooth animations and excellent UX.")
    
    return "\n".join(parts)


# ==========================================================
# SSE EVENT GENERATOR
# ==========================================================

async def generate_sse_events(
    prompt: str,
    is_modification: bool = False,
    base_project: dict = None,
    base_file_name: str = None
) -> AsyncGenerator[str, None]:
    """
    Generate SSE events during project generation.
    Yields events in SSE format: data: {json}\n\n
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
            emitter = create_emitter(callback=event_callback)
            
            if is_modification and base_project:
                # Use model router with Google as default (legacy route)
                provider = ModelRouter.get_provider("Google", "gemini-1.5-flash")
                patch = provider.generate_patch(prompt, base_project, emitter=emitter)
                result_holder["patch"] = patch
            else:
                # Use model router with Google as default (legacy route)
                provider = ModelRouter.get_provider("Google", "gemini-1.5-flash")
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
                    "details": ""
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
            # Poll queue with timeout to allow async context switching
            await asyncio.sleep(0.01)
            
            if not event_queue.empty():
                event = event_queue.get_nowait()
                
                if event is None:
                    # Generation complete
                    break
                
                # Yield SSE formatted event
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            await asyncio.sleep(0.05)
    
    # Wait for thread to complete
    thread.join(timeout=5.0)
    
    # Handle results
    if result_holder["error"]:
        error_event = {
            "event_type": "stream.failed",
            "payload": {"error": result_holder["error"]}
        }
        yield f"data: {json.dumps(error_event)}\n\n"
        return
    
    # Save project and emit final event
    try:
        if is_modification and result_holder["patch"]:
            patch = result_holder["patch"]
            patched_project, modified_files = apply_patch(base_project, patch)
            validate_project(patched_project)
            
            # Get base version
            base_version = None
            path, saved_data = save_project(
                patched_project, 
                is_modification=True,
                base_version=base_version,
                modified_files=modified_files
            )
            
            # Emit project saved event
            saved_event = {
                "event_type": "project.saved",
                "payload": {
                    "project_id": path.stem,
                    "path": str(path),
                    "is_modification": True,
                    "files_modified": modified_files,
                    "sections_changed": patch.get("sections_changed", [])
                }
            }
            yield f"data: {json.dumps(saved_event)}\n\n"
            
        elif result_holder["project"]:
            project = result_holder["project"]
            validate_project(project)
            path, saved_data = save_project(project, is_modification=False)
            
            # Emit project saved event
            saved_event = {
                "event_type": "project.saved",
                "payload": {
                    "project_id": path.stem,
                    "path": str(path),
                    "is_modification": False,
                    "files": list(project["project"]["files"].keys())
                }
            }
            yield f"data: {json.dumps(saved_event)}\n\n"
            
    except Exception as e:
        error_event = {
            "event_type": "error",
            "payload": {"message": f"Failed to save project: {str(e)}"}
        }
        yield f"data: {json.dumps(error_event)}\n\n"


# ==========================================================
# ENDPOINTS
# ==========================================================

@router.post("/generate", tags=["Generation"])
async def generate_project_endpoint(request: GenerateRequest):
    """
    Generate a new project (non-streaming).
    Returns the complete project after generation.
    
    For real-time updates, use GET /generate/stream instead.
    """
    try:
        prompt = build_enhanced_prompt(request)
        # Use model router with Google as default (legacy route)
        provider = ModelRouter.get_provider("Google", "gemini-1.5-flash")
        project = provider.generate_project(prompt)
        validate_project(project)
        path, saved_data = save_project(project, is_modification=False)
        
        return {
            "success": True,
            "project_id": path.stem,
            "path": str(path),
            "files": list(project["project"]["files"].keys()),
            "metadata": saved_data.get("metadata", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate/stream", tags=["Generation"])
async def generate_project_stream(
    prompt: str = Query(..., description="Description of the website to create", min_length=1),
    business_name: Optional[str] = Query(None, description="Business name"),
    website_type: Optional[str] = Query(None, description="Type of website"),
    color_scheme: Optional[str] = Query(None, description="Color scheme preference")
):
    """
    Generate a new project with SSE streaming.
    
    **Connect via EventSource:**
    ```javascript
    const eventSource = new EventSource('/api/generate/stream?prompt=Create a landing page');
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Event:', data.event_type, data.payload);
        
        switch(data.event_type) {
            case 'thinking.start':
                showThinkingIndicator();
                break;
            case 'progress.update':
                updateProgress(data.payload.step_id, data.payload.status);
                break;
            case 'chat.message':
                addChatMessage(data.payload.content);
                break;
            case 'fs.write':
                showFileWrite(data.payload.path);
                break;
            case 'project.saved':
                showSuccess(data.payload.project_id);
                break;
            case 'stream.complete':
                eventSource.close();
                break;
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
    };
    ```
    """
    # Build simple prompt from query params
    parts = [prompt]
    if business_name:
        parts.append(f"Business: {business_name}")
    if website_type:
        parts.append(f"Type: {website_type}")
    if color_scheme:
        parts.append(f"Style: {color_scheme}")
    
    full_prompt = "\n".join(parts)
    
    return StreamingResponse(
        generate_sse_events(full_prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/generate/stream", tags=["Generation"])
async def generate_project_stream_post(request: GenerateRequest):
    """
    Generate a new project with SSE streaming (POST version).
    Accepts full request body with all options.
    
    Use this when you need to send detailed requirements.
    """
    prompt = build_enhanced_prompt(request)
    
    return StreamingResponse(
        generate_sse_events(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/modify", tags=["Generation"])
async def modify_project_endpoint(request: ModifyRequest):
    """
    Modify an existing project (non-streaming).
    Returns the modified project after completion.
    
    For real-time updates, use POST /modify/stream instead.
    """
    try:
        # Find base project
        if request.project_id:
            # Look for specific project
            base_file = None
            for folder in [MODIFIED_DIR, OUTPUT_DIR]:
                matches = list(folder.glob(f"*{request.project_id}*.json"))
                if matches:
                    base_file = matches[0]
                    break
            if not base_file:
                raise HTTPException(status_code=404, detail=f"Project not found: {request.project_id}")
        else:
            # Use latest project
            base_file = get_latest_project(MODIFIED_DIR) or get_latest_project(OUTPUT_DIR)
            if not base_file:
                raise HTTPException(status_code=404, detail="No existing project found to modify")
        
        # Load base project
        with open(base_file, "r") as f:
            base_data = json.load(f)
        
        base_project = {"project": base_data["project"]}
        
        # Generate patch
        modification_prompt = f"Modify the existing project: {request.prompt}"
        # Use model router with Google as default (legacy route)
        provider = ModelRouter.get_provider("Google", "gemini-1.5-flash")
        patch = provider.generate_patch(modification_prompt, base_project)
        
        # Apply patch
        patched_project, modified_files = apply_patch(base_project, patch)
        validate_project(patched_project)
        
        # Save
        base_version = base_data.get("metadata", {}).get("version")
        path, saved_data = save_project(
            patched_project,
            is_modification=True,
            base_version=base_version,
            modified_files=modified_files
        )
        
        return {
            "success": True,
            "project_id": path.stem,
            "path": str(path),
            "base_project": base_file.stem,
            "files_modified": modified_files,
            "sections_changed": patch.get("sections_changed", []),
            "metadata": saved_data.get("metadata", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modify/stream", tags=["Generation"])
async def modify_project_stream(request: ModifyRequest):
    """
    Modify an existing project with SSE streaming.
    
    **Event flow:**
    1. `thinking.start` - AI analyzing project
    2. `progress.init` - Initialize progress steps
    3. `chat.message` - Status messages
    4. `edit.start/end` - Files being modified
    5. `project.saved` - Modifications saved
    6. `stream.complete` - Done
    """
    try:
        # Find base project
        if request.project_id:
            base_file = None
            for folder in [MODIFIED_DIR, OUTPUT_DIR]:
                matches = list(folder.glob(f"*{request.project_id}*.json"))
                if matches:
                    base_file = matches[0]
                    break
            if not base_file:
                raise HTTPException(status_code=404, detail=f"Project not found: {request.project_id}")
        else:
            base_file = get_latest_project(MODIFIED_DIR) or get_latest_project(OUTPUT_DIR)
            if not base_file:
                raise HTTPException(status_code=404, detail="No existing project found to modify")
        
        # Load base project
        with open(base_file, "r") as f:
            base_data = json.load(f)
        
        base_project = {"project": base_data["project"]}
        modification_prompt = f"Modify the existing project: {request.prompt}"
        
        return StreamingResponse(
            generate_sse_events(
                modification_prompt,
                is_modification=True,
                base_project=base_project,
                base_file_name=base_file.stem
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

