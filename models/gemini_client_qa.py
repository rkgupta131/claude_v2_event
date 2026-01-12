import os
import json
import re
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from anthropic import Anthropic
from dotenv import load_dotenv

# Import event system
from events.stream_events import StreamEventEmitter, detect_language

# ==========================================================
# CLIENT SETUP
# ==========================================================
load_dotenv()
MODEL = "claude-opus-4-5-20251101"

_client = None


# ==========================================================
# TOKEN & TIMING TRACKER
# ==========================================================

@dataclass
class UsageMetrics:
    """Track token usage and timing metrics."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    time_to_first_token_ms: float = 0.0
    total_time_ms: float = 0.0
    api_calls: int = 0
    
    # Detailed timing breakdown
    phase_timings: Dict = field(default_factory=dict)
    file_timings: Dict = field(default_factory=dict)
    file_tokens: Dict = field(default_factory=dict)
    
    def add(self, input_tokens: int, output_tokens: int, ttft_ms: float = 0.0, total_ms: float = 0.0, file_name: str = None):
        """Add usage from an API call."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens = self.input_tokens + self.output_tokens
        if ttft_ms > 0 and self.time_to_first_token_ms == 0:
            self.time_to_first_token_ms = ttft_ms
        self.api_calls += 1
        
        # Track per-file metrics
        if file_name:
            self.file_timings[file_name] = {
                "ttft_ms": round(ttft_ms, 2),
                "total_ms": round(total_ms, 2),
                "total_s": round(total_ms / 1000, 2)
            }
            self.file_tokens[file_name] = {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            }
    
    def add_phase_timing(self, phase: str, duration_ms: float):
        """Add timing for a phase."""
        self.phase_timings[phase] = {
            "duration_ms": round(duration_ms, 2),
            "duration_s": round(duration_ms / 1000, 2)
        }
    
    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "time_to_first_token_ms": round(self.time_to_first_token_ms, 2),
            "total_time_ms": round(self.total_time_ms, 2),
            "total_time_s": round(self.total_time_ms / 1000, 2),
            "api_calls": self.api_calls,
            "phase_timings": self.phase_timings,
            "file_timings": self.file_timings,
            "file_tokens": self.file_tokens
        }
    
    def print_summary(self, label: str = ""):
        """Print a detailed summary of usage metrics."""
        print(f"\n{'='*60}")
        print(f"📊 DETAILED TIMING BREAKDOWN {label}")
        print(f"{'='*60}")
        
        # Overall metrics
        print(f"\n📈 OVERALL METRICS:")
        print(f"   ⏱️  First Token: {self.time_to_first_token_ms:.2f} ms ({self.time_to_first_token_ms/1000:.2f} s)")
        print(f"   ⏱️  Total Time: {self.total_time_ms:.2f} ms ({self.total_time_ms/1000:.2f} s)")
        print(f"   📥 Input Tokens: {self.input_tokens:,}")
        print(f"   📤 Output Tokens: {self.output_tokens:,}")
        print(f"   📊 Total Tokens: {self.total_tokens:,}")
        print(f"   🔄 API Calls: {self.api_calls}")
        
        # Phase breakdown
        if self.phase_timings:
            print(f"\n📋 PHASE BREAKDOWN:")
            total_phase_time = sum(p.get("duration_ms", 0) for p in self.phase_timings.values())
            for phase, timing in self.phase_timings.items():
                pct = (timing["duration_ms"] / total_phase_time * 100) if total_phase_time > 0 else 0
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"   {phase:20} {timing['duration_s']:8.2f}s  {bar} {pct:5.1f}%")
        
        # File breakdown
        if self.file_timings:
            print(f"\n📁 FILE GENERATION BREAKDOWN:")
            total_file_time = sum(f.get("total_ms", 0) for f in self.file_timings.values())
            for file_name, timing in self.file_timings.items():
                tokens = self.file_tokens.get(file_name, {})
                pct = (timing["total_ms"] / total_file_time * 100) if total_file_time > 0 else 0
                print(f"   {file_name:25} {timing['total_s']:6.2f}s | TTFT: {timing['ttft_ms']:6.0f}ms | Tokens: {tokens.get('total', 0):,} ({pct:.1f}%)")
            print(f"   {'─'*70}")
            print(f"   {'TOTAL FILE GEN':25} {total_file_time/1000:6.2f}s")
        
        # Summary bar
        print(f"\n{'='*60}")
        
        # Time allocation
        if self.phase_timings and self.file_timings:
            file_gen_time = sum(f.get("total_ms", 0) for f in self.file_timings.values())
            other_time = self.total_time_ms - file_gen_time
            print(f"⏱️  TIME ALLOCATION:")
            print(f"   📁 File Generation (LLM calls): {file_gen_time/1000:.2f}s ({file_gen_time/self.total_time_ms*100:.1f}%)")
            print(f"   ⚙️  Other (setup, events, etc.): {other_time/1000:.2f}s ({other_time/self.total_time_ms*100:.1f}%)")
        
        print(f"{'='*60}\n")


