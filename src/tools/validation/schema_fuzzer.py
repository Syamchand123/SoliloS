from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
from src.tools.request_tools import make_request
import copy

async def find_required_fields(endpoint: str, valid_payload: Dict[str, Any], method: str = "POST"):
    """
    Reverse-engineer the required fields of an endpoint by fuzzy testing.
    
    Process:
    1. Sends a baseline request with `valid_payload` (Expects 200 OK).
    2. Iteratively removes one field at a time.
    3. If removal causes an Error (400+), the field is deemed "Required".
    4. If it succeeds, the field is "Optional".
    
    Args:
        endpoint: Target URL.
        valid_payload: A known working JSON body with all fields.
    """
    required_fields = []
    optional_fields = []
    
    # 1. Baseline Success Check
    baseline = await make_request(method, endpoint, body=valid_payload)
    if baseline.get("status") >= 400:
        return {
            "error": f"Baseline request failed with {baseline.get('status')}. Provide a valid payload first."
        }
        
    keys = list(valid_payload.keys())
    
    for key in keys:
        # Create payload WITHOUT this key
        test_payload = copy.deepcopy(valid_payload)
        del test_payload[key]
        
        res = await make_request(method, endpoint, body=test_payload)
        
        status = res.get("status")
        if status >= 400:
            required_fields.append(key)
        else:
            optional_fields.append(key)
            
    return {
        "endpoint": endpoint,
        "total_fields": len(keys),
        "required_fields": required_fields,
        "optional_fields": optional_fields
    }

def register_schema_fuzzer(mcp: FastMCP):
    mcp.tool()(find_required_fields)
