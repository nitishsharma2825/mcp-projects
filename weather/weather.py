from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE =  "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

# helper functions
async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description avaliable')}
Area: {props.get('areaDesc', 'Unknown')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

# tool execution
@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alertts for a given state.
    
    Args:
        state (str): The state to get alerts for.
    """
    url = f"{NWS_API_BASE}/alerts/active/area={state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "No alerts found."
    
    if not data["features"]:
        return "No active alerts for this state."
    
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get the weather forecast for a given location.

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast."
    
    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch forecast."

    # Format the forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:
        forcast = f"""
{period["name"]}:
Temperature: {period["temperature"]}.{period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forcast)
    
    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    mcp.run(transport='stdio')