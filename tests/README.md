# Health Check Tests

This directory contains health check tests for the deployed MCP server on Fly.io.

## Running Tests

### Install Dependencies

```bash
# Using uv (recommended)
uv sync --extra test

# Or using pip
pip install -e ".[test]"
```

### Run Tests

```bash
# Run against deployed server
pytest tests/test_health_check.py -v

# Run against a different server
MCP_SERVER_URL=https://your-server.com pytest tests/test_health_check.py -v

# Run against local server
MCP_SERVER_URL=http://localhost:8000 pytest tests/test_health_check.py -v
```

## What is Tested

The health check tests validate:

1. **test_server_is_responding**: Tests if the server is reachable and responding to HTTP requests
2. **test_server_basic_health**: Performs a basic health check to ensure the server process is running
3. **test_mcp_endpoint_list_tools**: Tests the MCP endpoint at `/mcp` and lists all available tools

## MCP Endpoint Testing

The test suite now includes a test that validates the MCP endpoint functionality by:
- Initializing an MCP session using the JSON-RPC protocol
- Listing all available tools from the server
- Verifying that expected tools are present

For interactive MCP protocol testing, you can also use the **MCP Inspector** tool:

```bash
npx -y @modelcontextprotocol/inspector https://metaodi-mcp-server.fly.dev
```

## GitHub Action

The health check runs automatically:
- After every successful deployment (via the "Fly Deploy" workflow)
- Every 6 hours on a schedule
- Manually via the GitHub Actions UI

See `.github/workflows/health-check.yml` for the workflow configuration.
