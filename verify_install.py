from src.main import mcp
import asyncio
import pprint

async def verify():
    print("Verifying MCP Tool Registration...")
    tools = await mcp.list_tools()
    print(f"Total Tools Registered: {len(tools)}")
    for t in tools:
        print(f"- {t.name}")
        
    assert len(tools) >= 44, f"Expected 44 tools, got {len(tools)}"
    print("\nVerification Successful!")

if __name__ == "__main__":
    asyncio.run(verify())
