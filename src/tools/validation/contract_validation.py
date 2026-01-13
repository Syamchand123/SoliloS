from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, Optional
import jsonschema
import yaml
import json

def validate_contract(response: Dict[str, Any], contract_type: str, schema: str):
    """
    Validate an API response body against a formal specific specification.
    
    Args:
        response: The response dictionary from `make_request`.
        contract_type: One of 'json_schema' or 'openapi'.
        schema: The schema definition (as a JSON string, Python dict, or YAML string).
        
    Returns:
        Valid: True/False and error details if mismatched.
    """
    body = response.get("body")
    if not body:
        return {"valid": False, "error": "Response has no body to validate"}
    
    try:
        # 1. Parse Schema
        if contract_type == "json_schema":
            try:
                schema_obj = json.loads(schema) if isinstance(schema, str) else schema
            except Exception as e:
                return {"valid": False, "error": f"Invalid JSON Schema: {str(e)}"}
                
            jsonschema.validate(instance=body, schema=schema_obj)
            return {"valid": True, "message": "Response matches JSON Schema."}
            
        elif contract_type == "openapi":
             # Simplified: User must pass the specific schema component or we'd need endpoints/methods
             # For MVP, we assume user passes the schema for the specific response model
             try:
                schema_obj = yaml.safe_load(schema) if isinstance(schema, str) else schema
             except Exception as e:
                return {"valid": False, "error": f"Invalid OpenAPI Schema: {str(e)}"}
             
             # OpenAPI schemas often need 'components' resolution, which is complex.
             # We assume self-contained schema for this tool scope.
             jsonschema.validate(instance=body, schema=schema_obj)
             return {"valid": True, "message": "Response matches OpenAPI Schema."}
             
        else:
            return {"valid": False, "error": f"Unknown contract type: {contract_type}"}
            
    except jsonschema.exceptions.ValidationError as e:
        return {
            "valid": False,
            "error": "Validation Failed",
            "details": {
                "message": e.message,
                "path": list(e.path),
                "schema_path": list(e.schema_path)
            }
        }
    except Exception as e:
        return {"valid": False, "error": f"Unexpected error: {str(e)}"}

def register_validation_tools(mcp: FastMCP):
    mcp.tool()(validate_contract)
