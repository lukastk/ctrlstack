# %% [markdown]
# # remote_controller

# %%
#|default_exp remote_controller

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()
import ctrlstack.remote_controller as this_module

# %%
#|export
from fastapi import FastAPI
from ctrlstack import Controller, ControllerMethodType, ctrl_method
from ctrlstack.controller_app import _add_method_to_class
import functools
from typing import Type, Optional, Union, Dict, Any, Callable, List, Tuple
import inspect
import requests
from typing import get_type_hints, get_args, get_origin
from pydantic import BaseModel
from dataclasses import is_dataclass, asdict
from ctrlstack.server import _construct_route
import json


# %% [markdown]
# Does FastAPI provide some kind of way of converting a set of args and kwargs into inputs to `requests`? That is, converting them into the `params` and `json` of `requests.post` and `requests.get` etc.
#
# I know FastAPI does some clever conversions here, and I'd like to replicate it. For instance, I know that if there is a Pydantic model in the arguments then it automatically means that you put it into `json`
#
# I basically want a function `prepare_requests_args(kwargs)` that gives me two dictionaries corresponding to `params` and `json` respectively

# %%
#|exporti
def map_args_with_signature_types(func: Callable, args: List[Any], kwargs: Dict[str, Any], skip_self: bool = True) -> Dict[str, Tuple[Optional[Type], Any]]:
    """
    Map each argument name to a tuple of (signature_type, value) for the given function call.
    If no type is annotated, signature_type will be None.
    """
    sig = inspect.signature(func)
    
    if skip_self:
        # Skip the first argument if it's 'self' or 'cls'
        params = list(sig.parameters.values())
        if params and params[0].name in ('self', 'cls'):
            sig = sig.replace(parameters=params[1:])
            
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    type_hints = get_type_hints(func)

    return {
        name: (type_hints.get(name), value)
        for name, value in bound.arguments.items()
    }


# %%
def example_func(a, b: int, c="default", d: Optional[str]=None):
    pass

result = map_args_with_signature_types(example_func, [10, 20], {"d": [1, 2, 3]})
print(result)


# %%
#|exporti
def prepare_requests_args(func: Callable, args: List[Any], kwargs: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    arg_map = map_args_with_signature_types(func, args, kwargs)
    
    params = {}
    json_body = {}
    num_body_params = 0

    for key, (sig_type, value) in arg_map.items():
        if value is None:
            continue
        
        is_optional = get_origin(sig_type) is Union and type(None) in get_args(sig_type)
        if is_optional:
            sig_type = [t for t in get_args(sig_type) if t is not None][0]
        if sig_type is None:
            sig_type = type(value)
            
        if get_origin(sig_type) in [list, tuple, dict]:
            sig_type = get_origin(sig_type)
            
        # Pydantic models -> json
        if issubclass(sig_type, BaseModel):
            json_body[key] = value.model_dump()
            num_body_params += 1
        # Dataclasses -> json
        elif is_dataclass(sig_type):
            json_body[key] = asdict(value)
            num_body_params += 1
        # Dicts -> json
        elif issubclass(sig_type, dict):
            json_body[key] = value
            num_body_params += 1
        # Lists of models/dicts -> json
        elif issubclass(sig_type, list) or issubclass(sig_type, tuple):
            if all(isinstance(v, BaseModel) for v in value):
                json_body[key] = [v.model_dump() for v in value]
            elif all(is_dataclass(v) for v in value):
                json_body[key] = [asdict(v) for v in value]
            else:
                json_body[key] = value
            num_body_params += 1
        # Primitives -> params
        elif sig_type in [int, float, str, bool]:
            params[key] = value
        else:
            params[key] = value  # Fallback for unsupported types
        
    if num_body_params == 1:
        json_body = next(iter(json_body.values())) # Unwrap single body param

    return params, json_body


# %%
class FooModel(BaseModel):
    name: str
    value: int

def example_func(a, b: int, c: List[int], d: FooModel, e: Dict):
    pass

params, body = prepare_requests_args(
    example_func,
    args=[],
    kwargs={
        'a': 10,
        'b': 20,
        'c': [1, 2, 3],
        'd': FooModel(name="test", value=42),
        'e': {'key1': 'value1', 'key2': 'value2'}
    }
)

print("Params:", params)
print("Body:", body)


# %%
#|export
class RemoteController(Controller):
    def __init__(self, url: str, api_key: Optional[str] = None):
        self.set_url(url)
        self._api_key = api_key
        
        if self._api_key:
            self._headers = {"X-API-Key": self._api_key}
        else:
            self._headers = {}
            
    def set_url(self, url: str):
        self._url = url.lstrip('/')
    
    def __init_subclass__(cls, base_controller_cls: Type[Controller], prepend_method_group: bool=True, **kwargs):
        super().__init_subclass__(**kwargs)
        
        def register_method(method: Callable, route: str):
            @ctrl_method(method_type=method._controller_method_type, group=method._controller_method_group)
            @functools.wraps(method)
            async def remote_method(self, *args, **kwargs):
                params, body = prepare_requests_args(method, args, kwargs)
                if method._controller_method_type == ControllerMethodType.QUERY:
                    response = requests.get(f"{self._url}/{route.lstrip('/')}", params=params, json=body, headers=self._headers)
                elif method._controller_method_type == ControllerMethodType.COMMAND:
                    response = requests.post(f"{self._url}/{route.lstrip('/')}", params=params, json=body, headers=self._headers)
                else:
                    raise ValueError(f"Unsupported method type: {method._controller_method_type}")
                if response.status_code != 200:
                    raise Exception(f"Error calling remote method {method.__name__}: {response.text}")
                json_response = response.json()
                if json_response:
                    return json_response
            _add_method_to_class(remote_method, cls, method.__name__, pass_self=True)
        
        for method_name in base_controller_cls.get_controller_methods():
            method = getattr(base_controller_cls, method_name)
            route = _construct_route(method, method_name, prepend_method_group)
            register_method(method, route)


# %%
#|export
def create_remote_controller(
    base_controller_cls: Type[Controller],
    url: str,
    api_key: Optional[str] = None,
) -> RemoteController:
    class _RemoteController(RemoteController, base_controller_cls=base_controller_cls): pass
    return _RemoteController(url, api_key)


# %%
# Check that the argument sets of RemoteController.__init__ and create_remote_controller match
argset1 = set(p.name for p in inspect.signature(RemoteController.__init__).parameters.values())
argset1.remove('self')
argset2 = set(p.name for p in inspect.signature(create_remote_controller).parameters.values())
argset2.remove('base_controller_cls')
assert argset1 == argset2

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

foo_remote_controller = create_remote_controller(FooController, url="http://localhost:8000")

# %%
# foo_remote_controller.baz?
