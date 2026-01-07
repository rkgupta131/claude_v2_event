# intent/classifier.py

import re

# def classify_intent(text: str) -> str:
#     text = text.lower().strip()

#     # If user is simply greeting
#     if any(g in text for g in ["hello", "hi", "hey", "good morning", "good evening"]):
#         return "greeting_only"

#     # Informational / Chat queries (DO NOT START BUILDER)
#     informational_patterns = [
#         r"what is",
#         r"explain",
#         r"how does",
#         r"tell me about",
#         r"define",
#         r"what are",
#         r"why is",
#         r"difference between",
#         r"how to learn",
#         r"examples of",
#         r"guide me",
#     ]
#     if any(re.search(p, text) for p in informational_patterns):
#         return "other"

#     # If user expresses intent to build a webpage
#     builder_keywords = [
#         "build",
#         "create",
#         "generate",
#         "make",
#         "design",
#         "construct",
#         "develop",
#         "i want a website",
#         "i want to build",
#         "i want to create",
#         "webpage for",
#         "website for",
#         "landing page for",
#     ]
#     if any(k in text for k in builder_keywords):
#         return "webpage_build"

#     # Greeting + builder intent
#     if any(g in text for g in ["hi", "hello", "hey"]) and any(
#         k in text for k in builder_keywords
#     ):
#         return "greeting_and_webpage"

#     # Default = chat mode
#     return "other"


# intent/classifier.py
"""
Thin wrapper for intent classification. Attempts to use the model classifier
from models.gemini_client.classify_intent(). If that fails (network/ADC),
falls back to a simple heuristic classifier so your app remains responsive.
"""

from typing import Tuple
import re

try:
    from models.gemini_client_qa import classify_intent as model_classify
except Exception:
    model_classify = None


def heuristic_classify(text: str) -> Tuple[str, dict]:
    txt = text.strip().lower()
    
    # 1. Illegal content detection - CHECK FIRST before anything else
    illegal_keywords = [
        # Hacking/Security
        "hack", "hacking", "ddos", "crack", "bypass", "unauthorized", "exploit",
        # Financial crimes
        "money laundering", "launder money", "laundering", "fraud", "fraudulent",
        "scam", "scammer", "phishing", "ponzi", "pyramid scheme",
        # Drugs
        "drug dealer", "drug dealing", "sell drugs", "buy drugs", "illegal drugs",
        # Weapons/Violence
        "illegal weapons", "bomb making", "terrorism", "terrorist",
        # Identity/Theft
        "steal", "stealing", "identity theft", "counterfeit", "fake id",
        # Adult/Exploitation
        "child exploitation", "human trafficking",
        # Gambling (illegal)
        "illegal gambling", "underground casino",
        # General illegal
        "illegal", "illicit", "criminal", "black market", "dark web", "darknet"
    ]
    
    if any(kw in txt for kw in illegal_keywords):
        return "illegal", {"explanation": "Detected potential illegal/harmful content request", "confidence": 0.99}
    
    # 2. Greetings - check for simple greetings
    greeting_patterns = [
        r"^(hi|hello|hey|yo|hi there|hello there|greetings|good morning|good afternoon|good evening)([!.,\s]*)$",
        r"^(hi|hello|hey|yo|hi there|hello there|greetings|good morning|good afternoon|good evening)([!.,\s]*)(how are you|how's it going|what's up|how do you do)",
    ]
    for pattern in greeting_patterns:
        if re.match(pattern, txt):
            return "greeting_only", {"explanation": "Simple greeting detected", "confidence": 0.9}
    
    # 3. General questions - educational/informational queries
    general_question_patterns = [
        r"^(what is|what's|what are|what were|what do|what does|what did)",
        r"^(how is|how are|how do|how does|how did|how can|how will|how would)",
        r"^(why is|why are|why do|why does|why did|why can|why would)",
        r"^(when is|when are|when do|when does|when did|when can|when will)",
        r"^(where is|where are|where do|where does|where did|where can)",
        r"^(who is|who are|who do|who does|who did|who can)",
        r"^(explain|describe|tell me about|tell me more|can you explain|can you describe)",
        r"^(define|definition of|meaning of|what does.*mean)",
        r"^(difference between|different from|compare|similar to)",
        r"^(examples? of|example|give me an example|show me an example)",
        r"^(help me understand|help with|i need help|can you help)",
    ]
    
    # Check if it's a general question (but not about building webpages)
    is_general_question = any(re.match(p, txt) for p in general_question_patterns)
    is_about_webpage_building = any(kw in txt for kw in (
        "build", "create", "make", "generate", "design", "develop", "construct",
        "webpage", "website", "landing page", "web page", "web site"
    ))
    
    if is_general_question and not is_about_webpage_building:
        return "chat", {"explanation": "General question detected - will answer conversationally", "confidence": 0.85}
    
    # 4. Webpage build/modify requests
    webpage_keywords = [
        "build a website", "build a webpage", "build website", "build webpage",
        "make a website", "make a webpage", "make website", "make webpage",
        "create a website", "create a webpage", "create website", "create webpage",
        "generate a website", "generate a webpage", "generate website", "generate webpage",
        "design a website", "design a webpage", "design website", "design webpage",
        "develop a website", "develop a webpage", "develop website", "develop webpage",
        "landing page", "web page for", "website for", "webpage for",
        "i want a website", "i want a webpage", "i need a website", "i need a webpage",
        "i want to build", "i want to create", "i want to make", "i want to design",
        "build me", "create me", "make me", "design me", "generate me",
    ]
    
    modification_keywords = ["modify", "change", "update", "edit", "alter", "fix", "improve", "adjust", "revise"]
    is_modification = any(kw in txt for kw in modification_keywords)
    
    if any(kw in txt for kw in webpage_keywords) or (is_modification and is_about_webpage_building):
        intent_type = "webpage_modify" if is_modification else "webpage_build"
        return intent_type, {"explanation": f"User wants to {intent_type.replace('webpage_', '')} a webpage", "confidence": 0.95}
    
    # 5. Greeting + webpage intent
    has_greeting = any(g in txt for g in ["hi", "hello", "hey", "greetings"])
    if has_greeting and is_about_webpage_building:
        return "greeting_and_webpage", {"explanation": "Greeting combined with webpage build request", "confidence": 0.9}
    
    # 6. Fallback to chat for everything else
    return "chat", {"explanation": "Default to chat mode - will answer conversationally", "confidence": 0.3}


def classify_intent(user_text: str) -> Tuple[str, dict]:
    if model_classify:
        try:
            label, meta = model_classify(user_text)
            return label, meta
        except Exception:
            # model failure — fall back
            return heuristic_classify(user_text)
    else:
        return heuristic_classify(user_text)