# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_remote_cli_units

# %%
#|default_exp test_remote_cli_units

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
import socket
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.remote_cli import create_remote_controller_cli, is_pickleable
from typer.testing import CliRunner

# %%
#|export
runner = CliRunner()

class FooController(Controller):
    @ctrl_cmd_method
    def bar(self): pass

    @ctrl_query_method
    def baz(self, x: int) -> str: pass

    @ctrl_method(ControllerMethodType.QUERY, "q")
    def qux(self): pass

# %%
#|export
# --- Validation ---

def test_create_remote_cli_non_controller_raises():
    with pytest.raises(TypeError, match="must be a subclass"):
        create_remote_controller_cli(str, url="http://localhost:8000")

def test_create_remote_cli_local_mode_with_url_raises():
    with pytest.raises(ValueError, match="url"):
        create_remote_controller_cli(
            FooController,
            url="http://localhost:8000",
            local_mode=True,
            lockfile_path="/tmp/test.lock",
        )

def test_create_remote_cli_non_local_with_controller_raises():
    with pytest.raises(ValueError, match="controller"):
        create_remote_controller_cli(
            FooController,
            url="http://localhost:8000",
            controller=FooController(),
        )

def test_create_remote_cli_local_mode_no_lockfile_raises():
    with pytest.raises(ValueError, match="lockfile_path"):
        create_remote_controller_cli(
            FooController,
            local_mode=True,
        )

# %%
#|export
# --- is_pickleable ---

def test_is_pickleable_lambda():
    assert is_pickleable(lambda x: x) is False

def test_is_pickleable_function():
    # Module-level (importable) functions are pickleable; locally-defined are not.
    # Use a known module-level function as the test subject.
    import os
    assert is_pickleable(os.getpid) is True

def test_is_pickleable_class_instance():
    assert is_pickleable(FooController()) is True

def test_is_pickleable_socket():
    s = socket.socket()
    try:
        assert is_pickleable(s) is False
    finally:
        s.close()

# %%
#|export
# --- Local mode CLI has lifecycle commands ---

def test_remote_cli_local_mode_has_lifecycle_commands():
    app = create_remote_controller_cli(
        FooController,
        local_mode=True,
        lockfile_path="/tmp/test_lifecycle.lock",
        start_local_server_automatically=False,
    )
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    help_text = result.stdout
    assert "start-local-server" in help_text
    assert "stop-local-server" in help_text
    assert "restart-local-server" in help_text
    assert "get-server-status" in help_text

# %%
#|export
# --- Non-local mode CLI ---

def test_remote_cli_non_local_no_lifecycle_commands():
    app = create_remote_controller_cli(
        FooController,
        url="http://localhost:8000",
    )
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    help_text = result.stdout
    assert "start-local-server" not in help_text
    assert "stop-local-server" not in help_text

def test_remote_cli_has_controller_methods():
    app = create_remote_controller_cli(
        FooController,
        url="http://localhost:8000",
    )
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    help_text = result.stdout
    assert "bar" in help_text
    assert "baz" in help_text
    assert "qux" in help_text

# %%
#|export
# --- No subcommand shows help ---

def test_remote_cli_no_subcommand_shows_help():
    app = create_remote_controller_cli(
        FooController,
        url="http://localhost:8000",
    )
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    # Help text should be shown
    assert "bar" in result.stdout or "Usage" in result.stdout
