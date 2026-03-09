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
from pydantic import BaseModel
from typing import List, Tuple, Optional
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.server import create_controller_server, _find_free_port
from ctrlstack.remote_controller import create_remote_controller

# %%
#|export
class FooMessage(BaseModel):
    body_msg: str

class BarMessage(BaseModel):
    body_msg: str

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
