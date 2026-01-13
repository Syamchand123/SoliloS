from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
from src.tools.request_tools import make_request
import asyncio
import os

COMMON_PATHS = [
    "/api", "/v1", "/health", "/swagger", "/docs", "/graphql", "/metrics",
    "/openapi.json", "/redoc"
]

import json
try:
    from haralyzer import HarParser, HarPage
    HAS_HAR = True
except ImportError:
    HAS_HAR = False

async def discover_api(base_url: str):
    """
    Scan a base URL for common API endpoints.
    
    Checks for: /api, /v1, /health, /swagger, /docs, /graphql, /metrics.
    Usage: Use this when you have a base URL but don't know the specific paths.
    """
    found = []
    
    # Clean base url
    base = base_url.rstrip("/")
    
    tasks = [make_request("GET", f"{base}{path}") for path in COMMON_PATHS]
    results = await asyncio.gather(*tasks)
    
    for i, res in enumerate(results):
        status = res.get("status")
        if status and status < 404:
            found.append({
                "path": COMMON_PATHS[i],
                "status": status,
                "type": "Probable Endpoint"
            })
            
    return {
        "base_url": base_url,
        "endpoints_found": len(found),
        "details": found
    }

def reverse_engineer_har(har_file_path: str):
    """
    Extract API endpoints and methods from a recorded HAR (HTTP Archive) file.
    
    Args:
        har_file_path: Absolute path to the .har file (must be within the allowed workspace).
    """
    if not HAS_HAR:
        return {"error": "haralyzer package not installed"}
        
    
    
    # Path Traversal Check
    safe_base = os.getcwd()
    abs_path = os.path.abspath(har_file_path)
    if not abs_path.startswith(safe_base):
        return {"error": "Security Alert: Access to external files is forbidden."}
        
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
            
        parser = HarParser(har_data)
        endpoints = set()
        
        for page in parser.pages:
            for entry in page.entries:
                req = entry.request
                # Basic normalization
                url = req.url.split("?")[0]
                endpoints.add(f"{req.method} {url}")
                
        return {
            "source": har_file_path,
            "unique_endpoints": len(endpoints),
            "endpoints": sorted(list(endpoints))
        }
    except Exception as e:
        return {"error": str(e)}

def reverse_engineer_api(log_data: str):
    """
    Parse raw text logs to find potential API paths using Regex.
    
    Looks for patterns like "GET /api/v1/users HTTP/1.1".
    """
    import re
    # Look for "METHOD /path HTTP" pattern
    # e.g. "GET /api/users/123 HTTP/1.1"
    pattern = r"(GET|POST|PUT|DELETE|PATCH)\s+([/\w\d\-\.]+)"
    
    found = set()
    for match in re.finditer(pattern, log_data):
        method, path = match.groups()
        found.add(f"{method} {path}")
        
    return {
        "inferred_endpoints": list(found)
    }

def register_discovery_tools(mcp: FastMCP):
    mcp.tool()(discover_api)
    mcp.tool()(reverse_engineer_api)
    mcp.tool()(reverse_engineer_har)
