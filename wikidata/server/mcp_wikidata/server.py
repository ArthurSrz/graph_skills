"""Main MCP server implementation for Wikidata."""

import asyncio
import logging
from typing import Any, Sequence

import click
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .config import Config
from .tools import WikidataTools

logger = logging.getLogger(__name__)


class WikidataServer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.server = Server("mcp-wikidata")
        self.tools = WikidataTools(config)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return self.tools.get_tool_definitions()

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> Any:
            return await self.tools.call_tool(name, arguments)

    async def run(self) -> None:
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-wikidata",
                    server_version="0.1.0",
                    capabilities=ServerCapabilities(
                        tools={}
                    ),
                ),
            )


@click.command()
@click.option(
    "--config-file",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Log level",
)
def main(config_file: str | None = None, log_level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, log_level))
    
    config = Config.from_file(config_file) if config_file else Config()
    server = WikidataServer(config)
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    main()