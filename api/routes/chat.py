"""
Chat and Classification Routes
Handle conversations and intent detection
"""

from fastapi import APIRouter, HTTPException

from api.schemas import (
    ChatRequest, ChatResponse,
    ClassifyRequest, ClassifyResponse,
    IntentType
)

# Import core modules
from models.gemini_client_qa import chat_with_claude
from intent.classifier import classify_intent

router = APIRouter()


# ==========================================================
# ENDPOINTS
# ==========================================================

@router.post("/chat", response_model=ChatResponse, tags=["Chat & Classification"])
async def chat_endpoint(request: ChatRequest):
    """
    Chat with the AI assistant.
    
    **Request:**
    ```json
    {
        "message": "What frameworks do you support?",
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
        "message": "I support React with Vite and TypeScript...",
        "conversation_id": "conv_123"
    }
    ```
    
    **Use Cases:**
    - General questions about the platform
    - Clarifying requirements before building
    - Getting help and guidance
    """
    try:
        # Convert history to expected format
        history = request.history or []
        
        # Call Claude
        response = chat_with_claude(request.message, history)
        
        return ChatResponse(
            message=response,
            conversation_id=request.conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/classify", response_model=ClassifyResponse, tags=["Chat & Classification"])
async def classify_intent_endpoint(request: ClassifyRequest):
    """
    Classify the intent of a user message.
    
    **Request:**
    ```json
    {
        "text": "Hello! Can you create a website for my bakery?"
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
    - `greeting_only` - Just a greeting (hi, hello)
    - `chat` - General conversation/questions
    - `webpage_build` - Request to create a new website
    - `webpage_modify` - Request to change existing website
    - `greeting_and_webpage` - Greeting + build request
    - `illegal` - Harmful/prohibited content
    
    **Use Case:**
    Use this to route user input to the appropriate handler:
    ```javascript
    const result = await fetch('/api/classify', {
        method: 'POST',
        body: JSON.stringify({ text: userInput })
    }).then(r => r.json());
    
    switch(result.intent) {
        case 'greeting_only':
            showGreetingResponse();
            break;
        case 'webpage_build':
            startBuildFlow();
            break;
        case 'webpage_modify':
            startModifyFlow();
            break;
        case 'chat':
            callChatEndpoint();
            break;
        case 'illegal':
            showBlockedMessage();
            break;
    }
    ```
    """
    try:
        intent, metadata = classify_intent(request.text)
        
        # Map intent string to enum
        intent_map = {
            "greeting_only": IntentType.GREETING,
            "chat": IntentType.CHAT,
            "webpage_build": IntentType.WEBPAGE_BUILD,
            "webpage_modify": IntentType.WEBPAGE_MODIFY,
            "greeting_and_webpage": IntentType.GREETING_AND_WEBPAGE,
            "illegal": IntentType.ILLEGAL
        }
        
        intent_type = intent_map.get(intent, IntentType.CHAT)
        
        return ClassifyResponse(
            intent=intent_type,
            confidence=metadata.get("confidence", 0.5),
            explanation=metadata.get("explanation", "")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")


@router.post("/greeting", tags=["Chat & Classification"])
async def greeting_endpoint(request: ChatRequest):
    """
    Generate a friendly greeting response.
    
    Use this when intent is classified as 'greeting_only'.
    
    **Response:**
    ```json
    {
        "message": "Hello!  I'm here to help you build amazing websites..."
    }
    ```
    """
    try:
        from intent.greeting_generator import generate_greeting_response
        
        response = generate_greeting_response(request.message)
        
        return {
            "message": response
        }
        
    except Exception as e:
        # Fallback greeting
        return {
            "message": "Hello! I'm your AI website builder. Tell me what kind of website you'd like to create, and I'll build it for you!"
        }

