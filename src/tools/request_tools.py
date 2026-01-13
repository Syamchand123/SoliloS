from mcp.server.fastmcp import FastMCP
from src.state import state, RequestModel, ResponseModel
import httpx
import time
import json
from typing import Dict, Any, Optional

async def set_auth(auth_type: str, value: str):
    """
    Set authentication for the session.
    
    Args:
        auth_type: One of 'bearer', 'header', 'basic'.
        value: The credential value.
            - For 'bearer': "my-token-123"
            - For 'header': "X-Custom-Auth: secret-key"
            - For 'basic': "username:password" (encodes automatically)
    """
    if auth_type.lower() == 'bearer':
        state.auth_headers["Authorization"] = f"Bearer {value}"
    elif auth_type.lower() == 'header':
        parts = value.split(':', 1)
        if len(parts) == 2:
            state.auth_headers[parts[0].strip()] = parts[1].strip()
    return f"Auth configured ({auth_type})"

async def make_request(
    method: str,
    url: str,
    body: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    save_as: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute an HTTP request.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH).
        url: Target URL. Supports variable substitution (e.g., "https://api.com/users/{{user_id}}").
        body: Request body. Can be a JSON string or a python dict. Supports substitution (e.g., {"id": "{{user_id}}"}).
        headers: Optional dictionary of headers.
        save_as: Name to save this request configuration as for future use in workflows.
        
    Returns:
        Dictionary containing 'status', 'headers', 'body', and 'time_ms'.
    """
    # 1. Substitute variables
    final_url = state.substitute_variables(url)
    
    # helper to handle dict bodies
    if isinstance(body, (dict, list)):
        body_str = json.dumps(body)
    else:
        body_str = body
        
    final_body = state.substitute_variables(body_str) if body_str else None
    
    # 2. Prepare headers (Merge session auth + provided headers)
    final_headers = state.auth_headers.copy()
    if headers:
        # Substitute vars in header values
        sub_headers = {k: state.substitute_variables(v) for k, v in headers.items()}
        final_headers.update(sub_headers)
        
    # 3. Store if requested
    if save_as:
        state.saved_requests[save_as] = RequestModel(
            method=method,
            url=url, # Save raw URL with vars
            headers=headers or {},
            body=body,
            description=f"Saved via make_request"
        )
    
    # 4. Execute
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=final_url,
                content=final_body,
                headers=final_headers,
                timeout=30.0 
            )
            elapsed = (time.perf_counter() - start) * 1000
            
            # Try to parse JSON
            try:
                resp_body = response.json()
            except Exception:
                resp_body = response.text
            
            result = {
                "status": response.status_code,
                "status_text": response.reason_phrase,
                "headers": dict(response.headers),
                "body": resp_body,
                "time_ms": round(elapsed, 2)
            }
            
            # Update history
            state.add_history(ResponseModel(
                url=final_url,
                status=response.status_code,
                time_ms=elapsed
            ))
            
            return result
            
    except Exception as e:
        return {"error": str(e), "time_ms": (time.perf_counter() - start) * 1000}

def get_saved_requests():
    """List all saved requests."""
    return list(state.saved_requests.keys())

def register_request_tools(mcp: FastMCP):
    mcp.tool()(set_auth)
    mcp.tool()(make_request)
    mcp.tool()(get_saved_requests)
