"""MCP tools implementation for Wikidata operations."""

import json
from typing import Any, Dict, List

from mcp.types import Tool, TextContent

from .config import Config
from .wikidata_client import WikidataClient


class WikidataTools:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = WikidataClient(config)

    def get_tool_definitions(self) -> List[Tool]:
        return [
            Tool(
                name="search_entities",
                description="Search for entities in Wikidata by text query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term"
                        },
                        "language": {
                            "type": "string", 
                            "description": "Language code (default: en)",
                            "default": "en"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10, max: 50)",
                            "default": 10,
                            "maximum": 50
                        },
                        "type": {
                            "type": "string",
                            "description": "Entity type filter (item, property)",
                            "enum": ["item", "property"]
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_entity",
                description="Get detailed information about a Wikidata entity",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "Wikidata entity ID (Q123, P456)"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language code (default: en)",
                            "default": "en"
                        },
                        "properties": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific properties to include"
                        },
                        "simplified": {
                            "type": "boolean",
                            "description": "Return simplified format (default: false)",
                            "default": False
                        }
                    },
                    "required": ["entity_id"]
                }
            ),
            Tool(
                name="sparql_query",
                description="Execute a SPARQL query against Wikidata",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SPARQL query"
                        },
                        "format": {
                            "type": "string",
                            "description": "Response format",
                            "enum": ["json", "csv", "xml"],
                            "default": "json"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 100, max: 1000)",
                            "default": 100,
                            "maximum": 1000
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_relations",
                description="Get relations of a Wikidata entity",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "Wikidata entity ID"
                        },
                        "relation_type": {
                            "type": "string",
                            "description": "Type of relations to retrieve",
                            "enum": ["incoming", "outgoing", "all"],
                            "default": "outgoing"
                        },
                        "property_filter": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by specific properties"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of relations",
                            "default": 20,
                            "maximum": 100
                        }
                    },
                    "required": ["entity_id"]
                }
            ),
            Tool(
                name="find_by_property",
                description="Find entities by property and value",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "property": {
                            "type": "string",
                            "description": "Property ID (P123)"
                        },
                        "value": {
                            "type": "string",
                            "description": "Property value to search for"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language code (default: en)",
                            "default": "en"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "maximum": 100
                        }
                    },
                    "required": ["property", "value"]
                }
            )
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            if name == "search_entities":
                result = await self.client.search_entities(**arguments)
            elif name == "get_entity":
                result = await self.client.get_entity(**arguments)
            elif name == "sparql_query":
                result = await self.client.sparql_query(**arguments)
            elif name == "get_relations":
                result = await self.client.get_relations(**arguments)
            elif name == "find_by_property":
                result = await self.client.find_by_property(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        except Exception as e:
            error_msg = str(e)
            if not error_msg.strip():
                error_msg = f"Unknown error occurred while executing {name}"
            
            return [
                TextContent(
                    type="text",
                    text=f"Error executing {name}: {error_msg}"
                )
            ]