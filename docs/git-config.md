# Configurazione Git e Token GitHub

## Il loop iniziale: come uscirne

C'è un problema: per clonare/scaricare il config da GitHub serve il token, ma il token sta nel config stesso. E per creare il config su GitHub serve il token.

**Soluzione**: il token lo crei su GitHub.com (fuori dal container) e poi lo passi al container.

### Passo 1: Crea il token su GitHub.com

1. Vai su **github.com** → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens**
2. Crea nuovo token:
   - **Name**: amstero-config
   - **Repository access**: Seleziona solo il repo `config` (quando lo crei)
   - **Permissions**: Contents: Read/Write
3. Copia il token (è una stringa come `ghp_xxxx`)

### Passo 2: Porta il token nel container

Una volta dentro il container:

```bash
# Crea il file con il token (incolla quello copiato sopra)
mkdir -p /workspace/repos/config/secrets
echo "ghp_xxxx" > /workspace/repos/config/secrets/github_token
```

---

## Prerequisiti

1. **Token GitHub**: Crealo su GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - Permissions: repo (read/write)
   - Scadenza: suggerito 1 anno

2. **gh CLI** (opzionale): Per creare repo da terminale
   ```bash
   apt update && apt install -y gh
   ```

---

## Scenario 1: Prima volta (creare config da zero)

### 1.1 Entrare nel container

```bash
docker compose exec -u root -it amstero-toolbox bash
```

### 1.2 Creare la struttura config

```bash
mkdir -p /workspace/repos/config/secrets
mkdir -p /workspace/repos/config/keys
```

### 1.3 Configurare git locale

```bash
cd /workspace/repos/config

# Inizializza git
git init

# Configura il tuo nome e email (senza virgolette, sostituisci i valori)
git config user.name TuoNome
git config user.email tua@email.com
```

### 1.4 Salvare il token GitHub

```bash
# Salva il token (sostituisci ghp_xxxx con il tuo token)
echo "ghp_xxxx" > /workspace/repos/config/secrets/github_token

# Oppure per gh CLI con token
echo "ghp_xxxx" > /workspace/repos/config/secrets/gh_token
```

### 1.5 Configurare git per usare il token

```bash
# Metodo 1: Credential helper
echo "https://tuousername:ghp_xxxx@github.com" > ~/.git-credentials
git config --global credential.helper store

# Metodo 2: gh auth (usa il token)
gh auth login --with-token < /workspace/repos/config/secrets/gh_token
```

### 1.6 Creare il repo GitHub

```bash
# Usa gh CLI (avrai prima fatto gh auth login come sopra)
cd /workspace/repos/config
gh repo create config --private --source=. --push
```

O manualmente:
- Vai su GitHub.com → New repository
- Nome: `config`
- Privato: sì
- Non inizializzare con README
- Segui le istruzioni per push

### 1.7 Struttura finale config

```
repos/config/
├── .git/
├── .gitconfig
├── README.md
├── secrets/
│   └── github_token
└── keys/
    └── github_ssh (opzionale)
```

---

## Scenario 2: Config già esistente (clonare da GitHub)

### 2.1 Entrare nel container

```bash
docker compose exec -u root -it amstero-toolbox bash
```

### 2.2 Clonare il repo config

```bash
cd /workspace/repos
# Sostituisci con il tuo username e token
git clone https://tuousername:ghp_xxxx@github.com/tuousername/config.git config
```

### 2.3 Applicare la configurazione git

```bash
cd /workspace/repos/config

# Usa le credenziali dal config
git config user.name $(git config --local user.name)
git config user.email $(git config --local user.email)

# Configura credential helper
git config --global credential.helper store
echo "https://tuousername:ghp_xxxx@github.com" > ~/.git-credentials
```

---

## Verifica configurazione

```bash
# Verifica git config
git config --list

# Test connessione GitHub
gh auth status

# Test cloning
git ls-remote https://github.com/tuousername/altro-repo.git
```

---

## Struttura consigliata del repo config

```
config/
├── .gitconfig
├── README.md
├── secrets/
│   ├── github_token
│   └── gh_token
├── keys/
│   ├── github_ssh
│   └── known_hosts
├── user/
│   └── profile.json
└── preferences.json
```

Il file `.gitconfig` nel repo:

```ini
[user]
    name = TuoNome
    email = tua@email.com

[core]
    sshCommand = ssh -o StrictHostKeyChecking=no -i keys/github_ssh

[credential "https://github.com"]
    helper = store
```

---

## Note di sicurezza

- **Mai** committare secrets in chiaro su Git
- Il token nel repo config dovrebbe essere cifrato (es. con `sops` + `age`)
- Alternativa: usare SSH keys invece di token
- `.gitignore` deve includere `secrets/`