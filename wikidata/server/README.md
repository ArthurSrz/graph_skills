# MCP Wikidata Server

Un serveur [Model Context Protocol (MCP)](https://modelcontextprotocol.io) qui fournit un accès aux données Wikidata pour les Large Language Models.

## 🔧 Fonctionnalités

- **5 outils MCP** pour interagir avec Wikidata :
  - `search_entities` : Recherche textuelle d'entités
  - `get_entity` : Récupération détaillée d'entités par ID
  - `sparql_query` : Exécution de requêtes SPARQL personnalisées
  - `get_relations` : Exploration des relations d'entités
  - `find_by_property` : Recherche par propriété-valeur

- **APIs supportées** :
  - Wikibase API (recherche et récupération d'entités)
  - SPARQL Query Service (requêtes complexes)
  - Support multilingue et cache intelligent

## 📋 Prérequis

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (gestionnaire de paquets Python moderne)

## 📦 Installation

### 1. Cloner le projet
```bash
git clone https://github.com/joelgombin/mcp-wikidata.git
cd mcp-wikidata
```

### 2. Installer les dépendances
```bash
uv sync
```

### 3. Tester l'installation
```bash
uv run python test_connection.py
```

## ⚙️ Configuration avec Claude Desktop

### Configuration recommandée (portable)

Ajoutez cette configuration à votre fichier Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json` sur macOS) :

```json
{
  "mcpServers": {
    "mcp-wikidata": {
      "command": "/path/to/your/mcp-wikidata/run_mcp_wikidata.sh",
      "args": []
    }
  }
}
```

**Important** : Remplacez `/path/to/your/mcp-wikidata/` par le chemin absolu vers votre dossier d'installation.

### Alternative avec uv direct

Si vous préférez une configuration sans script wrapper :

```json
{
  "mcpServers": {
    "mcp-wikidata": {
      "command": "uv",
      "args": ["run", "mcp-wikidata"],
      "cwd": "/path/to/your/mcp-wikidata",
      "env": {
        "PATH": "/usr/local/bin:/usr/bin:/bin:~/.local/bin"
      }
    }
  }
}
```

## 🧪 Tests et vérification

### Test avec MCP Inspector
```bash
npx @modelcontextprotocol/inspector uv run mcp-wikidata
```

### Tests manuels des APIs
```bash
uv run python test_manual.py
```

### Test client MCP complet
```bash
uv run python test_mcp_client.py
```

## 🔧 Utilisation des outils

### search_entities
Recherche d'entités par texte :
```python
{
  "query": "Einstein",
  "language": "en",
  "limit": 5,
  "type": "item"
}
```

### get_entity
Récupération d'entité par ID :
```python
{
  "entity_id": "Q937",
  "language": "en", 
  "simplified": true
}
```

### sparql_query
Requête SPARQL personnalisée :
```python
{
  "query": "SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q5 . SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\" . } } LIMIT 10",
  "format": "json"
}
```

### get_relations
Relations d'une entité :
```python
{
  "entity_id": "Q937",
  "relation_type": "outgoing",
  "limit": 20
}
```

### find_by_property
Recherche par propriété :
```python
{
  "property": "P106",
  "value": "physicist",
  "limit": 10
}
```

## ⚙️ Configuration avancée

### Variables d'environnement

Créez un fichier `.env` basé sur `.env.example` :

```bash
# User-Agent pour les requêtes API
WIKIDATA_USER_AGENT=MCP-Wikidata/0.1.0

# Limitation du taux de requêtes (par minute)
WIKIDATA_RATE_LIMIT=60

# Timeout des requêtes en secondes
WIKIDATA_TIMEOUT=30

# TTL du cache en secondes
WIKIDATA_CACHE_TTL=3600

# Nombre maximum de résultats par requête
WIKIDATA_MAX_RESULTS=50

# Langue par défaut
WIKIDATA_DEFAULT_LANGUAGE=en
```

### Logs de debug

Pour diagnostiquer des problèmes :
```bash
uv run mcp-wikidata --log-level DEBUG
```

## 🔧 Dépannage

### Erreur "server disconnected" dans Claude Desktop

1. **Vérifiez l'installation d'uv** :
   ```bash
   which uv
   # Doit retourner un chemin comme /Users/username/.local/bin/uv
   ```

2. **Testez le script wrapper** :
   ```bash
   ./run_mcp_wikidata.sh --help
   ```

3. **Vérifiez les permissions** :
   ```bash
   chmod +x run_mcp_wikidata.sh
   ```

4. **Redémarrez Claude Desktop** après modification de la configuration

### Erreur "spawned uv ENOENT"

Cette erreur indique que Claude Desktop ne trouve pas la commande `uv`. Le script wrapper `run_mcp_wikidata.sh` résout automatiquement ce problème en cherchant `uv` dans plusieurs emplacements courants.

### Logs de diagnostic

Les logs détaillés sont disponibles dans :
- Console de MCP Inspector
- Fichiers de log Claude Desktop (selon votre OS)
- Sortie stderr du serveur MCP

## 📁 Structure du projet

```
mcp-wikidata/
  ├ mcp_wikidata/           # Package principal
     ├ __init__.py
     ├ server.py           # Serveur MCP principal
     ├ config.py           # Configuration
     ├ tools.py            # Définitions des outils MCP
     └ wikidata_client.py  # Client API Wikidata
  ├ tests/                  # Tests
  ├ run_mcp_wikidata.sh    # Script wrapper (recommandé)
  ├ test_*.py              # Scripts de test
  ├ pyproject.toml         # Configuration du projet
  ├ .env.example           # Variables d'environnement
  └ README.md
```

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations  
- Ajouter de nouveaux outils MCP
- Améliorer la documentation

## 📄 Licence

MIT License - voir le fichier LICENSE pour plus de détails.

## 📚 Ressources utiles

- [Documentation MCP](https://modelcontextprotocol.io/docs)
- [API Wikidata](https://www.wikidata.org/wiki/Wikidata:Data_access)  
- [SPARQL Query Service](https://query.wikidata.org/)
- [Documentation uv](https://docs.astral.sh/uv/)

---

**Généré avec Claude Code** 🚀