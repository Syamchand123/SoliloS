from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import asyncio
import time
import numpy as np
from src.tools.request_tools import make_request

async def realistic_load_test(scenario: Dict[str, Any]):
    """
    Run a sophisticated load test with different user profiles (Virtual Users).
    
    Args:
        scenario: Dictionary defining the test. Example:
            {
                "duration": 30,  # seconds
                "users": {
                    "browsers": { "count": 10, "endpoint": "/home" },
                    "api_clients": { "count": 2, "endpoint": "/api/v1/status" }
                }
            }
            
    Usage:
        Use this to simulate real-world traffic with mixed usage patterns.
    """
    duration = scenario.get("duration", 10)
    users_config = scenario.get("users", {})
    
    start_time = time.time()
    results = []
    
    async def simulate_user(user_type: str, config: Dict):
        endpoint = config.get("endpoint")
        # In a real tool, we'd use 'pattern' and resolve it to a workflow
        
        while time.time() - start_time < duration:
            # Simulate 'Think Time'
            await asyncio.sleep(np.random.uniform(0.1, 1.0))
            
            res = await make_request("GET", endpoint) # Simplification
            res["user_type"] = user_type
            results.append(res)
            
    tasks = []
    for u_type, cfg in users_config.items():
        count = cfg.get("count", 1)
        for _ in range(count):
            tasks.append(simulate_user(u_type, cfg))
            
    # Run
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        pass # Timeout or cancel logic
        
    # Validations & Stats
    latencies = [r.get("time_ms", 0) for r in results if not r.get("error")]
    errors = [r for r in results if r.get("error")]
    
    return {
        "total_requests": len(results),
        "errors": len(errors),
        "throughput_rps": round(len(results) / duration, 2),
        "p95_latency": round(np.percentile(latencies, 95), 2) if latencies else 0,
        "details": f"Ran for {duration}s with {len(tasks)} virtual users."
    }

def register_load_tools(mcp: FastMCP):
    mcp.tool()(realistic_load_test)
