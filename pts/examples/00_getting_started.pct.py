# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Getting Started with ctrlstack
#
# ctrlstack lets you define a `Controller` class once, then automatically generate
# CLI apps, REST APIs, remote client proxies, and remote CLIs from it.
#
# This notebook walks through the core concepts.

# %% [markdown]
# ## Defining a Controller
#
# A `Controller` is a class that groups related operations. You decorate methods
# with `@ctrl_cmd_method` (state-changing) or `@ctrl_query_method` (read-only)
# to declare them as controller methods.

# %%
from ctrlstack import Controller, ctrl_cmd_method, ctrl_query_method

class TodoController(Controller):
    def __init__(self):
        self._todos = []

    @ctrl_cmd_method
    def add(self, text: str) -> str:
        """Add a new todo item."""
        self._todos.append({"text": text, "done": False})
        return f"Added: {text}"

    @ctrl_query_method
    def list_todos(self) -> list:
        """List all todo items."""
        return self._todos

    @ctrl_cmd_method
    def complete(self, index: int) -> str:
        """Mark a todo as complete."""
        self._todos[index]["done"] = True
        return f"Completed: {self._todos[index]['text']}"

# %% [markdown]
# ## Using the Controller directly
#
# You can use the controller as a regular Python object:

# %%
ctrl = TodoController()
print(ctrl.add("Buy groceries"))
print(ctrl.add("Write docs"))
print(ctrl.list_todos())
print(ctrl.complete(0))
print(ctrl.list_todos())

# %% [markdown]
# ## Method types: Commands vs Queries
#
# - **Commands** (`@ctrl_cmd_method`) are state-changing operations. They become
#   POST endpoints on the server and command-group entries in the CLI.
# - **Queries** (`@ctrl_query_method`) are read-only operations. They become
#   GET endpoints and query-group entries.
#
# You can also use the generic `@ctrl_method` decorator to specify a custom group:

# %%
from ctrlstack import ctrl_method, ControllerMethodType

class MyController(Controller):
    @ctrl_method(ControllerMethodType.QUERY, "admin")
    def system_info(self) -> str:
        return "System is healthy"

    @ctrl_method(ControllerMethodType.COMMAND, "admin")
    def reset(self) -> str:
        return "System reset"

# %% [markdown]
# ## Introspection
#
# Controllers provide methods to inspect their registered methods and groups:

# %%
print("All methods:", TodoController.get_controller_methods())
print("Commands only:", TodoController.get_controller_methods(method_type=ControllerMethodType.COMMAND))
print("Queries only:", TodoController.get_controller_methods(method_type=ControllerMethodType.QUERY))
print("Groups:", TodoController.get_controller_method_groups())

# %% [markdown]
# ## What's next?
#
# Now that you have a Controller, you can expose it as:
#
# - A **CLI app** (see `01_cli.pct.py`)
# - A **REST API server** (see `02_server.pct.py`)
# - A **remote controller proxy** (see `03_remote_controller.pct.py`)
# - A **remote CLI** with server lifecycle (see `04_remote_cli.pct.py`)
