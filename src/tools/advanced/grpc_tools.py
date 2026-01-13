from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, Optional, List
import grpc
import time
import json

# This generic client assumes it can send/receive simple payloads.
# For full gRPC support, one usually needs the compiled proto definitions.
# We will implement a 'json-like' reflection or generic call if possible,
# OR just expect raw bytes/simple implementation for the user to extend.

# For this MVP: We assume the user has a known service and method.
# Since we don't have the Proto descriptors loaded dynamically, we'll try to use
# the standard 'grpc_cli' style approach if it were available, but in pure Python,
# we need the stubs.
#
# Workaround: We will offer a connectivity check and a 'text-based' payload 
# if the server supports generic proto handling (unlikely).
# BETTER APPROACH for MVP: Connectivity Check + Reflection if enabled.

async def test_grpc(host: str, service: str, method: str, payload_json: str = "{}"):
    """
    Perform a basic connectivity check against a gRPC host.
    
    Capabilities:
    - Verifies TCP connection and gRPC Channel Readiness.
    - DOES NOT support calling methods with payloads (Use `call_grpc_dynamic` for that).
    
    Args:
        host: Target "hostname:port" (e.g. "localhost:50051").
        
    Returns:
        Connection status and error details if unreachable.
    """
    try:
        # 1. Connectivity Check
        channel = grpc.aio.insecure_channel(host)
        
        # Try to wait for connection
        try:
            await asyncio.wait_for(channel.channel_ready(), timeout=5.0)
            status = "Connected"
        except asyncio.TimeoutError:
             return {"error": f"Failed to connect to {host} (Timeout)"}
             
        # 2. Generic Call (Requires server reflection or known stub)
        # Since we don't have the stub, we can't easily make a call unless using
        # standard inspection tools.
        # Capability check only for MVP.
        
        return {
            "status": "Connected",
            "host": host,
            "message": "Channel is ready. Actual method invocation requires Protobuf stubs to be compiled into this MCP server.",
            "attempted_method": f"{service}/{method}"
        }
        
    except Exception as e:
        return {"error": str(e)}

def register_grpc_tool(mcp: FastMCP):
    mcp.tool()(test_grpc)
