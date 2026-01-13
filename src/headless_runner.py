"""
Headless Runner for API Analyst MCP Server
Usage: python headless_runner.py test_plan.json
"""

import sys
import json
import asyncio
from src.main import mcp
from src.tools.request_tools import make_request
from src.tools.scenarios.complex_flow import test_user_flow
from src.tools.reporting.report_generator import generate_test_report
# Import other tools as needed for direct access or rely on the tool registry if dynamically calling

async def run_plan(plan_file: str):
    """
    Execute a JSON Test Plan file headlessly.
    
    Schema for plan.json:
    {
        "name": "My Test Suite",
        "output_file": "report.html",
        "report_format": "html" (or "junit_xml"),
        "scenarios": [
            {
                "name": "Check Health",
                "tool": "make_request",
                "args": {"method": "GET", "url": "http://localhost:8000/health"}
            },
            {
                "name": "Complex User Flow",
                "tool": "test_user_flow",
                "args": {
                    "flow_definition": {
                        "steps": [...]
                    }
                }
            }
        ]
    }
    """
    try:
        with open(plan_file, "r") as f:
            plan = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {plan_file} not found.")
        sys.exit(1)
        
    print(f"Running Test Plan: {plan.get('name', 'Unnamed')}")
    results = []
    
    # Simple Orchestrator Logic
    # We iterate properly defined "jobs" or "scenarios"
    for scenario in plan.get("scenarios", []):
        name = scenario.get("name")
        tool_name = scenario.get("tool")
        args = scenario.get("args", {})
        
        print(f"Executing: {name} ({tool_name})...")
        
        try:
            # Dynamic Dispatch for Registered Tools
            # Note: FastMCP doesn't expose a simple "call by name" easily without the client wrapper
            # We will manually map commonly used tools for the runner or import functions directly.
            # Using direct import functions is safer for headless script.
            
            output = None
            success = False
            
            if tool_name == "test_user_flow":
                output = await test_user_flow(args.get("flow_definition"))
                success = output.get("success", False)
                
            elif tool_name == "make_request":
                output = await make_request(**args)
                success = output.get("status") < 400
                
            # Add more mappings as needed
            
            results.append({
                "name": name,
                "passed": success,
                "details": output
            })
            
        except Exception as e:
            print(f"Error in {name}: {e}")
            results.append({"name": name, "passed": False, "details": str(e)})

    # Generate Report
    report_format = plan.get("report_format", "junit_xml")
    report_out = generate_test_report(results, format=report_format)
    
    # If JUnit/HTML, we likely want to write to file
    if plan.get("output_file"):
        with open(plan.get("output_file"), "w") as f:
            f.write(report_out)
        print(f"Report written to {plan.get('output_file')}")
    else:
        print(report_out)
        
    # Exit Code
    failed = any(not r["passed"] for r in results)
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python headless_runner.py <plan.json>")
        sys.exit(1)
        
    asyncio.run(run_plan(sys.argv[1]))
