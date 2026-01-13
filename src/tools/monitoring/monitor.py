from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import asyncio
import time
import sqlite3
import os

from src.tools.request_tools import make_request
from src.state import state, DATA_DIR

# Persistence
DB_PATH = os.path.join(DATA_DIR, "monitor_history.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Check if project column exists (migration) (naive)
    try:
        c.execute("SELECT project FROM monitoring LIMIT 1")
    except sqlite3.OperationalError:
        # Schema mismatch, drop/recreate OR alter. Detailed migration is better, 
        # but for this script we'll just try to add column or ignore if fails
        try:
             c.execute("ALTER TABLE monitoring ADD COLUMN project TEXT")
        except:
             pass 

    c.execute('''CREATE TABLE IF NOT EXISTS monitoring
                 (endpoint TEXT, timestamp REAL, status INTEGER, time_ms REAL, project TEXT)''')
    conn.commit()
    conn.close()

# Initialize on module load
init_db()

async def monitor_endpoint(endpoint: str, interval: int = 60, iterations: int = 5):
    """
    Actively monitor an endpoint by polling it at intervals.
    
    Args:
        endpoint: URL to monitor.
        interval: Seconds between checks.
        iterations: Number of checks to perform.
        
    Side Effect:
        Writes results to internal SQLite DB for historical tracking.
    """
    results = []
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    project = state.current_project
    
    for _ in range(iterations):
        res = await make_request("GET", endpoint)
        status = res.get("status")
        time_ms = res.get("time_ms")
        ts = time.time()
        
        results.append({
            "timestamp": ts,
            "status": status,
            "time_ms": time_ms
        })
        
        c.execute("INSERT INTO monitoring VALUES (?, ?, ?, ?, ?)", (endpoint, ts, status, time_ms, project))
        conn.commit()
        
        if iterations > 1:
            await asyncio.sleep(interval)
            
    conn.close()
    
    return {
        "monitored": endpoint,
        "project": project,
        "samples": len(results),
        "status_codes": [r["status"] for r in results]
    }

def compare_over_time(endpoint: str, window_minutes: int = 15):
    """
    Analyze monitoring history to detect performance trends.
    
    Args:
        endpoint: URL to analyze.
        window_minutes: Time window to consider "recent" (vs historical average).
        
    Returns:
        Analysis of whether the endpoint is getting slower, faster, or stable.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    project = state.current_project
    
    # Get all history sorted by time, filtered by project
    c.execute("SELECT timestamp, time_ms FROM monitoring WHERE endpoint=? AND project=? ORDER BY timestamp ASC", (endpoint, project))
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return {"error": f"No monitoring data for this endpoint in project '{project}'."}
        
    history = [{"timestamp": r[0], "time_ms": r[1]} for r in rows]
        
    now = time.time()
    # Split into 'Recent' (last X mins) and 'Previous'
    cutoff = now - (window_minutes * 60)
    
    recent = [r for r in history if r["timestamp"] > cutoff]
    older = [r for r in history if r["timestamp"] <= cutoff]
    
    def avg_time(data):
        if not data: return 0
        return sum(r["time_ms"] for r in data) / len(data)
        
    return {
        "endpoint": endpoint,
        "current_avg_latency": round(avg_time(recent), 2),
        "previous_avg_latency": round(avg_time(older), 2),
        "data_points": {
            "recent": len(recent),
            "historical": len(older)
        },
        "trend": "slower" if avg_time(recent) > avg_time(older) else "stable/faster"
    }

def register_monitoring_tools(mcp: FastMCP):
    mcp.tool()(monitor_endpoint)
    mcp.tool()(compare_over_time)
