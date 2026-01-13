from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import re
import json

# Regex Patterns
PATTERNS = {
    "Email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "IPv4": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "API Key (Generic)": r"(?i)api_key|apikey|secret|token", # Simple heuristic key name check setup
    "AWS Key": r"AKIA[0-9A-Z]{16}",
    "Private Key": r"-----BEGIN PRIVATE KEY-----"
}

def scan_for_sensitive_data(response: Dict[str, Any]):
    """
    Scan response body and headers for exposed sensitive information (PII/Secrets).
    
    Detects patterns for:
    - Emails, IPv4 Addresses, SSNs.
    - API Keys (generic tokens), AWS Keys.
    - Private Keys.
    
    Usage: Run this on all new endpoints to prevent data leaks.
    """
    findings = []
    
    # helper to check string
    def check_text(text, source):
        for label, pattern in PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                 # Check for false positives or specific logic (e.g., Luhn for CC)
                 # For now, just report unique matches
                 unique_matches = list(set(matches))[:3] # Limit report
                 findings.append({
                     "type": label,
                     "source": source,
                     "count": len(matches),
                     "samples": unique_matches
                 })
    
    # 1. Check Body
    body_str = json.dumps(response.get("body", ""))
    check_text(body_str, "Body")
    
    # 2. Check Headers
    headers_str = json.dumps(response.get("headers", {}))
    check_text(headers_str, "Headers")
    
    return {
        "sensitive_data_found": len(findings) > 0,
        "findings": findings
    }

def register_sensitive_data_tool(mcp: FastMCP):
    mcp.tool()(scan_for_sensitive_data)
