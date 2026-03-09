# ---
# jupyter:
#   kernelspec:
#     display_name: ctrlstack
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_remote_cli

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()

# %%
import requests
import subprocess
import time
import json
from _test_server import FooController, FooMessage, BarMessage

# %%
!python _test_remote_cli.py stop-local-server > /dev/null
!python _test_remote_cli.py

# %%
%%capture res
!python _test_remote_cli.py get-server-status

# %%
assert res.stdout.strip() == 'No local server is running.'

# %%
%%capture res
!python _test_remote_cli.py bar

# %%
assert res.stdout.strip() == 'bar'

# %%
%%capture res
!python _test_remote_cli.py baz 123

# %%
assert res.stdout.strip() == 'baz 123'

# %%
%%capture res
!python _test_remote_cli.py qux

# %%
assert res.stdout.strip() == 'qux'

# %%
%%capture res
!python _test_remote_cli.py get-server-status

# %%
assert res.stdout.strip().startswith('Local server is running')

# %%
%%capture res
!python _test_remote_cli.py stop-local-server

# %%
assert res.stdout.strip().startswith('Stopped local server')

# %%
%%capture res
!python _test_remote_cli.py stop-local-server

# %%
assert res.stdout.strip().startswith('No local server running')
