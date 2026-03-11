# ---
# jupyter:
#   kernelspec:
#     display_name: ctrlstack (3.11.14)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Remote CLI
#
# A remote CLI combines a remote controller with a Typer CLI app. In **local mode**,
# it also manages the server lifecycle automatically — starting, stopping, and
# restarting a local server process.

# %% [markdown]
# ## Non-local mode (connecting to an existing server)
#
# When you already have a server running, create a remote CLI that connects to it:

# %%
from ctrlstack import Controller, ctrl_cmd_method, ctrl_query_method
from ctrlstack.remote_cli import create_remote_controller_cli
from typer.testing import CliRunner

runner = CliRunner()

class MyController(Controller):
    @ctrl_cmd_method
    def deploy(self, env: str) -> str:
        return f"Deployed to {env}"

    @ctrl_query_method
    def status(self) -> str:
        return "All systems go"

# Connect to an existing server
app = create_remote_controller_cli(
    MyController,
    url="http://localhost:8000",
)

# The CLI has all controller methods as commands
result = runner.invoke(app, ["--help"])
print(result.stdout)

# %% [markdown]
# ## Local mode (managed server lifecycle)
#
# In local mode, the CLI manages a local server for you. It adds lifecycle commands:
#
# - `start-local-server` — start the server in the background
# - `stop-local-server` — stop the running server
# - `restart-local-server` — restart the server
# - `get-server-status` — check if the server is running
#
# The server state is tracked via a lockfile.

# %%
app_local = create_remote_controller_cli(
    MyController,
    local_mode=True,
    lockfile_path="/tmp/ctrlstack_example.lock",
    start_local_server_automatically=False,  # Don't auto-start for this demo
)

# Lifecycle commands are available
result = runner.invoke(app_local, ["--help"])
print(result.stdout)

# %% [markdown]
# ## Auto-start behavior
#
# With `start_local_server_automatically=True` (the default in local mode), the CLI
# will automatically start the server before executing any command if it's not already
# running. This makes the CLI feel like a local tool while actually running a server
# behind the scenes.
#
# ```python
# app = create_remote_controller_cli(
#     MyController,
#     local_mode=True,
#     lockfile_path="/tmp/my_app.lock",
#     start_local_server_automatically=True,   # default
#     local_server_start_timeout=10.0,          # wait up to 10s for server
# )
# ```
#
# ## Typical usage pattern
#
# Define your controller, then create a CLI entry point in your `pyproject.toml`:
#
# ```python
# # my_app/cli.py
# from my_app.controller import MyController
# from ctrlstack.remote_cli import create_remote_controller_cli
#
# app = create_remote_controller_cli(
#     MyController,
#     local_mode=True,
#     lockfile_path="~/.my_app/server.lock",
# )
# ```
#
# ```toml
# # pyproject.toml
# [project.scripts]
# my-app = "my_app.cli:app"
# ```
