from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
from src.tools.request_tools import make_request
import asyncio

async def test_error_scenarios(endpoint: str, scenarios: List[str]):
    """
    Test how the API handles common error conditions (Fuzzing light).
    
    Args:
        endpoint: Target URL.
        scenarios: List of error types to simulate. Options:
            - "missing_field": Sends body missing keys.
            - "invalid_type": Sends strings where ints are expected.
            - "large_payload": Sends 10KB junk data.
            - "auth_token_expired": Sends expired bearer token.
            
    Returns:
        Pass if server returns 4xx Client Error. Fail if 500 Server Error or 200 Success.
    """
    results = []
    
    for scenario in scenarios:
        method = "POST" # Default to POST for payload testing
        body = {}
        headers = {}
        
        if scenario == "missing_field":
            body = {"some_field": "missing"} # Heuristic
        elif scenario == "invalid_type":
            body = {"id": "string_instead_of_int"}
        elif scenario == "large_payload":
            body = {"data": "A" * 10000}
        elif scenario == "auth_token_expired":
             headers = {"Authorization": "Bearer expired_token"}
             
        response = await make_request(method, endpoint, body=body, headers=headers)
        status = response.get("status")
        
        # Heuristic Assessment
        passed = False
        notes = ""
        
        if status >= 400 and status < 500:
             passed = True
             notes = "Correctly handled as Client Error"
        elif status >= 500:
             passed = False
             notes = "FAILED: Server crashed (500)"
        else:
             passed = False
             notes = "Unexpected Success (2xx)"
             
        results.append({
            "scenario": scenario,
            "status": status,
            "passed": passed,
            "notes": notes
        })
        
    return {
        "summary": "Error Handling stress test complete.",
        "results": results
    }

def register_scenario_tools(mcp: FastMCP):
    mcp.tool()(test_error_scenarios)
