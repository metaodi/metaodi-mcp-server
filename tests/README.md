# Health Check Tests

This directory contains health check tests for the deployed MCP server on Fly.io.

## Running Tests

### Install Dependencies

```bash
pip install -e ".[test]"
# or with uv:
uv pip install -e ".[test]"
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

The health check tests focus on basic server availability and connectivity:

1. **test_server_is_responding**: Tests if the server is reachable and responding to HTTP requests
2. **test_server_basic_health**: Performs a basic health check to ensure the server process is running

## Note on MCP Protocol Testing

These tests verify that the server is alive and responding, but do not test the full MCP protocol functionality (listing tools, resources, etc.). 

For detailed MCP protocol testing, use the **MCP Inspector** tool:

```bash
npx -y @modelcontextprotocol/inspector https://metaodi-mcp-server.fly.dev
```

The MCP server uses the `streamable-http` transport which requires the MCP SDK for full protocol interaction. Simple HTTP requests cannot test tools and resources functionality.

## GitHub Action

The health check runs automatically:
- After every successful deployment (via the "Fly Deploy" workflow)
- Every 6 hours on a schedule
- Manually via the GitHub Actions UI

See `.github/workflows/health-check.yml` for the workflow configuration.
