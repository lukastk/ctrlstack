# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_controller

# %%
#|default_exp test_controller

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
from ctrlstack.controller import Controller, ControllerMethodType, ctrl_method, ctrl_cmd_method, ctrl_query_method

# %%
#|export
# --- ControllerMethodType ---

def test_controller_method_type_values():
    assert ControllerMethodType.COMMAND.value == 'command'
    assert ControllerMethodType.QUERY.value == 'query'

def test_controller_method_type_has_two_members():
    assert len(ControllerMethodType) == 2

# %%
#|export
# --- ctrl_method decorator ---

def test_ctrl_method_sets_attributes():
    @ctrl_method(ControllerMethodType.COMMAND, "grp")
    def my_func(): pass
    assert my_func._is_controller_method is True
    assert my_func._controller_method_type == ControllerMethodType.COMMAND
    assert my_func._controller_method_group == "grp"

def test_ctrl_method_returns_same_function():
    def my_func(): pass
    result = ctrl_method(ControllerMethodType.COMMAND, "grp")(my_func)
    assert result is my_func

def test_ctrl_method_invalid_type_none():
    with pytest.raises(ValueError, match="ControllerMethodType"):
        ctrl_method(None, "grp")

def test_ctrl_method_invalid_type_string():
    with pytest.raises(ValueError, match="ControllerMethodType"):
        ctrl_method("command", "grp")

def test_ctrl_method_invalid_group_none():
    with pytest.raises(ValueError, match="Group must be a string"):
        ctrl_method(ControllerMethodType.COMMAND, None)

def test_ctrl_method_invalid_group_int():
    with pytest.raises(ValueError, match="Group must be a string"):
        ctrl_method(ControllerMethodType.COMMAND, 123)

# %%
#|export
# --- ctrl_cmd_method / ctrl_query_method ---

def test_ctrl_cmd_method_attributes():
    @ctrl_cmd_method
    def my_func(): pass
    assert my_func._is_controller_method is True
    assert my_func._controller_method_type == ControllerMethodType.COMMAND
    assert my_func._controller_method_group == 'cmd'

def test_ctrl_query_method_attributes():
    @ctrl_query_method
    def my_func(): pass
    assert my_func._is_controller_method is True
    assert my_func._controller_method_type == ControllerMethodType.QUERY
    assert my_func._controller_method_group == 'query'

# %%
#|export
# --- Controller.get_controller_methods ---

class SampleController(Controller):
    @ctrl_cmd_method
    def cmd_a(self): pass

    @ctrl_cmd_method
    def cmd_b(self): pass

    @ctrl_query_method
    def query_a(self): pass

    @ctrl_method(ControllerMethodType.QUERY, "custom")
    def query_custom(self): pass

    def regular_method(self): pass

class EmptyController(Controller): pass

def test_get_controller_methods_all():
    methods = SampleController.get_controller_methods()
    assert methods == ['cmd_a', 'cmd_b', 'query_a', 'query_custom']

def test_get_controller_methods_by_type_command():
    methods = SampleController.get_controller_methods(method_type=ControllerMethodType.COMMAND)
    assert methods == ['cmd_a', 'cmd_b']

def test_get_controller_methods_by_type_query():
    methods = SampleController.get_controller_methods(method_type=ControllerMethodType.QUERY)
    assert methods == ['query_a', 'query_custom']

def test_get_controller_methods_by_group():
    assert SampleController.get_controller_methods(group='cmd') == ['cmd_a', 'cmd_b']
    assert SampleController.get_controller_methods(group='query') == ['query_a']
    assert SampleController.get_controller_methods(group='custom') == ['query_custom']

def test_get_controller_methods_by_type_and_group():
    methods = SampleController.get_controller_methods(method_type=ControllerMethodType.QUERY, group='custom')
    assert methods == ['query_custom']

def test_get_controller_methods_empty():
    assert EmptyController.get_controller_methods() == []

def test_get_controller_methods_no_match():
    assert SampleController.get_controller_methods(group='nonexistent') == []

def test_non_decorated_methods_excluded():
    methods = SampleController.get_controller_methods()
    assert 'regular_method' not in methods

# %%
#|export
# --- Controller.get_controller_method_groups ---

def test_get_controller_method_groups():
    groups = SampleController.get_controller_method_groups()
    assert groups == ['cmd', 'cmd', 'query', 'custom']

def test_get_controller_method_groups_empty():
    assert EmptyController.get_controller_method_groups() == []

# %%
#|export
# --- Inheritance ---

class ParentController(Controller):
    @ctrl_cmd_method
    def parent_cmd(self): pass

class ChildController(ParentController):
    @ctrl_query_method
    def child_query(self): pass

def test_inheritance_carries_methods():
    methods = ChildController.get_controller_methods()
    assert 'parent_cmd' in methods
    assert 'child_query' in methods

def test_inheritance_parent_unaffected():
    methods = ParentController.get_controller_methods()
    assert 'parent_cmd' in methods
    assert 'child_query' not in methods
