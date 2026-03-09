# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # test_server_internals

# %%
#|default_exp test_server_internals

# %%
#|hide
import nblite; nblite.nbl_export()

# %%
#|export
import pytest
import os
import socket
from contextlib import closing
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.server import (
    create_controller_server,
    _construct_route,
    _is_port_free,
    _find_free_port,
    _pid_exists,
    _read_lockfile,
    _write_lockfile,
    _delete_lockfile,
    check_local_controller_server_process,
    stop_local_controller_server_process,
)

# %%
#|export
# --- _construct_route ---

def _make_method_with_attrs(group, method_type, name="test_method"):
    def func(): pass
    func.__name__ = name
    func._controller_method_group = group
    func._controller_method_type = method_type
    return func

def test_construct_route_with_group():
    m = _make_method_with_attrs("cmd", ControllerMethodType.COMMAND)
    assert _construct_route(m, "do_thing", prepend_method_group=True) == "/cmd/do_thing"

def test_construct_route_empty_group():
    m = _make_method_with_attrs("", ControllerMethodType.QUERY)
    assert _construct_route(m, "info", prepend_method_group=True) == "/info"

def test_construct_route_no_prepend():
    m = _make_method_with_attrs("cmd", ControllerMethodType.COMMAND)
    assert _construct_route(m, "do_thing", prepend_method_group=False) == "/do_thing"

def test_construct_route_custom_name():
    m = _make_method_with_attrs("grp", ControllerMethodType.COMMAND, name="original")
    assert _construct_route(m, "custom_name", prepend_method_group=True) == "/grp/custom_name"

def test_construct_route_default_name():
    m = _make_method_with_attrs("grp", ControllerMethodType.COMMAND, name="auto_name")
    assert _construct_route(m, prepend_method_group=True) == "/grp/auto_name"

# %%
#|export
# --- _is_port_free / _find_free_port ---

def test_is_port_free_unused():
    port = _find_free_port()
    assert _is_port_free(port) is True

def test_is_port_free_used():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.listen(1)
        assert _is_port_free(port) is False

def test_find_free_port_returns_int():
    port = _find_free_port()
    assert isinstance(port, int)
    assert port > 0

def test_find_free_port_is_free():
    port = _find_free_port()
    assert _is_port_free(port)

# %%
#|export
# --- _pid_exists ---

def test_pid_exists_own_pid():
    assert _pid_exists(os.getpid()) is True

def test_pid_exists_nonexistent():
    # Spawn a process and wait for it to finish, then check its PID
    import subprocess
    proc = subprocess.Popen(["true"])
    proc.wait()
    assert _pid_exists(proc.pid) is False

# %%
#|export
# --- lockfile helpers ---

def test_write_then_read_lockfile(tmp_path):
    path = str(tmp_path / "test.lock")
    _write_lockfile(path, 8080, 12345)
    result = _read_lockfile(path)
    assert result == (8080, 12345)

def test_read_lockfile_nonexistent(tmp_path):
    path = str(tmp_path / "nonexistent.lock")
    assert _read_lockfile(path) is None

def test_read_lockfile_invalid_format(tmp_path):
    path = str(tmp_path / "bad.lock")
    with open(path, "w") as f:
        f.write("only_one_line\n")
    with pytest.raises(ValueError, match="Invalid lockfile format"):
        _read_lockfile(path)

def test_delete_lockfile_exists(tmp_path):
    path = str(tmp_path / "del.lock")
    _write_lockfile(path, 8080, 12345)
    _delete_lockfile(path)
    assert not os.path.exists(path)

def test_delete_lockfile_nonexistent(tmp_path):
    path = str(tmp_path / "nope.lock")
    _delete_lockfile(path)  # Should not raise

# %%
#|export
# --- create_controller_server validation ---

def test_create_server_non_controller_raises():
    with pytest.raises(TypeError, match="must be an instance"):
        create_controller_server("not a controller")

def test_create_server_empty_controller():
    class Empty(Controller): pass
    app = create_controller_server(Empty())
    assert app is not None
    # Only FastAPI's built-in routes (openapi, docs, redoc) — no user-defined routes
    user_routes = [r for r in app.routes if hasattr(r, 'methods') and r.path not in (
        '/openapi.json', '/docs', '/docs/oauth2-redirect', '/redoc'
    )]
    assert len(user_routes) == 0

def test_create_server_prepend_false():
    class MyCtrl(Controller):
        @ctrl_cmd_method
        def do_thing(self): return "done"
    app = create_controller_server(MyCtrl(), prepend_method_group=False)
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.post('/do_thing')
    assert response.status_code == 200
    assert response.json() == "done"

def test_create_server_multiple_api_keys():
    class MyCtrl(Controller):
        @ctrl_query_method
        def info(self): return "secret"
    app = create_controller_server(MyCtrl(), api_keys=["key1", "key2"])
    from fastapi.testclient import TestClient
    client = TestClient(app)
    # key1 works
    r1 = client.get('/query/info', headers={"X-API-Key": "key1"})
    assert r1.status_code == 200
    # key2 works
    r2 = client.get('/query/info', headers={"X-API-Key": "key2"})
    assert r2.status_code == 200
    # wrong key rejected
    r3 = client.get('/query/info', headers={"X-API-Key": "bad"})
    assert r3.status_code == 401

# %%
#|export
# --- check/stop server with no lockfile ---

def test_check_server_no_lockfile(tmp_path):
    path = str(tmp_path / "nope.lock")
    port, pid, running = check_local_controller_server_process(path)
    assert (port, pid, running) == (None, None, False)

def test_stop_server_no_lockfile(tmp_path):
    path = str(tmp_path / "nope.lock")
    port, pid, existed = stop_local_controller_server_process(path)
    assert (port, pid, existed) == (None, None, False)

def test_check_server_stale_lockfile(tmp_path):
    path = str(tmp_path / "stale.lock")
    _write_lockfile(path, 9999, 99999)  # PID that doesn't exist
    port, pid, running = check_local_controller_server_process(path)
    assert (port, pid, running) == (None, None, False)
    assert not os.path.exists(path)  # Stale lockfile deleted

def test_stop_server_dead_pid(tmp_path):
    path = str(tmp_path / "dead.lock")
    _write_lockfile(path, 9999, 99999)
    port, pid, existed = stop_local_controller_server_process(path)
    assert (port, pid, existed) == (None, None, False)
    assert not os.path.exists(path)

# %%
#|export
# --- Server auth edge case ---

def test_server_auth_no_header():
    class MyCtrl(Controller):
        @ctrl_query_method
        def info(self): return "data"
    app = create_controller_server(MyCtrl(), api_keys=["secret"])
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get('/query/info')
    assert response.status_code == 401
