from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import time
import asyncio
import numpy as np
from src.tools.request_tools import make_request

def validate_response(response: Dict[str, Any], expectations: Dict[str, Any]):
    """
    Validate a response against a set of expectations.
    
    Args:
        response: The dictionary result from a `make_request` call.
        expectations: Dictionary of checks to run. Example:
            {
                "status": 200,
                "max_time_ms": 1000,
                "body_contains": ["success", "user_id"],
                "headers_contain": {"Content-Type": "application/json"}
            }
    
    Returns:
        {"passed": boolean, "failures": list_of_strings}
    """
    failures = []
    
    # Check Status
    if "status" in expectations:
        if response.get("status") != expectations["status"]:
            failures.append(f"Status mismatch: Expected {expectations['status']}, got {response.get('status')}")

    # Check Timing
    if "max_time_ms" in expectations:
        if response.get("time_ms", 99999) > expectations["max_time_ms"]:
            failures.append(f"Performance too slow: {response.get('time_ms')}ms > {expectations['max_time_ms']}ms")

    # Check Body Keys
    if "body_contains" in expectations:
        body = response.get("body", {})
        if isinstance(body, dict):
            for key in expectations["body_contains"]:
                if key not in body:
                    failures.append(f"Missing body key: {key}")
        elif isinstance(body, str):
             for key in expectations["body_contains"]:
                if key not in body:
                    failures.append(f"Body text missing: {key}")

    return {
        "passed": len(failures) == 0,
        "failures": failures
    }

async def quick_load_test(
    method: str, 
    url: str, 
    concurrency: int = 5, 
    count: int = 10,
    headers: Optional[Dict[str, str]] = None
):
    """
    Run a quick concurrency load test on an endpoint.
    
    Args:
        method: HTTP method (GET, POST, etc).
        url: Target URL.
        concurrency: Number of parallel requests (batch size).
        count: Total number of requests to execute.
        headers: Optional headers.
        
    Usage:
        Use this to check for race conditions or basic stability under load.
        For heavy stress testing, see `stress_test` tool.
    """
    latencies = []
    errors = 0
    status_codes = {}
    
    # We process in batches of 'concurrency'
    remaining = count
    
    while remaining > 0:
        batch_size = min(remaining, concurrency)
        tasks = [make_request(method, url, headers=headers) for _ in range(batch_size)]
        results = await asyncio.gather(*tasks)
        
        for res in results:
            if "error" in res:
                errors += 1
            else:
                latencies.append(res["time_ms"])
                sc = res["status"]
                status_codes[sc] = status_codes.get(sc, 0) + 1
        
        remaining -= batch_size
        
    # Stats
    if not latencies:
        return {"error": "No successful requests"}
        
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    
    return {
        "total_requests": count,
        "successful": len(latencies),
        "errors": errors,
        "status_distribution": status_codes,
        "latency_p50": round(p50, 2),
        "latency_p95": round(p95, 2),
        "latency_p99": round(p99, 2),
        "min": round(min(latencies), 2),
        "max": round(max(latencies), 2)
    }

async def compare_requests(method: str, url_a: str, url_b: str):
    """
    Compare responses from two URLs (e.g. Staging vs Production).
    
    Use this to verify parity between environments or to check if a refactor broke anything.
    """
    # Run in parallel
    res_a, res_b = await asyncio.gather(
        make_request(method, url_a),
        make_request(method, url_b)
    )
    
    diffs = []
    
    # Status
    if res_a.get("status") != res_b.get("status"):
        diffs.append(f"Status mismatch: A={res_a.get('status')}, B={res_b.get('status')}")
    
    # Time
    time_diff = abs(res_a.get("time_ms", 0) - res_b.get("time_ms", 0))
    if time_diff > 100:
        diffs.append(f"Significant timing difference: {round(time_diff, 2)}ms")
        
    # Body Keys (if dict)
    body_a = res_a.get("body")
    body_b = res_b.get("body")
    
    if isinstance(body_a, dict) and isinstance(body_b, dict):
        keys_a = set(body_a.keys())
        keys_b = set(body_b.keys())
        if keys_a != keys_b:
            diffs.append(f"Keys mismatch: A has {len(keys_a)}, B has {len(keys_b)}. Diff: {keys_a ^ keys_b}")
    elif body_a != body_b:
        # Simple string compare for now (could be noisy)
        diffs.append("Response body content differs")

    return {
        "match": len(diffs) == 0,
        "diffs": diffs,
        "response_a": {"status": res_a.get("status"), "time": res_a.get("time_ms")},
        "response_b": {"status": res_b.get("status"), "time": res_b.get("time_ms")}
    }

def register_analysis_tools(mcp: FastMCP):
    mcp.tool()(validate_response)
    mcp.tool()(quick_load_test)
    mcp.tool()(compare_requests)
