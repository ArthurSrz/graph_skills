# Configuration Claude Desktop pour MCP Wikidata

## 🎯 Options de configuration

Après le problème de compatibilité avec MCP Inspector/Claude Desktop, voici les **3 options testées** :

### ✅ Option 1 : Script Bash (recommandé, testé)
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

**Avantages** :
- ✅ Détecte automatiquement `uv`
- ✅ Filtre les arguments redondants 
- ✅ Fonctionne avec MCP Inspector et Claude Desktop
- ✅ Portable (fonctionne dans n'importe quel dossier)

### ✅ Option 2 : Lanceur Python (très robuste)
```json
{
  "mcpServers": {
    "mcp-wikidata": {
      "command": "python3",
      "args": ["/path/to/your/mcp-wikidata/mcp_wikidata_launcher.py"],
      "cwd": "/path/to/your/mcp-wikidata"
    }
  }
}
```

**Avantages** :
- ✅ Multiplateforme (Windows/macOS/Linux)
- ✅ Gestion d'erreurs avancée
- ✅ Filtrage intelligent des arguments
- ✅ Plus robuste que bash

### ⚠️ Option 3 : uv direct (peut poser problème)
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

**Problèmes potentiels** :
- ❌ Peut donner "spawned uv ENOENT" si PATH incorrect
- ❌ Dépend de la configuration système
- ❌ Arguments redondants avec MCP Inspector

## 🚀 Installation recommandée

1. **Utilisez l'Option 1** (script bash) pour la plupart des cas
2. **Utilisez l'Option 2** (Python) si vous avez des problèmes avec bash
3. **Évitez l'Option 3** sauf configuration système parfaite

## 🔧 Après configuration

1. **Redémarrez Claude Desktop** complètement
2. Le serveur MCP Wikidata apparaîtra avec 5 outils
3. Testez avec : `npx @modelcontextprotocol/inspector /path/to/run_mcp_wikidata.sh`

## 🐛 Résolution de problèmes

### "server disconnected"
- Vérifiez le chemin absolu dans la configuration
- Redémarrez Claude Desktop
- Testez le script manuellement : `./run_mcp_wikidata.sh --help`

### "spawned uv ENOENT" 
- Utilisez l'Option 1 ou 2 (pas l'Option 3)
- Les scripts wrapper résolvent automatiquement ce problème

### "Got unexpected extra arguments"
- ✅ **Résolu** : Les scripts filtrent maintenant les arguments redondants
- Les deux scripts wrapper gèrent ce cas automatiquement