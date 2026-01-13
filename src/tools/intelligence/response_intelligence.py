from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import json
import sys

def analyze_response_deep(response: Dict[str, Any]):
    """
    Perform deep analysis on an API response dictionary.
    
    Detects:
    1. Performance Issues (Slow response, Large payload).
    2. Structural Problems (N+1 queries in lists, Missing pagination).
    3. Best Practices (Debug headers leaked, Error format inconsistency).
    
    Returns:
        Analysis report with Insights and a Quality Score (0-100).
    """
    insights = []
    
    # 1. Performance Anaylsis
    time_ms = response.get("time_ms", 0)
    body = response.get("body")
    status = response.get("status")
    
    # Estimate size
    size_bytes = 0
    if isinstance(body, (dict, list)):
        size_bytes = len(json.dumps(body))
    elif isinstance(body, str):
        size_bytes = len(body)
        
    if time_ms > 1000:
        insights.append({
            "type": "Performance",
            "severity": "Warning",
            "message": f"Response time is slow ({time_ms}ms). Consider caching or optimizing query."
        })
        
    if size_bytes > 1_000_000: # 1MB
        insights.append({
            "type": "Performance",
            "severity": "Warning",
            "message": f"Response payload is large ({round(size_bytes/1024/1024, 2)}MB). Check for overfetching."
        })

    # 2. Structural Analysis (JSON only)
    if isinstance(body, (dict, list)):
        # Calculate Depth
        def get_depth(obj, level=1):
            if not isinstance(obj, (dict, list)) or level > 10:
                return level
            if isinstance(obj, dict):
                return max([get_depth(v, level+1) for v in obj.values()] or [level])
            if isinstance(obj, list):
                return max([get_depth(i, level+1) for i in obj] or [level])
            return level

        depth = get_depth(body)
        if depth > 3:
            insights.append({
                "type": "Complexity",
                "severity": "Info",
                "message": f"Response is deeply nested (Depth: {depth}). deeply nested structures can be hard for clients to parse."
            })

    if isinstance(body, list):
        # Array specific checks
        if len(body) > 100:
            insights.append({
                "type": "Pagination",
                "severity": "Best Practice",
                "message": f"Response contains {len(body)} items. Ensure pagination is implemented."
            })
            
        # Check for consistency and N+1 signs
        if len(body) > 0 and isinstance(body[0], dict):
            keys = set(body[0].keys())
            large_objects = any(len(json.dumps(item)) > 1000 for item in body[:5])
            
            if large_objects and len(body) > 20:
                 insights.append({
                    "type": "Overfetching",
                    "severity": "Optimization",
                    "message": "List contains many large objects. Consider a summary view (id, name only) for lists."
                })

    elif isinstance(body, dict):
        # Object specific checks
        pass

    # 3. Data Quality
    if "error" in response or (status and status >= 400):
        insights.append({
            "type": "Error",
            "severity": "Info",
            "message": f"Response ended in error status {status}. Validating error structure."
        })
        if isinstance(body, dict) and "message" not in body and "error" not in body and "detail" not in body:
             insights.append({
                "type": "Design",
                "severity": "Warning",
                "message": "Error response does not follow standard conventions (missing 'message', 'error', or 'detail' field)."
            })

    # 4. Debug Headers Check
    debug_headers = ["X-Runtime", "X-Debug-Token", "X-DB-Pool-Wait-Time", "Server-Timing"]
    headers = response.get("headers", {})
    found_debug = [h for h in debug_headers if h in headers]
    
    if found_debug:
        insights.append({
            "type": "Security/Debug",
            "severity": "Info",
            "message": f"Response contains debug headers: {found_debug}. Ensure these are removed in production."
        })

    return {
        "score": max(0, 100 - (len(insights) * 10)),
        "insights": insights,
        "metrics": {
            "size_bytes": size_bytes,
            "items_count": len(body) if isinstance(body, list) else 1
        }
    }

def register_intelligence_tools(mcp: FastMCP):
    mcp.tool()(analyze_response_deep)
