"""Wikidata API client implementation."""

import asyncio
import json
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from .config import Config


class WikidataClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = httpx.AsyncClient(
            headers={"User-Agent": config.user_agent},
            timeout=config.timeout,
        )
        self._rate_limiter = asyncio.Semaphore(config.rate_limit)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()

    async def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        async with self._rate_limiter:
            try:
                response = await self.session.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                raise Exception(f"Request timed out after {self.config.timeout} seconds")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    raise Exception(
                        "Wikidata API returned 403 Forbidden. "
                        "Your User-Agent string likely lacks required contact info. "
                        "Set WIKIDATA_USER_AGENT to: 'AppName/1.0 (https://your-contact-url)' "
                        "per https://meta.wikimedia.org/wiki/User-Agent_policy"
                    )
                elif e.response.status_code == 429:
                    raise Exception("Wikidata API is rate limiting requests. Please wait and try again.")
                elif e.response.status_code >= 500:
                    raise Exception(f"Wikidata server error ({e.response.status_code}). Please try again later.")
                else:
                    raise Exception(f"Wikidata API error {e.response.status_code}: {e.response.text[:200]}")
            except httpx.ConnectError:
                raise Exception(f"Cannot connect to Wikidata API. Check your internet connection.")

    async def search_entities(
        self, 
        query: str, 
        language: str = "en",
        limit: int = 10,
        type: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": language,
            "limit": min(limit, self.config.max_results),
            "format": "json",
        }
        
        if type:
            params["type"] = type

        data = await self._make_request(self.config.wikibase_api_url, params)
        
        entities = []
        for item in data.get("search", []):
            entities.append({
                "id": item.get("id"),
                "label": item.get("label"),
                "description": item.get("description", ""),
                "url": f"https://www.wikidata.org/entity/{item.get('id')}"
            })

        return {"entities": entities}

    async def get_entity(
        self,
        entity_id: str,
        language: str = "en",
        properties: Optional[List[str]] = None,
        simplified: bool = False
    ) -> Dict[str, Any]:
        params = {
            "action": "wbgetentities",
            "ids": entity_id,
            "languages": language,
            "format": "json",
        }

        if properties:
            params["props"] = "|".join(properties)

        data = await self._make_request(self.config.wikibase_api_url, params)
        
        if "entities" not in data or entity_id not in data["entities"]:
            raise ValueError(f"Entity {entity_id} not found")

        entity_data = data["entities"][entity_id]
        
        if simplified:
            return await self._simplify_entity(entity_data, language)

        return {"entity": entity_data}

    @staticmethod
    def _escape_sparql_string(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    @staticmethod
    def _extract_entity_refs(entity_data: Dict[str, Any]) -> List[str]:
        """Collect all Q-IDs referenced in claims for batch label fetching."""
        q_ids = set()
        for claims in entity_data.get("claims", {}).values():
            for claim in claims:
                mainsnak = claim.get("mainsnak", {})
                datavalue = mainsnak.get("datavalue", {})
                value = datavalue.get("value")
                if isinstance(value, dict) and "id" in value and value["id"].startswith("Q"):
                    q_ids.add(value["id"])
        return list(q_ids)

    async def _fetch_labels_batch(
        self, q_ids: List[str], language: str
    ) -> Dict[str, str]:
        """Fetch labels for a list of Q-IDs in one API call."""
        if not q_ids:
            return {}
        # Wikidata allows up to 50 IDs per request
        labels: Dict[str, str] = {}
        for i in range(0, len(q_ids), 50):
            batch = q_ids[i:i + 50]
            params = {
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "languages": language,
                "props": "labels",
                "format": "json",
            }
            data = await self._make_request(self.config.wikibase_api_url, params)
            for entity_id, entity in data.get("entities", {}).items():
                lang_labels = entity.get("labels", {})
                label = lang_labels.get(language, {}).get("value") or \
                        next(iter(lang_labels.values()), {}).get("value")
                if label:
                    labels[entity_id] = label
        return labels

    async def _simplify_entity(
        self, entity_data: Dict[str, Any], language: str
    ) -> Dict[str, Any]:
        entity: Dict[str, Any] = {
            "id": entity_data.get("id"),
            "labels": {},
            "descriptions": {},
            "properties": {}
        }

        if "labels" in entity_data:
            entity["labels"] = {
                lang: label["value"]
                for lang, label in entity_data["labels"].items()
            }

        if "descriptions" in entity_data:
            entity["descriptions"] = {
                lang: desc["value"]
                for lang, desc in entity_data["descriptions"].items()
            }

        # Batch-fetch labels for all referenced Q-IDs
        q_ids = self._extract_entity_refs(entity_data)
        ref_labels = await self._fetch_labels_batch(q_ids, language)

        if "claims" in entity_data:
            for prop_id, claims in entity_data["claims"].items():
                prop_values = []
                for claim in claims:
                    if "mainsnak" in claim and "datavalue" in claim["mainsnak"]:
                        value = claim["mainsnak"]["datavalue"]["value"]
                        if isinstance(value, dict) and "id" in value:
                            ref_id = value["id"]
                            prop_values.append({
                                "value": ref_id,
                                "label": ref_labels.get(ref_id, ref_id)
                            })
                        else:
                            prop_values.append({"value": str(value)})

                if prop_values:
                    entity["properties"][prop_id] = prop_values

        return {"entity": entity}

    async def sparql_query(
        self,
        query: str,
        format: str = "json",
        limit: int = 100
    ) -> Dict[str, Any]:
        if "LIMIT" not in query.upper():
            query += f" LIMIT {min(limit, 1000)}"

        params = {
            "query": query,
            "format": format
        }

        async with self._rate_limiter:
            try:
                response = await self.session.get(
                    self.config.sparql_endpoint,
                    params=params,
                    headers={
                        "Accept": f"application/sparql-results+{format}",
                        "User-Agent": self.config.user_agent
                    }
                )
                response.raise_for_status()

                if format == "json":
                    return response.json()
                else:
                    return {"result": response.text}

            except asyncio.TimeoutError:
                raise Exception(f"SPARQL query timed out after {self.config.timeout} seconds. Try simplifying your query or increasing the timeout.")
            except httpx.TimeoutException:
                raise Exception(f"SPARQL query timed out after {self.config.timeout} seconds. Try simplifying your query or increasing the timeout.")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    raise Exception(
                        "Wikidata API returned 403 Forbidden. "
                        "Your User-Agent string likely lacks required contact info. "
                        "Set WIKIDATA_USER_AGENT to: 'AppName/1.0 (https://your-contact-url)' "
                        "per https://meta.wikimedia.org/wiki/User-Agent_policy"
                    )
                elif e.response.status_code == 500:
                    raise Exception(f"SPARQL server error (500). Your query may have syntax errors or be too complex: {query[:100]}...")
                elif e.response.status_code == 429:
                    raise Exception("SPARQL service is rate limiting requests. Please wait and try again.")
                else:
                    raise Exception(f"SPARQL HTTP error {e.response.status_code}: {e.response.text[:200]}")
            except httpx.ConnectError:
                raise Exception(f"Cannot connect to SPARQL endpoint {self.config.sparql_endpoint}. Check your internet connection.")
            except Exception as e:
                if "timeout" in str(e).lower():
                    raise Exception(f"SPARQL query timed out after {self.config.timeout} seconds. Try simplifying your query or increasing the timeout.")
                raise Exception(f"SPARQL query failed: {str(e)}")

    async def _fetch_relations(
        self,
        entity_id: str,
        direction: str,
        limit: int,
        property_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        if direction == "outgoing":
            query = f"""
            SELECT ?property ?propertyLabel ?target ?targetLabel WHERE {{
              wd:{entity_id} ?property ?target .
              ?prop wikibase:directClaim ?property .
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
            }}
            LIMIT {limit}
            """
        else:
            query = f"""
            SELECT ?property ?propertyLabel ?source ?sourceLabel WHERE {{
              ?source ?property wd:{entity_id} .
              ?prop wikibase:directClaim ?property .
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
            }}
            LIMIT {limit}
            """

        result = await self.sparql_query(query)

        relations = []
        for binding in result.get("results", {}).get("bindings", []):
            relation = {
                "property": binding.get("property", {}).get("value", "").split("/")[-1],
                "property_label": binding.get("propertyLabel", {}).get("value", ""),
                "direction": direction
            }

            if direction == "outgoing":
                relation["target"] = {
                    "id": binding.get("target", {}).get("value", "").split("/")[-1],
                    "label": binding.get("targetLabel", {}).get("value", "")
                }
            else:
                relation["source"] = {
                    "id": binding.get("source", {}).get("value", "").split("/")[-1],
                    "label": binding.get("sourceLabel", {}).get("value", "")
                }

            relations.append(relation)

        return relations

    async def get_relations(
        self,
        entity_id: str,
        relation_type: str = "outgoing",
        property_filter: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        if relation_type == "all":
            half = (limit + 1) // 2
            outgoing = await self._fetch_relations(entity_id, "outgoing", half, property_filter)
            incoming = await self._fetch_relations(entity_id, "incoming", half, property_filter)
            return {"relations": outgoing + incoming}
        if relation_type not in ("outgoing", "incoming"):
            raise ValueError(f"Invalid relation_type: {relation_type}")
        return {"relations": await self._fetch_relations(entity_id, relation_type, limit, property_filter)}

    async def find_by_property(
        self,
        property: str,
        value: str,
        language: str = "en",
        limit: int = 10
    ) -> Dict[str, Any]:
        escaped_value = self._escape_sparql_string(value)
        query = f"""
        SELECT ?item ?itemLabel WHERE {{
          ?item wdt:{property} "{escaped_value}" .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{language}" . }}
        }}
        LIMIT {limit}
        """

        result = await self.sparql_query(query)
        
        entities = []
        for binding in result.get("results", {}).get("bindings", []):
            entities.append({
                "id": binding.get("item", {}).get("value", "").split("/")[-1],
                "label": binding.get("itemLabel", {}).get("value", "")
            })

        return {"entities": entities}