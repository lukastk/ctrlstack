# ---
# jupyter:
#   kernelspec:
#     display_name: ctrlstack
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_server

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()

# %%
import requests
import subprocess
import time
import json

# %% [markdown]
# Start the FastAPI server in the background

# %%
from ctrlstack.server import _find_free_port
port = _find_free_port()
server_process = subprocess.Popen(
    ["fastapi", "dev", "_test_server.py", '--port', str(port)],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
time.sleep(2)

# %%
response = requests.post(f'http://localhost:{port}/cmd/bar',
    params={
        'query_msg' : 'Hello from the query.'
    },
    json={
        'body_msg' : 'Hello from the body.'
    }
)
assert response.status_code == 200
assert json.loads(response.text) == 'Message 1: Hello from the query.\nMessage 2: Hello from the body.'

# %%
response = requests.post(f'http://localhost:{port}/cmd/bar2',
    params={
        'query_msg' : 'Hello from the query.'
    },
    json={
        'body1' : { 'body_msg' : '#1.' },
        'body2' : { 'body_msg' : '#2.' },
        'my_list' : [1, 2, 3],
        'my_tuple' : ('a', 'b')
    }
)
assert response.status_code == 200

# %%
print(json.loads(response.text))

# %%
response = requests.post(f'http://localhost:{port}/cmd/bar2',
    params={
        'query_msg' : 'Hello from the query.'
    },
    json={
        'body1' : { 'body_msg' : '#1.' },
        'body2' : { 'body_msg' : '#2.' },
        'my_list' : [1, 2, 3],
        'my_tuple' : ('a', 'b'),
        'body3' : { 'body_msg' : '#3.' }
    }
)
assert response.status_code == 200

# %%
print(json.loads(response.text))

# %%
response = requests.get(f'http://localhost:{port}/query/baz',
    params={
        'x' : 123,
    },
)
assert response.status_code == 200
assert json.loads(response.text) == 'baz 123'

# %%
response = requests.get(f'http://localhost:{port}/q/qux')
assert response.status_code == 200
assert json.loads(response.text) == 'qux'

# %%
response = requests.get(f'http://localhost:{port}/qux2')
assert response.status_code == 200
assert json.loads(response.text) == 'qux2'

# %% [markdown]
# Stop the FastAPI server

# %%
server_process.terminate()
server_process.wait()
