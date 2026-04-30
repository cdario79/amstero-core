import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
import questionary
from datetime import datetime

USER_CONFIG_PATH = Path("/workspace/repos/amstero-user-config")
CREDENTIALS_PATH = USER_CONFIG_PATH / "credentials"
RUNTIME_PATH = Path("/workspace/runtime/credentials")
ACCOUNTS_FILE = USER_CONFIG_PATH / "accounts.json"


def load_accounts():
    if not ACCOUNTS_FILE.exists():
        return {"version": "1.0", "credentials": {}, "default": None}
    with open(ACCOUNTS_FILE) as f:
        return json.load(f)


def save_accounts(accounts):
    ACCOUNTS_FILE.write_text(json.dumps(accounts, indent=2))


def init_config():
    print("\n" + "=" * 50)
    print("🤖 Amstero - Setup User Config")
    print("=" * 50 + "\n")

    choice = questionary.select(
        "Hai già un repository amstero-user-config su GitHub?",
        choices=[
            "Sì, voglio clonarlo",
            "No, voglio crearlo ora",
            "Esci"
        ]
    ).ask()

    if choice == "Esci":
        return

    if choice == "Sì, voglio clonarlo":
        clone_existing_config()
    else:
        create_new_config()

    print("\n🔐 Configurazione completata!")
    print("   Ora esegui: am config unlock")
    print()


def clone_existing_config():
    github_user = questionary.text("Il tuo username GitHub:").ask()
    repo_name = questionary.text("Nome del repository:", default="amstero-user-config").ask()
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

    clone_url = f"https://github.com/{github_user}/{repo_name}.git"

    try:
        if USER_CONFIG_PATH.exists():
            print("⚠️ La cartella amstero-user-config esiste già.")
            return

        print(f"📦 Clonando {github_user}/{repo_name}...")

        result = subprocess.run(
            ["git", "clone", clone_url, str(USER_CONFIG_PATH)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ Errore nel clone: {result.stderr}")
            print("💡 Prova con il token nell'URL:")
            clone_url = f"https://{github_user}:{token}@github.com/{github_user}/{repo_name}.git"
            subprocess.run(
                ["git", "clone", clone_url, str(USER_CONFIG_PATH)],
                check=True
            )

        print("✅ User-config clonato con successo!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Errore nel clone: {e}")
        print("💡 Controlla che il repo '{}' esista e che il token sia valido.".format(repo_name))


def create_new_config():
    github_user = questionary.text("Il tuo username GitHub:").ask()
    repo_name = questionary.text("Nome del repository:", default="amstero-user-config").ask()
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

    print("\n📁 Creando struttura amstero-user-config locale...")

    USER_CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    (CREDENTIALS_PATH / "github").mkdir(parents=True, exist_ok=True)
    (USER_CONFIG_PATH / "user").mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "init"], cwd=USER_CONFIG_PATH, check=True)
    subprocess.run(["git", "config", "user.name", github_user], cwd=USER_CONFIG_PATH, check=True)
    subprocess.run(["git", "config", "user.email", f"{github_user}@github.local"], cwd=USER_CONFIG_PATH, check=True)

    cred_name = questionary.text(
        "Nome per questo credential:",
        default="personal"
    ).ask()

    cred_description = questionary.text(
        "Descrizione (es. token globale, repo config, etc.):",
        default=f"Token per {repo_name}"
    ).ask()

    passphrase = questionary.password(
        "Scegli una passphrase per cifrare i token:",
        validate=lambda x: len(x) >= 8 or "Minimo 8 caratteri"
    ).ask()

    passphrase_confirm = questionary.password(
        "Conferma la passphrase:",
    ).ask()

    if passphrase != passphrase_confirm:
        print("❌ Le passphrase non coincidono.")
        return

    print("\n🔐 Creando struttura con passphrase...")

    credential_data = {
        "type": "github",
        "token": token,
        "scope": ["*"]
    }

    token_encrypted = subprocess.run(
        ["age", "--passphrase", "-p"],
        input=json.dumps(credential_data),
        capture_output=True,
        text=True
    ).stdout

    cred_file = CREDENTIALS_PATH / "github" / f"{cred_name}.age"
    cred_file.write_text(token_encrypted)

    accounts = {
        "version": "1.0",
        "default": cred_name,
        "credentials": {
            cred_name: {
                "type": "github",
                "name": cred_name,
                "credential": f"credentials/github/{cred_name}.age",
                "description": cred_description,
                "scope": ["*"],
                "created_at": datetime.now().isoformat() + "Z",
                "updated_at": datetime.now().isoformat() + "Z"
            }
        }
    }
    ACCOUNTS_FILE.write_text(json.dumps(accounts, indent=2))

    (USER_CONFIG_PATH / "README.md").write_text("""# Amstero User Config

Repository per la configurazione personale di Amstero.

## Struttura

- `credentials/` - Token cifrati con age (file .age)
  - `github/` - Credential GitHub
  - `ssh/` - Credential SSH
  - `database/` - Credential Database
  - `ftp/` - Credential FTP
  - `api/` - Credential API
- `accounts.json` - Indice dei credential
- `user/` - Profilo utente

## Sicurezza

I file `.age` sono cifrati con passphrase. Non committare mai:
- Token in chiaro
- File senza cifratura

## Primo setup

1. Clona questo repo nel container
2. Esegui `am config unlock` e inserisci la passphrase
3. I token saranno disponibili per git/gh

## Aggiungere nuovi credential

`am config add` - Aggiunge un nuovo credential
`am config add github` - Aggiunge credential GitHub
""")

    (USER_CONFIG_PATH / ".gitignore").write_text("""credentials/*.age
credentials/github/*.age
credentials/ssh/*.age
credentials/database/*.age
credentials/ftp/*.age
credentials/api/*.age
!credentials/README.md
""")

    print("✅ Struttura creata!")

    print("\n📦 Creando repository su GitHub...")
    try:
        subprocess.run(
            ["gh", "auth", "login", "--with-token"],
            input=token,
            text=True,
            check=True
        )
        subprocess.run(
            ["gh", "repo", "create", repo_name, "--private", "--source=.", "--push"],
            cwd=USER_CONFIG_PATH,
            check=True
        )
        print(f"✅ Repo '{repo_name}' creato e pushato!")
    except subprocess.CalledProcessError:
        print(f"❌ Errore nella creazione del repo su GitHub")
        print(f"💡 Puoi crearlo manualmente su github.com/new")

    print("\n" + "=" * 50)
    print("🎉 Setup completato!")
    print("=" * 50)
    print(f"\n✅ Ricorda la passphrase: {passphrase}")
    print("   Ti servirà per sbloccare i token ad ogni sessione.")
    print()


