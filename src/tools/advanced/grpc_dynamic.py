from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import subprocess
import sys
import os
import importlib.util
import grpc
from google.protobuf import json_format

# Helpers
GENERATED_DIR = os.path.join(os.getcwd(), "src", "protos_generated")
os.makedirs(GENERATED_DIR, exist_ok=True)
if GENERATED_DIR not in sys.path:
    sys.path.append(GENERATED_DIR)

def register_proto(proto_path: str):
    """
    Compile a .proto file definition for use with the MCP server.
    
    Args:
        proto_path: Absolute path to the .proto file on disk.
        
    Effect:
        Generates Python gRPC code (pb2) in the `src/protos_generated` folder, allowing `call_grpc_dynamic` to use it.
    """
    if not os.path.exists(proto_path):
        return {"error": f"Proto file not found: {proto_path}"}
        
    # Path Traversal Check
    safe_base = os.getcwd()
    abs_path = os.path.abspath(proto_path)
    if not abs_path.startswith(safe_base):
        return {"error": "Security Alert: Access to external files is forbidden."}
        
    # Command: python -m grpc_tools.protoc -I. --python_out=OUT --grpc_python_out=OUT input.proto
    # We assume imports are relative to the proto file's dir or server root.
    # For MVP, we point include path to the file directory.
    
    include_dir = os.path.dirname(os.path.abspath(proto_path))
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{include_dir}",
        f"--python_out={GENERATED_DIR}",
        f"--grpc_python_out={GENERATED_DIR}",
        proto_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {"error": "Compilation Failed", "details": result.stderr}
            
        return {
            "status": "Compiled",
            "output_dir": GENERATED_DIR,
            "message": "Proto compiled. You can now use call_grpc_dynamic."
        }
    except Exception as e:
        return {"error": str(e)}

async def call_grpc_dynamic(service_full_name: str, method_name: str, payload: Dict[str, Any], host: str = "localhost:50051", proto_name: str = "service"):
    """
    Make a gRPC call using a previously registered proto definition.
    
    Args:
        service_full_name: The fully qualified service name (e.g., "myservice.v1.PaymentService").
        method_name: The method to call (e.g., "ProcessPayment").
        payload: Dictionary representing the request message.
        host: Target gRPC server (e.g., "localhost:50051").
        proto_name: The filename of the original .proto (without extension). Used to locate generated modules.
    """
    # 1. Import the generated modules
    # Names are usually {proto_name}_pb2 and {proto_name}_pb2_grpc
    pb2_name = f"{proto_name}_pb2"
    grpc_name = f"{proto_name}_pb2_grpc"
    
    try:
        pb2 = importlib.import_module(pb2_name)
        pb2_grpc = importlib.import_module(grpc_name)
    except ImportError:
        # Retry mechanism if sys.path update wasn't caught?
        if GENERATED_DIR not in sys.path:
            sys.path.append(GENERATED_DIR)
        try:
             pb2 = importlib.import_module(pb2_name)
             pb2_grpc = importlib.import_module(grpc_name)
        except ImportError:
             return {"error": f"Modules {pb2_name}/{grpc_name} not found. Did you run register_proto first?"}
             
    # 2. Reflection to find Request Class
    # Usually: GetUserRequest is the type. We need to know what the method expects.
    # Without reflection, we have to guess or inspect the Stub.
    
    # Inspection:
    # Service Stub class name is usually MyServiceStub
    service_short = service_full_name.split(".")[-1]
    stub_class = getattr(pb2_grpc, f"{service_short}Stub", None)
    
    if not stub_class:
        return {"error": f"Stub {service_short}Stub not found in {grpc_name}."}
        
    # Connect
    async with grpc.aio.insecure_channel(host) as channel:
        stub = stub_class(channel)
        method_callable = getattr(stub, method_name, None)
        
        if not method_callable:
             return {"error": f"Method {method_name} not found on Stub."}
             
        # 3. Construct Request Object
        # We need the input type. Is there a way to get it from method_callable?
        # method_callable._request_serializer... is internal.
        # HARD PART: We don't know the Input Class Name just from the method name securely without reflection.
        # Heuristic: Method "GetUser" -> expects "GetUserRequest"?
        
        # Search for a message type in pb2 that matches "MethodNameRequest" or just try generic?
        # Better: Iterate all classes in pb2, see if one matches likelihood?
        # Standard: service definition in descriptor. 
        #
        # MVP Hack: User must provide input_type_name
        # Or we guess: {Method}Request
        
        request_class_name = f"{method_name}Request"
        request_class = getattr(pb2, request_class_name, None)
        
        if not request_class:
            # Fallback: Try keys of payload? No.
            # Try to list classes?
            return {"error": f"Could not guess Request Class (Checked {request_class_name}). please follow Naming Convensions."}
            
        # 4. Populate Request
        try:
            req_obj = json_format.ParseDict(payload, request_class())
        except Exception as e:
            return {"error": f"Failed to populate request: {e}"}
            
        # 5. Invoke
        try:
            response_obj = await method_callable(req_obj)
            return json_format.MessageToDict(response_obj)
        except grpc.RpcError as e:
            return {"error": f"RPC Failed: {e.code()} - {e.details()}"}

def register_dynamic_grpc_tool(mcp: FastMCP):
    mcp.tool()(register_proto)
    mcp.tool()(call_grpc_dynamic)
