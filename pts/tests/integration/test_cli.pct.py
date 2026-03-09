# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_cli

# %%
#|default_exp test_cli

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
from enum import Enum
from pydantic import BaseModel
from typing import List, Dict
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.cli import create_controller_cli
from ctrlstack.controller_app import ControllerApp
from typer.testing import CliRunner

# %%
#|export
class Priority(Enum):
    LOW = "low"
    HIGH = "high"

class MyModel(BaseModel):
    name: str
    value: int

runner = CliRunner()

capp = ControllerApp()

@capp.register_cmd()
async def bar():
    print("bar")

@capp.register_cmd()
def bar2(arg1: MyModel, arg2: dict, arg3: int):
    print("arg1:", arg1.model_dump())
    print("arg2:", arg2)
    print("arg3:", arg3)

@capp.register_query()
def baz(x: int) -> str:
    return f"baz {x}"

@capp.register_query()
def qux():
    return "qux"

@capp.register_cmd()
def with_list(items: List[int]) -> str:
    return f"sum={sum(items)}"

@capp.register_cmd()
def with_list_model(items: List[MyModel]) -> str:
    return f"count={len(items)}"

@capp.register_cmd()
def with_dict(data: Dict[str, int]) -> str:
    return f"keys={sorted(data.keys())}"

@capp.register_query()
def with_enum(priority: Priority) -> str:
    return f"priority={priority.value}"

cli_app = create_controller_cli(capp.get_controller())

# %%
#|export
def test_bar():
    result = runner.invoke(cli_app, ["bar"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "bar"

def test_bar2():
    result = runner.invoke(cli_app, ["bar2", '{"name": "test", "value": 42}', '{"key": "value"}', "123"])
    assert result.exit_code == 0
    assert result.stdout == "arg1: {'name': 'test', 'value': 42}\narg2: {'key': 'value'}\narg3: 123\n"

def test_baz():
    result = runner.invoke(cli_app, ["baz", "123"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "baz 123"

def test_qux():
    result = runner.invoke(cli_app, ["qux"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "qux"

def test_with_list():
    result = runner.invoke(cli_app, ["with_list", '[1, 2, 3]'])
    assert result.exit_code == 0
    assert result.stdout.strip() == "sum=6"

def test_with_list_model():
    result = runner.invoke(cli_app, ["with_list_model", '[{"name": "a", "value": 1}, {"name": "b", "value": 2}]'])
    assert result.exit_code == 0
    assert result.stdout.strip() == "count=2"

def test_with_dict():
    result = runner.invoke(cli_app, ["with_dict", '{"x": 1, "y": 2}'])
    assert result.exit_code == 0
    assert result.stdout.strip() == "keys=['x', 'y']"

def test_with_enum():
    result = runner.invoke(cli_app, ["with_enum", "high"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "priority=high"

# %%
# Quick manual check
result = runner.invoke(cli_app, ["bar"])
print(result.stdout)