def unlock():
    if not USER_CONFIG_PATH.exists():
        print("❌ User-config non trovato. Esegui prima 'am config init'")
        return

    if not ACCOUNTS_FILE.exists():
        print("❌ accounts.json non trovato. Esegui prima 'am config init'")
        return

    print("\n🔓 Sblocco credentials...")
    passphrase = questionary.password("Inserisci la passphrase:").ask()

    RUNTIME_PATH.mkdir(parents=True, exist_ok=True)
    (RUNTIME_PATH / "github").mkdir(parents=True, exist_ok=True)

    accounts = load_accounts()
    unlocked = []
    failed = []

    for name, info in accounts.get("credentials", {}).items():
        cred_file = USER_CONFIG_PATH / info["credential"]
        if cred_file.exists():
            try:
                decrypted = subprocess.run(
                    ["age", "-d", "-p"],
                    input=passphrase,
                    capture_output=True,
                    text=True,
                    stdin=open(str(cred_file))
                ).stdout.strip()

                cred_data = json.loads(decrypted)

                if cred_data.get("type") == "github":
                    runtime_file = RUNTIME_PATH / "github" / f"{name}.token"
                    runtime_file.write_text(cred_data["token"])
                    unlocked.append(name)
                    print(f"   ✅ {name} (GitHub)")
                else:
                    print(f"   ⚠️ {name}: tipo non supportato")

            except Exception as e:
                failed.append(name)
                print(f"   ❌ {name}: errore decifrazione")
        else:
            print(f"   ⚠️ {name}: file non trovato ({info['credential']})")

    if unlocked:
        (RUNTIME_PATH / ".unlocked").touch()

        default = accounts.get("default")
        if default and (RUNTIME_PATH / "github" / f"{default}.token").exists():
            token = (RUNTIME_PATH / "github" / f"{default}.token").read_text()
            (RUNTIME_PATH / "git-credentials").write_text(f"https://x-access-token:{token}@github.com\n")
            subprocess.run(
                ["git", "config", "--global", "credential.helper", "store --file /workspace/runtime/credentials/git-credentials"],
                shell=True,
                check=False
            )
            print("✅ Git credential helper configurato!")

        print(f"\n✅ Sbloccati {len(unlocked)} credential")
    else:
        print("❌ Nessun credential sbloccato")

    print()


