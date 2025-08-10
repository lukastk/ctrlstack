from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.server import create_controller_server
from pydantic import BaseModel

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
    
api_keys = [
    "my-secret-key"
]
    
app = create_controller_server(FooController(), api_keys=api_keys)