from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
from src.state import state

def create_project(name: str):
    """
    Create a new isolated project workspace.
    
    Isolation:
        Each project has its own separate environment variables, history, and monitoring data.
        Use this to separate different client contexts or testing scopes.
    """
    if name in state.project_variables:
        return {"error": f"Project '{name}' already exists."}
    
    state.project_variables[name] = {}
    
    # Auto-switch? Let's just create for now.
    return {
        "status": "Created",
        "project": name,
        "message": f"Project '{name}' created. Use switch_project('{name}') to activate."
    }

def switch_project(name: str):
    """
    Switch the active project context.
    
    Effect:
        - Saves the state of the current project.
        - Loads variables and history for the target project.
        - If 'name' does not exist, it will be automatically created.
    """
    # Allow switching to new projects implicitly or ensure they exist?
    # Let's ensure existence to prevent typos, except 'default'
    if name != "default" and name not in state.project_variables:
        # Auto-create if not exists? Or Error?
        # User friendliness -> Auto create
        state.project_variables[name] = {}
        created = True
    else:
        created = False
        
    state.current_project = name
    
    return {
        "status": "Switched",
        "current_project": name,
        "vars_loaded": len(state.get_effective_variables()),
        "created_new": created
    }

def register_project_tools(mcp: FastMCP):
    mcp.tool()(create_project)
    mcp.tool()(switch_project)
