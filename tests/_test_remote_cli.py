from ctrlstack import Controller, ControllerMethodType, ctrl_cmd_method, ctrl_query_method, ctrl_method
from ctrlstack.remote_cli import create_remote_controller_cli

class FooController(Controller):
    @ctrl_cmd_method
    async def bar(self):
        return "bar"
    
    @ctrl_query_method
    def baz(self, x: int) -> str:
        return f"baz {x}"
    
    @ctrl_method(ControllerMethodType.QUERY, "q")
    def qux(self):
        return "qux"
    
app = create_remote_controller_cli(
    FooController,
    local_mode=True,
    lockfile_path="/tmp/ctrlstack.lock",
)

if __name__ == "__main__":
    app()
