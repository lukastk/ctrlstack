# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_cli_edge_cases

# %%
#|default_exp test_cli_edge_cases

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
from pydantic import BaseModel
from typing import Optional
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.cli import create_controller_cli, _make_typer_compatible_func
from ctrlstack.controller_app import ControllerApp
from typer.testing import CliRunner

# %%
#|export
runner = CliRunner()

# %%
#|export
# --- create_controller_cli validation ---

def test_create_cli_non_controller_raises():
    with pytest.raises(TypeError, match="must be an instance"):
        create_controller_cli("not a controller")

# %%
#|export
# --- prepend_method_group ---

def test_create_cli_prepend_method_group():
    class MyCtrl(Controller):
        @ctrl_cmd_method
        def do_thing(self): return "done"
        @ctrl_method(ControllerMethodType.QUERY, "custom")
        def info(self): return "info"
    app = create_controller_cli(MyCtrl(), prepend_method_group=True)
    # cmd-do_thing and custom-info should be command names
    result = runner.invoke(app, ["cmd-do_thing"])
    assert result.exit_code == 0
    result2 = runner.invoke(app, ["custom-info"])
    assert result2.exit_code == 0
    assert result2.stdout.strip() == "info"

# %%
#|export
# --- CLI no subcommand shows help ---

def test_cli_no_subcommand_shows_help():
    capp = ControllerApp()
    @capp.register_cmd()
    def hello(): print("hi")
    app = create_controller_cli(capp.get_controller())
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "hello" in result.stdout.lower()

# %%
#|export
# --- Return value handling ---

def test_cli_returns_none_no_output():
    capp = ControllerApp()
    @capp.register_cmd()
    def noop(): return None
    app = create_controller_cli(capp.get_controller())
    result = runner.invoke(app, ["noop"])
    assert result.exit_code == 0
    assert result.stdout.strip() == ""

def test_cli_returns_zero_prints_zero():
    capp = ControllerApp()
    @capp.register_query()
    def get_zero() -> int: return 0
    app = create_controller_cli(capp.get_controller())
    result = runner.invoke(app, ["get_zero"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "0"

def test_cli_returns_false_prints_false():
    capp = ControllerApp()
    @capp.register_query()
    def get_false() -> bool: return False
    app = create_controller_cli(capp.get_controller())
    result = runner.invoke(app, ["get_false"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "False"

def test_cli_returns_empty_string_no_output():
    capp = ControllerApp()
    @capp.register_query()
    def get_empty() -> str: return ""
    app = create_controller_cli(capp.get_controller())
    result = runner.invoke(app, ["get_empty"])
    assert result.exit_code == 0
    # Empty string is not None, so echo is called but prints empty
    assert result.stdout.strip() == ""

# %%
#|export
# --- _make_typer_compatible_func edge cases ---

def test_make_typer_func_no_params():
    def no_params(): return "ok"
    wrapped = _make_typer_compatible_func(no_params)
    assert wrapped() == "ok"

def test_make_typer_func_all_primitives():
    def all_prims(a: int, b: str, c: float, d: bool): return f"{a},{b},{c},{d}"
    wrapped = _make_typer_compatible_func(all_prims)
    # No conversion should happen — signature unchanged
    assert wrapped(1, "x", 2.5, True) == "1,x,2.5,True"

def test_make_typer_func_optional_model():
    class MyModel(BaseModel):
        name: str
    def func(m: Optional[MyModel] = None): return m
    wrapped = _make_typer_compatible_func(func)
    # With None default
    assert wrapped() is None
    # With JSON string
    result = wrapped('{"name": "test"}')
    assert isinstance(result, MyModel)
    assert result.name == "test"

def test_make_typer_func_invalid_json():
    class MyModel(BaseModel):
        name: str
    def func(m: MyModel): pass
    wrapped = _make_typer_compatible_func(func)
    with pytest.raises(Exception):  # Pydantic validation error
        wrapped("not valid json")

# %%
#|export
# --- Async controller method via CLI ---

def test_cli_async_method():
    capp = ControllerApp()
    @capp.register_cmd()
    async def async_cmd(x: int) -> str: return f"result={x}"
    app = create_controller_cli(capp.get_controller())
    result = runner.invoke(app, ["async_cmd", "42"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "result=42"

# %%
#|export
# --- Default parameter ---

def test_cli_method_with_default_param():
    capp = ControllerApp()
    @capp.register_query()
    def greet(name: str = "world") -> str: return f"hello {name}"
    app = create_controller_cli(capp.get_controller())
    # With default
    result = runner.invoke(app, ["greet"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "hello world"
    # With explicit value
    result2 = runner.invoke(app, ["greet", "--name", "alice"])
    assert result2.exit_code == 0
    assert result2.stdout.strip() == "hello alice"

# %%
#|export
# --- Empty controller ---

def test_cli_empty_controller():
    class Empty(Controller): pass
    app = create_controller_cli(Empty())
    result = runner.invoke(app, [])
    assert result.exit_code == 0
