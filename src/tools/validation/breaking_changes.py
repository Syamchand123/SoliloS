from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
from src.tools.request_tools import make_request
import asyncio

def detect_breaking_changes(old_resp: Dict, new_resp: Dict):
    """
    Compare two API responses to identify backward-incompatible changes.
    
    Checks:
    - Status Code change.
    - Key removals from JSON body (Breaking).
    - Data Type changes (e.g., String -> Integer) (Breaking).
    
    Returns:
        List of issues or "Compatible".
    """
    issues = []
    
    # 1. Status Code
    if old_resp.get("status") != new_resp.get("status"):
        issues.append(f"Status changed from {old_resp.get('status')} to {new_resp.get('status')}")
        
    # 2. Key Removal (Breaking)
    old_body = old_resp.get("body", {})
    new_body = new_resp.get("body", {})
    
    if isinstance(old_body, dict) and isinstance(new_body, dict):
        missing_keys = set(old_body.keys()) - set(new_body.keys())
        if missing_keys:
            issues.append(f"BREAKING: Keys removed: {list(missing_keys)}")
            
        # Check type changes
        for k in old_body:
            if k in new_body:
                t1 = type(old_body[k]).__name__
                t2 = type(new_body[k]).__name__
                if t1 != t2:
                    issues.append(f"BREAKING: Type changed for '{k}': {t1} -> {t2}")

    return {
        "is_compatible": len(issues) == 0,
        "breaking_changes": issues
    }

async def compare_api_versions(url_v1: str, url_v2: str, method: str = "GET"):
    """
    Fetch and compare the same endpoint from two different URLs (v1 vs v2).
    
    Effect:
        Runs GET requests against both URLs and feeds results to `detect_breaking_changes`.
    """
    r1, r2 = await asyncio.gather(
        make_request(method, url_v1),
        make_request(method, url_v2)
    )
    
    return detect_breaking_changes(r1, r2)

def register_breaking_change_tools(mcp: FastMCP):
    mcp.tool()(detect_breaking_changes)
    mcp.tool()(compare_api_versions)
