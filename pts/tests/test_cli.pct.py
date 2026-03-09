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
import subprocess
import time
import json

# %%
res = subprocess.run(["python", "_test_cli.py"])

# %%
!python _test_cli.py bar

# %%
res = subprocess.run(["python", "_test_cli.py", "bar"], capture_output=True, text=True)
assert res.stdout.strip() == 'bar'

# %%
!python _test_cli.py bar2 '{"name": "test", "value": 42}' '{"key": "value"}' 123

# %%
res = subprocess.run(["python", "_test_cli.py", "bar2", '{"name": "test", "value": 42}', '{"key": "value"}', "123"], capture_output=True, text=True)
assert res.stdout == "arg1: {'name': 'test', 'value': 42}\narg2: {'key': 'value'}\narg3: 123\n"

# %%
!python _test_cli.py baz 123

# %%
res = subprocess.run(["python", "_test_cli.py", "baz", "123"], capture_output=True, text=True)
assert res.stdout.strip() == 'baz 123'

# %%
!python _test_cli.py qux

# %%
res = subprocess.run(["python", "_test_cli.py", "qux"], capture_output=True, text=True)
assert res.stdout.strip() == 'qux'
