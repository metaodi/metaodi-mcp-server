"""Health check tests for the deployed MCP server.

This test suite checks if the deployed MCP server on Fly.io is responding correctly.
It validates:
1. Server is reachable and responding to HTTP requests
2. Server process is running
3. Basic connectivity works

Note: The Fly.io server uses auto_stop_machines, so the first request may take
longer as it wakes up the machine.

For detailed MCP protocol testing (tools/resources), use the MCP client SDK
or the MCP Inspector tool.
"""

import os
import httpx
import pytest

# Get server URL from environment variable or use default
SERVER_URL = os.getenv("MCP_SERVER_URL", "https://metaodi-mcp-server.fly.dev")
# Timeout for requests (longer to account for server wake-up)
REQUEST_TIMEOUT = 60.0


@pytest.mark.asyncio
async def test_server_is_responding():
    """Test that the MCP server is responding to HTTP requests.
    
    Note: First request may take 10-20 seconds to wake up the Fly.io machine.
    This test validates basic server availability and connectivity.
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        try:
            # Try multiple endpoints that the server might respond to
            endpoints_to_try = [
                "/",
                "/sse",
                "/health",
                "/status"
            ]
            
            response = None
            successful_endpoint = None
            
            for endpoint in endpoints_to_try:
                try:
                    response = await client.get(f"{SERVER_URL}{endpoint}")
                    if response.status_code < 500:
                        successful_endpoint = endpoint
                        break  # Got a valid response (even if 404, server is responding)
                except httpx.HTTPStatusError:
                    continue
                except Exception as e:
                    # Server might be waking up, continue trying
                    print(f"Attempt {endpoint} failed: {e}")
                    continue
            
            if response is None:
                pytest.fail(f"Server at {SERVER_URL} is not responding to any known endpoints")
                
            # The server should respond with some status code < 500 (not a server error)
            # 404 is acceptable - it means server is running but endpoint doesn't exist
            # 405 (Method Not Allowed) is also acceptable for MCP servers
            assert response.status_code < 500, (
                f"Server returned error status code: {response.status_code}"
            )
            
            print(f"\n✅ Server is responding at {SERVER_URL}{successful_endpoint}")
            print(f"✅ Status code: {response.status_code}")
            print(f"✅ Server is alive and reachable!")
            
        except httpx.ConnectError as e:
            pytest.fail(
                f"Failed to connect to server at {SERVER_URL}. "
                f"The server might be down or the URL is incorrect. Error: {e}"
            )
        except httpx.TimeoutException:
            pytest.fail(
                f"Request to {SERVER_URL} timed out after {REQUEST_TIMEOUT}s. "
                f"The server might be slow to wake up or experiencing issues."
            )


@pytest.mark.asyncio 
async def test_server_basic_health():
    """Test server availability with a simple request.
    
    This is a simplified health check that just verifies the server
    process is running and responding to requests.
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        try:
            # Make a simple GET request to wake up and test the server
            response = await client.get(f"{SERVER_URL}/")
            
            # Any response < 500 means the server is functioning
            assert response.status_code < 500, (
                f"Server returned error: {response.status_code}"
            )
            
            print(f"\n✅ Basic health check passed")
            print(f"✅ Server returned status: {response.status_code}")
            
        except Exception as e:
            pytest.fail(f"Health check failed: {e}")


# NOTE: For detailed MCP protocol testing (listing tools, resources, etc.),
# use the MCP Inspector tool or the MCP client SDK:
#   npx -y @modelcontextprotocol/inspector <server-url>
#
# The streamable-http transport used by this server requires the MCP SDK
# to properly interact with tools and resources. Simple HTTP requests
# cannot test the full MCP protocol functionality.
#
# This health check focuses on basic server availability and connectivity,
# which is sufficient for monitoring deployment health.
