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
from pydantic import BaseModel
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.cli import create_controller_cli
from ctrlstack.controller_app import ControllerApp
from typer.testing import CliRunner

# %%
#|export
runner = CliRunner()

capp = ControllerApp()

@capp.register_cmd()
async def bar():
    print("bar")

class MyModel(BaseModel):
    name: str
    value: int

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

# %%
# Quick manual check
result = runner.invoke(cli_app, ["bar"])
print(result.stdout)