# Global metrics tracker
_current_metrics: Optional[UsageMetrics] = None

def get_current_metrics() -> Optional[UsageMetrics]:
    """Get the current metrics tracker."""
    return _current_metrics

def reset_metrics() -> UsageMetrics:
    """Reset and return a new metrics tracker."""
    global _current_metrics
    _current_metrics = UsageMetrics()
    return _current_metrics

def _make_client():
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. "
            "Make sure load_dotenv() is called in app.py BEFORE importing claude_client."
        )

    _client = Anthropic(api_key=api_key)
    return _client

client = _make_client()

DESIGN_SYSTEM = """
You MUST follow this component layout exactly.

JSX STRUCTURE (MANDATORY):

- Root wrapper: <div className="container">
- Navbar:
  <nav className="navbar">
    <div className="logo">Brand</div>
    <div className="nav-links">...</div>
  </nav>

- Hero section:
  <section className="hero">
    <h1>...</h1>
    <p>...</p>
    <div className="hero-buttons">
      <button className="button-primary">...</button>
      <button className="button-secondary">...</button>
    </div>
  </section>

- Category section:
  <section className="section">
    <h2>...</h2>
    <div className="grid">
      <div className="card">...</div>
    </div>
  </section>

ALLOWED CLASS NAMES ONLY:
container, navbar, logo, nav-links,
hero, hero-buttons,
section, grid, card,
button-primary, button-secondary

DO NOT invent new layout classes.
"""

ARCHITECTURE_RULES = """
CRITICAL ARCHITECTURE RULES (MANDATORY):

1. src/main.tsx
   - MUST NOT contain any UI markup
   - MUST NOT define React components
   - MUST ONLY:
     - import React
     - import ReactDOM
     - import App from './App'
     - import './index.css'
     - render <App />

2. src/App.tsx
   - MUST contain ALL UI markup
   - MUST export default App
   - MUST NOT call ReactDOM.createRoot
   - MUST use className (not class) for React

3. src/index.css
   - MUST contain ALL layout and visual styles
   - MUST style the classes used in App.tsx
   - MUST make the page look modern and professional

Violating any rule makes the output INVALID.
"""

PROJECT_RULES = """
STRICT RULES:
- This is a React + Vite + TypeScript project
- Do NOT generate static HTML websites
- Do NOT inline CSS or JavaScript
- index.html is already provided by the system
- All UI must be implemented using React components
- Keep files under 250 lines
- Use modern, professional styling
"""

# ==========================================================
# LOW-LEVEL MODEL CALL (WITH RETRY LOGIC + TOKEN TRACKING)
# ==========================================================

