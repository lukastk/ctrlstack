# ---
# jupyter:
#   kernelspec:
#     display_name: ctrlstack (3.11.14)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # REST API Servers from Controllers
#
# ctrlstack can turn any Controller into a [FastAPI](https://fastapi.tiangolo.com/)
# server. Query methods become GET endpoints, command methods become POST endpoints.

# %% [markdown]
# ## Basic server creation

# %%
from ctrlstack import Controller, ctrl_cmd_method, ctrl_query_method
from ctrlstack.server import create_controller_server
from fastapi.testclient import TestClient

class CalcController(Controller):
    @ctrl_query_method
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @ctrl_cmd_method
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b

app = create_controller_server(CalcController())
client = TestClient(app)

# %% [markdown]
# Query methods are mapped to GET endpoints, commands to POST.
# Primitive parameters become query parameters:

# %%
# GET /query/add?a=3&b=4
response = client.get("/query/add", params={"a": 3, "b": 4})
print(f"GET /query/add?a=3&b=4 -> {response.json()}")

# POST /cmd/multiply?a=3&b=4
response = client.post("/cmd/multiply", params={"a": 3, "b": 4})
print(f"POST /cmd/multiply?a=3&b=4 -> {response.json()}")

# %% [markdown]
# ## Route structure
#
# By default, routes are `/<group>/<method_name>`:
#
# - `@ctrl_cmd_method` -> group `cmd` -> `POST /cmd/<name>`
# - `@ctrl_query_method` -> group `query` -> `GET /query/<name>`
# - `@ctrl_method(type, "custom")` -> `/<http_method> /custom/<name>`
#
# With `prepend_method_group=False`, routes are just `/<method_name>`:

# %%
app_flat = create_controller_server(CalcController(), prepend_method_group=False)
client_flat = TestClient(app_flat)

response = client_flat.get("/add", params={"a": 10, "b": 20})
print(f"GET /add?a=10&b=20 -> {response.json()}")

# %% [markdown]
# ## Complex body parameters
#
# Pydantic models, dicts, and lists are automatically handled as JSON body parameters
# by FastAPI:

# %%
from pydantic import BaseModel
from typing import List

class Message(BaseModel):
    text: str
    priority: int

class MsgController(Controller):
    @ctrl_cmd_method
    def send(self, recipient: str, body: Message) -> str:
        """Send a message. `recipient` is a query param, `body` is JSON body."""
        return f"Sent to {recipient}: {body.text} (priority={body.priority})"

    @ctrl_cmd_method
    def send_batch(self, messages: List[Message]) -> str:
        """Send multiple messages. The list is the JSON body."""
        return f"Sent {len(messages)} messages"

app2 = create_controller_server(MsgController())
client2 = TestClient(app2)

# %%
# Primitive param -> query string, Pydantic model -> JSON body
response = client2.post(
    "/cmd/send",
    params={"recipient": "alice"},
    json={"text": "Hello!", "priority": 1}
)
print(response.json())

# List of models -> JSON body
response = client2.post(
    "/cmd/send_batch",
    json=[
        {"text": "msg1", "priority": 1},
        {"text": "msg2", "priority": 2},
    ]
)
print(response.json())

# %% [markdown]
# ## API Key authentication
#
# Pass `api_keys` to require an `X-API-Key` header on every request:

# %%
app_auth = create_controller_server(
    CalcController(),
    api_keys=["my-secret-key", "another-key"]
)
client_auth = TestClient(app_auth)

# Without key -> 401
response = client_auth.get("/query/add", params={"a": 1, "b": 2})
print(f"No key: {response.status_code}")

# With valid key -> 200
response = client_auth.get(
    "/query/add",
    params={"a": 1, "b": 2},
    headers={"X-API-Key": "my-secret-key"}
)
print(f"With key: {response.status_code}, result={response.json()}")

# %% [markdown]
# ## Running the server
#
# In production, use uvicorn to run the FastAPI app:
#
# ```python
# import uvicorn
# app = create_controller_server(MyController())
# uvicorn.run(app, host="0.0.0.0", port=8000)
# ```
