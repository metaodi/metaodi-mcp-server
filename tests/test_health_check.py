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

import json
import os
import httpx
import pytest

# Get server URL from environment variable or use default
SERVER_URL = os.getenv("MCP_SERVER_URL", "https://metaodi-mcp-server.fly.dev")
# Timeout for requests (longer to account for server wake-up)
REQUEST_TIMEOUT = 60.0


def parse_sse_response(response_text: str) -> dict:
    """Parse Server-Sent Events (SSE) response and extract JSON data.
    
    Args:
        response_text: The SSE formatted response text
        
    Returns:
        Parsed JSON data from the SSE response
        
    Raises:
        ValueError: If the response is not in expected SSE format
    """
    if "event: message" not in response_text:
        raise ValueError("Response is not in SSE format (missing 'event: message')")
    
    # Find the data line
    data_lines = [line for line in response_text.split('\n') if line.startswith('data: ')]
    if not data_lines:
        raise ValueError("No 'data:' line found in SSE response")
    
    # Extract and parse JSON
    data_json = data_lines[0].replace('data: ', '')
    return json.loads(data_json)


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


@pytest.mark.asyncio
async def test_mcp_endpoint_list_tools():
    """Test that the MCP endpoint can list all available tools.
    
    The MCP server runs on the /mcp endpoint and uses Server-Sent Events (SSE).
    This test validates that the server can list all available tools.
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        
        # Step 1: Initialize the MCP session
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "health-check-test",
                    "version": "1.0.0"
                }
            }
        }
        
        try:
            # Initialize session
            response = await client.post(
                f"{SERVER_URL}/mcp",
                json=init_request,
                headers=headers
            )
            
            assert response.status_code == 200, (
                f"MCP initialize endpoint returned status {response.status_code}"
            )
            
            # Get session ID from response headers
            session_id = response.headers.get("mcp-session-id")
            assert session_id, "No mcp-session-id header in initialize response"
            
            # Parse SSE response
            init_data = parse_sse_response(response.text)
            
            assert "result" in init_data, "Initialize response missing 'result'"
            result = init_data["result"]
            assert "serverInfo" in result, "Initialize response missing 'serverInfo'"
            server_info = result["serverInfo"]
            
            print(f"\n✅ MCP session initialized")
            print(f"✅ Server name: {server_info.get('name')}")
            print(f"✅ Server version: {server_info.get('version')}")
            print(f"✅ Session ID: {session_id}")
            
            # Step 2: List tools using the session ID
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            # Add session ID to headers
            headers_with_session = headers.copy()
            headers_with_session["mcp-session-id"] = session_id
            
            response = await client.post(
                f"{SERVER_URL}/mcp",
                json=tools_request,
                headers=headers_with_session
            )
            
            assert response.status_code == 200, (
                f"MCP tools/list endpoint returned status {response.status_code}"
            )
            
            # Parse SSE response
            tools_data = parse_sse_response(response.text)
            
            assert "result" in tools_data, "tools/list response missing 'result'"
            result = tools_data["result"]
            assert "tools" in result, "Response missing 'tools' field"
            tools = result["tools"]
            assert isinstance(tools, list), "Tools should be a list"
            assert len(tools) > 0, "No tools available"
            
            # Verify expected tools are present
            tool_names = [tool.get("name") for tool in tools]
            expected_tools = [
                "get_next_waste_collection",
                "get_next_waste_collection_for_type",
                "list_waste_regions",
                "list_waste_areas",
                "list_waste_types",
                "list_weather_stations",
                "get_weather_measurements",
            ]
            
            for expected_tool in expected_tools:
                assert expected_tool in tool_names, (
                    f"Expected tool '{expected_tool}' not found in available tools"
                )
            
            print(f"\n✅ Found {len(tools)} tools")
            print("✅ Available tools:")
            for tool in tools:
                tool_name = tool.get("name")
                tool_desc = tool.get("description", "No description")
                print(f"   - {tool_name}: {tool_desc[:80]}")
            
        except httpx.ConnectError as e:
            pytest.fail(
                f"Failed to connect to MCP endpoint at {SERVER_URL}/mcp. "
                f"Error: {e}"
            )
        except httpx.TimeoutException:
            pytest.fail(f"Request to MCP endpoint timed out after {REQUEST_TIMEOUT}s")
        except Exception as e:
            pytest.fail(f"Unexpected error testing MCP endpoint: {str(e)}")
