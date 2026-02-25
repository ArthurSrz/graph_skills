# Graph skills

A collection of Claude skills for knowledge graph construction and graphRAG workflows.

## Skills

### wikidata

MCP server and Claude skill for querying Wikidata's knowledge graph — entity lookup, relationship exploration, and custom SPARQL queries.

**Use cases:**
- Factual queries about real-world entities (people, places, organizations, concepts)
- Knowledge graph exploration via Wikidata's 100M+ items
- SPARQL queries against the Wikidata endpoint
- Cross-language entity lookup and property traversal

### pont-de-londres

Integration pattern for connecting a domain graph (structured, from CSV) to a lexical graph (automatically extracted from unstructured documents via LLM).

**Use cases:**
- graphRAG architectures
- PDF ingestion with metadata
- building Knowledge Graphs from heterogeneous sources
- neo4j-graphrag and SimpleKGPipeline workflows

## Installation

### Claude.ai / Claude App

1. Download the `pont-de-londres.zip` file from this repo
2. Go to **Settings > Capabilities > Skills**
3. Click **Upload skill** and select the ZIP file

### Claude Code

Copy the skill folder to your skills directory:

## Usage

Once installed, Claude will automatically use these skills when relevant to your task. You can also explicitly reference them:

> "Use the pont-de-londres pattern to integrate my CSV metadata with the extracted entities from my PDFs"

## Resources

- [graphrag101](https://github.com/ArthurSrz/graphrag101) - Reference implementation and tutorials
- [Anthropic Skills Documentation](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)

## License

Apache 2.0
