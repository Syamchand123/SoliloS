from mcp.server.fastmcp import FastMCP
from typing import Dict, Any

GITHUB_TEMPLATE = """
name: API Tests
on: [push]
jobs:
  api-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install mcp httpx
      - name: Run MCP Server Test
        run: python scripts/run_mcp_tests.py
"""

def export_to_ci(config: Dict[str, Any]):
    """
    Generate CI pipeline configuration files (e.g. GitHub Actions).
    
    Args:
        config: Configuration dictionary. Example:
            {"provider": "github", "workflow_name": "API Check"}
            
    Returns:
        Dictionary with filename and content, ready to be written to disk.
    """
    provider = config.get("provider", "github").lower()
    
    if provider == "github":
        return {
            "filename": ".github/workflows/api-test.yml",
            "content": GITHUB_TEMPLATE
        }
    else:
        return {"error": f"Provider {provider} not supported yet."}

def register_integration_tools(mcp: FastMCP):
    mcp.tool()(export_to_ci)
