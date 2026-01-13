import asyncio
import sys
import os

# Ensure src is in path
sys.path.append(os.getcwd())

from src.tools.env_tools import set_environment, set_variable
from src.tools.request_tools import make_request
from src.tools.security_tools import scan_endpoint_security
from src.tools.workflow_tools import run_workflow

async def run_demo():
    print("=== Starting API Analyst Demo (Direct Import) ===")
    
    # 1. Setup Environment
    print("\n[1] Setting up Environment 'staging'...")
    # set_environment is sync (in my impl? let's check. FastMCP wraps whatever it is. 
    # My code: def set_environment(...). It is sync.)
    res = set_environment(name="staging", variables={"base_url": "https://httpbin.org"})
    print(f"Result: {res}")
    
    # 2. Make Request
    print("\n[2] Making Request to {{base_url}}/get...")
    # make_request is async
    res = await make_request(method="GET", url="{{base_url}}/get", save_as="test_get")
    print(f"Status: {res.get('status')} (Time: {res.get('time_ms')}ms)")
    
    # 3. Security Scan
    print("\n[3] Scanning Security for {{base_url}}/get...")
    # scan is async
    res = await scan_endpoint_security(method="GET", url="https://httpbin.org/get")
    print(f"Security Score: {res.get('score')}")
    print(f"Missing Headers: {res.get('missing_security_headers')}")
    
    # 4. Workflow
    print("\n[4] Running Workflow (Get -> Delay -> Get)...")
    steps = [
        {"method": "GET", "url": "https://httpbin.org/delay/1"},
        {"method": "GET", "url": "https://httpbin.org/headers"}
    ]
    # workflow is async
    res = await run_workflow(steps=steps, workflow_name="demo_flow")
    print(f"Workflow Status: {res.get('status')}")
    print(f"Steps Completed: {res.get('steps_completed')}")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    asyncio.run(run_demo())
