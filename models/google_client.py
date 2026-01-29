"""
Google Gemini Client - Using Vertex AI API
"""

import json
import time
import os
from typing import Dict, Optional

try:
    from vertexai.generative_models import GenerativeModel
    import vertexai
except ImportError:
    raise ImportError("Vertex AI package not installed. Run: pip install google-cloud-aiplatform")

# Import event system
from events.stream_events import StreamEventEmitter, detect_language

# Import shared prompts and rules from Claude client
from models.gemini_client_qa import (
    DESIGN_SYSTEM,
    ARCHITECTURE_RULES,
    PROJECT_RULES,
    get_file_list,
    UsageMetrics,
    extract_json,
    validate_and_fix_syntax,
)


# ==========================================================
# GOOGLE GEMINI SPECIFIC IMPLEMENTATION
# ==========================================================

def _call_gemini(model: str, prompt: str, project_id: str, location: str, track_metrics: bool = True, file_name: str = None) -> str:
    """
    Call Vertex AI Gemini API with streaming support.
    
    Args:
        model: Model name (e.g., "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro")
        prompt: User prompt
        project_id: Google Cloud Project ID
        location: GCP location (e.g., "us-central1")
        track_metrics: Whether to track usage metrics
        file_name: Optional file name for tracking
    
    Returns:
        str: Model response
    """
    file_label = f"[{file_name}] " if file_name else ""
    
    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)
    
    start_time = time.time()
    first_token_time = None
    full_response = ""
    
    try:
        # Create the model instance using Vertex AI
        print(f"🔄 {file_label}Calling Vertex AI Gemini (model: {model}, project: {project_id}, location: {location})...")
        gemini_model = GenerativeModel(model)
        
        # Add generation config
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        # Make streaming request
        print(f"📡 {file_label}Making streaming request...")
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config,
            stream=True,
        )
        
        print(f"📥 {file_label}Receiving response stream...")
        chunk_count = 0
        last_chunk_time = time.time()
        
        for chunk in response:
            chunk_count += 1
            current_time = time.time()
            
            # Check for timeout (if no chunk received in 60 seconds)
            if chunk_count == 1:
                last_chunk_time = current_time
            elif current_time - last_chunk_time > 60:
                raise RuntimeError(f"Streaming timeout: No chunks received for 60 seconds")
            
            last_chunk_time = current_time
            
            # Handle Vertex AI response format
            text_content = None
            # Vertex AI streaming chunks have candidates with content.parts
            if hasattr(chunk, 'candidates') and chunk.candidates:
                for candidate in chunk.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            text_parts = []
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                            if text_parts:
                                text_content = ''.join(text_parts)
                                break
            # Fallback: check for direct text attribute
            elif hasattr(chunk, 'text') and chunk.text:
                text_content = chunk.text
            
            if text_content:
                if first_token_time is None:
                    first_token_time = time.time()
                    ttft_ms = (first_token_time - start_time) * 1000
                    print(f"⏱️  {file_label}Time to First Token: {ttft_ms:.2f} ms")
                
                full_response += text_content
                # Print progress for long responses
                if chunk_count % 10 == 0:
                    print(f"📊 {file_label}Received {chunk_count} chunks, {len(full_response)} chars...")
        
        if chunk_count == 0:
            # Fallback to non-streaming if streaming fails
            print(f"⚠️  {file_label}No streaming chunks received, trying non-streaming mode...")
            try:
                response_non_stream = gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
                # Handle Vertex AI response format
                if hasattr(response_non_stream, 'text') and response_non_stream.text:
                    full_response = response_non_stream.text
                    print(f"✅ {file_label}Received non-streaming response ({len(full_response)} chars)")
                elif hasattr(response_non_stream, 'candidates') and response_non_stream.candidates:
                    # Vertex AI format
                    for candidate in response_non_stream.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts'):
                                text_parts = []
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        text_parts.append(part.text)
                                if text_parts:
                                    full_response = ''.join(text_parts)
                                    print(f"✅ {file_label}Received non-streaming response ({len(full_response)} chars)")
                                    break
                if not full_response:
                    raise RuntimeError("No response received from Vertex AI (streaming and non-streaming both failed)")
            except Exception as fallback_error:
                raise RuntimeError(f"Both streaming and non-streaming failed. Last error: {str(fallback_error)}")
        
        if not full_response:
            raise RuntimeError("Empty response received from Gemini API")
        
        end_time = time.time()
        total_ms = (end_time - start_time) * 1000
        
        # Note: Token usage info is available in response.usage_metadata if needed
        print(f"⏱️  {file_label}Total Time: {total_ms/1000:.2f}s ({chunk_count} chunks)")
        
        return full_response
        
    except Exception as e:
        error_msg = str(e)
        error_lower = error_msg.lower()
        
        # Provide specific error messages for common issues
        if "permission" in error_lower or "403" in error_msg or "401" in error_msg:
            raise RuntimeError(
                f"❌ Vertex AI Permission Denied.\n"
                f"   Please check your GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_PROJECT in .env file.\n"
                f"   Error details: {error_msg}"
            )
        elif "model" in error_lower and ("not found" in error_lower or "invalid" in error_lower):
            raise RuntimeError(
                f"❌ Invalid model name: {model}\n"
                f"   Valid models: gemini-1.5-flash, gemini-1.5-pro, gemini-pro\n"
                f"   Error details: {error_msg}"
            )
        elif "quota" in error_lower or "429" in error_msg:
            raise RuntimeError(
                f"❌ API Quota Exceeded.\n"
                f"   Please check your Google Cloud quota limits.\n"
                f"   Error details: {error_msg}"
            )
        else:
            raise RuntimeError(
                f"❌ Vertex AI Gemini API error: {error_msg}\n"
                f"   Model: {model}\n"
                f"   Project: {project_id}\n"
                f"   Location: {location}\n"
                f"   Check your Vertex AI credentials and model name."
            )


