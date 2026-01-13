from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import json
import datetime
from jinja2 import Template

# Optional Libraries
try:
    from junit_xml import TestSuite, TestCase
    HAS_JUNIT = True
except ImportError:
    HAS_JUNIT = False

try:
    from weasyprint import HTML
    HAS_PDF = True
except (ImportError, OSError):
    HAS_PDF = False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>API Test Report</title>
    <style>
        body { font-family: sans-serif; padding: 20px; }
        .pass { color: green; }
        .fail { color: red; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>API Test Report</h1>
    <p>Generated at: {{ timestamp }}</p>
    
    <h2>Summary</h2>
    <p>Total Tests: {{ results|length }}</p>
    
    <h2>Details</h2>
    <table>
        <tr>
            <th>Test</th>
            <th>Status</th>
            <th>Details</th>
        </tr>
        {% for res in results %}
        <tr>
            <td>{{ res.name }}</td>
            <td class="{{ 'pass' if res.passed else 'fail' }}">{{ 'PASS' if res.passed else 'FAIL' }}</td>
            <td><pre>{{ res.details | tojson }}</pre></td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

def generate_test_report(results: List[Dict[str, Any]], format: str = "html", output_file: str = "report"):
    """
    Generate a formatted report from test results.
    
    Args:
        results: List of result dictionaries. E.g.
            [
                {"name": "Login Test", "passed": True, "details": "Token received", "time_ms": 120},
                {"name": "Profile Load", "passed": False, "details": "404 Not Found"}
            ]
        format: Output format: "html", "json", "markdown", "junit_xml", "pdf".
        output_file: Base filename to save the report to (e.g. "my_test_run").
    """
    timestamp = datetime.datetime.now().isoformat()
    
    if format.lower() == "json":
        return json.dumps({"timestamp": timestamp, "results": results}, indent=2)
        
    elif format.lower() == "html":
        template = Template(HTML_TEMPLATE)
        return template.render(timestamp=timestamp, results=results)
        
    elif format.lower() == "markdown":
        md = f"# API Test Report\nGenerated: {timestamp}\n\n"
        md += "| Test | Status | Details |\n|---|---|---|\n"
        for res in results:
            status = "✅ PASS" if res.get("passed") else "❌ FAIL"
            details = str(res.get("details"))[:100].replace("\n", " ")
            md += f"| {res.get('name', 'Unnamed')} | {status} | {details} |\n"
        return md

    elif format.lower() == "junit_xml":
        if not HAS_JUNIT:
            return "Error: junit-xml package not installed."
        
        test_cases = []
        for res in results:
            tc = TestCase(res.get("name", "Unnamed"), classname="MCP_Test", elapsed_sec=res.get("time_ms", 0)/1000)
            if not res.get("passed"):
                tc.add_failure_info(message="Test Failed", output=str(res.get("details")))
            test_cases.append(tc)
            
        ts = TestSuite("MCP API Tests", test_cases)
        return TestSuite.to_xml_string([ts])

    elif format.lower() == "pdf":
        if not HAS_PDF:
             return "Error: weasyprint package not installed (requires GTK libs on Windows)."
        
        # Render HTML first
        template = Template(HTML_TEMPLATE)
        html_string = template.render(timestamp=timestamp, results=results)
        
        # In MCP context, returning binary is tricky. We usually return path.
        # But here we return the PDF bytes logic or just success message if we wrote to file.
        # Since tools return text, let's write to file if possible or ERROR.
        # We will assume caller handles file I/O or we return error saying "Writing to file not supported in this tool signature, returning HTML"
        # Wait, user asked for output_file logic in scenario? No, just the content usually.
        # We'll return a message.
        
        try:
             # We can't easily return binary PDF in tool str output. 
             # We will try to write to 'output_file' if provided, else error.
             # Actually, creating a temp file is better.
             fname = output_file if output_file else "report"
             if not fname.endswith(".pdf"): fname += ".pdf"
             
             HTML(string=html_string).write_pdf(fname)
             return f"PDF generated successfully at {fname}"
        except Exception as e:
             return f"PDF Generation Error: {str(e)}"
        
    return "Unsupported format"

def register_reporting_tools(mcp: FastMCP):
    mcp.tool()(generate_test_report)
