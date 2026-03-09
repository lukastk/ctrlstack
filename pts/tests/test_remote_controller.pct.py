# ---
# jupyter:
#   kernelspec:
#     display_name: ctrlstack
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_remote_controller

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()

# %%
import requests
import subprocess
import time
import json
from ctrlstack.remote_controller import create_remote_controller
from _test_server import FooController, FooMessage, BarMessage

# %% [markdown]
# Start the FastAPI server in the background

# %%
port = 8765
server_process = subprocess.Popen(
    ["fastapi", "dev", "_test_server.py", '--port', str(port)],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
time.sleep(2)
remote_ctrl = create_remote_controller(FooController, url=f"http://localhost:{port}")

# %%
res = await remote_ctrl.bar(query_msg="Hello, World!", body=FooMessage(**{'body_msg': 'This is a body message'}))
assert res == 'Message 1: Hello, World!\nMessage 2: This is a body message'

# %%
res = await remote_ctrl.bar2(
    query_msg = 'Hello from the query.',
    body1 = FooMessage(body_msg='#1.'),
    body2 = BarMessage(body_msg='#2.'),
    my_list = [1,2,3],
    my_tuple = ('a','b'),
)
assert res == "Message 1: Hello from the query.\nMessage 2: #1.\nMessage 3: #2.\nMy list: [1, 2, 3]\nMy tuple: ('a', 'b')\nBody3: None"

# %%
res = await remote_ctrl.bar2(
    query_msg = 'Hello from the query.',
    body1 = FooMessage(body_msg='#1.'),
    body2 = BarMessage(body_msg='#2.'),
    my_list = [1,2,3],
    my_tuple = ('a','b'),
    body3 = BarMessage(body_msg="#3."),
)
assert res == "Message 1: Hello from the query.\nMessage 2: #1.\nMessage 3: #2.\nMy list: [1, 2, 3]\nMy tuple: ('a', 'b')\nBody3: #3."

# %%
res = await remote_ctrl.baz(
    x = 123
)
assert res == 'baz 123'

# %%
res = await remote_ctrl.qux()
assert res == 'qux'

# %% [markdown]
# Stop the FastAPI server

# %%
server_process.terminate()
server_process.wait()
