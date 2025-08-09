# %% [markdown]
# # controller

# %%
#|default_exp controller

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()
import ctrlstack.controller as this_module

# %%
#|export
from abc import ABC, abstractmethod
from enum import Enum


# %%
#|export
class ControllerMethodType(Enum):
    COMMAND = 'command'
    QUERY = 'query'

def ctrl_method(method_type: ControllerMethodType, group: str):
    """
    Decorator to define a Controller method
    """
    if group is None or not isinstance(group, str):
        raise ValueError("Group must be a string.")
    if not isinstance(method_type, ControllerMethodType):
        raise ValueError("Method type must be an instance of ControllerMethodType Enum.")
    def decorator(func):
        func._is_controller_method = True
        func._controller_method_group = group
        func._controller_method_type = method_type
        return func
    return decorator

def ctrl_cmd_method(func):
    """Decorator to define a command method in a Controller."""
    return ctrl_method(ControllerMethodType.COMMAND, 'cmd')(func)

def ctrl_query_method(func):
    """Decorator to define a query method in a Controller."""
    return ctrl_method(ControllerMethodType.QUERY, 'query')(func)


# %%
#|export
class Controller(ABC):
    @classmethod
    def get_controller_method_groups(cls):
        """List of controller method types in this controller."""
        return [getattr(cls, name)._controller_method_group for name in dir(cls) if hasattr(getattr(cls, name), '_controller_method_group')]
    
    @classmethod
    def get_controller_methods(cls, method_type: ControllerMethodType|None=None, group: str|None=None):
        """List of controller methods in this controller."""
        controller_methods = [name for name in dir(cls) if hasattr(getattr(cls, name), '_is_controller_method') and getattr(cls, name)._is_controller_method]
        if method_type is not None:
            controller_methods = [name for name in controller_methods if getattr(cls, name)._controller_method_type == method_type]
        if group is not None:
            controller_methods = [name for name in controller_methods if getattr(cls, name)._controller_method_group == group]
        return controller_methods


# %%
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
    
assert FooController.get_controller_method_groups() == ['cmd', 'query', 'q']
assert FooController.get_controller_methods() == ['bar', 'baz', 'qux']
assert FooController.get_controller_methods(group='cmd') == ['bar']
assert FooController.get_controller_methods(method_type=ControllerMethodType.COMMAND) == ['bar']
assert FooController.get_controller_methods(method_type=ControllerMethodType.QUERY) == ['baz', 'qux']
assert FooController.get_controller_methods(group='query') == ['baz']
assert FooController.get_controller_methods(group='q') == ['qux']
