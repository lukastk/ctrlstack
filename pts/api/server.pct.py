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
from typing import Callable, Optional, List
import inspect


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
def create_ctrl_server(controller: Controller, prepend_method_group: bool=True, api_keys: Optional[List[str]] = None) -> FastAPI:
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
    
app = create_ctrl_server(FooController())
