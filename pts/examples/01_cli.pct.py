# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # CLI Apps from Controllers
#
# ctrlstack can turn any Controller into a [Typer](https://typer.tiangolo.com/) CLI app.
# Each controller method becomes a CLI command, with arguments automatically mapped
# from the method signature.

# %% [markdown]
# ## Basic CLI creation

# %%
from ctrlstack import Controller, ctrl_cmd_method, ctrl_query_method
from ctrlstack.cli import create_controller_cli
from typer.testing import CliRunner

runner = CliRunner()

class GreetController(Controller):
    @ctrl_cmd_method
    def hello(self, name: str, greeting: str = "Hello") -> str:
        """Greet someone."""
        return f"{greeting}, {name}!"

    @ctrl_query_method
    def version(self) -> str:
        """Show the version."""
        return "1.0.0"

app = create_controller_cli(GreetController())

# %% [markdown]
# Each method becomes a CLI command. Parameters become CLI arguments or options:

# %%
result = runner.invoke(app, ["hello", "World"])
print(result.stdout)

result = runner.invoke(app, ["hello", "Alice", "--greeting", "Hi"])
print(result.stdout)

result = runner.invoke(app, ["version"])
print(result.stdout)

# %% [markdown]
# ## Complex argument types
#
# Primitive types (`int`, `str`, `float`, `bool`) are handled natively by Typer.
# Complex types like Pydantic models, `List`, and `Dict` are automatically accepted
# as JSON strings on the CLI and deserialized:

# %%
from pydantic import BaseModel
from typing import List, Dict

class Config(BaseModel):
    name: str
    debug: bool

class ToolController(Controller):
    @ctrl_cmd_method
    def configure(self, config: Config) -> str:
        """Apply a configuration."""
        return f"Configured: {config.name} (debug={config.debug})"

    @ctrl_cmd_method
    def process_items(self, items: List[int]) -> str:
        """Process a list of items."""
        return f"Sum: {sum(items)}"

    @ctrl_cmd_method
    def set_env(self, env: Dict[str, str]) -> str:
        """Set environment variables."""
        return f"Set {len(env)} variables"

app2 = create_controller_cli(ToolController())

# %%
# Pydantic model as JSON string
result = runner.invoke(app2, ["configure", '{"name": "prod", "debug": false}'])
print(result.stdout)

# List as JSON string
result = runner.invoke(app2, ["process_items", '[1, 2, 3, 4, 5]'])
print(result.stdout)

# Dict as JSON string
result = runner.invoke(app2, ["set_env", '{"HOST": "0.0.0.0", "PORT": "8080"}'])
print(result.stdout)

# %% [markdown]
# ## Enum arguments
#
# Enums are handled natively by Typer — pass the enum value as a string:

# %%
from enum import Enum

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"

class LogController(Controller):
    @ctrl_query_method
    def get_level(self, level: LogLevel) -> str:
        return f"Log level: {level.value}"

app3 = create_controller_cli(LogController())

result = runner.invoke(app3, ["get_level", "debug"])
print(result.stdout)

# %% [markdown]
# ## Command grouping with `prepend_method_group`
#
# By default, command names match the method name. With `prepend_method_group=True`,
# the method's group is prepended to the command name:

# %%
from ctrlstack import ctrl_method, ControllerMethodType

class GroupedController(Controller):
    @ctrl_cmd_method
    def deploy(self) -> str: return "Deployed"

    @ctrl_method(ControllerMethodType.QUERY, "admin")
    def status(self) -> str: return "OK"

app_grouped = create_controller_cli(GroupedController(), prepend_method_group=True)

result = runner.invoke(app_grouped, ["cmd-deploy"])
print(result.stdout)

result = runner.invoke(app_grouped, ["admin-status"])
print(result.stdout)
