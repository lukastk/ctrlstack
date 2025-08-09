from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.server import create_ctrl_server
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple, Optional

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
        return f"Message 1: {query_msg}\nMessage 2: {body1.body_msg}\nMessage 3: {body2.body_msg}\nMy list: {my_list}\nMy tuple: {my_tuple}\nBody3: {body3.body_msg if body3 else 'None'}"
    
    @ctrl_query_method
    def baz(self, x: int) -> str:
        return f"baz {x}"
    
    @ctrl_method(ControllerMethodType.QUERY, "q")
    def qux(self):
        return "qux"
    
app = create_ctrl_server(FooController())