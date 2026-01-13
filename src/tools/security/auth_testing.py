from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
from src.tools.request_tools import make_request
import asyncio

async def test_authorization(endpoint: str, matrix: Dict[str, Any]):
    """
    Test API authorization by running a matrix of user roles against an endpoint.
    
    Args:
        endpoint: Target URL path (e.g. "/users/{user_id}/profile").
        matrix: Dictionary defining test cases. Example:
            {
                "test_cases": [
                    {"as": "admin_user", "token": "abc_admin", "expect": 200},
                    {"as": "regular_user", "token": "abc_user", "expect": 403},
                    {"as": "anonymous", "token": null, "expect": 401}
                ]
            }
            
    Returns:
        Summary of which roles passed/failed their access expectations.
    """
    results = []
    
    test_cases = matrix.get("test_cases", [])
    
    for case in test_cases:
        user_alias = case.get("as")
        token = case.get("token")
        expected = case.get("expect")
        
        # Prepare Headers
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        # Execute
        # Note: We assume GET for simple auth test, or user needs to specify method.
        # Enhancements could take method/body in matrix.
        response = await make_request("GET", endpoint, headers=headers)
        
        status = response.get("status")
        passed = (status == expected)
        
        results.append({
            "test_case": user_alias,
            "status": status,
            "expected": expected,
            "passed": passed,
            "details": "Access granted" if status == 200 else "Access denied"
        })
        
    passed_count = sum(1 for r in results if r["passed"])
    
    return {
        "summary": f"Passed {passed_count}/{len(results)} authorization checks.",
        "vulnerable": passed_count < len(results),
        "results": results
    }

def register_auth_tools(mcp: FastMCP):
    mcp.tool()(test_authorization)