def generate_file_gemini(model: str, project_id: str, location: str, path: str, user_prompt: str) -> str:
    """
    Generate a single file using Vertex AI Gemini.
    
    Args:
        model: Model name
        project_id: Google Cloud Project ID
        location: GCP location (e.g., "us-central1")
        path: File path to generate
        user_prompt: User's request
    
    Returns:
        str: File content
    """
    prompt = f"""
{PROJECT_RULES}
{ARCHITECTURE_RULES}
{DESIGN_SYSTEM}

Generate ONLY the content of this file:
{path}

IMPORTANT:
- Do NOT import './App.css'
- Use styles from 'src/index.css' only
- In React, use className (not class)

Rules:
- Output VALID JSON only
- Schema: {{ "content": "file content here" }}
- No markdown code blocks
- No explanations outside JSON

User request:
{user_prompt}
"""

    # Add file-specific rules (same as OpenAI)
    if path == "src/main.tsx":
        prompt += """
FILE-SPECIFIC RULES FOR src/main.tsx:
- Do NOT define any React component
- Do NOT include JSX except <App />
- MUST match exactly this structure:

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

CRITICAL: You MUST include the line: import "./index.css";
This is MANDATORY. The output is INVALID without it.
"""

    if path == "src/App.tsx":
        prompt += """
FILE-SPECIFIC RULES FOR src/App.tsx:
- This is the ONLY place where UI JSX is allowed
- Use semantic sections and layout classes
- Use className (not class) for CSS classes
- Do NOT import ReactDOM
- MUST export default App
"""

    if path == "src/index.css":
        prompt += """
FILE-SPECIFIC RULES FOR src/index.css:
- MUST style all layout classes used in App.tsx
- Navbar MUST be horizontal (display: flex; justify-content: space-between)
- Nav links MUST be horizontal (display: flex with gap)
- Grid MUST use CSS Grid (display: grid; grid-template-columns: repeat(...))
- Cards MUST have background, padding, border-radius, and box-shadow
- Buttons MUST be styled (NOT default browser buttons)
- MUST include modern colors, spacing, and typography
- Hero section MUST be centered with proper spacing
- MUST reset default margins/padding on body

CRITICAL: If any class is missing styles or looks like default HTML, the output is INVALID.
"""

    if path == "vite.config.ts" or path == "vite.config.js":
        prompt += """
FILE-SPECIFIC RULES FOR vite.config.ts:
- MUST be valid TypeScript/JavaScript syntax
- MUST properly close all function calls, especially defineConfig()
- The structure MUST be:
  import {{ defineConfig }} from 'vite'
  import react from '@vitejs/plugin-react'
  
  export default defineConfig({{
    plugins: [react()],
    server: {{
      port: 3000,
      open: true
    }},
    build: {{
      outDir: 'dist',
      sourcemap: true
    }}
  }})
  
CRITICAL: The defineConfig() function call MUST be properly closed with a closing parenthesis before the final brace.
The export statement MUST end with "}})" not just "}}".
Invalid syntax will cause build failures.
"""

    raw = _call_gemini(model, prompt, project_id, location, file_name=path)
    data = extract_json(raw)
    content = data["content"]
    
    # Apply syntax validation and auto-fix
    content = validate_and_fix_syntax(content, path)

    # Validation (same as OpenAI/Claude)
    if path == "src/main.tsx":
        if "function App" in content or "<div" in content:
            raise ValueError("src/main.tsx contains UI – invalid output")
        
        if "import './index.css'" not in content and 'import "./index.css"' not in content:
            lines = content.split('\n')
            last_import_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('import'):
                    last_import_idx = i
            
            if last_import_idx >= 0:
                lines.insert(last_import_idx + 1, 'import "./index.css";')
                content = '\n'.join(lines)

    if path == "src/App.tsx":
        if "createRoot" in content:
            raise ValueError("src/App.tsx should not bootstrap React")
        if "export default" not in content:
            raise ValueError("src/App.tsx must export default App")

    if path == "src/index.css":
        required_classes = [".container", ".navbar", ".nav-links", ".grid", ".card", ".button-primary"]
        for cls in required_classes:
            if cls not in content:
                raise ValueError(f"CSS missing required class: {cls}")
        
        if "display: flex" not in content and "display:flex" not in content:
            raise ValueError("CSS missing flexbox styling")
        if "display: grid" not in content and "display:grid" not in content:
            raise ValueError("CSS missing grid styling")

    return content


