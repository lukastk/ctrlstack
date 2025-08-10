# ctrlstack

> A Python framework for creating unified controller interfaces that can be exposed as both CLI applications and FastAPI web services.

<!-- #region -->
Define your business logic once in a Controller class, and automatically generate both command-line tools and REST APIs from the same codebase.

## Features

- **Single Source of Truth**: Define methods once, get CLI and API automatically
- **Type Safety**: Full Pydantic integration for request/response validation
- **Async Support**: Native async/await support for both CLI and web endpoints
- **Flexible Routing**: Organize methods into logical groups
- **Remote Controllers**: Client-side proxies for seamless remote API calls
- **Authentication**: Built-in API key authentication support

## Quick Start

### Installation

```bash
pip install ctrlstack
```

### Basic Example

```python
from ctrlstack import Controller, ctrl_cmd_method, ctrl_query_method
from ctrlstack.server import create_controller_server
from ctrlstack.cli import create_controller_cli

class MyController(Controller):
    @ctrl_query_method
    def get_status(self) -> str:
        return "Service is running"
    
    @ctrl_cmd_method  
    async def send_message(self, message: str) -> str:
        return f"Received: {message}"

# Create FastAPI app
server_app = create_controller_server(MyController())

# Create CLI app  
cli_app = create_controller_cli(MyController())

if __name__ == "__main__":
    cli_app()
```

This creates:

**CLI Usage:**
```bash
python app.py get-status
# Output: Service is running

python app.py send-message "Hello World"  
# Output: Received: Hello World
```

**API Endpoints:**
- `GET /query/get_status` → Returns status
- `POST /cmd/send_message` → Accepts JSON body with message

### Remote Controller

Access your API as if it were a local controller:

```python
from ctrlstack.remote_controller import get_remote_controller

# Create remote controller client
remote_ctrl = get_remote_controller(
    MyController, 
    url="http://localhost:8000",
    api_key="your-api-key"
)

# Use exactly like local controller
status = await remote_ctrl.get_status()
result = await remote_ctrl.send_message(Message(text="Hello from remote!"))
```

### Dynamic Controller Building

```python
from ctrlstack.controller_app import ControllerApp

capp = ControllerApp()

@capp.register_query()
async def health_check() -> dict:
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@capp.register_cmd()
async def process_data(data: dict) -> str:
    return f"Processed {len(data)} items"

# Get FastAPI server
server_app = capp.get_server_app(api_keys=["secret-key"])

# Get CLI app
cli_app = capp.get_cli_app()
```

## Method Types

- **`@ctrl_query_method`**: GET endpoints, read-only operations
- **`@ctrl_cmd_method`**: POST endpoints, state-changing operations  
- **`@ctrl_method(type, group)`**: Custom method type and group

## Advanced Features

### Custom Routing Groups

```python
from ctrlstack import ControllerMethodType, ctrl_method

class AdminController(Controller):
    @ctrl_method(ControllerMethodType.COMMAND, "admin")
    def reset_database(self) -> str:
        return "Database reset"
    
    @ctrl_method(ControllerMethodType.QUERY, "admin")  
    def get_metrics(self) -> dict:
        return {"users": 100, "posts": 500}

# Creates routes: /admin/reset_database, /admin/get_metrics
```

### Authentication

```python
# Server with API key authentication
app = create_controller_server(
    MyController(), 
    api_keys=["secret-key-1", "secret-key-2"]
)

# Clients must include: X-API-Key: secret-key-1
```
<!-- #endregion -->

<!-- #region -->
## Development

### Prerequisites

- Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Install [direnv](https://direnv.net/) to automatically load the project virtual environment when entering it.
    - Mac: `brew install direnv`
    - Linux: `curl -sfL https://direnv.net/install.sh | bash`

### Setting up the environment

Run the following:

```bash
# In the root of the repo folder
uv sync --all-extras # Installs the virtual environment at './.venv'
direnv allow # Allows the automatic running of the script './.envrc'
nbl install-hooks # Installs a git hooks that ensures that notebooks are added properly
```

You are now set up to develop the codebase.

Further instructions:

- To export notebooks run `nbl export`.
- To clean notebooks run `nbl clean`.
- To see other available commands run just `nbl`.
- To add a new dependency run `uv add package-name`. See the the [uv documentation](https://docs.astral.sh/uv/) for more details.
- You need to `git add` all 'twinned' notebooks for the commit to be validated by the git-hook. For example, if you add `nbs/my-nb.ipynb`, you must also add `pts/my-nb.pct.py`.
- To render the documentation, run `nbl render-docs`. To preview it run `nbl preview-docs`
- To upgrade all dependencies run `uv sync --upgrade --all-extras`
<!-- #endregion -->
