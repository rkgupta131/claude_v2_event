"""
Phase 1 - Streaming Event System
Lovable-Style No-Code Builder Events

This module defines all streaming events as per the Phase1_LLM_Streaming_Contract.
Events keep users engaged during webpage generation with real-time feedback.
"""

import uuid
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Callable
from enum import Enum


# ==========================================================
# EVENT TYPES ENUM
# ==========================================================

class EventType(str, Enum):
    # Chat & Cognition
    CHAT_MESSAGE = "chat.message"
    THINKING_START = "thinking.start"
    THINKING_END = "thinking.end"
    
    # Progress & Planning
    PROGRESS_INIT = "progress.init"
    PROGRESS_UPDATE = "progress.update"
    PROGRESS_TRANSITION = "progress.transition"
    
    # Filesystem
    FS_CREATE = "fs.create"
    FS_WRITE = "fs.write"
    FS_DELETE = "fs.delete"
    
    # Edit Timeline
    EDIT_READ = "edit.read"
    EDIT_START = "edit.start"
    EDIT_END = "edit.end"
    EDIT_SECURITY_CHECK = "edit.security_check"
    
    # Build & Preview
    BUILD_START = "build.start"
    BUILD_LOG = "build.log"
    BUILD_ERROR = "build.error"
    PREVIEW_READY = "preview.ready"
    
    # Versions
    VERSION_CREATED = "version.created"
    VERSION_DEPLOYED = "version.deployed"
    
    # Suggestions & UI
    SUGGESTION = "suggestion"
    UI_MULTISELECT = "ui.multiselect"
    
    # Errors
    ERROR = "error"
    
    # Stream Lifecycle
    STREAM_COMPLETE = "stream.complete"
    STREAM_AWAIT_INPUT = "stream.await_input"
    STREAM_FAILED = "stream.failed"


class ProgressStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ==========================================================
# EVENT DATA CLASSES
# ==========================================================

@dataclass
class ProgressStep:
    id: str
    label: str
    status: str = "pending"
    
    def to_dict(self):
        return {"id": self.id, "label": self.label, "status": self.status}


@dataclass
class StreamEvent:
    """Universal Event Envelope"""
    event_type: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    project_id: str = "proj_current"
    conversation_id: str = "conv_current"
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "project_id": self.project_id,
            "conversation_id": self.conversation_id,
            "payload": self.payload
        }


# ==========================================================
# EVENT EMITTER CLASS
# ==========================================================

