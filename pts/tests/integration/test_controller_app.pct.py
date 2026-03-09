# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_controller_app

# %%
#|default_exp test_controller_app

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
import asyncio
from ctrlstack.controller import Controller, ControllerMethodType
from ctrlstack.controller_app import ControllerApp, _add_method_to_class

# %%
#|export
# --- ControllerApp basics ---

def test_controller_app_creates_controller_subclass():
    capp = ControllerApp()
    assert issubclass(capp.controller_cls, Controller)

def test_get_controller_returns_instance():
    capp = ControllerApp()
    ctrl = capp.get_controller()
    assert isinstance(ctrl, Controller)

# %%
#|export
# --- register_cmd ---

def test_register_cmd_default_name():
    capp = ControllerApp()
    @capp.register_cmd()
    def my_command(): return "result"
    assert 'my_command' in capp.controller_cls.get_controller_methods()

def test_register_cmd_custom_name():
    capp = ControllerApp()
    @capp.register_cmd(name="custom_cmd")
    def my_command(): return "result"
    assert 'custom_cmd' in capp.controller_cls.get_controller_methods()
    assert 'my_command' not in capp.controller_cls.get_controller_methods()

def test_register_cmd_returns_original_function():
    capp = ControllerApp()
    def my_func(): return "hello"
    result = capp.register_cmd()(my_func)
    assert result is my_func

def test_register_cmd_method_callable():
    capp = ControllerApp()
    @capp.register_cmd()
    def greet(name: str): return f"hello {name}"
    ctrl = capp.get_controller()
    assert ctrl.greet("world") == "hello world"

# %%
#|export
# --- register_query ---

def test_register_query_default_name():
    capp = ControllerApp()
    @capp.register_query()
    def my_query(): return "data"
    methods = capp.controller_cls.get_controller_methods(method_type=ControllerMethodType.QUERY)
    assert 'my_query' in methods

def test_register_query_custom_name():
    capp = ControllerApp()
    @capp.register_query(name="custom_q")
    def my_query(): return "data"
    assert 'custom_q' in capp.controller_cls.get_controller_methods()

# %%
#|export
# --- register (generic) ---

def test_register_generic():
    capp = ControllerApp()
    @capp.register(ControllerMethodType.COMMAND, group="ops")
    def deploy(): return "deployed"
    methods = capp.controller_cls.get_controller_methods(group="ops")
    assert 'deploy' in methods

def test_register_generic_custom_name():
    capp = ControllerApp()
    @capp.register(ControllerMethodType.QUERY, group="info", name="sys_info")
    def get_info(): return "info"
    assert 'sys_info' in capp.controller_cls.get_controller_methods()

# %%
#|export
# --- Async methods ---

def test_registered_async_method():
    capp = ControllerApp()
    @capp.register_cmd()
    async def async_cmd(x: int): return x * 2
    ctrl = capp.get_controller()
    result = asyncio.run(ctrl.async_cmd(5))
    assert result == 10

# %%
#|export
# --- Multiple registrations ---

def test_multiple_registrations():
    capp = ControllerApp()
    @capp.register_cmd()
    def cmd1(): return "c1"
    @capp.register_cmd()
    def cmd2(): return "c2"
    @capp.register_query()
    def q1(): return "q1"
    ctrl = capp.get_controller()
    assert ctrl.cmd1() == "c1"
    assert ctrl.cmd2() == "c2"
    assert ctrl.q1() == "q1"

# %%
#|export
# --- Isolation between ControllerApp instances ---

def test_separate_controller_apps_isolated():
    capp1 = ControllerApp()
    capp2 = ControllerApp()
    @capp1.register_cmd()
    def only_in_app1(): return "app1"
    @capp2.register_cmd()
    def only_in_app2(): return "app2"
    assert 'only_in_app1' in capp1.controller_cls.get_controller_methods()
    assert 'only_in_app1' not in capp2.controller_cls.get_controller_methods()
    assert 'only_in_app2' in capp2.controller_cls.get_controller_methods()
    assert 'only_in_app2' not in capp1.controller_cls.get_controller_methods()

# %%
#|export
# --- _add_method_to_class ---

def test_add_method_to_class_sync():
    class TestCtrl(Controller): pass
    def my_func(): return "sync"
    _add_method_to_class(my_func, TestCtrl, "my_method")
    inst = TestCtrl()
    assert inst.my_method() == "sync"

def test_add_method_to_class_async():
    class TestCtrl(Controller): pass
    async def my_func(): return "async"
    _add_method_to_class(my_func, TestCtrl, "my_method")
    inst = TestCtrl()
    result = asyncio.run(inst.my_method())
    assert result == "async"

def test_add_method_to_class_pass_self_true():
    class TestCtrl(Controller):
        value = 42
    def my_func(self): return self.value
    _add_method_to_class(my_func, TestCtrl, "get_value", pass_self=True)
    inst = TestCtrl()
    assert inst.get_value() == 42

def test_add_method_to_class_pass_self_false():
    class TestCtrl(Controller): pass
    def my_func(): return "no self"
    _add_method_to_class(my_func, TestCtrl, "no_self_method", pass_self=False)
    inst = TestCtrl()
    assert inst.no_self_method() == "no self"

def test_add_method_to_class_uses_name():
    class TestCtrl(Controller): pass
    def original_name(): return "x"
    _add_method_to_class(original_name, TestCtrl, "custom_name")
    assert hasattr(TestCtrl, "custom_name")
    assert not hasattr(TestCtrl, "original_name")
