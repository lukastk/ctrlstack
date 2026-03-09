# %% [markdown]
# # test_server_with_auth

# %%
#|default_exp test_server_with_auth

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
import json
from pydantic import BaseModel
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.server import create_controller_server
from fastapi.testclient import TestClient

# %%
#|export
class FooMessage(BaseModel):
    body_msg: str

class FooController(Controller):
    @ctrl_cmd_method
    async def bar(self, query_msg: str, body: FooMessage) -> str:
        return f"Message 1: {query_msg}\nMessage 2: {body.body_msg}"

    @ctrl_query_method
    def baz(self, x: int) -> str:
        return f"baz {x}"

    @ctrl_method(ControllerMethodType.QUERY, "q")
    def qux(self):
        return "qux"

api_keys = ["my-secret-key"]
fastapi_app = create_controller_server(FooController(), api_keys=api_keys)
client = TestClient(fastapi_app)

# %%
#|export
def test_wrong_api_key_rejected():
    response = client.post('/cmd/bar', headers={'X-API-Key': 'wrong-key'})
    assert response.status_code == 401

def test_bar_with_valid_key():
    response = client.post('/cmd/bar',
        headers={'X-API-Key': 'my-secret-key'},
        params={'query_msg': 'Hello from the query.'},
        json={'body_msg': 'Hello from the body.'}
    )
    assert response.status_code == 200
    assert response.json() == 'Message 1: Hello from the query.\nMessage 2: Hello from the body.'

def test_baz_with_valid_key():
    response = client.get('/query/baz',
        headers={'X-API-Key': 'my-secret-key'},
        params={'x': 123},
    )
    assert response.status_code == 200
    assert response.json() == 'baz 123'

def test_qux_with_valid_key():
    response = client.get('/q/qux', headers={'X-API-Key': 'my-secret-key'})
    assert response.status_code == 200
    assert response.json() == 'qux'
