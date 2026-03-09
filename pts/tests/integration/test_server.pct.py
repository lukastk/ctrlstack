# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_server

# %%
#|default_exp test_server

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
import json
from enum import Enum
from pydantic import BaseModel
from typing import List, Tuple, Optional, Dict
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.server import create_controller_server
from fastapi.testclient import TestClient

# %%
#|export
class Priority(Enum):
    LOW = "low"
    HIGH = "high"

class FooMessage(BaseModel):
    body_msg: str

class BarMessage(BaseModel):
    body_msg: str

class NestedBody(BaseModel):
    msg: FooMessage
    tag: str

class FooController(Controller):
    @ctrl_cmd_method
    async def bar(self, query_msg: str, body: FooMessage) -> str:
        return f"Message 1: {query_msg}\nMessage 2: {body.body_msg}"

    @ctrl_cmd_method
    async def bar2(
        self,
        query_msg: str,
        body1: FooMessage,
        body2: BarMessage,
        my_list: List[int],
        my_tuple: Tuple[str, str],
        body3: Optional[BarMessage] = None
    ) -> str:
        return (
            f"Message 1: {query_msg}\nMessage 2: {body1.body_msg}\n"
            f"Message 3: {body2.body_msg}\nMy list: {my_list}\n"
            f"My tuple: {my_tuple}\nBody3: {body3.body_msg if body3 else 'None'}"
        )

    @ctrl_query_method
    def baz(self, x: int) -> str:
        return f"baz {x}"

    @ctrl_method(ControllerMethodType.QUERY, "q")
    def qux(self):
        return "qux"

    @ctrl_method(ControllerMethodType.QUERY, "")
    def qux2(self):
        return "qux2"

    @ctrl_query_method
    def echo_enum(self, priority: Priority) -> str:
        return f"priority={priority.value}"

    @ctrl_cmd_method
    def nested_body(self, body: NestedBody) -> str:
        return f"msg={body.msg.body_msg}, tag={body.tag}"

    @ctrl_query_method
    def return_model(self, name: str) -> FooMessage:
        return FooMessage(body_msg=name)

    @ctrl_query_method
    def return_falsy_int(self) -> int:
        return 0

    @ctrl_query_method
    def return_false(self) -> bool:
        return False

fastapi_app = create_controller_server(FooController())
client = TestClient(fastapi_app)

# %%
#|export
def test_bar():
    response = client.post('/cmd/bar',
        params={'query_msg': 'Hello from the query.'},
        json={'body_msg': 'Hello from the body.'}
    )
    assert response.status_code == 200
    assert response.json() == 'Message 1: Hello from the query.\nMessage 2: Hello from the body.'

def test_bar2_without_optional():
    response = client.post('/cmd/bar2',
        params={'query_msg': 'Hello from the query.'},
        json={
            'body1': {'body_msg': '#1.'},
            'body2': {'body_msg': '#2.'},
            'my_list': [1, 2, 3],
            'my_tuple': ('a', 'b'),
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert 'Body3: None' in data

def test_bar2_with_optional():
    response = client.post('/cmd/bar2',
        params={'query_msg': 'Hello from the query.'},
        json={
            'body1': {'body_msg': '#1.'},
            'body2': {'body_msg': '#2.'},
            'my_list': [1, 2, 3],
            'my_tuple': ('a', 'b'),
            'body3': {'body_msg': '#3.'},
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert 'Body3: #3.' in data

def test_baz():
    response = client.get('/query/baz', params={'x': 123})
    assert response.status_code == 200
    assert response.json() == 'baz 123'

def test_qux():
    response = client.get('/q/qux')
    assert response.status_code == 200
    assert response.json() == 'qux'

def test_qux2():
    response = client.get('/qux2')
    assert response.status_code == 200
    assert response.json() == 'qux2'

def test_echo_enum():
    response = client.get('/query/echo_enum', params={'priority': 'high'})
    assert response.status_code == 200
    assert response.json() == 'priority=high'

def test_nested_body():
    response = client.post('/cmd/nested_body',
        json={'msg': {'body_msg': 'hello'}, 'tag': 't1'}
    )
    assert response.status_code == 200
    assert response.json() == 'msg=hello, tag=t1'

def test_return_model():
    response = client.get('/query/return_model', params={'name': 'test'})
    assert response.status_code == 200
    assert response.json() == {'body_msg': 'test'}

def test_return_falsy_int():
    response = client.get('/query/return_falsy_int')
    assert response.status_code == 200
    assert response.json() == 0

def test_return_false():
    response = client.get('/query/return_false')
    assert response.status_code == 200
    assert response.json() is False
