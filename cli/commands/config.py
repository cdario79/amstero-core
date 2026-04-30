import os
import sys
import subprocess
from pathlib import Path
import questionary

USER_CONFIG_PATH = Path("/workspace/repos/user-config")
SECRETS_PATH = USER_CONFIG_PATH / "secrets"


def init_config():
    print("\n" + "=" * 50)
    print("🤖 Amstero - Configurazione User Config")
    print("=" * 50 + "\n")

    choice = questionary.select(
        "Hai già un repository user-config su GitHub?",
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
    repo_name = questionary.text("Nome del repository:", default="user-config").ask()
    token = questionary.password("Il tuo Personal Access Token:").ask()

    print("\n📋 Per creare il token su GitHub.com:")
    print("  1. Vai su github.com → Settings → Developer settings")
    print("  2. Personal access tokens → Fine-grained tokens")
    print("  3. Crea nuovo token:")
    print("     - Repository access: seleziona il repo '{}'".format(repo_name))
    print("     - Permissions: Contents (Read/Write)")
    print()

    if not token:
        print("❌ Token richiesto per clonare.")
        return

    clone_url = f"https://{github_user}:{token}@github.com/{github_user}/{repo_name}.git"

    try:
        if USER_CONFIG_PATH.exists():
            print("⚠️ La cartella user-config esiste già.")
            return

        print(f"📦 Clonando {github_user}/{repo_name}...")
        subprocess.run(
            ["git", "clone", clone_url, str(USER_CONFIG_PATH)],
            check=True
        )
        print("✅ User-config clonato con successo!")

        decrypt_secrets(token)

    except subprocess.CalledProcessError as e:
        print(f"❌ Errore nel clone: {e}")
        print("💡 Controlla che il repo '{}' esista e che il token sia valido.".format(repo_name))


def create_new_config():
    github_user = questionary.text("Il tuo username GitHub:").ask()
    repo_name = questionary.text("Nome del repository:", default="user-config").ask()
    token = questionary.password("Il tuo Personal Access Token:").ask()

    if not github_user or not token or not repo_name:
        print("❌ Username, nome repo e token richiesti.")
        return

    print("\n" + "─" * 50)
    print("📋 ISTRUZIONI PER CREARE IL TOKEN:")
    print("─" * 50)
    print("1. Vai su https://github.com/settings/tokens")
    print("2. Clicca 'Generate new token' → 'Fine-grained token'")
    print("3. Configura:")
    print("   - Token name: amstero-{}".format(repo_name))
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

    print("\n📁 Creando struttura user-config locale...")

    USER_CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    SECRETS_PATH.mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "init"], cwd=USER_CONFIG_PATH, check=True)
    subprocess.run(["git", "config", "user.name", local_name], cwd=USER_CONFIG_PATH, check=True)
    subprocess.run(["git", "config", "user.email", local_email], cwd=USER_CONFIG_PATH, check=True)

    print("\n🔐 Generando chiave di cifratura...")
    key_path = USER_CONFIG_PATH / "secrets" / "age.key"
    subprocess.run(["age-keygen", "-o", str(key_path)], check=True, capture_output=True)

    public_key = subprocess.run(
        ["age-keygen", "-y", str(key_path)],
        capture_output=True, text=True
    ).stdout.strip()

    print("✅ Chiave di cifratura generata!")
    print(f"   Salva questa chiave in un posto sicuro:")
    print(f"   {public_key}")

    token_encrypted = subprocess.run(
        ["age", "-R", str(key_path)],
        input=token,
        capture_output=True,
        text=True
    ).stdout

    (SECRETS_PATH / "github_token.age").write_text(token_encrypted)

    readme = f"""# Amstero User Config

Repository per la configurazione personale di Amstero.

## Struttura

- `secrets/` - Token e chiavi cifrati con age
- `keys/` - Chiavi SSH
- `user/` - Profilo utente

## Sicurezza

I file in `secrets/` sono cifrati con age. Non publicare mai:
- File `.age` non cifrati
- Chiavi private (`age.key`)
- Token in chiaro
"""
    (USER_CONFIG_PATH / "README.md").write_text(readme)

    (USER_CONFIG_PATH / ".gitignore").write_text("""secrets/*.key
secrets/*.age
!secrets/README.md
""")

    print("✅ Struttura creata e token cifrato!")

    print("\n📦 Creando repository su GitHub...")
    try:
        subprocess.run(
            ["gh", "repo", "create", repo_name, "--private", "--source=.", "--push"],
            cwd=USER_CONFIG_PATH,
            input=f"{token}\n",
            text=True,
            check=True
        )
        print(f"✅ Repo '{repo_name}' creato e pushato!")
    except subprocess.CalledProcessError:
        print(f"❌ Errore nella creazione del repo su GitHub")
        print("💡 Puoi crearlo manualmente su github.com")
        print(f"   Poi esegui:")
        print(f"   cd {USER_CONFIG_PATH}")
        print(f"   git remote add origin https://{github_user}:TOKEN@github.com/{github_user}/{repo_name}.git")
        print(f"   git push -u origin main")

    print("\n🔐 IMPORTANTE: Salva la chiave di cifratura!")
    print("   La chiave in secrets/age.key serve per decifrare i token.")
    print("   Senza di essa non potrai recuperare i secrets.")
    print("   Consiglio: copiala e salvala in un password manager.")


def decrypt_secrets(token):
    print("\n🔐 Controllo secrets cifrati...")

    key_path = SECRETS_PATH / "age.key"
    token_encrypted = SECRETS_PATH / "github_token.age"

    if not key_path.exists():
        print("⚠️ Chiave di cifratura non trovata.")
        print("   Se è la prima volta che cloni, assicurati di avere la chiave.")
        return

    if token_encrypted.exists():
        try:
            decrypted = subprocess.run(
                ["age", "-d", "-i", str(key_path)],
                input=token_encrypted.read_text(),
                capture_output=True,
                text=True
            ).stdout.strip()

            (SECRETS_PATH / "github_token").write_text(decrypted)
            print("✅ Token decifrato e salvato!")
        except subprocess.CalledProcessError:
            print("❌ Errore nella decifrazione. Controlla la chiave.")

    print("\n⚙️ Applicando configurazione git...")

    subprocess.run(
        ["git", "config", "--global", "credential.helper", "store"],
        check=False
    )

    cred_path = Path.home() / ".git-credentials"
    cred_path.parent.mkdir(parents=True, exist_ok=True)
    cred_path.write_text(f"https://{token}:@github.com")

    config_git = USER_CONFIG_PATH / ".gitconfig"
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
    print("  - Prova: git clone di un altro repo")
    print("  - Esegui: am --help per vedere i comandi")
    print()