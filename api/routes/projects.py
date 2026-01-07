"""
Project Management Routes
List, fetch, and manage generated projects
"""

import json
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from api.schemas import ProjectResponse, ProjectListResponse, ProjectListItem

router = APIRouter()

# Directories
OUTPUT_DIR = Path("output")
MODIFIED_DIR = Path("modified_output")


# ==========================================================
# HELPERS
# ==========================================================

def load_project(file_path: Path) -> dict:
    """Load a project from disk."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_project_files(project_data: dict) -> dict:
    """Extract file contents from project."""
    files = {}
    for path, file_data in project_data.get("project", {}).get("files", {}).items():
        if isinstance(file_data, dict):
            files[path] = file_data.get("content", "")
        else:
            files[path] = str(file_data)
    return files


def project_to_list_item(file_path: Path) -> ProjectListItem:
    """Convert a project file to a list item."""
    try:
        data = load_project(file_path)
        metadata = data.get("metadata", {})
        files = data.get("project", {}).get("files", {})
        
        return ProjectListItem(
            id=file_path.stem,
            version=metadata.get("version", 0),
            is_modification=metadata.get("is_modification", False),
            created_at=metadata.get("created_at", metadata.get("timestamp", "")),
            file_count=len(files)
        )
    except Exception as e:
        return ProjectListItem(
            id=file_path.stem,
            version=0,
            is_modification=False,
            created_at="",
            file_count=0
        )


# ==========================================================
# ENDPOINTS
# ==========================================================

@router.get("/projects", response_model=ProjectListResponse, tags=["Projects"])
async def list_projects(
    type: Optional[str] = Query(None, description="Filter by type: 'original' or 'modified'"),
    limit: int = Query(50, description="Maximum number of projects to return", ge=1, le=100),
    offset: int = Query(0, description="Number of projects to skip", ge=0)
):
    """
    List all projects.
    
    **Query Parameters:**
    - `type`: Filter by 'original' or 'modified'
    - `limit`: Max projects to return (default 50)
    - `offset`: Pagination offset
    
    **Response:**
    ```json
    {
        "total": 10,
        "projects": [
            {
                "id": "project_v1_20250101_120000",
                "version": 1,
                "is_modification": false,
                "created_at": "2025-01-01T12:00:00",
                "file_count": 5
            }
        ]
    }
    ```
    """
    projects = []
    
    # Collect project files
    if type == "original":
        files = list(OUTPUT_DIR.glob("project_v*.json"))
    elif type == "modified":
        files = list(MODIFIED_DIR.glob("project_v*.json"))
    else:
        files = list(OUTPUT_DIR.glob("project_v*.json")) + list(MODIFIED_DIR.glob("project_v*.json"))
    
    # Sort by modification time (newest first)
    files = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
    
    total = len(files)
    
    # Apply pagination
    files = files[offset:offset + limit]
    
    # Convert to list items
    for file_path in files:
        projects.append(project_to_list_item(file_path))
    
    return ProjectListResponse(total=total, projects=projects)


@router.get("/projects/latest", tags=["Projects"])
async def get_latest_project(
    type: Optional[str] = Query(None, description="Filter by type: 'original' or 'modified'")
):
    """
    Get the most recent project.
    
    **Query Parameters:**
    - `type`: 'original' or 'modified' (default: any)
    
    **Response:**
    Returns the full project with all files.
    """
    # Find latest project
    if type == "original":
        folders = [OUTPUT_DIR]
    elif type == "modified":
        folders = [MODIFIED_DIR]
    else:
        folders = [MODIFIED_DIR, OUTPUT_DIR]  # Prefer modified
    
    latest_file = None
    latest_time = 0
    
    for folder in folders:
        for f in folder.glob("project_v*.json"):
            mtime = f.stat().st_mtime
            if mtime > latest_time:
                latest_time = mtime
                latest_file = f
    
    if not latest_file:
        raise HTTPException(status_code=404, detail="No projects found")
    
    data = load_project(latest_file)
    
    return {
        "id": latest_file.stem,
        "path": str(latest_file),
        "metadata": data.get("metadata", {}),
        "files": get_project_files(data)
    }


@router.get("/projects/{project_id}", tags=["Projects"])
async def get_project(project_id: str):
    """
    Get a specific project by ID.
    
    **Path Parameters:**
    - `project_id`: The project ID (filename without extension)
    
    **Example:**
    ```
    GET /api/projects/project_v1_20250101_120000
    ```
    
    **Response:**
    ```json
    {
        "id": "project_v1_20250101_120000",
        "path": "output/project_v1_20250101_120000.json",
        "metadata": {
            "version": 1,
            "is_modification": false,
            "created_at": "2025-01-01T12:00:00"
        },
        "files": {
            "index.html": "<!DOCTYPE html>...",
            "src/App.tsx": "export function App()..."
        }
    }
    ```
    """
    # Search in both directories
    for folder in [OUTPUT_DIR, MODIFIED_DIR]:
        # Try exact match first
        exact_path = folder / f"{project_id}.json"
        if exact_path.exists():
            data = load_project(exact_path)
            return {
                "id": project_id,
                "path": str(exact_path),
                "metadata": data.get("metadata", {}),
                "files": get_project_files(data)
            }
        
        # Try partial match
        matches = list(folder.glob(f"*{project_id}*.json"))
        if matches:
            file_path = matches[0]
            data = load_project(file_path)
            return {
                "id": file_path.stem,
                "path": str(file_path),
                "metadata": data.get("metadata", {}),
                "files": get_project_files(data)
            }
    
    raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


@router.get("/projects/{project_id}/files", tags=["Projects"])
async def list_project_files(project_id: str):
    """
    List files in a project without content.
    
    **Response:**
    ```json
    {
        "project_id": "project_v1_20250101_120000",
        "files": [
            {"path": "index.html", "size": 500},
            {"path": "src/App.tsx", "size": 1200}
        ]
    }
    ```
    """
    # Find project
    for folder in [OUTPUT_DIR, MODIFIED_DIR]:
        for pattern in [f"{project_id}.json", f"*{project_id}*.json"]:
            matches = list(folder.glob(pattern))
            if matches:
                file_path = matches[0]
                data = load_project(file_path)
                
                files_list = []
                for path, file_data in data.get("project", {}).get("files", {}).items():
                    if isinstance(file_data, dict):
                        content = file_data.get("content", "")
                    else:
                        content = str(file_data)
                    
                    files_list.append({
                        "path": path,
                        "size": len(content)
                    })
                
                return {
                    "project_id": file_path.stem,
                    "files": files_list
                }
    
    raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


@router.get("/projects/{project_id}/files/{file_path:path}", tags=["Projects"])
async def get_project_file(project_id: str, file_path: str):
    """
    Get a specific file from a project.
    
    **Example:**
    ```
    GET /api/projects/project_v1_20250101_120000/files/src/App.tsx
    ```
    
    **Response:**
    ```json
    {
        "project_id": "project_v1_20250101_120000",
        "file_path": "src/App.tsx",
        "content": "export function App() { ... }",
        "size": 1200
    }
    ```
    """
    # Find project
    for folder in [OUTPUT_DIR, MODIFIED_DIR]:
        for pattern in [f"{project_id}.json", f"*{project_id}*.json"]:
            matches = list(folder.glob(pattern))
            if matches:
                project_path = matches[0]
                data = load_project(project_path)
                
                files = data.get("project", {}).get("files", {})
                
                if file_path not in files:
                    raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
                
                file_data = files[file_path]
                if isinstance(file_data, dict):
                    content = file_data.get("content", "")
                else:
                    content = str(file_data)
                
                return {
                    "project_id": project_path.stem,
                    "file_path": file_path,
                    "content": content,
                    "size": len(content)
                }
    
    raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


@router.delete("/projects/{project_id}", tags=["Projects"])
async def delete_project(project_id: str):
    """
    Delete a project.
    
    **Warning:** This permanently deletes the project file.
    """
    # Find and delete project
    for folder in [OUTPUT_DIR, MODIFIED_DIR]:
        for pattern in [f"{project_id}.json", f"*{project_id}*.json"]:
            matches = list(folder.glob(pattern))
            if matches:
                file_path = matches[0]
                file_path.unlink()
                return {
                    "success": True,
                    "deleted": file_path.stem,
                    "message": f"Project {file_path.stem} deleted"
                }
    
    raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

