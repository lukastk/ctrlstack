# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_type_utils

# %%
#|default_exp test_type_utils

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
from enum import Enum
from typing import Optional, List, Dict, Union
from pydantic import BaseModel
from ctrlstack.type_utils import is_query_param_type, serialize_value, deserialize_value, serialize_for_query_param

# %%
#|export
class Priority(Enum):
    LOW = "low"
    HIGH = "high"

class Inner(BaseModel):
    x: int

class Outer(BaseModel):
    name: str
    inner: Inner

# %%
#|export
# --- is_query_param_type tests ---

def test_is_query_param_type_int():
    assert is_query_param_type(int) is True

def test_is_query_param_type_float():
    assert is_query_param_type(float) is True

def test_is_query_param_type_str():
    assert is_query_param_type(str) is True

def test_is_query_param_type_bool():
    assert is_query_param_type(bool) is True

def test_is_query_param_type_enum():
    assert is_query_param_type(Priority) is True

def test_is_query_param_type_optional_int():
    assert is_query_param_type(Optional[int]) is True

def test_is_query_param_type_optional_enum():
    assert is_query_param_type(Optional[Priority]) is True

def test_is_query_param_type_basemodel():
    assert is_query_param_type(Inner) is False

def test_is_query_param_type_dict():
    assert is_query_param_type(dict) is False

def test_is_query_param_type_dict_generic():
    assert is_query_param_type(Dict[str, int]) is False

def test_is_query_param_type_list_int():
    assert is_query_param_type(List[int]) is False

def test_is_query_param_type_list_model():
    assert is_query_param_type(List[Inner]) is False

def test_is_query_param_type_none():
    assert is_query_param_type(None) is False

def test_is_query_param_type_union():
    assert is_query_param_type(Union[int, str]) is False

# %%
#|export
# --- serialize_value tests ---

def test_serialize_basemodel():
    m = Inner(x=42)
    assert serialize_value(m, Inner) == {'x': 42}

def test_serialize_nested_model():
    m = Outer(name="test", inner=Inner(x=1))
    assert serialize_value(m, Outer) == {'name': 'test', 'inner': {'x': 1}}

def test_serialize_list_of_models():
    models = [Inner(x=1), Inner(x=2)]
    assert serialize_value(models, List[Inner]) == [{'x': 1}, {'x': 2}]

def test_serialize_dict():
    d = {"a": 1, "b": 2}
    assert serialize_value(d, Dict[str, int]) == {"a": 1, "b": 2}

def test_serialize_enum():
    assert serialize_value(Priority.HIGH, Priority) == "high"

def test_serialize_primitive():
    assert serialize_value(42, int) == 42
    assert serialize_value("hello", str) == "hello"

# %%
#|export
# --- deserialize_value tests ---

def test_deserialize_basemodel():
    result = deserialize_value({'x': 42}, Inner)
    assert isinstance(result, Inner)
    assert result.x == 42

def test_deserialize_nested_model():
    result = deserialize_value({'name': 'test', 'inner': {'x': 1}}, Outer)
    assert isinstance(result, Outer)
    assert isinstance(result.inner, Inner)

def test_deserialize_list_of_models():
    result = deserialize_value([{'x': 1}, {'x': 2}], List[Inner])
    assert len(result) == 2
    assert all(isinstance(m, Inner) for m in result)

def test_deserialize_dict():
    result = deserialize_value({"a": 1, "b": 2}, Dict[str, int])
    assert result == {"a": 1, "b": 2}

def test_deserialize_enum():
    result = deserialize_value("high", Priority)
    assert result == Priority.HIGH

def test_deserialize_primitive():
    assert deserialize_value(42, int) == 42

# %%
#|export
# --- Round-trip tests ---

def test_roundtrip_model():
    m = Outer(name="rt", inner=Inner(x=99))
    assert deserialize_value(serialize_value(m, Outer), Outer) == m

def test_roundtrip_list_of_models():
    models = [Inner(x=1), Inner(x=2)]
    result = deserialize_value(serialize_value(models, List[Inner]), List[Inner])
    assert result == models

def test_roundtrip_enum():
    assert deserialize_value(serialize_value(Priority.LOW, Priority), Priority) == Priority.LOW

# %%
#|export
# --- serialize_for_query_param tests ---

def test_serialize_for_query_param_enum():
    assert serialize_for_query_param(Priority.HIGH) == "high"
    assert serialize_for_query_param(Priority.LOW) == "low"

def test_serialize_for_query_param_int():
    assert serialize_for_query_param(42) == 42

def test_serialize_for_query_param_str():
    assert serialize_for_query_param("hello") == "hello"

def test_serialize_for_query_param_bool():
    assert serialize_for_query_param(True) is True

# %%
#|export
# --- Additional is_query_param_type edge cases ---

def test_is_query_param_type_optional_float():
    assert is_query_param_type(Optional[float]) is True

def test_is_query_param_type_optional_bool():
    assert is_query_param_type(Optional[bool]) is True

def test_is_query_param_type_optional_model():
    assert is_query_param_type(Optional[Inner]) is False

def test_is_query_param_type_optional_list():
    assert is_query_param_type(Optional[List[int]]) is False
