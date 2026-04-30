#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="${1:-$PWD}"
AMSTERO_CORE_REPO="${AMSTERO_CORE_REPO:-https://github.com/cdario79/amstero-core.git}"
AMSTERO_CORE_DIR="$WORKSPACE_DIR/repos/amstero-core-code"
CONFIG_DIR="$WORKSPACE_DIR/repos/config"

echo ""
echo "Amstero Bootstrap"
echo "================="
echo ""
echo "Workspace: $WORKSPACE_DIR"
echo "Core repo: $AMSTERO_CORE_REPO"
echo ""

# Normalize workspace directory
mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"

# Base folders
mkdir -p "$WORKSPACE_DIR/repos"
mkdir -p "$WORKSPACE_DIR/shared/logs"
mkdir -p "$WORKSPACE_DIR/shared/cache"
mkdir -p "$WORKSPACE_DIR/shared/tmp"
mkdir -p "$WORKSPACE_DIR/runtime/mounts"
mkdir -p "$WORKSPACE_DIR/runtime/sessions"
mkdir -p "$WORKSPACE_DIR/runtime/locks"
mkdir -p "$WORKSPACE_DIR/runtime/execution"

# Workspace marker
if [ ! -f "$WORKSPACE_DIR/.amstero-workspace" ]; then
  cat > "$WORKSPACE_DIR/.amstero-workspace" <<EOF
AMSTERO_WORKSPACE=1
VERSION=0.1.0
EOF
fi

# Clone Amstero Core
if [ ! -d "$AMSTERO_CORE_DIR/.git" ]; then
  if [ -d "$AMSTERO_CORE_DIR" ] && [ "$(ls -A "$AMSTERO_CORE_DIR" 2>/dev/null)" ]; then
    echo "ERRORE: $AMSTERO_CORE_DIR esiste ma non è un repository Git vuoto."
    echo "Rimuovilo o spostalo prima di continuare."
    exit 1
  fi

  echo "Clono Amstero Core in repos/amstero-core-code..."
  git clone "$AMSTERO_CORE_REPO" "$AMSTERO_CORE_DIR"
else
  echo "Amstero Core già presente: repos/amstero-core-code"
fi

# Init user config repo
mkdir -p "$CONFIG_DIR"

if [ ! -d "$CONFIG_DIR/.git" ]; then
  echo "Inizializzo repo config utente in repos/config..."
  git -C "$CONFIG_DIR" init
else
  echo "Repo config già inizializzato: repos/config"
fi

mkdir -p "$CONFIG_DIR/registry"
mkdir -p "$CONFIG_DIR/user"
mkdir -p "$CONFIG_DIR/secrets/clients"
mkdir -p "$CONFIG_DIR/ssh"
mkdir -p "$CONFIG_DIR/env/projects"

if [ ! -f "$CONFIG_DIR/registry/projects.json" ]; then
  cat > "$CONFIG_DIR/registry/projects.json" <<'EOF'
{
  "projects": {
    "amstero-core": {
      "code_repo": "repos/amstero-core-code",
      "spec_repo": "repos/amstero-core-spec",
      "type": "system",
      "role": "Core Amstero",
      "linked_projects": []
    }
  }
}
EOF
fi

if [ ! -f "$CONFIG_DIR/user/preferences.json" ]; then
  cat > "$CONFIG_DIR/user/preferences.json" <<'EOF'
{
  "default_editor": "opencode",
  "default_shell": "bash",
  "workspace_view": "virtual"
}
EOF
fi

if [ ! -f "$CONFIG_DIR/.gitignore" ]; then
  cat > "$CONFIG_DIR/.gitignore" <<'EOF'
# Non salvare mai segreti in chiaro
*.plain
*.local
*.decrypted
*.key
id_rsa
id_ed25519

# File temporanei
.DS_Store
tmp/
cache/
EOF
fi

if [ ! -f "$CONFIG_DIR/README.md" ]; then
  cat > "$CONFIG_DIR/README.md" <<'EOF'
# Amstero Config

Questo repository contiene la configurazione personale del workspace Amstero.

Può essere collegato a un repository remoto dell’utente.

## Contenuto

- `registry/projects.json` → elenco progetti e repo collegati
- `user/preferences.json` → preferenze locali
- `secrets/` → segreti cifrati
- `ssh/` → chiavi o configurazioni SSH cifrate
- `env/` → file ambiente cifrati

## Regola di sicurezza

Non committare mai password, token o chiavi private in chiaro.

Usare file cifrati, ad esempio con:

```text
sops + age
```
EOF
fi

# Commit iniziale config se non ci sono commit
if ! git -C "$CONFIG_DIR" rev-parse --verify HEAD >/dev/null 2>&1; then
  git -C "$CONFIG_DIR" add .
  git -C "$CONFIG_DIR" commit -m "init amstero config" >/dev/null 2>&1 || true
fi

# Run Amstero Core setup if available
if [ -f "$AMSTERO_CORE_DIR/setup.sh" ]; then
  echo "Eseguo setup di Amstero Core..."
  bash "$AMSTERO_CORE_DIR/setup.sh" "$WORKSPACE_DIR"
else
  echo "setup.sh non trovato in Amstero Core. Nessun problema per ora."
fi

echo ""
echo "Workspace Amstero pronto."
echo ""
echo "Struttura principale:"
echo "  repos/                  repository reali"
echo "  repos/amstero-core-code core del sistema"
echo "  repos/config            configurazione utente"
echo "  shared/                 cache, log, temporanei"
echo "  runtime/                stato vivo rigenerabile"
echo ""
echo "Prossimi comandi consigliati:"
echo "  cd "$WORKSPACE_DIR""
echo "  cd repos/config"
echo "  git remote add origin <TUO_REPO_CONFIG>"
echo "  git push -u origin main"
echo ""
