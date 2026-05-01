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


def encrypt_with_age(data: str, passphrase: str) -> str:
    import base64
    import json
    import os
    import hashlib
    from cryptography.fernet import Fernet

    # Generate random salt
    salt = os.urandom(16)

    # Derive key using PBKDF2
    key = hashlib.pbkdf2_hmac('sha256', passphrase.encode(), salt, 100000, dklen=32)

    # Use Fernet (AES-128-CBC with HMAC)
    f = Fernet(base64.urlsafe_b64encode(key))
    encrypted = f.encrypt(data.encode())

    # Package with salt
    result = {
        'salt': base64.b64encode(salt).decode(),
        'data': base64.b64encode(encrypted).decode()
    }
    return base64.b64encode(json.dumps(result).encode()).decode()


def decrypt_with_age(encrypted_data: str, passphrase: str) -> str:
    import base64
    import json
    import hashlib
    from cryptography.fernet import Fernet

    # Decode wrapper
    wrapper = json.loads(base64.b64decode(encrypted_data.encode()).decode())

    # Derive key
    salt = base64.b64decode(wrapper['salt'])
    key = hashlib.pbkdf2_hmac('sha256', passphrase.encode(), salt, 100000, dklen=32)

    # Decrypt
    f = Fernet(base64.urlsafe_b64encode(key))
    decrypted = f.decrypt(base64.b64decode(wrapper['data']))
    return decrypted.decode()


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

    token_encrypted = encrypt_with_age(json.dumps(credential_data), passphrase)

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


