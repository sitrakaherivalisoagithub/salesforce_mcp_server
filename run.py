import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any

import click
import uvicorn
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
import mcp.types as types
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

# Local imports
from salesforce_mcp.event_store import InMemoryEventStore
from salesforce_mcp.salesforce_client import SalesforceClient
from salesforce_mcp.tools_schema import get_tools_schema

logger = logging.getLogger(__name__)

# --- Main entry point with Click and Uvicorn ---

@click.command()
@click.option("--port", default=3000, help="Port to listen on for HTTP.", show_default=True)
@click.option("--host", default="127.0.0.1", help="Host to listen on.", show_default=True)
@click.option("--sf-username", envvar="SF_USERNAME", required=True, help="Salesforce username (or via SF_USERNAME env var).")
@click.option("--sf-password", envvar="SF_PASSWORD", required=True, help="Salesforce password (or via SF_PASSWORD env var).")
@click.option("--sf-token", envvar="SF_TOKEN", required=True, help="Salesforce security token (or via SF_TOKEN env var).")
@click.option("--sf-domain", envvar="SF_DOMAIN", default="login", help="Salesforce domain ('login' for prod, 'test' for sandbox).", show_default=True)
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR).", show_default=True)
def main(
    port: int,
    host: str,
    sf_username: str,
    sf_password: str,
    sf_token: str,
    sf_domain: str,
    log_level: str,
) -> int:
    """Starts the MCP Server for Salesforce."""
    # Configure logging
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Reduce noise from some libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger.info(f"Starting Salesforce MCP server on http://{host}:{port}")

    # Initialize the Salesforce client
    try:
        sf_client = SalesforceClient(
            username=sf_username,
            password=sf_password,
            security_token=sf_token,
            domain=sf_domain
        )
    except Exception as e:
        logger.error(f"Could not initialize Salesforce client: {e}")
        return 1
    
    # Create the MCP server
    app = Server("salesforce-manager")

    # Register the list_tools handler
    @app.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        logger.debug("list_tools called")
        return get_tools_schema()

    # Register the call_tool handler
    @app.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.ContentBlock]:
        logger.debug(f"Tool called: {name} with arguments: {arguments}")
        arguments = arguments or {}
        
        try:
            # Map tool names to client functions
            tool_function_map = {
                "search_contact": sf_client.search_contact,
                "get_account_details": sf_client.get_account_details,
                "list_open_opportunities": sf_client.list_open_opportunities,
                "log_activity": sf_client.log_activity,
                "get_case_details": sf_client.get_case_details,
                "list_open_cases": sf_client.list_open_cases,
                "create_case": sf_client.create_case,
                "add_comment_to_case": sf_client.add_comment_to_case,
                "search_salesforce": sf_client.search_salesforce,
            }
            
            if name not in tool_function_map:
                raise ValueError(f"Unknown tool: {name}")
                
            # Call the corresponding function with unpacked arguments
            results = tool_function_map[name](**arguments)
            
            # Convert the result to a ContentBlock
            import json
            results_text = json.dumps(results, indent=2, default=str)
            
            return [types.TextContent(type="text", text=results_text)]
        
        except Exception as e:
            logger.error(f"Error calling tool '{name}': {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Error: {e}")]

    # --- Starlette/Uvicorn Configuration ---
    
    event_store = InMemoryEventStore()
    session_manager = StreamableHTTPSessionManager(app=app, event_store=event_store)

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        """Handler for streamable HTTP requests."""
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app_lifespan: Starlette) -> AsyncIterator[None]:
        """Manages the application's lifespan (startup/shutdown)."""
        async with session_manager.run():
            logger.info("Session manager started.")
            yield
            logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=(log_level.upper() == "DEBUG"),
        routes=[Mount("/mcp", app=handle_streamable_http)],
        lifespan=lifespan,
    )

    # Start the Uvicorn server
    uvicorn.run(
        starlette_app, 
        host=host, 
        port=port, 
        log_level=log_level.lower()
    )

    return 0

if __name__ == "__main__":
    main()
