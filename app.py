from typing import Any

import httpx
import datetime
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("openerz")

# Constants
OPENERZ_API = "https://openerz.metaodi.ch/api"
USER_AGENT = "metaodi-mcp-app/1.0"


async def make_request(url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Make a request to the OpenERZ API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    params = params or {}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url, params=params, headers=headers, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_calendar_entry(entry: dict) -> str:
    """Format an OpenERZ calendar entry into a readable string."""
    return f"""
Date: {entry.get("date", "Unknown")}
Waste Type: {entry.get("waste_type", "Unknown")}
Region: {entry.get("region", "Unknown")}
Area: {entry.get("area", "Unknown")}
Description: {entry.get("description", "No description available")}
"""

async def get_waste_collection_data(region: str, waste_type: str | None = None, area: str | None = None) -> str:
    """Get next waste collection for a region and waste type.

    Args:
        region: The region to get waste collection information for
        waste_type: The type of waste to get collection information for
    """
    # Validate region against server-provided list (if available)
    regions_url = f"{OPENERZ_API}/parameter/regions"
    regions_data = await make_request(regions_url)

    if region not in regions_data.get("result", []):
        return f"Region '{region}' is not valid. Use the 'list_waste_regions' tool to see valid values."

    # Try to fetch calendar entries for the region
    calendar_url = f"{OPENERZ_API}/calendar"

    calendar_params = {
        "limit": 10,
        "region": region,
        "sort": "date",
        "start": datetime.datetime.now().date().isoformat(),
    }
    if waste_type:
        calendar_params["types"] = waste_type
    if area:
        calendar_params["area"] = area
    
    data = await make_request(calendar_url, calendar_params)

    if not data:
        return "Unable to fetch waste collection data for this region."

    # Normalize possible response shapes to a list of entries
    entries = data.get("result", [])

    if not entries:
        return "No upcoming waste collection entries found for this region."
    
    areas = set(e.get("area") for e in entries if e.get("area"))
    if len(areas) > 1 and not area:
        return f"Multiple areas found for region '{region}'. Please specify an area using the 'area' parameter. Use the 'list_waste_areas' tool to see valid values."

    formatted = [format_calendar_entry(e) for e in entries[:10]]
    return "\n---\n".join(formatted)

@mcp.tool()
async def get_next_waste_collection(region: str, area: str | None = None) -> str:
    """Get next waste collection for a region.

    Args:
        region: The region to get waste collection information for
    """
    return await get_waste_collection_data(region, waste_type=None, area=area)


@mcp.tool()
async def get_next_paper_collection(region: str, area: str | None = None) -> str:
    """Get next paper waste collection for a region.

    Args:
        region: The region to get paper waste collection information for
        area: The area within the region to get paper waste collection information for
    """
    return await get_waste_collection_data(region, waste_type="paper", area=area)

@mcp.tool()
async def get_next_cardboard_collection(region: str, area: str | None = None) -> str:
    """Get next cardboard waste collection for a region.

    Args:
        region: The region to get cardboard waste collection information for
        area: The area within the region to get cardboard waste collection information for
    """
    return await get_waste_collection_data(region, waste_type="cardboard")

@mcp.tool()
async def list_waste_regions() -> str:
    """List valid region identifiers from the OpenERZ API.

    This tool queries the API and returns a human-readable list of region ids/names
    so callers can provide a valid `region` value to `get_next_waste_collection`.
    """
    url = f"{OPENERZ_API}/parameter/regions"
    data = await make_request(url)
    if not data:
        return "Unable to fetch regions from OpenERZ API."

    regions = data["result"]
    return "\n".join(regions)


@mcp.tool()
async def list_waste_areas(region: str) -> str:
    """List valid areas identifiers for a certain region from the OpenERZ API.

    This tool queries the API and returns a human-readable list of area names
    so callers can provide a valid `area` value to `get_next_waste_collection`.
    """
    url = f"{OPENERZ_API}/parameter/areas"
    params = {"region": region}
    data = await make_request(url, params=params)
    if not data:
        return f"Unable to fetch areas for region {region} from OpenERZ API."

    areas = list(e.get("area") for e in data["result"] if e.get("area"))
    return "\n".join(sorted(areas))


def main():
    # Initialize and run the server
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