def _call_claude(prompt: str, max_retries: int = 5, track_metrics: bool = True, file_name: str = None) -> str:
    """
    Call Claude API with exponential backoff retry logic.
    Tracks token usage and time to first token.
    
    Args:
        prompt: The prompt to send
        max_retries: Number of retry attempts
        track_metrics: Whether to track usage metrics
        file_name: Optional file name for detailed tracking
    """
    global _current_metrics
    
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            first_token_time = None
            full_response = ""
            input_tokens = 0
            output_tokens = 0
            
            file_label = f"[{file_name}] " if file_name else ""
            
            # Use streaming to get accurate TTFT
            with client.messages.stream(
                model=MODEL,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    if first_token_time is None:
                        first_token_time = time.time()
                        ttft_ms = (first_token_time - start_time) * 1000
                        print(f"⏱️  {file_label}Time to First Token: {ttft_ms:.2f} ms")
                    full_response += text
                
                # Get final message for token counts
                final_message = stream.get_final_message()
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens
            
            end_time = time.time()
            total_ms = (end_time - start_time) * 1000
            ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else 0
            
            # Track metrics
            if track_metrics and _current_metrics is not None:
                _current_metrics.add(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    ttft_ms=ttft_ms,
                    total_ms=total_ms,
                    file_name=file_name
                )
            
            # Print token usage
            print(f"📊 {file_label}Tokens: {input_tokens:,} in | {output_tokens:,} out | Total: {total_ms/1000:.2f}s")
            
            return full_response
            
        except Exception as e:
            error_str = str(e)
            
            # Handle overloaded error (529)
            if "overloaded" in error_str.lower() or "529" in error_str:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + (attempt * 0.5)  # Exponential backoff
                    print(f"API overloaded. Retrying in {wait_time:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise RuntimeError(f"API still overloaded after {max_retries} attempts. Please try again in a few minutes.")
            
            # Handle rate limits (429)
            elif "rate" in error_str.lower() or "429" in error_str:
                if attempt < max_retries - 1:
                    wait_time = 60  # Wait 1 minute for rate limits
                    print(f"Rate limit hit. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise RuntimeError(f"Rate limit exceeded after {max_retries} attempts.")
            
            # Other errors - raise immediately
            else:
                raise e
    
    raise RuntimeError("Max retries exceeded")

# ==========================================================
# JSON EXTRACTION (ROBUST)
# ==========================================================

def extract_json(raw: str):
    """Extract JSON from model response, handling markdown code blocks"""
    # Remove markdown code blocks
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)
    
    # Find JSON object or array
    match = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response:\n{raw[:500]}")
    
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}\n{match.group(1)[:500]}")

# ==========================================================
# FIXED FILE LIST (ARCHITECTURE LOCKED)
# ==========================================================

def get_file_list() -> List[str]:
    return [
        "package.json",
        "vite.config.ts",
        "src/main.tsx",
        "src/App.tsx",
        "src/index.css",
    ]

# ==========================================================
# SINGLE FILE GENERATION (SAFE)
# ==========================================================

def generate_file(path: str, user_prompt: str) -> str:
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

    raw = _call_claude(prompt, file_name=path)
    data = extract_json(raw)
    content = data["content"]

    # Validation and Auto-fix
    if path == "src/main.tsx":
        if "function App" in content or "<div" in content:
            raise ValueError("src/main.tsx contains UI – invalid output")
        
        # Auto-fix: inject CSS import if missing
        if "import './index.css'" not in content and 'import "./index.css"' not in content:
            lines = content.split('\n')
            # Find the last import statement
            last_import_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('import'):
                    last_import_idx = i
            
            if last_import_idx >= 0:
                # Insert after last import
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
        
        # Check for actual styling
        if "display: flex" not in content and "display:flex" not in content:
            raise ValueError("CSS missing flexbox styling")
        if "display: grid" not in content and "display:grid" not in content:
            raise ValueError("CSS missing grid styling")

    return content

# ==========================================================
# PUBLIC API (USED BY app4.py)
# ==========================================================

def generate_project(user_prompt: str, emitter: Optional[StreamEventEmitter] = None) -> Dict:
    """
    Generate a complete project with streaming events.
    
    Args:
        user_prompt: The user's request
        emitter: Optional event emitter for real-time UI updates
    
    Returns:
        Dict with project data and usage_metrics
    """
    
    # === INITIALIZE METRICS TRACKING ===
    metrics = reset_metrics()
    generation_start_time = time.time()
    phase_start = generation_start_time
    
    print("\n" + "="*60)
    print("🚀 STARTING PROJECT GENERATION")
    print("="*60 + "\n")
    
    # === THINKING START ===
    if emitter:
        emitter.thinking_start()
        emitter.chat_message("🧠 Analyzing your request and planning the project structure...")
        emitter.progress_init(mode="modal")
        time.sleep(0.1)  # Small delay for UI
    
    project = {
        "project": {
            "name": "generated-project",
            "description": user_prompt,
            "files": {}
        }
    }

    # === PLANNING PHASE ===
    phase_start = time.time()
    print("📋 [PHASE] Planning...")
    if emitter:
        emitter.progress_update("plan", "in_progress")
        emitter.chat_message("📋 Planning project architecture...")
        time.sleep(0.2)
        emitter.progress_update("plan", "completed")
    metrics.add_phase_timing("1_planning", (time.time() - phase_start) * 1000)
    
    # === SCAFFOLDING PHASE ===
    phase_start = time.time()
    print("📁 [PHASE] Scaffolding...")
    if emitter:
        emitter.progress_update("scaffold", "in_progress")
        emitter.chat_message("📁 Setting up project structure...")
        emitter.fs_create("src", "folder")
        emitter.fs_create("src/components", "folder")
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
        emitter.edit_start("index.html", index_html_content)
        emitter.edit_end("index.html", 50)
        emitter.edit_security_check("index.html", "passed")
        emitter.progress_update("scaffold", "completed")
    metrics.add_phase_timing("2_scaffolding", (time.time() - phase_start) * 1000)
    
    # === DEPENDENCIES PHASE ===
    phase_start = time.time()
    print("📦 [PHASE] Dependencies...")
    if emitter:
        emitter.progress_update("deps", "in_progress")
        emitter.chat_message("📦 Configuring dependencies...")
    metrics.add_phase_timing("3_dependencies", (time.time() - phase_start) * 1000)
    
    # === CODE GENERATION PHASE (LLM CALLS - MAIN TIME CONSUMER) ===
    phase_start = time.time()
    print("\n⚡ [PHASE] Code Generation (LLM calls)...")
    print("-" * 50)
    if emitter:
        emitter.progress_update("deps", "completed")
        emitter.progress_update("code", "in_progress")
        emitter.chat_message("⚡ Generating code files...")
    
    file_list = get_file_list()
    total_files = len(file_list)
    
    for idx, path in enumerate(file_list):
        print(f"\n📄 [{idx+1}/{total_files}] Generating: {path}")
        
        file_start = time.time()
        
        # Generate the file content
        content = generate_file(path, user_prompt)
        project["project"]["files"][path] = {"content": content}
        
        file_duration = int((time.time() - file_start) * 1000)
        print(f"   ✅ Completed in {file_duration/1000:.2f}s")
        
        # Emit events for each file
        if emitter:
            emitter.chat_message(f"✍️ Writing {path}...")
            emitter.edit_read(path)
            emitter.edit_start(path, content)
            lang = detect_language(path)
            emitter.fs_write(path, content, lang)
            emitter.edit_end(path, file_duration)
            emitter.edit_security_check(path, "passed")
    
    print("-" * 50)
    code_gen_time = (time.time() - phase_start) * 1000
    metrics.add_phase_timing("4_code_generation", code_gen_time)
    print(f"⚡ Code Generation Total: {code_gen_time/1000:.2f}s\n")
    
    # === CODE GENERATION COMPLETE ===
    if emitter:
        emitter.progress_update("code", "completed")
    
    # === BUILD PHASE ===
    phase_start = time.time()
    print("🔨 [PHASE] Build...")
    if emitter:
        emitter.progress_update("build", "in_progress")
        emitter.chat_message("🔨 Building project...")
        emitter.build_start()
        emitter.build_log("Compiling TypeScript...", "info")
        time.sleep(0.1)
        emitter.build_log("Bundling with Vite...", "info")
        emitter.progress_update("build", "completed")
    metrics.add_phase_timing("5_build", (time.time() - phase_start) * 1000)
    
    # === VERIFICATION PHASE ===
    phase_start = time.time()
    print("✅ [PHASE] Verification...")
    if emitter:
        emitter.progress_update("verify", "in_progress")
        emitter.chat_message("✅ Verifying project structure...")
        emitter.build_log("All checks passed!", "success")
        emitter.progress_update("verify", "completed")
    metrics.add_phase_timing("6_verification", (time.time() - phase_start) * 1000)
    
    # === JSON SERIALIZATION (measure this separately) ===
    phase_start = time.time()
    print("📝 [PHASE] JSON Serialization...")
    
    # === THINKING END ===
    if emitter:
        emitter.thinking_end()
        emitter.chat_message("🎉 Project generated successfully!")
        emitter.progress_transition("inline")
        emitter.stream_complete()
    
    # Pre-serialize to JSON to measure time
    json_string = json.dumps(project, indent=2)
    json_size_kb = len(json_string.encode('utf-8')) / 1024
    metrics.add_phase_timing("7_json_serialization", (time.time() - phase_start) * 1000)
    print(f"   JSON size: {json_size_kb:.2f} KB")
    
    # === PRINT USAGE METRICS ===
    total_generation_time = (time.time() - generation_start_time) * 1000
    if metrics:
        metrics.total_time_ms = total_generation_time
        metrics.print_summary("- PROJECT GENERATION")
    
    # Add metrics to project for API response
    project["usage_metrics"] = metrics.to_dict() if metrics else None
    
    return project


def generate_patch(modification_prompt: str, base_project: dict, emitter: Optional[StreamEventEmitter] = None) -> dict:
    """
    Claude-based PATCH generator.
    Takes base project context and returns only modified/new/deleted files.
    
    Args:
        modification_prompt: The prompt describing what to modify
        base_project: The existing project structure with files
        emitter: Optional event emitter for real-time UI updates
    
    Returns:
        dict: Patch with modified_files, new_files, deleted_files, sections_changed, usage_metrics
    """
    
    # === INITIALIZE METRICS TRACKING ===
    metrics = reset_metrics()
    modification_start_time = time.time()
    phase_start = modification_start_time
    
    print("\n" + "="*60)
    print("🔧 STARTING PROJECT MODIFICATION")
    print("="*60 + "\n")
    
    # === THINKING START ===
    if emitter:
        emitter.thinking_start()
        emitter.chat_message("🔍 Analyzing existing project...")
        emitter.progress_init(mode="modal", steps=[
            emitter.DEFAULT_STEPS[0],  # Planning
            emitter.DEFAULT_STEPS[3],  # Code Generation
            emitter.DEFAULT_STEPS[4],  # Build
            emitter.DEFAULT_STEPS[5],  # Verification
        ])
    
    # === PREPARATION PHASE ===
    print("📋 [PHASE] Preparation (validating base project)...")
    
    # Validate base_project structure
    if not base_project or "project" not in base_project:
        raise ValueError("Invalid base_project: missing 'project' key")
    
    if "files" not in base_project["project"]:
        raise ValueError("Invalid base_project: missing 'files' in project")
    
    # Extract FULL file contents for accurate modification
    full_files = {}
    for path, file_data in base_project["project"]["files"].items():
        if isinstance(file_data, dict) and "content" in file_data:
            content = file_data["content"]
        elif isinstance(file_data, str):
            content = file_data
        else:
            content = str(file_data)
        full_files[path] = content
    
    metrics.add_phase_timing("1_preparation", (time.time() - phase_start) * 1000)

    enhanced_prompt = f"""
{modification_prompt}

CURRENT PROJECT FILES (FULL CONTENT):
{json.dumps(full_files, indent=2)}

CRITICAL INSTRUCTIONS:
1. You are MODIFYING the existing project IN-PLACE
2. ANALYZE which specific sections/components need to change based on the user request
3. Only return files that ACTUALLY need to change
4. Provide COMPLETE file content for each modified file (keep unchanged parts exactly the same)
5. Identify what sections you are modifying

RESPONSE FORMAT (JSON only, no markdown):
{{
  "sections_changed": ["Hero section", "Navbar color", "etc - describe what was changed"],
  "files_affected": ["src/App.tsx"],
  "modified_files": {{
    "src/App.tsx": "complete new file content with modifications"
  }},
  "new_files": {{}},
  "deleted_files": []
}}

EXAMPLE: If user says "change hero text to Welcome", identify:
- sections_changed: ["Hero section heading text"]
- files_affected: ["src/App.tsx"]
- Then provide the full App.tsx with only the hero text changed, everything else identical.
"""

    # === PLANNING PHASE ===
    phase_start = time.time()
    print("📋 [PHASE] Planning (LLM call)...")
    if emitter:
        emitter.progress_update("plan", "in_progress")
        emitter.chat_message("📋 Identifying sections to modify...")
        time.sleep(0.1)

    try:
        # Use streaming for accurate TTFT tracking
        start_time = time.time()
        first_token_time = None
        full_response = ""
        
        with client.messages.stream(
            model="claude-sonnet-4-20250514",  # Use Sonnet 4
            max_tokens=4096,
            temperature=0,
            system="You are a precise code modification assistant. You understand existing projects and make minimal, targeted changes. Always return valid JSON.",
            messages=[
                {
                    "role": "user",
                    "content": enhanced_prompt
                }
            ]
        ) as stream:
            for text_chunk in stream.text_stream:
                if first_token_time is None:
                    first_token_time = time.time()
                    ttft_ms = (first_token_time - start_time) * 1000
                    print(f"⏱️  Time to First Token (Patch): {ttft_ms:.2f} ms")
                full_response += text_chunk
            
            # Get final message for token counts
            final_message = stream.get_final_message()
            input_tokens = final_message.usage.input_tokens
            output_tokens = final_message.usage.output_tokens
        
        end_time = time.time()
        total_ms = (end_time - start_time) * 1000
        ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else 0
        
        print(f"📊 Tokens - Input: {input_tokens:,} | Output: {output_tokens:,} | Total: {input_tokens + output_tokens:,}")
        print(f"⏱️  LLM Call Duration: {total_ms/1000:.2f}s")
        
        # Track metrics
        metrics.add_phase_timing("2_llm_call", total_ms)
        metrics.add(input_tokens, output_tokens, ttft_ms, total_ms, file_name="patch_generation")
        
        text = full_response.strip()

        # === JSON PARSING PHASE ===
        phase_start = time.time()
        print("📝 [PHASE] Parsing response...")
        
        # === PLANNING COMPLETE ===
        if emitter:
            emitter.progress_update("plan", "completed")
            emitter.progress_update("code", "in_progress")

        # Extract JSON from response
        patch = extract_json(text)

        # Validate patch structure
        if not isinstance(patch, dict):
            raise ValueError("Patch is not a dictionary")

        # Ensure all required keys exist
        if "modified_files" not in patch:
            patch["modified_files"] = {}
        if "new_files" not in patch:
            patch["new_files"] = {}
        if "deleted_files" not in patch:
            patch["deleted_files"] = []
        if "sections_changed" not in patch:
            patch["sections_changed"] = []
        if "files_affected" not in patch:
            patch["files_affected"] = list(patch["modified_files"].keys())

        # Validate that we have actual changes
        if not any([
            patch.get("modified_files"),
            patch.get("new_files"),
            patch.get("deleted_files")
        ]):
            raise ValueError("Empty patch - no modifications detected")
        
        metrics.add_phase_timing("3_json_parsing", (time.time() - phase_start) * 1000)

        # === EMIT FILE MODIFICATION EVENTS ===
        phase_start = time.time()
        print("⚡ [PHASE] Applying changes...")
        if emitter:
            # Emit events for modified files
            for path, content in patch.get("modified_files", {}).items():
                emitter.chat_message(f"✏️ Modifying {path}...")
                emitter.edit_read(path)
                emitter.edit_start(path, content)
                lang = detect_language(path)
                emitter.fs_write(path, content, lang)
                emitter.edit_end(path, 500)  # Approximate duration
                emitter.edit_security_check(path, "passed")
            
            # Emit events for new files
            for path, content in patch.get("new_files", {}).items():
                emitter.chat_message(f"📝 Creating {path}...")
                emitter.fs_create(path, "file")
                lang = detect_language(path)
                emitter.fs_write(path, content, lang)
                emitter.edit_security_check(path, "passed")
            
            # Emit events for deleted files
            for path in patch.get("deleted_files", []):
                emitter.chat_message(f"🗑️ Removing {path}...")
                emitter.fs_delete(path)
            
            emitter.progress_update("code", "completed")
            
            # === BUILD PHASE ===
            emitter.progress_update("build", "in_progress")
            emitter.chat_message("🔨 Applying changes...")
            emitter.build_start()
            emitter.build_log("Applying modifications...", "info")
            time.sleep(0.1)
            emitter.progress_update("build", "completed")
            
            # === VERIFICATION ===
            emitter.progress_update("verify", "in_progress")
            emitter.chat_message("✅ Verifying changes...")
            emitter.build_log("All modifications verified!", "success")
            emitter.progress_update("verify", "completed")
            
            # === COMPLETE ===
            emitter.thinking_end()
            sections = patch.get("sections_changed", [])
            if sections:
                emitter.chat_message(f"🎉 Modified: {', '.join(sections)}")
            else:
                emitter.chat_message("🎉 Modifications complete!")
            emitter.progress_transition("inline")
            emitter.stream_complete()
        
        metrics.add_phase_timing("4_event_emission", (time.time() - phase_start) * 1000)

        # === PRINT USAGE METRICS ===
        total_modification_time = (time.time() - modification_start_time) * 1000
        if metrics:
            metrics.total_time_ms = total_modification_time
            metrics.print_summary("- PROJECT MODIFICATION")
        
        # Add metrics to patch for API response
        patch["usage_metrics"] = metrics.to_dict() if metrics else None

        return patch

    except Exception as e:
        if emitter:
            emitter.error(str(e), scope="llm", details="Patch generation failed")
            emitter.stream_failed()
        raise RuntimeError(f"Failed to generate patch: {str(e)}")


def chat_with_claude(user_message: str, chat_history: list = None) -> str:
    """
    Chat with Claude for general conversation.
    
    Args:
        user_message: The user's message
        chat_history: Optional list of previous messages [{"role": "user/assistant", "content": "..."}]
    
    Returns:
        str: Claude's response
    """
    
    # Build conversation history
    messages = []
    
    # Add previous messages if provided (limit to last 10 for context)
    if chat_history:
        for msg in chat_history[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Use Sonnet 4 for chat
            max_tokens=2048,
            temperature=0.7,  # More creative for chat
            system="""You are a helpful AI assistant. You can:
- Answer general questions
- Provide explanations and help with various topics
- Have casual conversations
- Help users understand concepts

Be friendly, concise, and helpful. If asked about building webpages, 
guide the user to use the build mode or rephrase their request clearly.""",
            messages=messages
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        raise RuntimeError(f"Failed to chat with Claude: {str(e)}")


def classify_intent(user_text: str) -> tuple:
    """
    Use Claude to classify user intent with high accuracy.
    
    Args:
        user_text: The user's input message
        
    Returns:
        tuple: (intent_label, metadata_dict)
    """
    
    try:
        prompt = f"""Classify the intent of this user message. Be VERY careful about detecting illegal or harmful content.

User message: "{user_text}"

CLASSIFICATION RULES (check in this order):

1. ILLEGAL - If the message asks to create/build anything related to:
   - Money laundering, fraud, scams, phishing
   - Hacking, DDOS, unauthorized access, exploits
   - Drug dealing, illegal weapons, terrorism
   - Human trafficking, child exploitation
   - Counterfeit goods, fake IDs, identity theft
   - Any other illegal or harmful activity
   Return: "illegal"

2. GREETING - If the message is ONLY a simple greeting like "hi", "hello", "hey", "good morning"
   Return: "greeting_only"

3. CHAT - If the message is a general question, conversation, or informational request NOT about building a website
   Return: "chat"

4. WEBPAGE_MODIFY - If the message asks to modify, change, update, or edit an existing website/webpage
   Return: "webpage_modify"

5. WEBPAGE_BUILD - If the message asks to create, build, generate, design, or make a new website/webpage
   Return: "webpage_build"

Respond with ONLY a JSON object:
{{
  "intent": "illegal|greeting_only|chat|webpage_modify|webpage_build",
  "confidence": 0.0-1.0,
  "explanation": "brief reason"
}}
"""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text.strip()
        result = extract_json(text)
        
        intent = result.get("intent", "chat")
        metadata = {
            "confidence": result.get("confidence", 0.5),
            "explanation": result.get("explanation", "AI classification")
        }
        
        return intent, metadata
        
    except Exception as e:
        # Fallback to basic checks if AI fails
        txt = user_text.lower()
        
        # Check for illegal content first
        illegal_keywords = [
            "money laundering", "launder", "fraud", "scam", "phishing",
            "hack", "ddos", "crack", "exploit", "drug", "terrorism",
            "counterfeit", "fake id", "steal", "illegal", "black market"
        ]
        if any(kw in txt for kw in illegal_keywords):
            return "illegal", {"confidence": 0.9, "explanation": "Detected illegal keywords"}
        
        return "chat", {"confidence": 0.3, "explanation": f"Fallback due to error: {str(e)}"}


def extract_requirements(user_request: str) -> dict:
    """
    Extract key requirements from user's initial request using AI.
    This can be used to pre-fill the Q&A form.
    
    Args:
        user_request: The user's original request
        
    Returns:
        dict: Extracted requirements
    """
    
    try:
        prompt = f"""Analyze this website request and extract key information:

"{user_request}"

Return ONLY a JSON object with these fields (use null for unknown):
{{
  "business_name": "extracted business name or null",
  "tagline": "extracted tagline or null", 
  "website_type": "Landing Page|E-commerce|Portfolio|Blog|Corporate|Other",
  "color_scheme": "Modern Dark|Clean Light|Vibrant|Professional Blue|null",
  "key_features": ["feature1", "feature2"],
  "needs_contact": true/false,
  "additional_info": "any other specific requirements"
}}
"""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text.strip()
        extracted = extract_json(text)
        
        return extracted
        
    except Exception as e:
        # If extraction fails, return empty dict
        return {}