from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
from src.state import state
from src.tools.request_tools import make_request
import logging

logger = logging.getLogger(__name__)

async def test_user_flow(flow_definition: Dict[str, Any]):
    """
    Execute a defined multi-step user journey.
    
    Args:
        flow_definition: {
            "name": "Checkout Flow",
            "steps": [
                {"action": "Login", "method": "POST", "url": "/login", "body": {"user": "test"}},
                {"action": "Add to Cart", "method": "POST", "url": "/cart", "body": {"item": "123"}}
            ],
            "rollback_on_failure": true
        }
        
    Returns:
        Step-by-step execution capabilities log.
    """
    steps = flow_definition.get("steps", [])
    name = flow_definition.get("name", "Unnamed Flow")
    
    executed_steps = []
    error = None
    
    # Execution
    for i, step in enumerate(steps):
        action = step.get("action") # e.g. "login" -> mapped to a request or arbitrary name
        # For this tool, we assume 'action' implies a construct request object or raw request
        # Simplified: expecting 'method' and 'url' directly in step for MVP
        
        method = step.get("method", "GET")
        url = step.get("url")
        
        if not url:
             executed_steps.append({"step": i, "error": "Missing URL"})
             error = "Invalid Step Definition"
             break
             
        res = await make_request(method, url, body=step.get("body"), headers=step.get("headers"))
        
        if res.get("status") and res.get("status") >= 400:
            error = f"Step {i} ({action}) failed with status {res.get('status')}"
            break
            
        executed_steps.append({"step": i, "action": action, "status": res.get("status")})
        
        # Extraction
        if "extract" in step:
            extract_map = step["extract"]
            from src.tools.workflow_tools import get_nested_value
            for var_name, path in extract_map.items():
                val = None
                if path.startswith("body."):
                    val = get_nested_value(res.get("body"), path[5:])
                elif path.startswith("headers."):
                    val = get_nested_value(res.get("headers"), path[8:])
                elif path == "status":
                    val = res.get("status")
                    
                if val is not None:
                    state.variables[var_name] = str(val)
                    executed_steps[-1][f"extracted_{var_name}"] = str(val)
            
    # Rollback Logic
    if error and flow_definition.get("rollback_on_failure"):
        logger.info("Flow failed. Initiating Rollback...")
        # In a real app, we'd look up inverse actions (DELETE for POST)
        # Here we just log it as a placeholder for the logic
        executed_steps.append({"info": "Rollback triggered (Not fully implemented in MVP)"})
        
    return {
        "flow": name,
        "success": error is None,
        "error": error,
        "history": executed_steps
    }

def register_complex_flow_tool(mcp: FastMCP):
    mcp.tool()(test_user_flow)