def unlock(args=None):
    if args is None:
        args = []

    if not USER_CONFIG_PATH.exists():
        print("❌ User-config non trovato. Esegui prima 'am config init'")
        return

    if not ACCOUNTS_FILE.exists():
        print("❌ accounts.json non trovato. Esegui prima 'am config init'")
        return

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--passphrase", "-p", help="Passphrase per sbloccare")
    parsed, _ = parser.parse_known_args(args)
    args_passphrase = parsed.passphrase if parsed else None

    print("\n🔓 Sblocco credentials...")
    if args_passphrase:
        passphrase = args_passphrase
    else:
        passphrase = questionary.password("Inserisci la passphrase:").ask()

    RUNTIME_PATH.mkdir(parents=True, exist_ok=True)
    (RUNTIME_PATH / "github").mkdir(parents=True, exist_ok=True)

    accounts = load_accounts()
    unlocked = []
    failed = []

    (RUNTIME_PATH / "ssh" / "keys").mkdir(parents=True, exist_ok=True)

    for name, info in accounts.get("credentials", {}).items():
        cred_file = USER_CONFIG_PATH / info["credential"]
        if cred_file.exists():
            try:
                encrypted_content = cred_file.read_text()
                decrypted = decrypt_with_age(encrypted_content, passphrase)

                cred_data = json.loads(decrypted)

                if cred_data.get("type") == "github":
                    runtime_file = RUNTIME_PATH / "github" / f"{name}.token"
                    runtime_file.write_text(cred_data["token"])
                    unlocked.append(name)
                    print(f"   ✅ {name} (GitHub HTTPS)")
                elif cred_data.get("type") == "ssh":
                    private_key_file = RUNTIME_PATH / "ssh" / "keys" / f"{name}.key"
                    public_key_file = RUNTIME_PATH / "ssh" / "keys" / f"{name}.pub"
                    private_key_file.write_text(cred_data.get("private_key", ""))
                    public_key_file.write_text(cred_data.get("public_key", ""))
                    private_key_file.chmod(0o600)
                    unlocked.append(name)
                    print(f"   ✅ {name} (SSH)")
                else:
                    print(f"   ⚠️ {name}: tipo non supportato")

            except Exception as e:
                failed.append(name)
                print(f"   ❌ {name}: errore decifrazione - {e}")
        else:
            print(f"   ⚠️ {name}: file non trovato ({info['credential']})")

    if unlocked:
        (RUNTIME_PATH / ".unlocked").touch()

        default = accounts.get("default")
        if default and (RUNTIME_PATH / "github" / f"{default}.token").exists():
            token = (RUNTIME_PATH / "github" / f"{default}.token").read_text()
            (RUNTIME_PATH / "git-credentials").write_text(f"https://x-access-token:{token}@github.com\n")
            subprocess.run(
                ["git", "config", "--global", "credential.helper", "store"],
                check=False
            )
            subprocess.run(
                ["git", "config", "--global", "credential.store", "/workspace/runtime/credentials/git-credentials"],
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
    # GitHub
    parser.add_argument("--token", help="Token GitHub")
    parser.add_argument("--github-user", help="Username GitHub")
    parser.add_argument("--github-email", help="Email GitHub")
    parser.add_argument("--owners", help="Owner (account/org separati da virgola)")
    # SSH
    parser.add_argument("--private-key-path", help="Path alla chiave privata SSH")
    parser.add_argument("--public-key-path", help="Path alla chiave pubblica SSH")
    parser.add_argument("--hosts", help="Hosts per SSH (es. github.com,gitlab.com)")

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
    elif cred_type == "ssh":
        add_ssh_credential(parsed)
    else:
        print(f"❌ Tipo '{cred_type}' non ancora implementato.")
        print("   Usa 'am config add github' o 'am config add ssh'")


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

    if parsed.github_user:
        github_user = parsed.github_user
    else:
        github_user = questionary.text("Username GitHub:").ask()

    if parsed.github_email:
        github_email = parsed.github_email
    else:
        github_email = questionary.text("Email GitHub:").ask()

    if parsed.owners:
        owners = [s.strip() for s in parsed.owners.split(",")]
    else:
        owners_input = questionary.text("Owner (account/organizzazioni separati da virgola):", default=github_user).ask()
        owners = [s.strip() for s in owners_input.split(",") if s.strip()]

    if not owners:
        owners = [github_user]

    print("\n🔐 Cifratura del credential...")

    passphrase = questionary.password("Inserisci la passphrase:").ask()

    credential_data = {
        "type": "github",
        "auth_type": "https",
        "github_user": github_user,
        "github_email": github_email,
        "token": token,
        "owners": owners
    }

    token_encrypted = encrypt_with_age(json.dumps(credential_data), passphrase)

    (CREDENTIALS_PATH / "github").mkdir(parents=True, exist_ok=True)
    cred_file = CREDENTIALS_PATH / "github" / f"{name}.age"
    cred_file.write_text(token_encrypted)

    accounts["credentials"][name] = {
        "type": "github",
        "name": name,
        "credential": f"credentials/github/{name}.age",
        "description": description,
        "owners": owners,
        "created_at": datetime.now().isoformat() + "Z",
        "updated_at": datetime.now().isoformat() + "Z"
    }

    if not accounts.get("default"):
        accounts["default"] = name

    save_accounts(accounts)

    print(f"\n✅ Credential GitHub '{name}' aggiunto!")
    print(f"   Owners: {', '.join(owners)}")
    print(f"   Per attivarlo: am config unlock")
    print()


def add_ssh_credential(parsed):
    accounts = load_accounts()

    if parsed.name:
        name = parsed.name
    else:
        name = questionary.text("Nome del credential SSH:").ask()

    if not name:
        print("❌ Nome richiesto")
        return

    if name in accounts.get("credentials", {}):
        print(f"❌ Credential '{name}' esiste già")
        return

    if parsed.description:
        description = parsed.description
    else:
        description = questionary.text("Descrizione:", default=f"Credential SSH {name}").ask()

    if parsed.private_key_path:
        private_key = Path(parsed.private_key_path).read_text()
    else:
        private_key = questionary.text("Contenuto chiave privata SSH (o path):").ask()
        if Path(private_key).exists():
            private_key = Path(private_key).read_text()

    if parsed.public_key_path:
        public_key = Path(parsed.public_key_path).read_text()
    else:
        public_key = questionary.text("Contenuto chiave pubblica SSH (o path):").ask()
        if Path(public_key).exists():
            public_key = Path(public_key).read_text()

    passphrase = questionary.text("Passphrase chiave (vuoto se nessuna):", default="").ask()
    if passphrase == "":
        passphrase = None

    if parsed.hosts:
        hosts = [s.strip() for s in parsed.hosts.split(",")]
    else:
        hosts_input = questionary.text("Hosts (es. github.com,gitlab.com):", default="github.com").ask()
        hosts = [s.strip() for s in hosts_input.split(",") if s.strip()]

    print("\n🔐 Cifratura del credential SSH...")

    passphrase_for_encrypt = questionary.password("Inserisci la passphrase:").ask()

    credential_data = {
        "type": "ssh",
        "private_key": private_key,
        "public_key": public_key,
        "passphrase": passphrase,
        "hosts": hosts
    }

    token_encrypted = encrypt_with_age(json.dumps(credential_data), passphrase_for_encrypt)

    (CREDENTIALS_PATH / "ssh").mkdir(parents=True, exist_ok=True)
    cred_file = CREDENTIALS_PATH / "ssh" / f"{name}.age"
    cred_file.write_text(token_encrypted)

    accounts["credentials"][name] = {
        "type": "ssh",
        "name": name,
        "credential": f"credentials/ssh/{name}.age",
        "description": description,
        "hosts": hosts,
        "created_at": datetime.now().isoformat() + "Z",
        "updated_at": datetime.now().isoformat() + "Z"
    }

    save_accounts(accounts)

    print(f"\n✅ Credential SSH '{name}' aggiunto!")
    print(f"   Hosts: {', '.join(hosts)}")
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