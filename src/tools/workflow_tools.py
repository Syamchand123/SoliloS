from mcp.server.fastmcp import FastMCP
from src.state import state, WorkflowModel
from src.tools.request_tools import make_request
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_nested_value(data: Any, path: str) -> Any:
    """
    Extract a value from a nested dictionary/list structure using dot notation.
    
    Args:
        data: The root dictionary or list.
        path: Path string, e.g. "users.0.profile.email".
        
    Returns:
        The found value, or None if the path doesn't exist.
    """
    parts = path.split('.')
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            if 0 <= idx < len(current):
                current = current[idx]
            else:
                return None
        else:
            return None
        if current is None:
            return None
    return current

async def run_workflow(steps: List[Dict[str, Any]], workflow_name: Optional[str] = None):
    """
    Run a sequence of requests as a workflow.
    
    Args:
        steps: List of step definitions. Examples:
            [
                { "method": "POST", "url": "https://api.com/login", "body": {...}, "extract": {"auth_token": "body.token"} },
                { "method": "GET", "url": "https://api.com/users/me", "headers": {"Authorization": "Bearer {{auth_token}}"} }
            ]
        workflow_name: Optional name to save this workflow definition.
        
    Extraction:
        Use "extract": {"var_name": "path"} to save response data to variables.
        Paths: "body.key", "headers.key", "status".
    """
    results = []
    
    for i, step in enumerate(steps):
        step_id = f"step_{i+1}"
        logger.info(f"Running step {i+1}")
        
        # Determine Request Parameters
        if "request_name" in step:
            # Load saved request
            req_name = step["request_name"]
            if req_name not in state.saved_requests:
                return {"error": f"Saved request '{req_name}' not found", "step": i+1}
            saved = state.saved_requests[req_name]
            method = saved.method
            url = saved.url
            body = saved.body
            headers = saved.headers
        else:
            # Raw request
            method = step.get("method", "GET")
            url = step.get("url")
            body = step.get("body")
            headers = step.get("headers", {})
            
        if not url:
             return {"error": "Missing URL in step", "step": i+1}
        
        # Invoke make_request directly
        response = await make_request(method, url, body, headers)
        
        if "error" in response:
            return {"error": f"Step {i+1} failed: {response['error']}", "results": results}
            
        results.append({
            "step": i+1,
            "status": response.get("status"),
            "url": url, 
            "time_ms": response.get("time_ms")
        })
        
        # Extraction Logic
        if "extract" in step:
            extract_map = step["extract"]
            for var_name, path in extract_map.items():
                if path.startswith("body."):
                    val = get_nested_value(response.get("body"), path[5:])
                elif path.startswith("headers."):
                    val = get_nested_value(response.get("headers"), path[8:])
                elif path == "status":
                    val = response.get("status")
                else:
                    val = None
                    
                if val is not None:
                    state.variables[var_name] = str(val)
                    results[-1][f"extracted_{var_name}"] = str(val)
                else:
                    results[-1][f"extracted_{var_name}"] = "NOT_FOUND"

    if workflow_name:
        state.saved_workflows[workflow_name] = WorkflowModel(name=workflow_name, steps=[s.get("request_name", "raw") for s in steps])

    return {"status": "success", "steps_completed": len(results), "details": results}

def list_workflows():
    """
    List the names of all currently saved workflows.
    """
    return list(state.saved_workflows.keys())

def register_workflow_tools(mcp: FastMCP):
    mcp.tool()(run_workflow)
    mcp.tool()(list_workflows)
