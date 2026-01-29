"""
Pydantic Schemas for API Request/Response Validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ==========================================================
# ENUMS
# ==========================================================

class WebsiteType(str, Enum):
    LANDING_PAGE = "Landing Page"
    ECOMMERCE = "E-commerce Shop"
    PORTFOLIO = "Portfolio"
    BLOG = "Blog"
    CORPORATE = "Corporate Website"
    OTHER = "Other"


class ColorScheme(str, Enum):
    MODERN_DARK = "Modern Dark"
    CLEAN_LIGHT = "Clean Light"
    VIBRANT = "Vibrant & Colorful"
    PROFESSIONAL_BLUE = "Professional Blue"
    ELEGANT_PURPLE = "Elegant Purple"
    AI_DECIDE = "Let AI Decide"


class IntentType(str, Enum):
    GREETING = "greeting_only"
    CHAT = "chat"
    WEBPAGE_BUILD = "webpage_build"
    WEBPAGE_MODIFY = "webpage_modify"
    GREETING_AND_WEBPAGE = "greeting_and_webpage"
    ILLEGAL = "illegal"


# ==========================================================
# REQUEST SCHEMAS
# ==========================================================

class GenerateRequest(BaseModel):
    """Request body for generating a new project."""
    prompt: str = Field(..., description="User's request describing what to build", min_length=1)
    
    # Optional detailed requirements
    business_name: Optional[str] = Field(None, description="Business or website name")
    tagline: Optional[str] = Field(None, description="Tagline or main message")
    website_type: Optional[WebsiteType] = Field(None, description="Type of website")
    color_scheme: Optional[ColorScheme] = Field(None, description="Preferred color scheme")
    key_features: Optional[List[str]] = Field(None, description="Key features or products")
    sections: Optional[List[str]] = Field(None, description="Sections to include")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    additional_info: Optional[str] = Field(None, description="Additional requirements")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a landing page for my coffee shop called 'Bean Dreams'",
                "business_name": "Bean Dreams",
                "tagline": "Where every cup tells a story",
                "website_type": "Landing Page",
                "color_scheme": "Modern Dark",
                "key_features": ["Artisan Coffee", "Fresh Pastries", "Cozy Atmosphere"],
                "sections": ["About Us", "Products/Services", "Contact Form"]
            }
        }


class ModifyRequest(BaseModel):
    """Request body for modifying an existing project."""
    prompt: str = Field(..., description="Description of modifications to make", min_length=1)
    project_id: Optional[str] = Field(None, description="ID of project to modify. If not provided, uses latest project.")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Change the hero section text to 'Welcome to Paradise' and make the buttons blue",
                "project_id": "project_v1_20250101_120000"
            }
        }


class ChatRequest(BaseModel):
    """Request body for chat messages."""
    message: str = Field(..., description="User's message", min_length=1)
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    history: Optional[List[Dict[str, str]]] = Field(None, description="Previous messages for context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What frameworks do you support?",
                "conversation_id": "conv_123"
            }
        }


class ClassifyRequest(BaseModel):
    """Request body for intent classification."""
    text: str = Field(..., description="Text to classify", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello! Can you create a website for my bakery?"
            }
        }


class ModelFamily(str, Enum):
    """Supported AI model families."""
    OPENAI = "OpenAI"
    GOOGLE = "Google"
    MISTRAL = "Mistral"


class EventType(str, Enum):
    """Type of operation to perform."""
    GENERATE = "generate"
    MODIFY = "modify"


class UnifiedRequest(BaseModel):
    """Unified request schema for all AI operations."""
    prompt: str = Field(..., description="User's request or modification prompt", min_length=1)
    project_id: Optional[str] = Field(None, description="Project ID (required for modify event_type)")
    event_type: EventType = Field(EventType.GENERATE, description="Operation type: generate or modify")
    model_family: ModelFamily = Field(ModelFamily.GOOGLE, description="AI provider to use")
    model_name: str = Field("gemini-1.5-flash", description="Specific model name")
    
    # Optional detailed requirements (for generation)
    business_name: Optional[str] = Field(None, description="Business or website name")
    tagline: Optional[str] = Field(None, description="Tagline or main message")
    website_type: Optional[WebsiteType] = Field(None, description="Type of website")
    color_scheme: Optional[ColorScheme] = Field(None, description="Preferred color scheme")
    key_features: Optional[List[str]] = Field(None, description="Key features or products")
    sections: Optional[List[str]] = Field(None, description="Sections to include")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    additional_info: Optional[str] = Field(None, description="Additional requirements")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a landing page for a coffee shop",
                "project_id": None,
                "event_type": "generate",
                "model_family": "Google",
                "model_name": "gemini-1.5-flash",
                "business_name": "Bean Dreams",
                "website_type": "Landing Page"
            }
        }


# ==========================================================
# RESPONSE SCHEMAS
# ==========================================================

class ProjectMetadata(BaseModel):
    """Metadata for a project."""
    version: int
    timestamp: str
    is_modification: bool
    base_version: Optional[int] = None
    base_file: Optional[str] = None
    modified_files: Optional[List[str]] = None
    sections_changed: Optional[List[str]] = None
    created_at: str


class ProjectFile(BaseModel):
    """A single file in a project."""
    path: str
    content: str
    language: Optional[str] = None


class ProjectResponse(BaseModel):
    """Response containing a project."""
    id: str = Field(..., description="Project ID (filename)")
    metadata: ProjectMetadata
    files: Dict[str, str] = Field(..., description="Map of file paths to content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "project_v1_20250101_120000",
                "metadata": {
                    "version": 1,
                    "timestamp": "20250101_120000",
                    "is_modification": False,
                    "created_at": "2025-01-01T12:00:00"
                },
                "files": {
                    "index.html": "<!DOCTYPE html>...",
                    "src/App.tsx": "export function App()..."
                }
            }
        }


class ProjectListItem(BaseModel):
    """Summary of a project for listing."""
    id: str
    version: int
    is_modification: bool
    created_at: str
    file_count: int


class ProjectListResponse(BaseModel):
    """Response containing list of projects."""
    total: int
    projects: List[ProjectListItem]


class ClassifyResponse(BaseModel):
    """Response from intent classification."""
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    message: str
    conversation_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str


# ==========================================================
# EVENT SCHEMAS (for SSE streaming)
# ==========================================================

class StreamEvent(BaseModel):
    """Universal event envelope for SSE streaming."""
    event_id: str
    event_type: str
    timestamp: str
    project_id: str
    conversation_id: str
    payload: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_abc123",
                "event_type": "progress.update",
                "timestamp": "2025-01-01T12:00:00Z",
                "project_id": "proj_123",
                "conversation_id": "conv_456",
                "payload": {
                    "step_id": "code",
                    "status": "in_progress"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