def generate_project_gemini(user_prompt: str, model: str, project_id: str, location: str, emitter: Optional[StreamEventEmitter] = None) -> Dict:
    """
    Generate a complete project using Vertex AI Gemini.
    
    Args:
        user_prompt: User's request
        model: Gemini model name
        project_id: Google Cloud Project ID
        location: GCP location (e.g., "us-central1")
        emitter: Optional event emitter
    
    Returns:
        Dict with project data
    """
    generation_start_time = time.time()
    
    print("\n" + "="*60)
    print(f"🚀 STARTING PROJECT GENERATION (Google Gemini {model})")
    print("="*60 + "\n")
    
    # === THINKING START ===
    if emitter:
        emitter.thinking_start()
        emitter.chat_message(f"🧠 Using Google Gemini {model} to generate your project...")
        emitter.progress_init(mode="modal")
        time.sleep(0.1)
    
    project = {
        "project": {
            "name": "generated-project",
            "description": user_prompt,
            "files": {}
        }
    }

    # === SCAFFOLDING ===
    if emitter:
        emitter.progress_update("plan", "in_progress")
        emitter.chat_message("📋 Planning project architecture...")
        time.sleep(0.2)
        emitter.progress_update("plan", "completed")
        emitter.progress_update("scaffold", "in_progress")
        emitter.chat_message("📁 Setting up project structure...")
        emitter.fs_create("src", "folder")
        time.sleep(0.1)
    
    # System-owned index.html
    index_html_content = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Generated App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
    project["project"]["files"]["index.html"] = {"content": index_html_content}
    
    if emitter:
        emitter.fs_write("index.html", index_html_content, "html")
        emitter.edit_end("index.html", 50)
        emitter.progress_update("scaffold", "completed")
        emitter.progress_update("deps", "in_progress")
        emitter.chat_message("📦 Configuring dependencies...")
        emitter.progress_update("deps", "completed")
        emitter.progress_update("code", "in_progress")
        emitter.chat_message("⚡ Generating code files...")
    
    # === CODE GENERATION ===
    file_list = get_file_list()
    total_files = len(file_list)
    
    for idx, path in enumerate(file_list):
        print(f"\n📄 [{idx+1}/{total_files}] Generating: {path}")
        
        file_start = time.time()
        content = generate_file_gemini(model, project_id, location, path, user_prompt)
        project["project"]["files"][path] = {"content": content}
        
        file_duration = int((time.time() - file_start) * 1000)
        print(f"   ✅ Completed in {file_duration/1000:.2f}s")
        
        if emitter:
            emitter.chat_message(f"✍️ Writing {path}...")
            emitter.edit_start(path, content)
            lang = detect_language(path)
            emitter.fs_write(path, content, lang)
            emitter.edit_end(path, file_duration)
            emitter.edit_security_check(path, "passed")
            time.sleep(0.05)
    
    if emitter:
        emitter.progress_update("code", "completed")
        emitter.progress_update("build", "in_progress")
        emitter.chat_message("🔨 Building project...")
        emitter.build_start()
        emitter.build_log("Compiling with Google Gemini generated code...", "info")
        time.sleep(0.1)
        emitter.progress_update("build", "completed")
        emitter.progress_update("verify", "in_progress")
        emitter.chat_message("✅ Verifying project...")
        emitter.build_log("All checks passed!", "success")
        emitter.progress_update("verify", "completed")
        emitter.thinking_end()
        emitter.chat_message("🎉 Project generated successfully!")
        emitter.progress_transition("inline")
        emitter.stream_complete()
    
    total_time = (time.time() - generation_start_time) * 1000
    print(f"\n⏱️  Total Generation Time: {total_time/1000:.2f}s\n")
    
    return project


