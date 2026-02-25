---
name: mcp-wikidata
description: Query Wikidata's knowledge graph for factual information, entity lookup, relationship exploration, and SPARQL queries. Use when the user asks about real-world facts, people, places, organizations, or scientific concepts — or needs to run a custom SPARQL query.
---

# Wikidata MCP Skill

## Setup

The MCP server must be installed and running for this skill to work.

1. Unzip the skill and place the `server/` folder wherever you prefer
2. Run `uv sync` inside `server/` to install dependencies
3. Add the server to your Claude config (see `server/CONFIGURATION.md` for options)
4. Set your `WIKIDATA_USER_AGENT` env variable (e.g. `MCP-Wikidata/0.1.0 (your@email.com)`)

## When to Use This Skill

Use this skill when the user:
- Asks a factual question about a real-world entity (person, place, organization, concept)
- Needs to find a Wikidata entity ID (Q-number or P-number)
- Wants to explore relationships between entities
- Asks for entities sharing a property value
- Needs to run a custom SPARQL query against the Wikidata knowledge graph
- Requests cross-language label lookups

## Available Tools

Call these tools directly via MCP — they are loaded automatically.

| MCP Tool | Required params | Purpose |
|----------|-----------------|---------|
| `mcp__mcp-wikidata__search_entities` | `query` | Text search for entities |
| `mcp__mcp-wikidata__get_entity` | `entity_id` | Full entity data by ID (with resolved labels) |
| `mcp__mcp-wikidata__sparql_query` | `query` | Custom SPARQL execution |
| `mcp__mcp-wikidata__get_relations` | `entity_id` | Outgoing / incoming / all relations |
| `mcp__mcp-wikidata__find_by_property` | `property`, `value` | Find entities by property value |

## Workflows

### Identify an entity
1. `mcp__mcp-wikidata__search_entities(query="<name>", limit=5)` — pick the best match by description
2. `mcp__mcp-wikidata__get_entity(entity_id="Q...", simplified=true)` — compact summary with resolved human-readable labels

### Explore relationships
```
mcp__mcp-wikidata__get_relations(entity_id="Q42", relation_type="all", limit=30)
```
- `"outgoing"` = what this entity links to
- `"incoming"` = what links to this entity
- `"all"` = both directions combined (limit split evenly)

### Find entities by shared property
1. `mcp__mcp-wikidata__search_entities(query="country of citizenship", type="property")` → P27
2. `mcp__mcp-wikidata__find_by_property(property="P27", value="France", limit=20)`

### Custom SPARQL
```sparql
SELECT ?person ?personLabel WHERE {
  ?person wdt:P31 wd:Q5 .
  ?person wdt:P106 wd:Q169470 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
} LIMIT 20
```
Use `wdt:` (direct claims) for simple lookups. Always include `SERVICE wikibase:label` for readable labels.

## get_entity: simplified vs full

- `simplified=true` — returns labels, descriptions, and properties with **resolved human-readable labels** (e.g. `"label": "human"` not `"label": "Q5"`). Preferred for most use cases.
- `simplified=false` (default) — returns the raw Wikidata JSON dump. Useful when you need all claim metadata (qualifiers, references, etc.).

## Common Property IDs

| Concept | Property |
|---------|----------|
| instance of | P31 |
| subclass of | P279 |
| country | P17 |
| occupation | P106 |
| date of birth | P569 |
| date of death | P570 |
| educated at | P69 |
| award received | P166 |
| Nobel Prize laureate | P166 + Q7191 |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| "403 Forbidden" | User-Agent issue | Check `WIKIDATA_USER_AGENT` in server config |
| "Entity not found" | Wrong Q-number | Re-run `search_entities` |
| "SPARQL 500" | Syntax error or query too complex | Simplify query, check IDs |
| "rate limiting" | Too many calls | Wait and retry |
| "timed out" | Query too broad | Add `LIMIT` or filter more tightly |
