import os
import sys
import subprocess
from pathlib import Path
import questionary

CONFIG_PATH = Path("/workspace/repos/config")
SECRETS_PATH = CONFIG_PATH / "secrets"


def init_config():
    print("\n" + "=" * 50)
    print("🤖 Amstero - Configurazione Iniziale")
    print("=" * 50 + "\n")

    choice = questionary.select(
        "Hai già un repository config su GitHub?",
        choices=[
            "Sì, voglio clonarlo",
            "No, voglio crearlo ora",
            "Esci"
        ]
    ).ask()

    if choice == "Esci":
        print("Operazione annullata.")
        return

    if choice == "Sì, voglio clonarlo":
        clone_existing_config()
    else:
        create_new_config()


def clone_existing_config():
    github_user = questionary.text("Il tuo username GitHub:").ask()
    token = questionary.password("Il tuo Personal Access Token:").ask()

    print("\n📋 Per creare il token su GitHub.com:")
    print("  1. Vai su github.com → Settings → Developer settings")
    print("  2. Personal access tokens → Fine-grained tokens")
    print("  3. Crea nuovo token:")
    print("     - Repository access: seleziona il repo 'config'")
    print("     - Permissions: Contents (Read/Write)")
    print()

    if not token:
        print("❌ Token richiesto per clonare.")
        return

    clone_url = f"https://{github_user}:{token}@github.com/{github_user}/config.git"

    try:
        config_path = Path("/workspace/repos/config")
        if config_path.exists():
            print("⚠️ La cartella config esiste già.")
            return

        print(f"📦 Clonando {github_user}/config...")
        subprocess.run(
            ["git", "clone", clone_url, str(config_path)],
            check=True
        )
        print("✅ Config clonato con successo!")

        apply_config(token)

    except subprocess.CalledProcessError as e:
        print(f"❌ Errore nel clone: {e}")
        print("💡 Controlla che il repo 'config' esista e che il token sia valido.")


def create_new_config():
    github_user = questionary.text("Il tuo username GitHub:").ask()
    token = questionary.password("Il tuo Personal Access Token:").ask()

    if not github_user or not token:
        print("❌ Username e token richiesti.")
        return

    print("\n" + "─" * 50)
    print("📋 ISTRUZIONI PER CREARE IL TOKEN:")
    print("─" * 50)
    print("1. Vai su https://github.com/settings/tokens")
    print("2. Clicca 'Generate new token' → 'Fine-grained token'")
    print("3. Configura:")
    print("   - Token name: amstero-config")
    print("   - Repository access: All repositories")
    print("   - Permissions → Contents: Read and write")
    print("4. Clicca 'Generate token' e copia la stringa")
    print("─" * 50 + "\n")

    confirm = questionary.confirm(
        "Hai già creato il token? Vuoi continuare?",
        default=True
    ).ask()

    if not confirm:
        print("Crea il token e poi riesegui il comando.")
        return

    local_name = questionary.text("Il tuo nome per git config:", default="Tuo Nome").ask()
    local_email = questionary.text("La tua email per git config:", default="tua@email.com").ask()

    print("\n📁 Creando struttura config locale...")

    CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    SECRETS_PATH.mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "init"], cwd=CONFIG_PATH, check=True)
    subprocess.run(["git", "config", "user.name", local_name], cwd=CONFIG_PATH, check=True)
    subprocess.run(["git", "config", "user.email", local_email], cwd=CONFIG_PATH, check=True)

    (SECRETS_PATH / "github_token").write_text(token)

    readme = f"""# Amstero User Config

Repository per la configurazione personale di Amstero.

## Contenuto

- `secrets/` - Token e chiavi (non committare in chiaro)
- `keys/` - Chiavi SSH
- `user/` - Profilo utente

## Note

Questo repo contiene dati sensibili. Non publicare mai secrets in chiaro.
"""
    (CONFIG_PATH / "README.md").write_text(readme)

    print("✅ Struttura creata!")

    print("\n📋 Per creare il repo su GitHub:")
    print(f"  1. Vai su https://github.com/new")
    print(f"  2. Repository name: config")
    print(f"  3. Visibility: Private")
    print(f"  4. NON selezionare 'Add a README file'")
    print(f"  5. Clicca 'Create repository'")
    print(f"  6. Poi esegui:")
    print(f"     cd /workspace/repos/config")
    print(f"     git remote add origin https://{github_user}:TOKEN@github.com/{github_user}/config.git")
    print(f"     git branch -M main")
    print(f"     git push -u origin main")

    print("\n💡 Alternativa: usa 'gh repo create config --private' dopo aver fatto gh auth login")

    apply_config(token)


def apply_config(token):
    print("\n⚙️ Applicando configurazione git...")

    token_file = SECRETS_PATH / "github_token"
    if token_file.exists():
        token_file.write_text(token)

    subprocess.run(
        ["git", "config", "--global", "credential.helper", "store"],
        check=False
    )

    cred_path = Path.home() / ".git-credentials"
    cred_path.parent.mkdir(parents=True, exist_ok=True)

    config_git = CONFIG_PATH / ".gitconfig"
    if config_git.exists():
        subprocess.run(
            ["git", "config", "--global", "include.path", str(config_git)],
            check=False
        )

    print("✅ Configurazione applicata!")

    print("\n" + "=" * 50)
    print("🎉 Setup completato!")
    print("=" * 50)
    print("\nProssimi passi:")
    print("  - Pusha il config su GitHub (se nuovo)")
    print("  - Prova: git clone di un altro repo")
    print("  - Esegui: am --help per vedere i comandi")
    print()