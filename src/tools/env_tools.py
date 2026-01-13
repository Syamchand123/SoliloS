from mcp.server.fastmcp import FastMCP
from src.state import state
from typing import Dict

def set_environment(name: str, variables: Dict[str, str]):
    """
    Define or update a named environment configuration.
    
    Args:
        name: Environment identifier (e.g. 'staging', 'production').
        variables: Dictionary of base variables (e.g. {'base_url': 'https://stage.api.com', 'api_key': 'abc'}).
    """
    if name not in state.environments:
        state.environments[name] = {}
    state.environments[name].update(variables)
    return f"Environment '{name}' updated with {list(variables.keys())}"

def switch_environment(name: str):
    """
    Switch the active environment.
    Args:
        name: Name of the environment to switch to.
    """
    if name not in state.environments:
        return f"Error: Environment '{name}' does not exist. Available: {list(state.environments.keys())}"
    
    state.current_environment = name
    return f"Switched to environment: '{name}'"

def set_variable(key: str, value: str):
    """
    Set a dynamic variable for the current session.
    
    Usage:
        Use this to store temporary values like 'auth_token' or 'user_id' that shouldn't be hardcoded in the environment.
        Variables set here OVERRIDE environment variables of the same name.
    """
    state.variables[key] = value
    return f"Variable '{{{{ {key} }}}}' set."

def get_state_debug():
    """Returns the current state (active env, variables, request count)."""
    return {
        "current_environment": state.current_environment,
        "effective_variables": state.get_effective_variables(),
        "saved_requests": list(state.saved_requests.keys()),
        "history_count": len(state.history)
    }

def register_env_tools(mcp: FastMCP):
    mcp.tool()(set_environment)
    mcp.tool()(switch_environment)
    mcp.tool()(set_variable)
    mcp.tool()(get_state_debug)
