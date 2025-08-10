from pydantic import BaseModel
from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.cli import create_controller_cli

from ctrlstack.controller_app import ControllerApp

capp = ControllerApp()

@capp.register_cmd()
async def bar():
    print("bar")
    
class MyModel(BaseModel):
    name: str
    value: int
    
@capp.register_cmd()
def bar2(arg1: MyModel, arg2: dict, arg3: int):
    print("arg1:", arg1.model_dump())
    print("arg2:", arg2)
    print("arg3:", arg3)

@capp.register_query()
def baz(x: int) -> str:
    return f"baz {x}"

@capp.register_query()
def qux():
    return "qux"

app = create_controller_cli(capp.get_controller())

if __name__ == "__main__":
    app()