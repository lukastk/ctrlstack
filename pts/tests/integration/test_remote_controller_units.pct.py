# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_remote_controller_units

# %%
#|default_exp test_remote_controller_units

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.remote_controller import (
    map_args_with_signature_types,
    prepare_requests_args,
    RemoteController,
    create_remote_controller,
)

# %%
#|export
class Priority(Enum):
    LOW = "low"
    HIGH = "high"

class MyModel(BaseModel):
    name: str
    value: int

# %%
#|export
# --- map_args_with_signature_types ---

def test_map_args_basic():
    def func(a: int, b: str): pass
    result = map_args_with_signature_types(func, [1, "hello"], {})
    assert result == {'a': (int, 1), 'b': (str, "hello")}

def test_map_args_skip_self_true():
    def func(self, a: int): pass
    result = map_args_with_signature_types(func, [10], {}, skip_self=True)
    assert 'self' not in result
    assert result == {'a': (int, 10)}

def test_map_args_skip_self_false():
    def func(self, a: int): pass
    result = map_args_with_signature_types(func, ["instance", 10], {}, skip_self=False)
    assert 'self' in result
    assert result['a'] == (int, 10)

def test_map_args_no_type_hints():
    def func(a, b): pass
    result = map_args_with_signature_types(func, [1, 2], {})
    assert result == {'a': (None, 1), 'b': (None, 2)}

def test_map_args_with_defaults():
    def func(a: int, b: str = "default"): pass
    result = map_args_with_signature_types(func, [1], {})
    assert result == {'a': (int, 1), 'b': (str, "default")}

def test_map_args_too_few_args():
    def func(a: int, b: str): pass
    with pytest.raises(TypeError):
        map_args_with_signature_types(func, [1], {})

def test_map_args_kwargs():
    def func(a: int, b: str): pass
    result = map_args_with_signature_types(func, [], {'a': 1, 'b': "hi"})
    assert result == {'a': (int, 1), 'b': (str, "hi")}

# %%
#|export
# --- prepare_requests_args ---

def test_prepare_args_all_query_params():
    def func(self, a: int, b: str, c: float): pass
    params, body = prepare_requests_args(func, [1, "hi", 2.5], {})
    assert params == {'a': 1, 'b': "hi", 'c': 2.5}
    assert body == {}

def test_prepare_args_single_body_param():
    def func(self, m: MyModel): pass
    model = MyModel(name="test", value=42)
    params, body = prepare_requests_args(func, [model], {})
    assert params == {}
    assert body == {'name': 'test', 'value': 42}  # Unwrapped (single body param)

def test_prepare_args_multiple_body_params():
    def func(self, m1: MyModel, m2: MyModel): pass
    model1 = MyModel(name="a", value=1)
    model2 = MyModel(name="b", value=2)
    params, body = prepare_requests_args(func, [model1, model2], {})
    assert params == {}
    assert body == {'m1': {'name': 'a', 'value': 1}, 'm2': {'name': 'b', 'value': 2}}

def test_prepare_args_none_values_skipped():
    def func(self, a: int, b: Optional[str] = None): pass
    params, body = prepare_requests_args(func, [1], {})
    assert params == {'a': 1}
    assert body == {}

def test_prepare_args_mixed_params():
    def func(self, query_msg: str, body: MyModel): pass
    model = MyModel(name="test", value=1)
    params, body = prepare_requests_args(func, ["hello", model], {})
    assert params == {'query_msg': "hello"}
    assert body == {'name': 'test', 'value': 1}  # Unwrapped

def test_prepare_args_enum_query_param():
    def func(self, p: Priority): pass
    params, body = prepare_requests_args(func, [Priority.HIGH], {})
    assert params == {'p': 'high'}  # Enum .value extracted
    assert body == {}

def test_prepare_args_dict_body():
    def func(self, data: Dict[str, int]): pass
    params, body = prepare_requests_args(func, [{"a": 1, "b": 2}], {})
    assert params == {}
    assert body == {"a": 1, "b": 2}  # Unwrapped

def test_prepare_args_list_body():
    def func(self, items: List[int]): pass
    params, body = prepare_requests_args(func, [[1, 2, 3]], {})
    assert params == {}
    assert body == [1, 2, 3]  # Unwrapped

# %%
#|export
# --- RemoteController ---

def test_remote_controller_init_url():
    class Base(Controller):
        @ctrl_query_method
        def info(self): pass
    rc = create_remote_controller(Base, url="http://localhost:8000")
    assert rc._url == "http://localhost:8000"

def test_remote_controller_init_api_key():
    class Base(Controller):
        @ctrl_query_method
        def info(self): pass
    rc = create_remote_controller(Base, url="http://localhost:8000", api_key="secret")
    assert rc._headers == {"X-API-Key": "secret"}

def test_remote_controller_init_no_api_key():
    class Base(Controller):
        @ctrl_query_method
        def info(self): pass
    rc = create_remote_controller(Base, url="http://localhost:8000")
    assert rc._headers == {}

def test_remote_controller_set_url():
    class Base(Controller):
        @ctrl_query_method
        def info(self): pass
    rc = create_remote_controller(Base, url="http://localhost:8000")
    rc.set_url("http://localhost:9000")
    assert rc._url == "http://localhost:9000"

def test_create_remote_controller_returns_remote_controller():
    class Base(Controller):
        @ctrl_query_method
        def info(self): pass
    rc = create_remote_controller(Base, url="http://localhost:8000")
    assert isinstance(rc, RemoteController)

def test_create_remote_controller_has_methods():
    class Base(Controller):
        @ctrl_cmd_method
        def cmd1(self): pass
        @ctrl_query_method
        def query1(self): pass
    rc = create_remote_controller(Base, url="http://localhost:8000")
    assert hasattr(rc, 'cmd1')
    assert hasattr(rc, 'query1')

def test_init_subclass_non_controller_raises():
    with pytest.raises(TypeError, match="must be a subclass"):
        class Bad(RemoteController, base_controller_cls=str): pass
