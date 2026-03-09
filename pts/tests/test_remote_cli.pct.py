# %% [markdown]
# # test_remote_cli

# %%
#|default_exp test_remote_cli

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
import subprocess
import sys
import textwrap
from ctrlstack.server import stop_local_controller_server_process

# %%
#|export
_REMOTE_CLI_SCRIPT = textwrap.dedent('''\
    from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
    from ctrlstack.remote_cli import create_remote_controller_cli

    class FooController(Controller):
        @ctrl_cmd_method
        async def bar(self):
            return "bar"

        @ctrl_query_method
        def baz(self, x: int) -> str:
            return f"baz {{x}}"

        @ctrl_method(ControllerMethodType.QUERY, "q")
        def qux(self):
            return "qux"

    app = create_remote_controller_cli(
        FooController,
        local_mode=True,
        lockfile_path="{lockfile_path}",
    )

    if __name__ == "__main__":
        app()
''')

# %%
#|export
@pytest.fixture()
def remote_cli(tmp_path):
    """Create a temporary remote CLI script and lockfile, with cleanup."""
    lockfile = tmp_path / "ctrlstack_test.lock"
    script = tmp_path / "remote_cli.py"
    script.write_text(_REMOTE_CLI_SCRIPT.format(lockfile_path=str(lockfile)))
    yield str(script), str(lockfile)
    # Cleanup: stop server if running
    stop_local_controller_server_process(str(lockfile))

def _run_cli(script_path: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, script_path] + list(args),
        capture_output=True, text=True, timeout=30,
    )

# %%
#|export
def test_no_server_initially(remote_cli):
    script, lockfile = remote_cli
    res = _run_cli(script, "get-server-status")
    assert res.stdout.strip() == "No local server is running."

def test_server_lifecycle(remote_cli):
    script, lockfile = remote_cli

    # Auto-start via a command
    res = _run_cli(script, "bar")
    assert res.stdout.strip() == "bar"

    # Server should now be running
    res = _run_cli(script, "get-server-status")
    assert res.stdout.strip().startswith("Local server is running")

    # Other commands should work
    res = _run_cli(script, "baz", "123")
    assert res.stdout.strip() == "baz 123"

    res = _run_cli(script, "qux")
    assert res.stdout.strip() == "qux"

    # Stop the server
    res = _run_cli(script, "stop-local-server")
    assert res.stdout.strip().startswith("Stopped local server")

    # Stopping again should say no server
    res = _run_cli(script, "stop-local-server")
    assert res.stdout.strip().startswith("No local server running")
