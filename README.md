# metaodi-mcp-server

MCP server for my tools like OpenERZ or tecdottir.

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

## Usage

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