# ---
# jupyter:
#   kernelspec:
#     display_name: ctrlstack (3.11.14)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Type Marshalling
#
# ctrlstack uses Pydantic v2's `TypeAdapter` for unified type serialization and
# deserialization across all layers (CLI, server, remote controller). This means
# you can use rich Python types in your controller methods and they just work
# everywhere.

# %% [markdown]
# ## How types are routed
#
# When making HTTP requests, ctrlstack classifies each parameter:
#
# | Type | Where it goes | Example |
# |------|--------------|---------|
# | `int`, `float`, `str`, `bool` | URL query param | `?count=5` |
# | `Enum` | URL query param (as `.value`) | `?level=high` |
# | `Optional[primitive]` | URL query param | `?name=alice` |
# | `BaseModel` | JSON body | `{"name": "alice"}` |
# | `List[...]`, `Dict[...]` | JSON body | `[1, 2, 3]` |
# | Everything else | JSON body | (serialized via TypeAdapter) |

# %% [markdown]
# ## Example: using all the types

# %%
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel
from ctrlstack import Controller, ctrl_cmd_method, ctrl_query_method
from ctrlstack.server import create_controller_server
from fastapi.testclient import TestClient

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Address(BaseModel):
    street: str
    city: str

class Person(BaseModel):
    name: str
    age: int
    address: Address  # Nested model

class DemoController(Controller):
    @ctrl_query_method
    def get_priority(self, level: Priority) -> str:
        """Enum as query param."""
        return f"Priority: {level.value}"

    @ctrl_cmd_method
    def create_person(self, person: Person) -> str:
        """Nested Pydantic model as JSON body."""
        return f"Created {person.name} from {person.address.city}"

    @ctrl_cmd_method
    def process_scores(self, scores: Dict[str, int]) -> int:
        """Dict as JSON body."""
        return sum(scores.values())

    @ctrl_cmd_method
    def tag_items(self, ids: List[int], label: str) -> str:
        """List body + string query param."""
        return f"Tagged {len(ids)} items as '{label}'"

    @ctrl_query_method
    def return_model(self, name: str) -> Person:
        """Return a Pydantic model — serialized as JSON automatically."""
        return Person(name=name, age=30, address=Address(street="123 Main", city="NY"))

    @ctrl_query_method
    def return_list(self) -> List[Person]:
        """Return a list of models."""
        return [
            Person(name="Alice", age=30, address=Address(street="1st", city="LA")),
            Person(name="Bob", age=25, address=Address(street="2nd", city="SF")),
        ]

app = create_controller_server(DemoController())
client = TestClient(app)

# %% [markdown]
# ### Enum query parameter

# %%
r = client.get("/query/get_priority", params={"level": "high"})
print(r.json())

# %% [markdown]
# ### Nested model body

# %%
r = client.post("/cmd/create_person", json={
    "name": "Alice",
    "age": 30,
    "address": {"street": "123 Main St", "city": "Portland"}
})
print(r.json())

# %% [markdown]
# ### Dict body

# %%
r = client.post("/cmd/process_scores", json={"math": 95, "science": 87, "english": 92})
print(f"Total: {r.json()}")

# %% [markdown]
# ### Mixed: List body + string query param

# %%
r = client.post("/cmd/tag_items", params={"label": "urgent"}, json=[1, 2, 3, 4, 5])
print(r.json())

# %% [markdown]
# ### Model return values

# %%
r = client.get("/query/return_model", params={"name": "Charlie"})
print(r.json())

r = client.get("/query/return_list")
print(f"Got {len(r.json())} people: {[p['name'] for p in r.json()]}")

# %% [markdown]
# ## CLI type handling
#
# On the CLI, complex types are passed as JSON strings:

# %%
from ctrlstack.cli import create_controller_cli
from typer.testing import CliRunner

runner = CliRunner()
cli_app = create_controller_cli(DemoController())

# Enum — passed as its string value directly
result = runner.invoke(cli_app, ["get_priority", "medium"])
print(result.stdout)

# Pydantic model — passed as JSON string
result = runner.invoke(cli_app, ["create_person", '{"name": "Bob", "age": 25, "address": {"street": "Oak Ave", "city": "SF"}}'])
print(result.stdout)

# Dict — passed as JSON string
result = runner.invoke(cli_app, ["process_scores", '{"math": 100, "art": 85}'])
print(result.stdout)

# %% [markdown]
# ## Remote controller deserialization
#
# When using a remote controller, return values are deserialized back to proper
# Python types. A `Person` returned from the server comes back as a `Person` instance,
# not a raw dict. See `03_remote_controller.pct.py` for a full example.
