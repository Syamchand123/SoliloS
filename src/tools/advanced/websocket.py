from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
try:
    import websockets
    HAS_WS = True
except ImportError:
    HAS_WS = False
import asyncio

async def test_websocket(url: str, messages: List[str]):
    """
    Connect to a WebSocket endpoint, send a sequence of messages, and record replies.
    
    Args:
        url: WebSocket URL (e.g. "ws://localhost:8000/ws").
        messages: List of strings to send sequentially.
        
    Returns:
        Summary of sent messages, received replies (with 2s timeout per reply), and any errors.
    """
    if not HAS_WS:
        return {"error": "websockets package not installed"}
    
    replies = []
    errors = []
    
    try:
        async with websockets.connect(url, timeout=5) as websocket:
            for msg in messages:
                await websocket.send(msg)
                try:
                    reply = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    replies.append(reply)
                except asyncio.TimeoutError:
                    errors.append(f"Timeout waiting for reply to {msg}")
                    
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}
        
    return {
        "sent": len(messages),
        "received": len(replies),
        "replies": replies,
        "errors": errors
    }

def register_websocket_tool(mcp: FastMCP):
    mcp.tool()(test_websocket)
