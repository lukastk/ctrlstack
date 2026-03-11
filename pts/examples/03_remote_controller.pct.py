# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Remote Controller
#
# A remote controller is a proxy object that has the same interface as the original
# Controller, but each method call is forwarded as an HTTP request to a running server.
#
# This lets you call remote server methods as if they were local Python methods.

# %% [markdown]
# ## Setup: start a server in the background

# %%
import threading, time, uvicorn
from ctrlstack import Controller, ctrl_cmd_method, ctrl_query_method
from ctrlstack.server import create_controller_server, _find_free_port
from ctrlstack.remote_controller import create_remote_controller
from pydantic import BaseModel
from typing import List
from enum import Enum
import asyncio

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Task(BaseModel):
    title: str
    priority: Priority

class TaskController(Controller):
    def __init__(self):
        self._tasks: List[Task] = []

    @ctrl_cmd_method
    def add_task(self, task: Task) -> str:
        self._tasks.append(task)
        return f"Added: {task.title}"

    @ctrl_query_method
    def get_tasks(self) -> List[Task]:
        return self._tasks

    @ctrl_query_method
    def count(self) -> int:
        return len(self._tasks)

# Start a server in a background thread
port = _find_free_port()
server_app = create_controller_server(TaskController())
config = uvicorn.Config(server_app, host="127.0.0.1", port=port, log_level="error")
server = uvicorn.Server(config)
thread = threading.Thread(target=server.run, daemon=True)
thread.start()
for _ in range(50):
    if server.started: break
    time.sleep(0.1)
print(f"Server running on port {port}")

# %% [markdown]
# ## Creating a remote controller
#
# `create_remote_controller` takes the Controller *class* (not instance) and a URL.
# It dynamically creates a proxy with the same method signatures:

# %%
remote = create_remote_controller(TaskController, url=f"http://localhost:{port}")
print(type(remote))

# %% [markdown]
# ## Calling remote methods
#
# Remote methods are async. They serialize arguments, send HTTP requests, and
# deserialize responses — including Pydantic models:

# %%
# Add tasks (command -> POST)
result = asyncio.run(remote.add_task(task=Task(title="Write docs", priority=Priority.HIGH)))
print(result)

result = asyncio.run(remote.add_task(task=Task(title="Fix bug", priority=Priority.LOW)))
print(result)

# Query tasks (query -> GET) — returns deserialized Task models
tasks = asyncio.run(remote.get_tasks())
print(f"\nTasks: {tasks}")
print(f"Type: {type(tasks[0])}")  # Task, not dict!

# Falsy values are returned correctly (not swallowed)
count = asyncio.run(remote.count())
print(f"\nCount: {count}")

# %% [markdown]
# ## Key features
#
# - **Pydantic models** are serialized to JSON and deserialized back automatically
# - **Enum values** are passed as query parameters using their `.value`
# - **Return types** are deserialized to proper Python objects (models, lists, etc.)
# - **Falsy values** (`0`, `""`, `[]`, `False`) are returned correctly

# %%
# Clean up
server.should_exit = True
thread.join(timeout=5)
