from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import asyncio
import time
from src.tools.request_tools import make_request

async def stress_test(endpoint: str, start_users: int = 5, step_users: int = 5, max_users: int = 50, duration_per_step: int = 5):
    """
    Gradually increase concurrency to find the API's breaking point.
    
    Process:
    1. Start with `start_users`.
    2. Add `step_users` after each iteration.
    3. Stop if Error Rate > 10% or `max_users` is reached.
    
    Returns:
        The "Breaking Point" (max users sustained before errors).
    """
    current_users = start_users
    results = []
    breaking_point = None
    
    print(f"Starting Stress Test: {endpoint}")
    
    while current_users <= max_users:
        step_start = time.time()
        errors = 0
        latencies = []
        
        # Launch concurrent requests
        # In a real tool we'd loop for 'duration_per_step'
        # Simplified: Just fire one batch of 'current_users' requests
        
        tasks = [make_request("GET", endpoint) for _ in range(current_users)]
        batch_res = await asyncio.gather(*tasks)
        
        for res in batch_res:
            if res.get("status") >= 500 or res.get("error"):
                errors += 1
            else:
                latencies.append(res.get("time_ms", 0))
                
        # Analysis
        if latencies:
            avg_lat = sum(latencies) / len(latencies)
        else:
            avg_lat = 0
            
        step_result = {
            "users": current_users,
            "errors": errors,
            "avg_latency": round(avg_lat, 2)
        }
        results.append(step_result)
        
        # Check for failure (Threshold: > 10% errors)
        if errors > (current_users * 0.1):
            breaking_point = f"Failed at {current_users} users (Error Rate: {round(errors/current_users*100, 1)}%)"
            break
            
        current_users += step_users
        await asyncio.sleep(1) # Cooldown
        
    return {
        "breaking_point": breaking_point or "Did not break within limits",
        "max_users_tested": current_users if breaking_point else max_users,
        "step_results": results
    }

def register_stress_tool(mcp: FastMCP):
    mcp.tool()(stress_test)
