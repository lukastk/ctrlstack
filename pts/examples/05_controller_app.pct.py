# ---
# jupyter:
#   kernelspec:
#     display_name: ctrlstack (3.11.14)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # ControllerApp: Functional-Style Registration
#
# `ControllerApp` provides a decorator-based API for building controllers without
# defining a class. This is useful for small apps where a class hierarchy feels
# like overkill.

# %% [markdown]
# ## Basic usage
#
# Create a `ControllerApp`, then register functions as commands or queries:

# %%
from ctrlstack.controller_app import ControllerApp
from ctrlstack.cli import create_controller_cli
from typer.testing import CliRunner

runner = CliRunner()
capp = ControllerApp()

@capp.register_cmd()
def greet(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

@capp.register_query()
def version() -> str:
    """Get the app version."""
    return "2.0.0"

# %%
# Use the controller directly
ctrl = capp.get_controller()
print(ctrl.greet("World"))
print(ctrl.version())

# %%
# Or create a CLI from it
app = create_controller_cli(ctrl)

result = runner.invoke(app, ["greet", "Alice"])
print(result.stdout)

result = runner.invoke(app, ["version"])
print(result.stdout)

# %% [markdown]
# ## Custom command names
#
# By default, the function name becomes the command name. You can override it:

# %%
capp2 = ControllerApp()

@capp2.register_cmd(name="say-hello")
def hello_func(name: str) -> str:
    return f"Hi, {name}!"

print(capp2.controller_cls.get_controller_methods())

# %% [markdown]
# ## Custom groups with `register()`
#
# For full control, use `register()` with an explicit method type and group:

# %%
from ctrlstack import ControllerMethodType

capp3 = ControllerApp()

@capp3.register(ControllerMethodType.QUERY, group="system")
def health_check() -> str:
    return "healthy"

@capp3.register(ControllerMethodType.COMMAND, group="system")
def restart() -> str:
    return "restarting..."

print("Methods:", capp3.controller_cls.get_controller_methods())
print("Groups:", capp3.controller_cls.get_controller_method_groups())

# %% [markdown]
# ## Async functions
#
# Async functions work seamlessly — the CLI layer handles `asyncio.run()` for you:

# %%
import asyncio

capp4 = ControllerApp()

@capp4.register_cmd()
async def fetch_data(url: str) -> str:
    # Simulate async work
    await asyncio.sleep(0.01)
    return f"Fetched data from {url}"

ctrl4 = capp4.get_controller()
result = await ctrl4.fetch_data("https://example.com")
print(result)

# Works through CLI too
app4 = create_controller_cli(ctrl4)
result = runner.invoke(app4, ["fetch_data", "https://example.com"])
print(result.stdout)

# %% [markdown]
# ## Composability
#
# The decorated functions remain unchanged — you can still call them directly.
# `ControllerApp` adds them to a controller *without modifying the originals*:

# %%
capp5 = ControllerApp()

@capp5.register_cmd()
def add(a: int, b: int) -> int:
    return a + b

# The function is still a normal function
assert add(2, 3) == 5

# And it's also registered on the controller
ctrl5 = capp5.get_controller()
assert ctrl5.add(2, 3) == 5
