# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_remote_controller

# %%
#|default_exp test_remote_controller

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
import asyncio
import threading
import time
import uvicorn
from enum import Enum
from pydantic import BaseModel
from typing import List, Tuple, Optional, Dict
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.server import create_controller_server, _find_free_port
from ctrlstack.remote_controller import create_remote_controller

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
    def return_list_of_models(self) -> List[FooMessage]:
        return [FooMessage(body_msg="a"), FooMessage(body_msg="b")]

    @ctrl_query_method
    def return_falsy_int(self) -> int:
        return 0

    @ctrl_query_method
    def return_falsy_string(self) -> str:
        return ""

    @ctrl_query_method
    def return_falsy_list(self) -> List[int]:
        return []

    @ctrl_query_method
    def return_false(self) -> bool:
        return False

    @ctrl_cmd_method
    def accept_dict(self, data: Dict[str, int]) -> str:
        return f"sum={sum(data.values())}"

# %%
#|export
@pytest.fixture(scope="module")
def server_port():
    """Start a uvicorn server in a background thread and yield the port."""
    port = _find_free_port()
    app = create_controller_server(FooController())
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)
    yield port
    server.should_exit = True
    thread.join(timeout=5)

@pytest.fixture(scope="module")
def remote_ctrl(server_port):
    return create_remote_controller(FooController, url=f"http://localhost:{server_port}")

# %%
#|export
def test_bar(remote_ctrl):
    res = asyncio.run(remote_ctrl.bar(
        query_msg="Hello, World!",
        body=FooMessage(body_msg='This is a body message')
    ))
    assert res == 'Message 1: Hello, World!\nMessage 2: This is a body message'

def test_bar2_without_optional(remote_ctrl):
    res = asyncio.run(remote_ctrl.bar2(
        query_msg='Hello from the query.',
        body1=FooMessage(body_msg='#1.'),
        body2=BarMessage(body_msg='#2.'),
        my_list=[1, 2, 3],
        my_tuple=('a', 'b'),
    ))
    assert "Body3: None" in res

def test_bar2_with_optional(remote_ctrl):
    res = asyncio.run(remote_ctrl.bar2(
        query_msg='Hello from the query.',
        body1=FooMessage(body_msg='#1.'),
        body2=BarMessage(body_msg='#2.'),
        my_list=[1, 2, 3],
        my_tuple=('a', 'b'),
        body3=BarMessage(body_msg="#3."),
    ))
    assert "Body3: #3." in res

def test_baz(remote_ctrl):
    res = asyncio.run(remote_ctrl.baz(x=123))
    assert res == 'baz 123'

def test_qux(remote_ctrl):
    res = asyncio.run(remote_ctrl.qux())
    assert res == 'qux'

def test_echo_enum(remote_ctrl):
    res = asyncio.run(remote_ctrl.echo_enum(priority=Priority.HIGH))
    assert res == 'priority=high'

def test_nested_body(remote_ctrl):
    body = NestedBody(msg=FooMessage(body_msg="hello"), tag="t1")
    res = asyncio.run(remote_ctrl.nested_body(body=body))
    assert res == 'msg=hello, tag=t1'

def test_return_model(remote_ctrl):
    res = asyncio.run(remote_ctrl.return_model(name="test"))
    assert isinstance(res, FooMessage)
    assert res.body_msg == "test"

def test_return_list_of_models(remote_ctrl):
    res = asyncio.run(remote_ctrl.return_list_of_models())
    assert isinstance(res, list)
    assert len(res) == 2
    assert all(isinstance(m, FooMessage) for m in res)

def test_return_falsy_int(remote_ctrl):
    res = asyncio.run(remote_ctrl.return_falsy_int())
    assert res == 0

def test_return_falsy_string(remote_ctrl):
    res = asyncio.run(remote_ctrl.return_falsy_string())
    assert res == ""

def test_return_falsy_list(remote_ctrl):
    res = asyncio.run(remote_ctrl.return_falsy_list())
    assert res == []

def test_return_false(remote_ctrl):
    res = asyncio.run(remote_ctrl.return_false())
    assert res is False

def test_accept_dict(remote_ctrl):
    res = asyncio.run(remote_ctrl.accept_dict(data={"a": 1, "b": 2}))
    assert res == 'sum=3'
