# %% [markdown]
# # server

# %%
#|default_exp server

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()
import ctrlstack.server as this_module

# %%
#|export
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED
from ctrlstack import Controller, ControllerMethodType
import functools
from typing import Callable, Optional, List, Tuple, Dict, Any
import inspect
import signal, os
from pathlib import Path


# %%
#|exporti
def _construct_route(method: Callable, method_name:Optional[str]=None, prepend_method_group: bool=True):
    method_name = method_name or method.__name__
    if prepend_method_group:
        route = f"/{method._controller_method_group}/{method_name}" if method._controller_method_group else f"/{method_name}"
    else:
        route = f"/{method_name}"
    return route


# %%
#|export
def create_controller_server(controller: Controller, prepend_method_group: bool=True, api_keys: Optional[List[str]] = None) -> FastAPI:
    """
    Get the controller server instance.
    
    Args:
        controller (Controller): The controller to get the server for.
 
    Returns:
        FastAPI: The controller server instance.
    """
    if api_keys is None:
        app = FastAPI()
    else:
        api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        async def get_api_key(api_key: str = Security(api_key_header)):
            if api_key in api_keys:
                return api_key
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API Key",
            )
        app = FastAPI(dependencies=[Depends(get_api_key)])        
    
    def register_func(func: Callable, route: str, http_method: str):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
        match http_method:
            case "GET": app.get(route)(wrapper)
            case "POST": app.post(route)(wrapper)
            case _: raise ValueError(f"Unsupported HTTP method: {http_method}")
    
    method_names = controller.get_controller_methods()
    for method_name in method_names:
        method = getattr(controller, method_name)
        if hasattr(method, "_is_controller_method"):
            route = _construct_route(method, method_name, prepend_method_group)
            match method._controller_method_type:
                case ControllerMethodType.QUERY:
                    register_func(method, route, "GET")
                case ControllerMethodType.COMMAND:
                    register_func(method, route, "POST")
                case _:
                    raise ValueError(f"Unsupported method type: {method._controller_method_type}")

    return app


# %%
from ctrlstack import ctrl_cmd_method, ctrl_query_method, ctrl_method

class FooController(Controller):
    @ctrl_cmd_method
    def bar(self):
        pass
    
    @ctrl_query_method
    def baz(self, x: int) -> str:
        pass
    
    @ctrl_method(ControllerMethodType.QUERY, "q")
    def qux(self):
        pass
    
app = create_controller_server(FooController())

# %%
#|exporti
import socket
from contextlib import closing
import uvicorn

def _is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if the given port is available for binding."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.connect_ex((host, port)) != 0

def _find_free_port(host: str = "127.0.0.1") -> int:
    """Find and return an available port on the given host."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind((host, 0))  # 0 = OS picks a free port
        return s.getsockname()[1]
    
def _start_fastapi_server(app: FastAPI,
                         port: int,
                         uvicorn_kwargs: Optional[Dict[str, Any]] = None):
    uvicorn.run(app, host="127.0.0.1", port=port, **(uvicorn_kwargs or {}))
    
def _pid_exists(pid: int) -> bool:
    """Return True if a process with the given PID exists."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    else:
        return True


# %%
assert _is_port_free(_find_free_port())


# %%
#|export
def start_local_controller_server_process(
    controller: Controller|Callable[[], Controller],
    lockfile_path: str,
    port: Optional[int] = None,
) -> Tuple[int, int, bool]:
    """
    Start a local server for the given controller.
    
    Args:
        controller (Controller|Callable[[], Controller]): The controller or a callable that returns the controller to run.
        lockfile_path (str): Path to the lockfile that stores the port and PID.
        port (Optional[int]): The port to run the server on. If None, a free port will be found.
    """
    if port is None:
        port = _find_free_port()
    
    if Path(lockfile_path).exists():
        lines = Path(lockfile_path).read_text().splitlines()
        if len(lines) == 2:
            _port = int(lines[0].strip())
            pid = int(lines[1].strip())
            
            # Check if the PID is still running
            if not _pid_exists(pid):
                Path(lockfile_path).unlink()
                start_local_controller_server_process(controller, lockfile_path, port)
            
            return _port, pid, False
        else:
            raise ValueError(f"Invalid lockfile format: {lockfile_path}")
        
    controller = controller() if callable(controller) else controller
    app = create_controller_server(controller)
    
    with open(lockfile_path, "w") as f:
        f.write(f"{port}\n{os.getpid()}\n")
    
    _start_fastapi_server(app, port=port)


# %%
#|export
def get_local_controller_server_status(lockfile_path: str) -> Tuple[int, int, bool]:
    """
    Get the status of the server from the lockfile.
    
    Args:
        lockfile_path (str): Path to the lockfile that stores the port and PID.
        
    Returns:
        Tuple[int, int, bool]: A tuple containing the port number, process ID, and a boolean indicating if the server is running.
    """
    if not Path(lockfile_path).exists():
        return None, None, False
    
    lines = Path(lockfile_path).read_text().splitlines()
    if len(lines) != 2:
        raise ValueError(f"Invalid lockfile format: {lockfile_path}")
    
    port = int(lines[0].strip())
    pid = int(lines[1].strip())
    
    return port, pid, _pid_exists(pid)


# %%
#|export
def check_local_controller_server_process(
    lockfile_path: str,
) -> Tuple[Optional[int], Optional[int], bool]:
    """
    Check if a local server process is running and return its port and PID.
    
    Args:
        lockfile_path (str): Path to the lockfile that stores the port and PID.
        port (Optional[int]): The port to check. If None, the port from the lockfile will be used.
        
    Returns:
        Tuple[Optional[int], Optional[int], bool]: A tuple containing the port number, process ID, and a boolean indicating if the server is running.
    """
    if Path(lockfile_path).exists():
        lines = Path(lockfile_path).read_text().splitlines()
        if len(lines) == 2:
            _port = int(lines[0].strip())
            pid = int(lines[1].strip())
            
            # Check if the PID is still running
            if _pid_exists(pid):
                return _port, pid, True
        else:
            raise ValueError(f"Invalid lockfile format: {lockfile_path}")
    return None, None, False


# %%
#|export
def stop_local_controller_server_process(lockfile_path: str):
    if Path(lockfile_path).exists():
        lines = Path(lockfile_path).read_text().splitlines()
        if len(lines) == 2:
            port = int(lines[0].strip())
            pid = int(lines[1].strip())
            
            # Check if the PID is still running
            if _pid_exists(pid):
                os.kill(pid, signal.SIGTERM)
                return port, pid, True
            
            Path(lockfile_path).unlink()
        else:
            raise ValueError(f"Invalid lockfile format: {lockfile_path}")
    return None, None, False
