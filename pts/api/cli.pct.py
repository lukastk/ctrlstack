# %% [markdown]
# # cli

# %%
#|default_exp cli

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()
import ctrlstack.cli as this_module

# %%
#|export
import typer
from ctrlstack import Controller, ControllerMethodType
import functools
from typing import List, Callable, Optional
import inspect
import asyncio

# %%
#|hide
show_doc(this_module.create_controller_cli)


# %%
#|export
def create_controller_cli(controller: Controller, prepend_method_group: bool=False) -> typer.Typer:
    """
    Get the controller server instance.
    
    Args:
        controller (Controller): The controller to get the server for.

    Returns:
        FastAPI: The controller server instance.
    """
    app = typer.Typer(invoke_without_command=True)
    
    @app.callback()
    def entrypoint(ctx: typer.Context):
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
                
    def register_func(func: Callable, cmd_name: str):
        if inspect.iscoroutinefunction(func):
            @app.command(name=cmd_name)
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                res = asyncio.run(func(*args, **kwargs))
                if res is not None:
                    typer.echo(res)
        else:
            @app.command(name=cmd_name)
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                res = func(*args, **kwargs)
                if res is not None:
                    typer.echo(res)
    
    method_names = controller.get_controller_methods()
    for method_name in method_names:
        method = getattr(controller, method_name)
        if hasattr(method, "_is_controller_method"):
            if prepend_method_group:
                cmd_name = f"{method._controller_method_group}-{method_name}" if method._controller_method_group else method_name
            else:
                cmd_name = method_name
            register_func(method, cmd_name)

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
    
app = create_controller_cli(FooController())
