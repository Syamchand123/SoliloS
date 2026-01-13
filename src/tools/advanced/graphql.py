from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, Optional
from src.tools.request_tools import make_request

async def query_graphql(endpoint: str, query: str, variables: Optional[Dict] = None):
    """
    Execute a GraphQL query against an endpoint.
    
    Args:
        endpoint: URL of the GraphQL server.
        query: The Graph Query string (e.g. "query { users { name } }").
        variables: Optional dictionary of variables (e.g. {"id": "123"}).
        
    Returns:
        Standard GraphQL response format (data, errors).
    """
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
        
    response = await make_request("POST", endpoint, body=payload)
    
    body = response.get("body", {})
    
    # GraphQL Specific Validations
    has_errors = False
    error_list = []
    
    if isinstance(body, dict):
        if "errors" in body:
            has_errors = True
            error_list = body["errors"]
            
    return {
        "status": response.get("status"),
        "has_gql_errors": has_errors,
        "errors": error_list,
        "data": body.get("data") if isinstance(body, dict) else None
    }

def register_graphql_tool(mcp: FastMCP):
    mcp.tool()(query_graphql)
