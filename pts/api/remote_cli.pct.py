# %% [markdown]
# # remote_cli

# %%
#|default_exp remote_cli

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()
import ctrlstack.remote_cli as this_module

# %%
#|export
from fastapi import FastAPI
import functools
from typing import Type, Optional, Callable
import typer
import inspect
import subprocess
import sys
import time, math
from ctrlstack import Controller, ControllerMethodType
from ctrlstack.cli import create_controller_cli
from ctrlstack.server import create_controller_server, start_local_controller_server_process, check_local_controller_server_process, stop_local_controller_server_process, _find_free_port
from ctrlstack.remote_controller import create_remote_controller

# %% [markdown]
# - Create a function that can start a fastapi server locally, but only if a lock file doesnt exist.
#    - It randomises the port name and stores it in the lock file.
#    - If the lock file exists but the port is not occupied, it removes the lock file and starts the server.
# - Define additional typer commands that can be used to start, stop and restart the server.

# %%
#|exporti
import pickle
def is_pickleable(obj):
    try:
        pickle.dumps(obj)
        return True
    except Exception:
        return False


# %%
assert not is_pickleable(lambda x: x)
def foo(): pass
assert is_pickleable(foo)


# %%
#|export
def create_remote_controller_cli(
    base_controller_cls: Type[Controller],
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    local_mode: bool = False,
    start_local_server_automatically: bool = True,
    lockfile_path: Optional[str] = None,
    controller: Controller|Callable[[], Controller] = None,
    local_server_start_timeout: float = 10.0
) -> typer.Typer:
    if not issubclass(base_controller_cls, Controller):
        raise TypeError("base_controller_cls must be a subclass of ctrlstack.Controller")
    if local_mode and url is not None:
        raise ValueError("If 'local_mode' is True then 'url' must be None.")
    if not local_mode and controller is not None:
        raise ValueError("If 'local_mode' is False then 'controller' must be None.")
    if local_mode:
        url = "http://localhost" # Placeholder
        
    remote_controller = create_remote_controller(base_controller_cls, url, api_key)
    cli_app = create_controller_cli(remote_controller)
    
    if local_mode:
        controller = controller or base_controller_cls()
        
        if lockfile_path is None:
            raise ValueError("If 'local_mode' is True then 'lockfile_path' must be specified.")
        
        @cli_app.command()
        def start_local_server(verbose: bool = True, port: Optional[int] = None):
            start_local_controller_server_process(controller, lockfile_path, port=port)
        
        @cli_app.command()
        def get_server_status():
            port, pid, server_is_running = check_local_controller_server_process(lockfile_path)
            if server_is_running:
                typer.echo(f"Local server is running on port {port} with PID {pid}.")
            else:
                typer.echo("No local server is running.")
        
        @cli_app.command()
        def stop_local_server(verbose: bool = True):
            port, pid, proc_existed = stop_local_controller_server_process(lockfile_path)
            if verbose:
                if proc_existed:
                    typer.echo(f"Stopped local server on port {port} with PID {pid}.")
                else:
                    typer.echo(f"No local server running.")
                    
        @cli_app.command()
        def restart_local_server(verbose: bool = True, port: Optional[int] = None):
            port, pid, proc_existed = stop_local_controller_server_process(lockfile_path)
            if verbose:
                if proc_existed:
                    typer.echo(f"Stopped local server on port {port} with PID {pid}.")
                else:
                    typer.echo(f"No local server running.")
            port = port or _find_free_port()
            start_local_controller_server_process(controller, lockfile_path, port=port)
                    
        @cli_app.callback()
        def entrypoint(ctx: typer.Context): 
            if start_local_server_automatically and ctx.invoked_subcommand is not None and ctx.invoked_subcommand not in ["start-local-server", "get-server-status", "stop-local-server"]:
                _, _, server_is_running = check_local_controller_server_process(lockfile_path)
                if not server_is_running:
                    subprocess.Popen([sys.executable, sys.argv[0]] + ["start-local-server"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                sleep_time = 0.1
                max_tries = math.ceil(local_server_start_timeout / sleep_time)
                for _ in range(max_tries):
                    port, pid, server_is_running = check_local_controller_server_process(lockfile_path)
                    if server_is_running:
                        break
                    time.sleep(sleep_time)
                if not server_is_running:
                    typer.echo(f"Local server did not start within {local_server_start_timeout} seconds. Please check the logs.")
                    raise typer.Exit(code=1)
                remote_controller.set_url(f"http://localhost:{port}")
            
            if ctx.invoked_subcommand is None:
                typer.echo(ctx.get_help())
        
    return cli_app
    


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
    
remote_controller = create_remote_controller(FooController, "local")
    
remote_cli_app = create_remote_controller_cli(
    FooController,
    local_mode=True,
    lockfile_path="/tmp/ctrlstack.lock",
)
