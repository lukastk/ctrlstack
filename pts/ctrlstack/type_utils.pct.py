# ---
# jupyter:
#   kernelspec:
#     display_name: ctrlstack
#     language: python
#     name: python3
# ---

# %% [markdown]
# # type_utils

# %%
#|default_exp type_utils

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()
import ctrlstack.type_utils as this_module

# %%
#|export
from typing import Any, Union, get_origin, get_args
from enum import Enum
from pydantic import TypeAdapter

# %%
#|export
def is_query_param_type(type_hint) -> bool:
    """True if type should be a URL query param (int/float/str/bool/Enum/Optional thereof)."""
    if type_hint is None:
        return False
    origin = get_origin(type_hint)
    if origin is Union:
        args = [a for a in get_args(type_hint) if a is not type(None)]
        if len(args) == 1:
            return is_query_param_type(args[0])
        return False
    if type_hint in (int, float, str, bool):
        return True
    if isinstance(type_hint, type) and issubclass(type_hint, Enum):
        return True
    return False

# %%
#|export
def serialize_for_query_param(value: Any) -> Any:
    """Convert a query param value to its wire format (e.g. Enum -> .value)."""
    if isinstance(value, Enum):
        return value.value
    return value

# %%
#|export
def serialize_value(value: Any, type_hint) -> Any:
    """Serialize any Python value to JSON-safe form via TypeAdapter."""
    return TypeAdapter(type_hint).dump_python(value, mode='json')

# %%
#|export
def deserialize_value(data: Any, type_hint) -> Any:
    """Deserialize JSON data to a typed Python object via TypeAdapter."""
    return TypeAdapter(type_hint).validate_python(data)

# %%
# Inline tests for is_query_param_type
from typing import Optional, List, Dict
from pydantic import BaseModel

class Priority(Enum):
    LOW = "low"
    HIGH = "high"

class MyModel(BaseModel):
    name: str

# Primitives
assert is_query_param_type(int) == True
assert is_query_param_type(float) == True
assert is_query_param_type(str) == True
assert is_query_param_type(bool) == True

# Enum
assert is_query_param_type(Priority) == True

# Optional of primitives/enum
assert is_query_param_type(Optional[int]) == True
assert is_query_param_type(Optional[str]) == True
assert is_query_param_type(Optional[Priority]) == True

# Complex types -> False (should go to body)
assert is_query_param_type(MyModel) == False
assert is_query_param_type(dict) == False
assert is_query_param_type(Dict[str, int]) == False
assert is_query_param_type(List[int]) == False
assert is_query_param_type(List[MyModel]) == False
assert is_query_param_type(None) == False
assert is_query_param_type(Union[int, str]) == False

# %%
# Inline tests for serialize_for_query_param
assert serialize_for_query_param(Priority.HIGH) == "high"
assert serialize_for_query_param(Priority.LOW) == "low"
assert serialize_for_query_param(42) == 42
assert serialize_for_query_param("hello") == "hello"
assert serialize_for_query_param(True) is True

# %%
# Inline tests for serialize_value / deserialize_value

class Inner(BaseModel):
    x: int

class Outer(BaseModel):
    name: str
    inner: Inner

# BaseModel round-trip
m = Outer(name="test", inner=Inner(x=42))
serialized = serialize_value(m, Outer)
assert serialized == {'name': 'test', 'inner': {'x': 42}}
assert isinstance(deserialize_value(serialized, Outer), Outer)

# List[BaseModel] round-trip
models = [Inner(x=1), Inner(x=2)]
serialized = serialize_value(models, List[Inner])
assert serialized == [{'x': 1}, {'x': 2}]
deserialized = deserialize_value(serialized, List[Inner])
assert all(isinstance(m, Inner) for m in deserialized)

# Dict[str, int]
d = {"a": 1, "b": 2}
serialized = serialize_value(d, Dict[str, int])
assert serialized == {"a": 1, "b": 2}
assert deserialize_value(serialized, Dict[str, int]) == d

# Enum
assert serialize_value(Priority.HIGH, Priority) == "high"
assert deserialize_value("high", Priority) == Priority.HIGH

# Primitives pass through
assert serialize_value(42, int) == 42
assert deserialize_value(42, int) == 42
assert serialize_value("hello", str) == "hello"
