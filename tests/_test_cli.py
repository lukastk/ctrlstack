from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.cli import create_ctrl_cli

class FooController(Controller):
    @ctrl_cmd_method
    async def bar(self):
        print("bar")
    
    @ctrl_query_method
    def baz(self, x: int) -> str:
        return f"baz {x}"
    
    @ctrl_method(ControllerMethodType.QUERY, "q")
    def qux(self):
        return "qux"
    
app = create_ctrl_cli(FooController())

if __name__ == "__main__":
    app()