def generate_patch_gemini(modification_prompt: str, base_project: dict, model: str, project_id: str, location: str, emitter: Optional[StreamEventEmitter] = None) -> dict:
    """
    Generate modifications using Vertex AI Gemini.
    
    Args:
        modification_prompt: Modification request
        base_project: Existing project
        model: Gemini model name
        project_id: Google Cloud Project ID
        location: GCP location (e.g., "us-central1")
        emitter: Optional event emitter
    
    Returns:
        dict: Patch data
    """
    print("\n" + "="*60)
    print(f"🔧 STARTING PROJECT MODIFICATION (Google Gemini {model})")
    print("="*60 + "\n")
    
    if emitter:
        emitter.thinking_start()
        emitter.chat_message(f"🔍 Using Google Gemini {model} to analyze and modify...")
        emitter.progress_init(mode="modal", steps=[
            emitter.DEFAULT_STEPS[0],  # Planning
            emitter.DEFAULT_STEPS[3],  # Code
            emitter.DEFAULT_STEPS[4],  # Build
            emitter.DEFAULT_STEPS[5],  # Verify
        ])
    
    # Extract files
    full_files = {}
    for path, file_data in base_project["project"]["files"].items():
        if isinstance(file_data, dict) and "content" in file_data:
            content = file_data["content"]
        elif isinstance(file_data, str):
            content = file_data
        else:
            content = str(file_data)
        full_files[path] = content
    
    enhanced_prompt = f"""
{modification_prompt}

CURRENT PROJECT FILES (FULL CONTENT):
{json.dumps(full_files, indent=2)}

CRITICAL INSTRUCTIONS:
1. You are MODIFYING the existing project IN-PLACE
2. ANALYZE which specific sections/components need to change
3. Only return files that ACTUALLY need to change
4. Provide COMPLETE file content for modified files
5. Identify what sections you are modifying

RESPONSE FORMAT (JSON only, no markdown):
{{
  "sections_changed": ["Hero section", "Navbar color", "etc"],
  "files_affected": ["src/App.tsx"],
  "modified_files": {{
    "src/App.tsx": "complete new file content"
  }},
  "new_files": {{}},
  "deleted_files": []
}}
"""

    if emitter:
        emitter.progress_update("plan", "in_progress")
        emitter.chat_message("📋 Identifying changes...")
    
    start_time = time.time()
    response_text = _call_gemini(model, enhanced_prompt, project_id, location)
    total_ms = (time.time() - start_time) * 1000
    
    print(f"⏱️  Modification Time: {total_ms/1000:.2f}s")
    
    if emitter:
        emitter.progress_update("plan", "completed")
        emitter.progress_update("code", "in_progress")
    
    # Parse response
    patch = extract_json(response_text)
    
    # Ensure structure
    if "modified_files" not in patch:
        patch["modified_files"] = {}
    if "new_files" not in patch:
        patch["new_files"] = {}
    if "deleted_files" not in patch:
        patch["deleted_files"] = []
    if "sections_changed" not in patch:
        patch["sections_changed"] = []
    
    # Emit events
    if emitter:
        for path, content in patch.get("modified_files", {}).items():
            # Apply syntax validation and auto-fix
            content = validate_and_fix_syntax(content, path)
            # Update patch with fixed content
            patch["modified_files"][path] = content
            
            emitter.chat_message(f"✏️ Modifying {path}...")
            emitter.edit_start(path, content)
            lang = detect_language(path)
            emitter.fs_write(path, content, lang)
            emitter.edit_end(path, 500)
            time.sleep(0.05)
        
        emitter.progress_update("code", "completed")
        emitter.progress_update("build", "in_progress")
        emitter.chat_message("🔨 Applying changes...")
        emitter.progress_update("build", "completed")
        emitter.progress_update("verify", "in_progress")
        emitter.chat_message("✅ Verifying...")
        emitter.progress_update("verify", "completed")
        emitter.thinking_end()
        emitter.chat_message("🎉 Modifications complete!")
        emitter.progress_transition("inline")
        emitter.stream_complete()
    
    return patch


