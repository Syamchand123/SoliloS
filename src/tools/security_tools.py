from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
from src.tools.request_tools import make_request
import asyncio

PAYLOADS = {
    "SQLi": ["' OR '1'='1", "1; DROP TABLE users", "' UNION SELECT 1,2,3--"],
    "XSS": ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"],
    "PathTraversal": ["../../../../etc/passwd", "..\\..\\windows\\win.ini"]
}

REQUIRED_HEADERS = [
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options"
]

async def scan_endpoint_security(method: str, url: str):
    """
    Perform a PASSIVE security scan of an endpoint.
    
    Checks:
    - Missing Security Headers (HSTS, X-Frame-Options, etc).
    - Information Leakage (Stack traces, Server versions).
    
    Safe to run on production (does not inject payloads).
    """
    response = await make_request(method, url)
    
    if "error" in response:
        return {"error": response["error"]}
        
    headers = response.get("headers", {})
    missing_headers = []
    for h in REQUIRED_HEADERS:
        # Case insensitive check
        if not any(k.lower() == h.lower() for k in headers.keys()):
            missing_headers.append(h)
            
    # Check for leakage
    leaks = []
    body_str = str(response.get("body", ""))
    if "Stack trace" in body_str or "Traceback" in body_str:
        leaks.append("Stack trace exposed in body")
    if "server" in headers:
        leaks.append(f"Server header exposed: {headers['server']}")
        
    return {
        "missing_security_headers": missing_headers,
        "information_leakage": leaks,
        "score": 100 - (len(missing_headers) * 10) - (len(leaks) * 20)
    }

async def fuzz_endpoint(method: str, url: str, target_param: str):
    """
    Perform an ACTIVE security fuzzing test.
    
    DANGER: This injects malicious payloads (SQLi, XSS) into the target parameter.
    Do NOT run this on production systems unless authorized.
    
    Args:
        target_param: The query parameter to fuzz (e.g. 'id' in ?id=1).
    """
    vulnerabilities = []
    
    # Test each payload
    for category, payloads in PAYLOADS.items():
        for payload in payloads:
            # Construct fuzzed URL
            fuzzed_url = f"{url}{'&' if '?' in url else '?'}{target_param}={payload}"
            
            # Execute
            resp = await make_request(method, fuzzed_url)
            
            status = resp.get("status")
            body = str(resp.get("body", ""))
            
            # Detection Logic
            if status == 500:
                vulnerabilities.append({
                    "type": category,
                    "payload": payload,
                    "evidence": "Returned 500 Internal Server Error"
                })
            elif payload in body and category == "XSS":
                 vulnerabilities.append({
                    "type": "Reflected XSS",
                    "payload": payload,
                    "evidence": "Payload reflected in response body"
                })
                
    return {
        "vulnerabilities_found": len(vulnerabilities),
        "details": vulnerabilities
    }

def register_security_tools(mcp: FastMCP):
    mcp.tool()(scan_endpoint_security)
    mcp.tool()(fuzz_endpoint)
