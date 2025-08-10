# %% [markdown]
# # controller_app

# %%
#|default_exp controller_app

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()
import ctrlstack.controller_app as this_module

# %%
#|export
from ctrlstack.controller import Controller, ControllerMethodType, ctrl_method, ctrl_cmd_method, ctrl_query_method
import functools
from typing import Type, Callable, Optional
import inspect


# %%
#|exporti
def _add_method_to_class(func: Callable, controller_cls: Type[Controller], name: Optional[str], pass_self: bool = False):
    if inspect.iscoroutinefunction(func):
        async def method(self, *args, **kwargs):
            if pass_self: return await func(self, *args, **kwargs)
            return await func(*args, **kwargs)
    else:
        def method(self, *args, **kwargs):
            if pass_self: return func(self, *args, **kwargs)
            return func(*args, **kwargs)
        
    # Keep metadata, but fix what inspect sees
    functools.update_wrapper(method, func)

    # Build a signature that excludes `self` since the method will be bound to the instance
    orig_sig = inspect.signature(func)
    params = list(orig_sig.parameters.values())
    
    # Remove 'self' parameter if it exists (it will be handled by the bound method)
    if params and params[0].name in ('self', 'cls'):
        params = params[1:]
    
    method.__signature__ = inspect.Signature(
        parameters=params,
        return_annotation=orig_sig.return_annotation
    )
        
    method.__name__ = name or func.__name__
    setattr(controller_cls, method.__name__, method)


# %%
#|export
class ControllerApp:
    def __init__(self):
        class _Controller(Controller): pass
        self._controller_cls = _Controller
    
    @property
    def controller_cls(self) -> Type[Controller]:
        return self._controller_cls
    
    def register(self, method_type: ControllerMethodType, group: str, name: Optional[str] = None):
        def decorator(func: Callable):
            _func = ctrl_method(method_type=method_type, group=group)(func)
            _add_method_to_class(_func, self._controller_cls, name)
            return func
        return decorator
    
    def register_cmd(self, name: Optional[str] = None):
        def decorator(func: Callable):
            _func = ctrl_cmd_method(func)
            _add_method_to_class(_func, self._controller_cls, name)
            return func
        return decorator
    
    def register_query(self, name: Optional[str] = None):
        def decorator(func: Callable):
            _func = ctrl_query_method(func)
            _add_method_to_class(_func, self._controller_cls, name)
            return func
        return decorator
    
    def get_controller(self) -> Type[Controller]:
        return self._controller_cls()
    
    def crreate_server_app(self, *args, **kwargs) -> 'FastAPI':
        from ctrlstack.server import create_controller_server
        return create_controller_server(self.get_controller(), *args, **kwargs)
    
    def create_cli_app(self, *args, **kwargs) -> 'ClickApp':
        from ctrlstack.cli import create_controller_cli
        return create_controller_cli(self.get_controller(), *args, **kwargs)


# %%
capp = ControllerApp()

@capp.register(ControllerMethodType.COMMAND, group="test")
def foo():
    """A simple test function."""
    return "Hello, World!"

@capp.register_cmd(name="bar_cmd")
def bar():
    """A simple test function."""
    return "Hello, World!"

@capp.register_query(name="baz_query")
def baz():
    """A simple test function."""
    return "Hello, World!"

assert capp.controller_cls.get_controller_methods() == ['bar_cmd', 'baz_query', 'foo']
assert capp.controller_cls.get_controller_method_groups() == ['cmd', 'query', 'test']
assert capp.get_controller().foo() == "Hello, World!"
assert capp.get_controller().bar_cmd() == "Hello, World!"
assert capp.get_controller().baz_query() == "Hello, World!"

cli_app = capp.create_cli_app()
server_app = capp.crreate_server_app()