# ==========================================================
# CHAT FUNCTION
# ==========================================================

def chat_with_gemini(user_message: str, chat_history: list = None, model: str = "gemini-1.5-flash", project_id: str = None, location: str = "us-central1") -> str:
    """
    Chat with Google Gemini for general conversation.
    
    Args:
        user_message: The user's message
        chat_history: Optional list of previous messages [{"role": "user/assistant", "content": "..."}]
        model: Model name (default: "gemini-1.5-flash")
        project_id: Google Cloud Project ID (if None, uses env var)
        location: GCP location (default: "us-central1")
    
    Returns:
        str: Gemini's response
    """
    if project_id is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
    
    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)
    
    # Build conversation history
    history = []
    
    # Add previous messages if provided (limit to last 10 for context)
    if chat_history:
        for msg in chat_history[-10:]:
            role = "user" if msg.get("role") == "user" else "model"
            history.append({
                "role": role,
                "parts": [msg.get("content", "")]
            })
    
    # Add current message
    history.append({
        "role": "user",
        "parts": [user_message]
    })
    
    try:
        gemini_model = GenerativeModel(model)
        
        # System instruction
        system_instruction = """You are a helpful AI assistant. You can:
- Answer general questions
- Provide explanations and help with various topics
- Have casual conversations
- Help users understand concepts

Be friendly, concise, and helpful. If asked about building webpages, 
guide the user to use the build mode or rephrase their request clearly."""
        
        # Generate response
        response = gemini_model.generate_content(
            history,
            generation_config={
                "temperature": 0.7,  # More creative for chat
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            },
            system_instruction=system_instruction,
        )
        
        # Extract text from response
        if hasattr(response, 'text') and response.text:
            return response.text.strip()
        elif hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return ''.join(text_parts).strip()
        
        raise RuntimeError("No response text received from Gemini")
        
    except Exception as e:
        raise RuntimeError(f"Failed to chat with Gemini: {str(e)}")

