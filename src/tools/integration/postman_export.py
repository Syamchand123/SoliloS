from mcp.server.fastmcp import FastMCP
from typing import Dict, Any
from src.state import state
import json
import uuid

def export_to_postman(collection_name: str = "MCP Export"):
    """
    Generate a Postman Collection (v2.1) JSON from the server's current state.
    
    Includes:
    - All requests saved via `save_as`.
    - All workflows saved via `run_workflow`.
    - Current environment variables.
    
    Returns:
        JSON string representing the Postman Collection.
    """
    collection_id = str(uuid.uuid4())
    
    item_list = []
    
    # 1. Export Saved Requests
    for name, req in state.saved_requests.items():
        # Postman Request Object
        pm_req = {
            "name": name,
            "request": {
                "method": req.method,
                "header": [{"key": k, "value": v} for k, v in req.headers.items()],
                "url": {
                    "raw": req.url,
                    "host": req.url.split("/")[:3] # simplification
                },
                "description": req.description
            }
        }
        
        if req.body:
            pm_req["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(req.body) if isinstance(req.body, (dict, list)) else str(req.body)
            }
            
        item_list.append(pm_req)
        
    # 2. Export Workflows (as Folders)
    for wf_name, wf in state.saved_workflows.items():
        folder_items = []
        for step_name in wf.steps:
            if step_name in state.saved_requests:
                # Copy existing request logic
                r = state.saved_requests[step_name]
                # ... (reuse mapping logic would be better, duplicating for minimal dependency)
                folder_items.append({
                    "name": step_name,
                    "request": {
                        "method": r.method,
                        "header": [{"key": k, "value": v} for k, v in r.headers.items()],
                        "url": {"raw": r.url}
                    }
                })
                
        item_list.append({
            "name": wf_name,
            "item": folder_items
        })

    collection = {
        "info": {
            "_postman_id": collection_id,
            "name": collection_name,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": item_list,
        "variable": [
            {"key": k, "value": v} for k, v in state.variables.items()
        ]
    }
    
    return json.dumps(collection, indent=2)

def register_postman_tool(mcp: FastMCP):
    mcp.tool()(export_to_postman)
