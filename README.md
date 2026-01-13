# SoliloS: Autonomous API Analyst (MCP Server)

**SoliloS** is a production-grade **Model Context Protocol (MCP)** server designed to give AI Agents (like Claude) the power to autonomously **test, analyze, and secure** APIs.

It goes beyond simple "HTTP Requests" by providing intelligent tools for:
*   **Security Fuzzing** (SQLi, XSS, IDOR)
*   **Load Testing & Chaos Engineering**
*   **Deep Response Analysis** (Performance & Design Critique)
*   **Stateful Workflows** (Multi-step Auth flows with rollback)

---

## 🚀 Quick Start (Docker)

The easiest way to run SoliloS is via Docker.

```bash
# 1. Build the image
docker build -t solilos .

# 2. Run the container (Persistent Data)
docker run -d -p 8000:8000 -v "${PWD}/data:/app/data" solilos
```

## 🔌 Connecting to Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "solilos": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "${PWD}/data:/app/data",
        "solilos"
      ]
    }
  }
}
```

*(Note: For development with inspector, use `npx @modelcontextprotocol/inspector http://localhost:8000/sse`)*

---

## 🛠️ Feature Highlights

### 1. Autonomous Security Scanning
SoliloS includes tools that proactively hunt for vulnerabilities.
*   `scan_endpoint_security`: Checks headers, SSL, and leakage.
*   `fuzz_endpoint`: Injects common payloads (SQLi, XSS) to find weak points.
*   `test_authorization`: Verifies if User A can access User B's data (IDOR).

### 2. Intelligent Analysis
*   `analyze_response_deep`: Critiques API design JSON structure, nesting depth (< 3 levels recommended), and efficient data usage.
*   `detect_breaking_changes`: Compares two API responses (e.g. Staging vs Prod) to ensure stability.

### 3. Stateful Workflows
Chain requests together with logic.
```json
// Example: Complete User Journey
[
  { "action": "Signup", "extract": { "uid": "body.id" } },
  { "action": "Login", "extract": { "token": "body.access_token" } },
  { "action": "Get Profile", "headers": { "Authorization": "Bearer {{token}}" } }
]
```

### 4. Resilience Testing
*   `stress_test`: Simulates concurrent users.
*   `chaos_test`: Randomly fails or delays requests to test client robustness.

---

## 📂 Project Structure

*   `src/tools/`: The core tool logic (modularized by domain).
*   `src/state.py`: In-memory state management (environments, auth, variables).
*   `src/headless_runner.py`: Script for running Test Plans in CI/CD.
*   `tests/`: Demo flows and verification scripts.

---

## 📜 License
MIT License. Built with ❤️ for the AI Agent community.
