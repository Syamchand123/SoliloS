from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
from src.tools.request_tools import make_request
import asyncio
import random

async def chaos_test(endpoint: str, scenarios: List[str] = ["delay", "fail"]):
    """
    Simulate client-side chaos or send malformed requests to test server resilience.
    
    Args:
        endpoint: Target URL.
        scenarios: List of chaos modes to run. Options:
            - "malformed_json": Sends invalid JSON to see if server crashes (500) or handles gracefully (400).
            - "concurrent_spam": Sends a burst of parallel requests to test race conditions.
    """
    
    results = []
    
    for mode in scenarios:
        if mode == "malformed_json":
             # Send bad json
             res = await make_request("POST", endpoint, body="{bad keys")
             results.append({"mode": mode, "status": res.get("status")})
             
        elif mode == "concurrent_spam":
             # Try to race
             tasks = [make_request("GET", endpoint) for _ in range(10)]
             await asyncio.gather(*tasks)
             results.append({"mode": mode, "status": "Done"})
             
    return {"chaos_results": results}

def register_chaos_tool(mcp: FastMCP):
    mcp.tool()(chaos_test)