def lock():
    if not RUNTIME_PATH.exists():
        print("ℹ️ Nessun credential da bloccare.")
        return

    import shutil
    for subdir in ["github", "ssh", "database", "ftp", "api"]:
        subpath = RUNTIME_PATH / subdir
        if subpath.exists():
            for f in subpath.glob("*"):
                if f.is_file():
                    f.unlink()

    git_creds = RUNTIME_PATH / "git-credentials"
    if git_creds.exists():
        git_creds.unlink()

    unlocked_file = RUNTIME_PATH / ".unlocked"
    if unlocked_file.exists():
        unlocked_file.unlink()

    print("🔒 Credentials bloccati!")
    print()


def status():
    if not USER_CONFIG_PATH.exists():
        print("❌ User-config non configurato")
        return

    print("\n📊 Status User Config")
    print("─" * 30)

    if not ACCOUNTS_FILE.exists():
        print("⚠️ accounts.json non trovato")
        return

    accounts = load_accounts()

    print(f"📁 Path: {USER_CONFIG_PATH}")
    print(f"📋 Credential definiti: {len(accounts.get('credentials', {}))}")
    print(f"⭐ Default: {accounts.get('default', 'N/A')}")
    print()

    print("Credential:")
    for name, info in accounts.get("credentials", {}).items():
        is_unlocked = (RUNTIME_PATH / info.get("type", "github") / f"{name}.token").exists() if RUNTIME_PATH.exists() else False
        status_icon = "🔓" if is_unlocked else "🔒"
        print(f"  {status_icon} {name} ({info.get('type', 'N/A')})")
        print(f"      {info.get('description', 'N/A')}")
        print(f"      file: {info.get('credential', 'N/A')}")

    print()
    is_unlocked = RUNTIME_PATH.exists() and (RUNTIME_PATH / ".unlocked").exists()
    print(f"Stato sessione: {'🔓 Sbloccato' if is_unlocked else '🔒 Bloccato'}")
    print()


def add_credential(args=None):
    if not USER_CONFIG_PATH.exists():
        print("❌ User-config non configurato. Esegui prima 'am config init'")
        return

    parser = argparse.ArgumentParser(description="Aggiungi credential")
    parser.add_argument("--type", "-t", choices=["github", "ssh", "database", "ftp", "api"],
                        help="Tipo di credential")
    parser.add_argument("--name", "-n", help="Nome del credential")
    parser.add_argument("--description", "-d", help="Descrizione")
    parser.add_argument("--token", help="Token GitHub (solo per type=github)")
    parser.add_argument("--scope", help="Scope GitHub separati da virgola (solo per type=github)")
    parser.add_argument("--org", help="Organizzazione GitHub (opzionale)")

    parsed = parser.parse_args(args if args else [])

    if parsed.type:
        cred_type = parsed.type
    else:
        cred_type = questionary.select(
            "Tipo di credential:",
            choices=["GitHub", "SSH", "Database", "FTP", "API", "Esci"]
        ).ask()

        if cred_type == "Esci":
            return

        cred_type = cred_type.lower()

    if cred_type == "github":
        add_github_credential(parsed)
    else:
        print(f"❌ Tipo '{cred_type}' non ancora implementato.")
        print("   Per ora è disponibile solo GitHub.")
        print("   Usa 'am config add github' per aggiungere un credential GitHub.")


