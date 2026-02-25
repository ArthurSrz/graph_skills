#!/bin/bash

# Script wrapper pour MCP Wikidata - pour compatibilité Claude Desktop
# Détecte automatiquement l'environnement et lance le serveur

set -e

# Obtenir le répertoire du script (permet l'installation dans n'importe quel dossier)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Aller dans le répertoire du projet
cd "$SCRIPT_DIR"

# Variables d'environnement pour Wikidata
export WIKIDATA_USER_AGENT="${WIKIDATA_USER_AGENT:-Claude-Desktop-MCP-Wikidata/0.1.0}"

# Essayer de trouver uv dans différents emplacements courants
UV_PATHS=(
    "$HOME/.local/bin/uv"
    "$HOME/.cargo/bin/uv" 
    "/usr/local/bin/uv"
    "/opt/homebrew/bin/uv"
    "$(which uv 2>/dev/null)"
)

UV_CMD=""
for uv_path in "${UV_PATHS[@]}"; do
    if [[ -n "$uv_path" && -x "$uv_path" ]]; then
        UV_CMD="$uv_path"
        break
    fi
done

if [[ -z "$UV_CMD" ]]; then
    echo "Erreur: uv n'est pas trouvé. Veuillez installer uv: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

# Filtrer les arguments redondants que MCP Inspector peut passer
FILTERED_ARGS=()
for arg in "$@"; do
    # Ignorer les arguments qui sont déjà dans notre commande
    if [[ "$arg" != "run" && "$arg" != "mcp-wikidata" ]]; then
        FILTERED_ARGS+=("$arg")
    fi
done

# Lancer le serveur MCP
exec "$UV_CMD" run mcp-wikidata "${FILTERED_ARGS[@]}"