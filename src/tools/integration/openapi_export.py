from mcp.server.fastmcp import FastMCP
from typing import Dict, Any
from src.state import state
import json
import yaml

def export_to_openapi(title: str = "API Export", version: str = "1.0.0", format: str = "yaml"):
    """
    Export all saved requests (from `make_request` with `save_as`) to an OpenAPI 3.0 Specification.
    
    Args:
        title: Title of the API.
        version: Version string.
        format: "yaml" or "json".
    """
    paths = {}
    
    for name, req in state.saved_requests.items():
        # Heuristic to find path vs host
        # e.g. http://localhost:8000/users/1 -> /users/1
        url = req.url
        path = "/" + "/".join(url.split("/")[3:]) if "http" in url else url
        
        # OpenAPI requires templated paths to use {}, but we use {{}}
        # Convert {{var}} to {var} for standard compliance
        path = path.replace("{{", "{").replace("}}", "}")
        
        if path not in paths:
            paths[path] = {}
            
        method = req.method.lower()
        
        paths[path][method] = {
            "summary": name,
            "description": req.description or f"Request for {name}",
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {} # Schema inference impossible without response examples
                    }
                }
            }
        }
        
        # Basic Body Config
        if req.body:
             paths[path][method]["requestBody"] = {
                 "content": {
                     "application/json": {
                         "example": req.body
                     }
                 }
             }

    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version
        },
        "paths": paths
    }
    
    if format.lower() == "json":
        return json.dumps(openapi_spec, indent=2)
    else:
        return yaml.dump(openapi_spec, sort_keys=False)

def register_openapi_tool(mcp: FastMCP):
    mcp.tool()(export_to_openapi)
