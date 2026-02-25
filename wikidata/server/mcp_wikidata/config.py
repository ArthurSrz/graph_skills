"""Configuration management for MCP Wikidata server."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv


class Config(BaseModel):
    user_agent: str = Field(
        default="MCP-Wikidata/0.1.0 (https://github.com/mcp-wikidata; change-to-your-contact@example.com)",
        description="User-Agent string for API requests"
    )
    
    rate_limit: int = Field(
        default=60,
        description="Maximum requests per minute"
    )
    
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    
    cache_ttl: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
    
    max_results: int = Field(
        default=50,
        description="Maximum number of results per request"
    )
    
    sparql_endpoint: str = Field(
        default="https://query.wikidata.org/sparql",
        description="SPARQL endpoint URL"
    )
    
    wikibase_api_url: str = Field(
        default="https://www.wikidata.org/w/api.php",
        description="Wikibase API endpoint URL"
    )
    
    default_language: str = Field(
        default="en",
        description="Default language code"
    )

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        
        return cls(
            user_agent=os.getenv("WIKIDATA_USER_AGENT", "MCP-Wikidata/0.1.0 (https://github.com/mcp-wikidata; change-to-your-contact@example.com)"),
            rate_limit=int(os.getenv("WIKIDATA_RATE_LIMIT", "60")),
            timeout=int(os.getenv("WIKIDATA_TIMEOUT", "30")),
            cache_ttl=int(os.getenv("WIKIDATA_CACHE_TTL", "3600")),
            max_results=int(os.getenv("WIKIDATA_MAX_RESULTS", "50")),
            sparql_endpoint=os.getenv(
                "WIKIDATA_SPARQL_ENDPOINT", 
                "https://query.wikidata.org/sparql"
            ),
            wikibase_api_url=os.getenv(
                "WIKIDATA_API_URL", 
                "https://www.wikidata.org/w/api.php"
            ),
            default_language=os.getenv("WIKIDATA_DEFAULT_LANGUAGE", "en"),
        )

    @classmethod
    def from_file(cls, config_path: Optional[str] = None) -> "Config":
        if config_path and Path(config_path).exists():
            import json
            with open(config_path) as f:
                config_data = json.load(f)
            return cls(**config_data)
        return cls.from_env()