def add_github_credential(parsed):
    accounts = load_accounts()

    if parsed.name:
        name = parsed.name
    else:
        name = questionary.text("Nome del credential:").ask()

    if not name:
        print("❌ Nome richiesto")
        return

    if name in accounts.get("credentials", {}):
        print(f"❌ Credential '{name}' esiste già")
        return

    if parsed.description:
        description = parsed.description
    else:
        description = questionary.text("Descrizione:", default=f"Credential GitHub {name}").ask()

    if parsed.token:
        token = parsed.token
    else:
        token = questionary.password("Token GitHub:").ask()

    if not token:
        print("❌ Token richiesto")
        return

    if parsed.scope:
        scope = [s.strip() for s in parsed.scope.split(",")]
    else:
        scope_input = questionary.text("Scope (repo separati da virgola, * per tutti):", default="*").ask()
        scope = [s.strip() for s in scope_input.split(",")]

    org = parsed.org
    if not org:
        org = questionary.text("Organizzazione (opzionale):").ask()
        if org == "":
            org = None

    print("\n🔐 Cifratura del credential...")

    passphrase = questionary.password("Inserisci la passphrase:").ask()

    credential_data = {
        "type": "github",
        "token": token,
        "scope": scope,
        "org": org
    }

    token_encrypted = subprocess.run(
        ["age", "--passphrase", "-p"],
        input=json.dumps(credential_data),
        capture_output=True,
        text=True
    ).stdout

    (CREDENTIALS_PATH / "github").mkdir(parents=True, exist_ok=True)
    cred_file = CREDENTIALS_PATH / "github" / f"{name}.age"
    cred_file.write_text(token_encrypted)

    accounts["credentials"][name] = {
        "type": "github",
        "name": name,
        "credential": f"credentials/github/{name}.age",
        "description": description,
        "scope": scope,
        "org": org,
        "created_at": datetime.now().isoformat() + "Z",
        "updated_at": datetime.now().isoformat() + "Z"
    }

    if not accounts.get("default"):
        accounts["default"] = name

    save_accounts(accounts)

    print(f"\n✅ Credential '{name}' aggiunto!")
    print(f"   File: {cred_file}")
    print(f"   Tipo: GitHub")
    print(f"   Per attivarlo: am config unlock")
    print()


def list_credentials():
    if not USER_CONFIG_PATH.exists():
        print("❌ User-config non configurato")
        return

    if not ACCOUNTS_FILE.exists():
        print("⚠️ Nessun account definito")
        return

    accounts = load_accounts()
    cred_type = None

    print("\n📋 Credentials:")
    for name, info in accounts.get("credentials", {}).items():
        is_unlocked = (RUNTIME_PATH / info.get("type", "github") / f"{name}.token").exists() if RUNTIME_PATH.exists() else False
        status = "🔓" if is_unlocked else "🔒"
        print(f"  {status} {name}")
        print(f"      tipo: {info.get('type', 'N/A')}")
        print(f"      {info.get('description', 'N/A')}")
        print(f"      scope: {info.get('scope', [])}")

    print()


def remove_credential(args=None):
    if not USER_CONFIG_PATH.exists():
        print("❌ User-config non configurato")
        return

    if not ACCOUNTS_FILE.exists():
        print("⚠️ Nessun account definito")
        return

    accounts = load_accounts()

    parser = argparse.ArgumentParser(description="Rimuovi credential")
    parser.add_argument("name", help="Nome del credential da rimuovere")
    parsed = parser.parse_args(args if args else [])

    name = parsed.name if parsed.name else questionary.text("Nome del credential da rimuovere:").ask()

    if not name:
        print("❌ Nome richiesto")
        return

    if name not in accounts.get("credentials", {}):
        print(f"❌ Credential '{name}' non trovato")
        return

    cred_info = accounts["credentials"][name]
    cred_file = USER_CONFIG_PATH / cred_info["credential"]

    confirm = questionary.confirm(
        f"Vuoi rimuovere il credential '{name}'?",
        default=True
    ).ask()

    if not confirm:
        return

    if cred_file.exists():
        cred_file.unlink()

    del accounts["credentials"][name]

    if accounts.get("default") == name:
        accounts["default"] = list(accounts["credentials"].keys())[0] if accounts["credentials"] else None

    save_accounts(accounts)

    print(f"✅ Credential '{name}' rimosso!")
    print()