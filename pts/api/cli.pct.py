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
from typing import List, Callable, Optional, get_origin, get_args, Dict, Union, Any, Mapping
import inspect
import asyncio
import json
from pydantic import BaseModel


# %%
#|exporti
def _is_dict_annotation(annotation):
    origin = get_origin(annotation)
    if origin is dict or origin is Dict or annotation is dict:
        return True
    # Handle Optional[Dict] and Union types
    if origin is not None and hasattr(origin, "__origin__"):
        origin = origin.__origin__
    if origin is not None and origin.__name__ == "Union":
        args = get_args(annotation)
        return any(_is_dict_annotation(arg) for arg in args if arg is not type(None))
    return False


# %%
assert _is_dict_annotation(dict)
assert _is_dict_annotation(Dict)
assert _is_dict_annotation(Dict[str, int])
assert _is_dict_annotation(Optional[Dict[str, str]])


# %%
#|exporti
def _unwrap_optional(annotation):
    """
    If annotation is Optional[T], return T. Otherwise, return annotation.
    """
    origin = get_origin(annotation)
    if origin is not None and origin.__name__ == "Union":
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


# %%
assert _unwrap_optional(Dict[str, int]) == Dict[str, int]
assert _unwrap_optional(Optional[Dict[str, int]]) == Dict[str, int]
assert _unwrap_optional(str) == str
assert _unwrap_optional(Optional[str]) == str
assert _unwrap_optional(None) == None


# %%
#|exporti
def _is_pydantic_model(tp) -> bool:
    return isinstance(tp, type) and issubclass(tp, BaseModel)

def _make_typer_compatible_func(func):
    sig = inspect.signature(func)
    params = list(sig.parameters.values())

    new_params = []
    # store converters per-arg instead of classes; more flexible
    converters: dict[str, Callable[[str], Any]] = {}
    changed_params: set[str] = set()

    for p in params:
        ann = p.annotation
        if ann is inspect._empty:
            new_params.append(p)
            continue

        ann2 = _unwrap_optional(ann)

        if _is_pydantic_model(ann2):
            # CLI receives JSON string -> parse -> model(**dict)
            new_params.append(p.replace(annotation=str))
            converters[p.name] = (lambda M: (lambda s: M(**json.loads(s))))(ann2)
            changed_params.add(p.name)
        elif _is_dict_annotation(ann2):
            # CLI receives JSON string -> dict
            new_params.append(p.replace(annotation=str))
            converters[p.name] = lambda s: json.loads(s)
            changed_params.add(p.name)
        else:
            new_params.append(p)

    new_sig = sig.replace(parameters=new_params)

    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def new_func(*args, **kwargs):
            bound = new_sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for name, conv in converters.items():
                if name in bound.arguments and isinstance(bound.arguments[name], str):
                    bound.arguments[name] = conv(bound.arguments[name])
            return await func(*bound.args, **bound.kwargs)
    else:
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            bound = new_sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for name, conv in converters.items():
                if name in bound.arguments and isinstance(bound.arguments[name], str):
                    bound.arguments[name] = conv(bound.arguments[name])
            return func(*bound.args, **bound.kwargs)

    new_func.__signature__ = new_sig
    orig_ann = dict(getattr(func, "__annotations__", {}))
    for name in changed_params:
        orig_ann[name] = str
    new_func.__annotations__ = orig_ann

    return new_func


# %%
class MyArg(BaseModel):
    name: str
    value: int

@_make_typer_compatible_func
def foo(arg1: MyArg, arg2: dict, arg3: int):
    print(arg1.model_dump())
    print(arg2)
    print(arg3)

foo(
    arg1='{"name": "test", "value": 42}',
    arg2='{"key": "value"}',
    arg3=123
)

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
    if not isinstance(controller, Controller):
        raise TypeError("The controller must be an instance of ctrlstack.Controller")
    
    app = typer.Typer(invoke_without_command=True)
    
    @app.callback()
    def entrypoint(ctx: typer.Context):
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            
    def register_func(bound_method: Callable, cmd_name: str): 
        func = _make_typer_compatible_func(bound_method.__func__)
        
        if inspect.iscoroutinefunction(bound_method):
            def wrapper(*args, **kwargs):
                res = asyncio.run(func(bound_method.__self__, *args, **kwargs))
                if res is not None: typer.echo(res)
        else:
            def wrapper(*args, **kwargs):
                res = func(bound_method.__self__, *args, **kwargs)
                if res is not None: typer.echo(res)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        wrapper.__annotations__ = func.__annotations__
        # Remove the first parameter (self) from the signature
        old_sig = inspect.signature(func)
        new_sig = old_sig.replace(
            parameters=list(old_sig.parameters.values())[1:]
        )
        wrapper.__signature__ = new_sig
        app.command(name=cmd_name)(wrapper)
    
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
    
    @ctrl_cmd_method
    def bar2(self, arg: dict):
        print(f"Executing bar2 command with arg: {arg}")
    
    @ctrl_query_method
    def baz(self, x: int) -> str:
        pass
    
    @ctrl_method(ControllerMethodType.QUERY, "q")
    def qux(self):
        pass
    
app = create_controller_cli(FooController())

# %%
from typer.testing import CliRunner
runner = CliRunner()
result = runner.invoke(app, ["bar2", '{"key": "value"}'])
print(result.stdout)
