"""
Simple greeting generator that uses a short template. Kept intentionally small.
"""

def generate_greeting_response(user_text: str) -> str:
    """Generate a friendly greeting response"""
    t = user_text.lower().strip()
    
    # Check for different greeting types
    if any(g in t for g in ["good morning", "morning"]):
        return "Good morning!  How can I assist you today? I can help you with general questions or create beautiful webpages for you!"
    elif any(g in t for g in ["good afternoon"]):
        return "Good afternoon! How can I assist you today? I can help you with general questions or create beautiful webpages for you!"
    elif any(g in t for g in ["good evening", "evening"]):
        return "Good evening! How can I assist you today? I can help you with general questions or create beautiful webpages for you!"
    elif any(g in t for g in ["hi", "hello", "hey", "greetings"]):
        return "Hello! How can I help you today? I can answer your questions or help you build a webpage - just let me know what you need!"
    else:
        return "Hello! How can I assist you today?"