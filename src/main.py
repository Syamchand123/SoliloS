from mcp.server.fastmcp import FastMCP
import logging
import sys


# Import tool registrars
from src.tools.env_tools import register_env_tools
from src.tools.request_tools import register_request_tools
from src.tools.workflow_tools import register_workflow_tools
from src.tools.analysis_tools import register_analysis_tools
from src.tools.security_tools import register_security_tools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastMCP Server
mcp = FastMCP("SoliloS")

# Register all tools
# Register all tools
register_env_tools(mcp)
register_request_tools(mcp)
register_workflow_tools(mcp)
register_analysis_tools(mcp)
register_security_tools(mcp)

# Register New Advanced Tools
from src.tools.intelligence.response_intelligence import register_intelligence_tools
from src.tools.validation.contract_validation import register_validation_tools
from src.tools.security.auth_testing import register_auth_tools
from src.tools.scenarios.error_testing import register_scenario_tools
from src.tools.scenarios.load_testing import register_load_tools
from src.tools.reporting.report_generator import register_reporting_tools
from src.tools.integration.ci_export import register_integration_tools

# Batch 2 Imports
from src.tools.security.sensitive_data import register_sensitive_data_tool
from src.tools.security.rate_limit import register_rate_limit_tool
from src.tools.validation.breaking_changes import register_breaking_change_tools
from src.tools.scenarios.complex_flow import register_complex_flow_tool
from src.tools.monitoring.monitor import register_monitoring_tools
from src.tools.discovery.api_discovery import register_discovery_tools
from src.tools.advanced.graphql import register_graphql_tool
from src.tools.advanced.chaos import register_chaos_tool
from src.tools.advanced.websocket import register_websocket_tool

register_intelligence_tools(mcp)
register_validation_tools(mcp)
register_auth_tools(mcp)
register_scenario_tools(mcp)
register_load_tools(mcp)
register_reporting_tools(mcp)
register_integration_tools(mcp)

# Batch 2 Registration
register_sensitive_data_tool(mcp)
register_rate_limit_tool(mcp)
register_breaking_change_tools(mcp)
register_complex_flow_tool(mcp)
register_monitoring_tools(mcp)
register_discovery_tools(mcp)
register_graphql_tool(mcp)
register_chaos_tool(mcp)
register_websocket_tool(mcp)

# Batch 3 Imports
from src.tools.scenarios.stress_testing import register_stress_tool
from src.tools.integration.postman_export import register_postman_tool
from src.tools.integration.openapi_export import register_openapi_tool
from src.tools.advanced.grpc_tools import register_grpc_tool

# Batch 3 Registration
register_stress_tool(mcp)
register_postman_tool(mcp)
register_openapi_tool(mcp)
register_grpc_tool(mcp)

# Gap Integration Imports
from src.tools.validation.compare_environments import register_env_comparison_tool
from src.tools.validation.schema_fuzzer import register_schema_fuzzer

# Gap Registration
register_env_comparison_tool(mcp)
register_schema_fuzzer(mcp)

# Final Polish Imports
from src.tools.project_tools import register_project_tools
from src.tools.advanced.grpc_dynamic import register_dynamic_grpc_tool

# Final Polish Registration
register_project_tools(mcp)
register_dynamic_grpc_tool(mcp)

import os

if __name__ == "__main__":
    if os.getenv("MCP_TRANSPORT") == "sse":
        import uvicorn
        print("Starting SoliloS in SSE Mode on Port 8000...", file=sys.stderr)
        
        # Introspect to find the ASGI app
        app = getattr(mcp, "sse_app", None) or getattr(mcp, "_sse_app", None)
        
        if app:
            uvicorn.run(app, host="0.0.0.0", port=8000)
        else:
            # Fallback: Try running the object itself (if it's the app)
            # or strictly fail and log attributes to debug
            print(f"Warning: Could not find 'sse_app'. Attributes: {[d for d in dir(mcp) if 'app' in d or 'sse' in d]}", file=sys.stderr)
            try:
                uvicorn.run(mcp, host="0.0.0.0", port=8000)
            except Exception as e:
                print(f"CRITICAL: Failed to run mcp object as ASGI app: {e}", file=sys.stderr)
                sys.exit(1)
    else:
        mcp.run()
