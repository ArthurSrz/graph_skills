# MCP Wikidata - Spécifications techniques

## Vue d'ensemble

Le serveur MCP Wikidata fournit un accès standardisé aux données de Wikidata pour les Large Language Models via le Model Context Protocol. Il permet aux LLMs d'interroger, explorer et récupérer des informations structurées depuis la base de connaissances Wikidata.

## Architecture

### Protocole MCP
- **Version** : 2025-06-18
- **Transport** : JSON-RPC 2.0
- **Communication** : Bidirectionnelle (client-serveur)

### APIs Wikidata utilisées
1. **Wikibase API** (via MediaWiki Action API - `https://www.wikidata.org/w/api.php`)
   - Actions Wikibase : `wbgetentities`, `wbsearchentities`, `wbeditentity`
   - Extensions spécifiques à Wikidata/Wikibase
   - Format de réponse : JSON
   
2. **SPARQL Query Service** (`https://query.wikidata.org/sparql`)
   - Requêtes SPARQL complexes sur le graphe RDF
   - Format de réponse : JSON, XML, CSV, TSV
   - Endpoint : `https://query.wikidata.org/sparql`

3. **Linked Data Interface** (`https://www.wikidata.org/entity/`)
   - Accès direct aux entités en RDF
   - Négociation de contenu automatique
   - Formats : JSON-LD, RDF/XML, Turtle, N-Triples

## Outils MCP

### 1. search_entities
**Description** : Recherche textuelle d'entités dans Wikidata

**Paramètres** :
- `query` (string, requis) : Terme de recherche
- `language` (string, optionnel) : Code langue (défaut: "en")
- `limit` (number, optionnel) : Nombre max de résultats (défaut: 10, max: 50)
- `type` (string, optionnel) : Type d'entité filtré

**Réponse** :
```json
{
  "entities": [
    {
      "id": "Q42",
      "label": "Douglas Adams",
      "description": "English author and humorist",
      "url": "https://www.wikidata.org/entity/Q42"
    }
  ]
}
```

### 2. get_entity
**Description** : Récupération complète d'une entité par son ID

**Paramètres** :
- `entity_id` (string, requis) : ID Wikidata (Q123, P456)
- `language` (string, optionnel) : Code langue (défaut: "en")
- `properties` (array, optionnel) : Liste de propriétés à inclure
- `simplified` (boolean, optionnel) : Format simplifié (défaut: false)

**Réponse** :
```json
{
  "entity": {
    "id": "Q42",
    "labels": {"en": "Douglas Adams", "fr": "Douglas Adams"},
    "descriptions": {"en": "English author and humorist"},
    "properties": {
      "P31": [{"value": "Q5", "label": "human"}],
      "P106": [{"value": "Q36180", "label": "writer"}]
    }
  }
}
```

### 3. sparql_query
**Description** : Exécution de requêtes SPARQL personnalisées

**Paramètres** :
- `query` (string, requis) : Requête SPARQL
- `format` (string, optionnel) : Format de réponse ("json", "csv", "xml")
- `limit` (number, optionnel) : Limite de résultats (défaut: 100, max: 1000)

**Réponse** :
```json
{
  "results": {
    "bindings": [
      {
        "item": {"type": "uri", "value": "http://www.wikidata.org/entity/Q42"},
        "label": {"type": "literal", "value": "Douglas Adams"}
      }
    ]
  }
}
```

### 4. get_relations
**Description** : Explorer les relations d'une entité

**Paramètres** :
- `entity_id` (string, requis) : ID de l'entité
- `relation_type` (string, optionnel) : Type de relation ("incoming", "outgoing", "all")
- `property_filter` (array, optionnel) : Filtrer par propriétés spécifiques
- `limit` (number, optionnel) : Nombre max de relations

**Réponse** :
```json
{
  "relations": [
    {
      "property": "P50",
      "property_label": "author",
      "direction": "incoming",
      "target": {"id": "Q25169", "label": "The Hitchhiker's Guide to the Galaxy"}
    }
  ]
}
```

### 5. find_by_property
**Description** : Recherche d'entités par propriété et valeur

**Paramètres** :
- `property` (string, requis) : ID de la propriété (P123)
- `value` (string, requis) : Valeur recherchée
- `language` (string, optionnel) : Code langue
- `limit` (number, optionnel) : Nombre max de résultats

## Gestion des erreurs

### Codes d'erreur MCP standard
- `-32700` : Parse error
- `-32600` : Invalid Request
- `-32601` : Method not found
- `-32602` : Invalid params
- `-32603` : Internal error

### Erreurs spécifiques Wikidata
- `1001` : Entity not found
- `1002` : Invalid SPARQL query
- `1003` : Rate limit exceeded
- `1004` : API timeout
- `1005` : Invalid property ID

## Configuration

### Variables d'environnement
- `WIKIDATA_USER_AGENT` : User-Agent pour les requêtes API
- `WIKIDATA_RATE_LIMIT` : Limite de requêtes par minute (défaut: 60)
- `WIKIDATA_TIMEOUT` : Timeout des requêtes en secondes (défaut: 30)
- `WIKIDATA_CACHE_TTL` : TTL du cache en secondes (défaut: 3600)

### Limites opérationnelles
- **Requêtes par minute** : 60 (configurable)
- **Timeout par requête** : 30 secondes
- **Taille max des résultats** : 1000 entités
- **Cache** : 1 heure par défaut

## Sécurité

### Authentification
- Pas d'authentification requise (API publique Wikidata)
- Rate limiting côté serveur pour éviter l'abus

### Validation des entrées
- Sanitisation des requêtes SPARQL
- Validation des IDs d'entités et propriétés
- Limitation des tailles de requêtes

## Performance

### Optimisations
- Cache en mémoire des entités fréquemment demandées
- Requêtes batch pour les récupérations multiples
- Compression gzip des réponses
- Connection pooling HTTP

### Métriques
- Temps de réponse moyen
- Taux de cache hit/miss
- Nombre de requêtes par endpoint
- Erreurs par type

## Compatibilité

### Versions MCP supportées
- 2025-06-18 (courante)
- Rétrocompatibilité avec versions précédentes

### Langages de programmation
- Implémentation de référence : Python 3.8+
- SDKs MCP officiels supportés

## Évolutions futures

### Version 1.1 (prévue)
- Support des modifications d'entités (lecture seule actuellement)
- Intégration avec Wikidata Commons pour les médias
- Recherche fuzzy avancée
- Webhooks pour les changements d'entités

### Version 2.0 (planifiée)
- Support complet de l'édition Wikidata
- Gestion des conflits de modification
- Authentification OAuth pour les modifications
- API GraphQL en complément de SPARQL