from mcp.server.fastmcp import FastMCP
from typing import Dict, Any
from src.tools.request_tools import make_request
import asyncio
import time

async def test_rate_limiting(endpoint: str, max_requests: int = 50):
    """
    Test endpoint rate limiting by sending bursts of concurrent requests.
    
    Effect:
    - Sends requests in batches of 5.
    - Stops immediately if 429 Too Many Requests is received.
    - Returns details on the rate limit headers (X-RateLimit-Remaining, etc).
    """
    results = []
    start_time = time.time()
    limit_hit = False
    limit_headers = {}
    
    # Send bursts of 5
    for i in range(0, max_requests, 5):
        tasks = [make_request("GET", endpoint) for _ in range(5)]
        batch_results = await asyncio.gather(*tasks)
        
        for res in batch_results:
            status = res.get("status")
            if status == 429:
                limit_hit = True
                limit_headers = res.get("headers", {})
                break
        
        if limit_hit:
            break
            
        time.sleep(0.1) # Small safety delay
        
    analysis = {
        "rate_limit_detected": limit_hit,
        "requests_sent": i + 5 if not limit_hit else "Approx " + str(i),
        "headers_found": {}
    }
    
    if limit_hit:
        # Extract Standard Rate Limit Headers
        for h in ["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"]:
             # Case insensitive lookup
             for k, v in limit_headers.items():
                 if k.lower() == h.lower():
                     analysis["headers_found"][h] = v
                     
    return analysis

def register_rate_limit_tool(mcp: FastMCP):
    mcp.tool()(test_rate_limiting)
