# metaodi-mcp-server

MCP server for my tools like OpenERZ or tecdottir.

The server is deployed at: **https://mcp.metaodi.ch**

## Available Tools

### OpenERZ (Waste Collection)
- `get_next_waste_collection(region, area?)`
- `get_next_waste_collection_for_type(waste_type, region, area?)`
- `list_waste_regions()`
- `list_waste_areas(region)`
- `list_waste_types(region)`

### Tecdottir (Weather)
- `list_weather_stations()`
- `get_weather_measurements(station, start_date?, end_date?, limit?)`

## Using the Server

### Configure in Claude Desktop

To use this MCP server with Claude Desktop, add the following to your Claude Desktop configuration file:

**Location of config file:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**

```json
{
  "mcpServers": {
    "metaodi": {
      "url": "https://mcp.metaodi.ch/mcp"
    }
  }
}
```

After updating the configuration, restart Claude Desktop to apply the changes.

### Configure in ChatGPT

To use this MCP server with ChatGPT:

1. Open ChatGPT settings
2. Navigate to the MCP servers section
3. Add a new server with the URL: `https://mcp.metaodi.ch/mcp`
4. Save the configuration

### Test with MCP Inspector

You can also test the server interactively using the MCP Inspector tool:

```bash
npx -y @modelcontextprotocol/inspector https://mcp.metaodi.ch
```

## Development Usage

Python SDK: https://github.com/modelcontextprotocol/python-sdk

```
uv run mcp
```

Run OpenERZ:

```
uv run mcp run openerz.py
```


MCP Inspector:

```
npx -y @modelcontextprotocol/inspector uv run mcp run openerz.py
```

## Health Check

The deployed server at **https://mcp.metaodi.ch** has automated health checks that run:
- After every deployment
- Every 6 hours on a schedule
- Manually via GitHub Actions

To run health checks locally:

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests against deployed server
pytest tests/test_health_check.py -v

# Run against local server
MCP_SERVER_URL=http://localhost:8000 pytest tests/test_health_check.py -v
```

See `tests/README.md` for more information.