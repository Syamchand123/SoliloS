from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
from src.tools.validation.breaking_changes import compare_api_versions
import asyncio

async def compare_environments(endpoints: List[str], environments: Dict[str, str]):
    """
    Run breaking change detection across a LIST of endpoints between two environments.
    
    Args:
        endpoints: List of relative paths (e.g. ["/api/users", "/api/orders"]).
        environments: Dictionary with exactly two keys. Example:
            {"staging": "https://stm.api.com", "prod": "https://api.com"}
            
    Returns:
        Summary report of compatibility for each endpoint.
    """
    if len(environments) != 2:
        return {"error": "Currently supports exactly 2 environments for comparison"}
        
    names = list(environments.keys())
    url_a_base = environments[names[0]]
    url_b_base = environments[names[1]]
    
    results = []
    
    for path in endpoints:
        # Construct full URLs
        url_a = f"{url_a_base.rstrip('/')}/{path.lstrip('/')}"
        url_b = f"{url_b_base.rstrip('/')}/{path.lstrip('/')}"
        
        diff = await compare_api_versions(url_a, url_b)
        
        results.append({
            "endpoint": path,
            "compatible": diff.get("is_compatible"),
            "changes": diff.get("breaking_changes")
        })
        
    return {
        "summary": f"Compared {len(endpoints)} endpoints between {names[0]} and {names[1]}",
        "details": results
    }

def register_env_comparison_tool(mcp: FastMCP):
    mcp.tool()(compare_environments)