class StreamEventEmitter:
    """
    Manages streaming events during project generation.
    Collects events and provides callbacks for real-time UI updates.
    """
    
    # Default progress steps for a new build
    DEFAULT_STEPS = [
        ProgressStep("plan", "Planning"),
        ProgressStep("scaffold", "Scaffolding"),
        ProgressStep("deps", "Dependencies"),
        ProgressStep("code", "Code Generation"),
        ProgressStep("build", "Build"),
        ProgressStep("verify", "Verification"),
    ]
    
    def __init__(self, callback: Optional[Callable[[StreamEvent], None]] = None):
        """
        Initialize the event emitter.
        
        Args:
            callback: Optional function called for each emitted event.
                     Used for real-time UI updates.
        """
        self.events: List[StreamEvent] = []
        self.callback = callback
        self.thinking_start_time: Optional[float] = None
        self.current_step: Optional[str] = None
        self.steps: List[ProgressStep] = []
        self.project_id = f"proj_{uuid.uuid4().hex[:6]}"
        self.conversation_id = f"conv_{uuid.uuid4().hex[:6]}"
    
    def _emit(self, event_type: EventType, payload: Dict[str, Any]) -> StreamEvent:
        """Internal method to emit an event."""
        event = StreamEvent(
            event_type=event_type.value,
            payload=payload,
            project_id=self.project_id,
            conversation_id=self.conversation_id
        )
        self.events.append(event)
        
        if self.callback:
            self.callback(event)
        
        return event
    
    # ==========================================================
    # THINKING EVENTS
    # ==========================================================
    
    def thinking_start(self) -> StreamEvent:
        """Emit thinking.start - Show 'Thinking...' indicator."""
        self.thinking_start_time = time.time()
        return self._emit(EventType.THINKING_START, {})
    
    def thinking_end(self) -> StreamEvent:
        """Emit thinking.end - Show 'Thought for X seconds'."""
        duration_ms = 0
        if self.thinking_start_time:
            duration_ms = int((time.time() - self.thinking_start_time) * 1000)
        return self._emit(EventType.THINKING_END, {"duration_ms": duration_ms})
    
    # ==========================================================
    # CHAT EVENTS
    # ==========================================================
    
    def chat_message(self, content: str) -> StreamEvent:
        """Emit chat.message - Human-readable narration."""
        return self._emit(EventType.CHAT_MESSAGE, {"content": content})
    
    # ==========================================================
    # PROGRESS EVENTS
    # ==========================================================
    
    def progress_init(self, mode: str = "modal", steps: Optional[List[ProgressStep]] = None) -> StreamEvent:
        """
        Emit progress.init - Initialize progress visualization.
        
        Args:
            mode: "modal" or "inline"
            steps: List of progress steps. Uses defaults if not provided.
        """
        # IMPORTANT: Always create NEW steps with "pending" status
        # Don't copy status from DEFAULT_STEPS as they may have been modified
        if steps:
            self.steps = [ProgressStep(s.id, s.label, "pending") for s in steps]
        else:
            self.steps = [ProgressStep(s.id, s.label, "pending") for s in self.DEFAULT_STEPS]
        
        return self._emit(EventType.PROGRESS_INIT, {
            "mode": mode,
            "steps": [s.to_dict() for s in self.steps]
        })
    
    def progress_update(self, step_id: str, status: str) -> StreamEvent:
        """
        Emit progress.update - Update a step's status.
        
        Args:
            step_id: ID of the step to update
            status: New status (pending, in_progress, completed, failed)
        """
        # Update internal state
        for step in self.steps:
            if step.id == step_id:
                step.status = status
                break
        
        self.current_step = step_id if status == "in_progress" else self.current_step
        return self._emit(EventType.PROGRESS_UPDATE, {
            "step_id": step_id,
            "status": status
        })
    
    def progress_transition(self, mode: str) -> StreamEvent:
        """Emit progress.transition - Transition from modal to inline."""
        return self._emit(EventType.PROGRESS_TRANSITION, {"mode": mode})
    
    # ==========================================================
    # FILESYSTEM EVENTS
    # ==========================================================
    
    def fs_create(self, path: str, kind: str = "folder") -> StreamEvent:
        """
        Emit fs.create - Create a folder/file.
        
        Args:
            path: Path to create
            kind: "folder" or "file"
        """
        return self._emit(EventType.FS_CREATE, {
            "path": path,
            "kind": kind
        })
    
    def fs_write(self, path: str, content: str, language: str = "typescript") -> StreamEvent:
        """
        Emit fs.write - Write file content.
        This is the SINGLE SOURCE OF TRUTH for code.
        
        Args:
            path: File path
            content: File content (full content, not truncated)
            language: Programming language
        """
        return self._emit(EventType.FS_WRITE, {
            "path": path,
            "kind": "file",
            "language": language,
            "content": content
        })
    
    def fs_delete(self, path: str) -> StreamEvent:
        """Emit fs.delete - Delete a file."""
        return self._emit(EventType.FS_DELETE, {"path": path})
    
    # ==========================================================
    # EDIT TIMELINE EVENTS
    # ==========================================================
    
    def edit_read(self, path: str) -> StreamEvent:
        """Emit edit.read - Reading a file."""
        return self._emit(EventType.EDIT_READ, {"path": path})
    
    def edit_start(self, path: str, content: str = "") -> StreamEvent:
        """
        Emit edit.start - Start editing a file.
        Can be emitted multiple times for typing animation.
        """
        return self._emit(EventType.EDIT_START, {
            "path": path,
            "content": content
        })
    
    def edit_end(self, path: str, duration_ms: int) -> StreamEvent:
        """Emit edit.end - Finished editing a file."""
        return self._emit(EventType.EDIT_END, {
            "path": path,
            "duration_ms": duration_ms
        })
    
    def edit_security_check(self, path: str, status: str = "passed") -> StreamEvent:
        """Emit edit.security_check - Security validation result."""
        return self._emit(EventType.EDIT_SECURITY_CHECK, {
            "path": path,
            "status": status
        })
    
    # ==========================================================
    # BUILD & PREVIEW EVENTS
    # ==========================================================
    
    def build_start(self, container_id: str = "ctr_001") -> StreamEvent:
        """Emit build.start - Build process started."""
        return self._emit(EventType.BUILD_START, {"container_id": container_id})
    
    def build_log(self, message: str, level: str = "info") -> StreamEvent:
        """Emit build.log - Build log message."""
        return self._emit(EventType.BUILD_LOG, {
            "level": level,
            "message": message
        })
    
    def build_error(self, message: str, details: str = "") -> StreamEvent:
        """Emit build.error - Build failed."""
        return self._emit(EventType.BUILD_ERROR, {
            "message": message,
            "details": details
        })
    
    def preview_ready(self, url: str, port: int = 5173) -> StreamEvent:
        """Emit preview.ready - Preview URL is available."""
        return self._emit(EventType.PREVIEW_READY, {
            "url": url,
            "port": port
        })
    
    # ==========================================================
    # VERSION EVENTS
    # ==========================================================
    
    def version_created(self, version_id: str, label: str = "", status: str = "stable") -> StreamEvent:
        """Emit version.created - New version created."""
        return self._emit(EventType.VERSION_CREATED, {
            "version_id": version_id,
            "label": label,
            "status": status
        })
    
    def version_deployed(self, version_id: str, environment: str = "preview") -> StreamEvent:
        """Emit version.deployed - Version deployed."""
        return self._emit(EventType.VERSION_DEPLOYED, {
            "version_id": version_id,
            "environment": environment
        })
    
    # ==========================================================
    # SUGGESTION & UI EVENTS
    # ==========================================================
    
    def suggestion(self, id: str, label: str, options: List[str]) -> StreamEvent:
        """Emit suggestion - Show next action suggestions."""
        return self._emit(EventType.SUGGESTION, {
            "id": id,
            "label": label,
            "options": options
        })
    
    def ui_multiselect(self, id: str, title: str, options: List[Dict[str, str]]) -> StreamEvent:
        """Emit ui.multiselect - Show multi-select modal."""
        return self._emit(EventType.UI_MULTISELECT, {
            "id": id,
            "title": title,
            "options": options
        })
    
    # ==========================================================
    # ERROR EVENTS
    # ==========================================================
    
    def error(self, message: str, scope: str = "llm", details: str = "", 
              actions: Optional[List[str]] = None) -> StreamEvent:
        """Emit error - Error occurred."""
        return self._emit(EventType.ERROR, {
            "scope": scope,
            "message": message,
            "details": details,
            "actions": actions or ["retry", "ask_user"]
        })
    
    # ==========================================================
    # STREAM LIFECYCLE EVENTS
    # ==========================================================
    
    def stream_complete(self) -> StreamEvent:
        """Emit stream.complete - Stream finished successfully."""
        return self._emit(EventType.STREAM_COMPLETE, {})
    
    def stream_await_input(self, reason: str = "suggestion") -> StreamEvent:
        """Emit stream.await_input - Waiting for user input."""
        return self._emit(EventType.STREAM_AWAIT_INPUT, {"reason": reason})
    
    def stream_failed(self) -> StreamEvent:
        """Emit stream.failed - Stream failed."""
        return self._emit(EventType.STREAM_FAILED, {})
    
    # ==========================================================
    # UTILITY METHODS
    # ==========================================================
    
    def get_all_events(self) -> List[Dict]:
        """Get all events as dictionaries."""
        return [e.to_dict() for e in self.events]
    
    def get_events_by_type(self, event_type: EventType) -> List[StreamEvent]:
        """Get events filtered by type."""
        return [e for e in self.events if e.event_type == event_type.value]
    
    def clear(self):
        """Clear all events."""
        self.events = []
        self.thinking_start_time = None
        self.current_step = None


# ==========================================================
# HELPER FUNCTION FOR FILE LANGUAGE DETECTION
# ==========================================================

def detect_language(path: str) -> str:
    """Detect programming language from file path."""
    ext_map = {
        ".tsx": "typescript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".js": "javascript",
        ".css": "css",
        ".html": "html",
        ".json": "json",
        ".py": "python",
        ".md": "markdown",
    }
    for ext, lang in ext_map.items():
        if path.endswith(ext):
            return lang
    return "plaintext"


# ==========================================================
# CONVENIENCE FUNCTION FOR QUICK SETUP
# ==========================================================

def create_emitter(callback: Optional[Callable] = None) -> StreamEventEmitter:
    """Create a new event emitter with optional callback."""
    return StreamEventEmitter(callback=callback)

