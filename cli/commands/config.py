import os
import sys
import subprocess
import json
from pathlib import Path
import questionary

USER_CONFIG_PATH = Path("/workspace/repos/amstero-user-config")
CREDENTIALS_PATH = USER_CONFIG_PATH / "credentials"
RUNTIME_PATH = Path("/workspace/runtime/credentials")
ACCOUNTS_FILE = USER_CONFIG_PATH / "accounts.json"
RUNTIME_LOCK_FILE = RUNTIME_PATH / ".locked"


def init_config():
    print("\n" + "=" * 50)
    print("🤖 Amstero - Setup User Config")
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

    print("\n📁 Creando struttura user-config locale...")

    USER_CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_PATH.mkdir(parents=True, exist_ok=True)
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

    token_encrypted = subprocess.run(
        ["age", "--passphrase", "-p"],
        input=token,
        capture_output=True,
        text=True
    ).stdout

    (CREDENTIALS_PATH / f"{cred_name}.age").write_text(token_encrypted)

    accounts = {
        "accounts": {
            cred_name: {
                "type": "user",
                "credential": f"credentials/{cred_name}.age",
                "scope": ["*"],
                "description": cred_description
            }
        },
        "default": cred_name
    }
    ACCOUNTS_FILE.write_text(json.dumps(accounts, indent=2))

    (USER_CONFIG_PATH / "README.md").write_text("""# Amstero User Config

Repository per la configurazione personale di Amstero.

## Struttura

- `credentials/` - Token cifrati con age (file .age)
- `accounts.json` - Definizione degli account
- `user/` - Profilo utente

## Sicurezza

I file `.age` sono cifrati con passphrase. Non committare mai:
- Token in chiaro
- File senza cifratura

## Primo setup

1. Clona questo repo nel container
2. Esegui `am config unlock` e inserisci la passphrase
3. I token saranno disponibili per git/gh

## Aggiungere nuovi token

`am config add` - Aggiunge un nuovo credential
""")

    (USER_CONFIG_PATH / ".gitignore").write_text("""credentials/*.age
!credentials/README.md
""")

    (CREDENTIALS_PATH / "README.md").write_text("""# Credentials

Questa cartella contiene i token cifrati.

I file .age sono protetti con passphrase.
Non committare file non cifrati.
""")

    print("✅ Struttura creata!")

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
        print(f"💡 Puoi crearlo manualmente su github.com/new")
        print(f"   Poi esegui: cd {USER_CONFIG_PATH} && git remote add origin ...")

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

    with open(ACCOUNTS_FILE) as f:
        accounts = json.load(f)

    unlocked = []
    failed = []

    for name, info in accounts.get("accounts", {}).items():
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

                runtime_file = RUNTIME_PATH / f"{name}.token"
                runtime_file.write_text(decrypted)
                unlocked.append(name)
                print(f"   ✅ {name}")
            except Exception as e:
                failed.append(name)
                print(f"   ❌ {name}: errore decifrazione")
        else:
            print(f"   ⚠️ {name}: file non trovato ({info['credential']})")

    if unlocked:
        RUNTIME_PATH.joinpath(".unlocked").touch()
        print(f"\n✅ Sbloccati {len(unlocked)} credential")

        cred_helper = f"store --file /workspace/runtime/credentials/git-credentials"
        subprocess.run(["git", "config", "--global", "credential.helper", cred_helper], check=False)

        with open(RUNTIME_PATH / "git-credentials", "w") as f:
            for name in unlocked:
                token = (RUNTIME_PATH / f"{name}.token").read_text()
                f.write(f"https://x-access-token:{token}@github.com\n")

        print("✅ Git credential helper configurato!")
    else:
        print("❌ Nessun credential sbloccato")

    print()


def lock():
    if not RUNTIME_PATH.exists():
        print("ℹ️ Nessun credential da bloccare.")
        return

    for f in RUNTIME_PATH.glob("*.token"):
        f.unlink()

    git_creds = RUNTIME_PATH / "git-credentials"
    if git_creds.exists():
        git_creds.unlink()

    locked = RUNTIME_PATH.joinpath(".locked")
    locked.touch()

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

    with open(ACCOUNTS_FILE) as f:
        accounts = json.load(f)

    print(f"📁 Path: {USER_CONFIG_PATH}")
    print(f"📋 Account definiti: {len(accounts.get('accounts', {}))}")
    print(f"⭐ Default: {accounts.get('default', 'N/A')}")
    print()

    print("Account:")
    for name, info in accounts.get("accounts", {}).items():
        locked = not (RUNTIME_PATH / f"{name}.token").exists() if RUNTIME_PATH.exists() else True
        status_icon = "🔒" if locked else "🔓"
        print(f"  {status_icon} {name}")
        print(f"      {info.get('description', 'N/A')}")
        print(f"      credential: {info.get('credential', 'N/A')}")

    print()
    is_unlocked = RUNTIME_PATH.exists() and (RUNTIME_PATH / ".unlocked").exists()
    print(f"Stato sessione: {'🔓 Sbloccato' if is_unlocked else '🔒 Bloccato'}")
    print()


def add_credential():
    if not USER_CONFIG_PATH.exists():
        print("❌ User-config non configurato. Esegui prima 'am config init'")
        return

    name = questionary.text("Nome del credential (es. cliente-x, mia-org):").ask()
    if not name:
        print("❌ Nome richiesto")
        return

    description = questionary.text("Descrizione (es. token per repo cliente):", default=f"Credential {name}").ask()
    scope = questionary.text("Scope (es. * per tutti, oppure nome repo specifico):", default="*").ask()

    token = questionary.password("Token GitHub:").ask()
    if not token:
        print("❌ Token richiesto")
        return

    print("\n🔐 Cifrazione del token...")

    passphrase = questionary.password("Inserisci la passphrase:").ask()

    token_encrypted = subprocess.run(
        ["age", "--passphrase", "-p"],
        input=token,
        capture_output=True,
        text=True
    ).stdout

    cred_file = CREDENTIALS_PATH / f"{name}.age"
    cred_file.write_text(token_encrypted)

    with open(ACCOUNTS_FILE) as f:
        accounts = json.load(f)

    accounts["accounts"][name] = {
        "type": "user",
        "credential": f"credentials/{name}.age",
        "scope": [scope] if scope != "*" else ["*"],
        "description": description
    }

    ACCOUNTS_FILE.write_text(json.dumps(accounts, indent=2))

    print(f"\n✅ Credential '{name}' aggiunto!")
    print(f"   File: {cred_file}")
    print(f"   Per attivarlo: am config unlock")
    print()


def list_credentials():
    if not USER_CONFIG_PATH.exists():
        print("❌ User-config non configurato")
        return

    if not ACCOUNTS_FILE.exists():
        print("⚠️ Nessun account definito")
        return

    with open(ACCOUNTS_FILE) as f:
        accounts = json.load(f)

    print("\n📋 Credentials:")
    for name, info in accounts.get("accounts", {}).items():
        is_unlocked = (RUNTIME_PATH / f"{name}.token").exists() if RUNTIME_PATH.exists() else False
        status = "🔓" if is_unlocked else "🔒"
        print(f"  {status} {name}")
        print(f"      {info.get('description', 'N/A')}")
        print(f"      scope: {info.get('scope', [])}")

    print()