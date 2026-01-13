from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import re
import os
from datetime import datetime

# Persistence Configuration
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.getcwd(), "data"))
os.makedirs(DATA_DIR, exist_ok=True)

class RequestModel(BaseModel):
    method: str
    url: str
    body: Optional[Any] = None
    headers: Dict[str, str] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = None

class WorkflowModel(BaseModel):
    name: str
    steps: List[str]  # List of saved request names to run
    description: Optional[str] = None

class ResponseModel(BaseModel):
    url: str
    status: int
    time_ms: float
    error: Optional[str] = None

class SessionState:
    def __init__(self):
        self.environments: Dict[str, Dict[str, str]] = {
            "default": {
                "base_url": "http://localhost:8000"
            }
        }
        self.current_environment: str = "default"
        
        # Project Isolation
        self.current_project: str = "default"
        
        # Dynamic variables for the current session (overrides env vars)
        self.variables: Dict[str, str] = {}
        # Per-Project Variables: {project_name: {key: val}}
        self.project_variables: Dict[str, Dict[str, str]] = {}
        
        self.auth_headers: Dict[str, str] = {}
        
        self.saved_requests: Dict[str, RequestModel] = {}
        self.saved_workflows: Dict[str, WorkflowModel] = {}
        
        self.history: List[ResponseModel] = []
    
    def get_effective_variables(self) -> Dict[str, str]:
        """Combine env vars, project vars, and global session vars."""
        env_vars = self.environments.get(self.current_environment, {})
        project_vars = self.project_variables.get(self.current_project, {})
        return {**env_vars, **project_vars, **self.variables}
    
    def substitute_variables(self, text: str) -> str:
        """Replace {{key}} with values from current environment/variables."""
        if not text:
            return text
            
        vars_map = self.get_effective_variables()
        
        def replace(match):
            key = match.group(1).strip()
            # Also support system vars like {{project_id}}
            if key == "project_id": return self.current_project
            return str(vars_map.get(key, match.group(0))) # Return original if not found
            
        return re.sub(r'\{\{(.+?)\}\}', replace, text)
    
    def add_history(self, response: ResponseModel):
        self.history.append(response)
        if len(self.history) > 100:
            self.history.pop(0)

# Global state instance
state = SessionState()
