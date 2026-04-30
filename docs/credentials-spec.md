# Specifiche Sistema Credentials Amstero

## Panoramica

Il sistema di credentials di Amstero permette di gestire in modo sicuro e centralizzato credenziali per diversi servizi. Ogni credential è cifrato con `age` usando una passphrase unica (scelta durante `am config init`).

---

## Struttura Directory

```
amstero-user-config/
├── accounts.json                    # Indice di tutti i credential
├── credentials/
│   ├── github/
│   │   ├── personal.age
│   │   └── cliente-a.age
│   ├── ssh/
│   │   └── server-prod.age
│   ├── database/
│   │   └── prod.age
│   ├── ftp/
│   │   └── backup.age
│   └── api/
│       └── openai.age
└── config/
    └── credentials.schema.json
```

---

## accounts.json Schema

```json
{
  "version": "1.0",
  "default": "personal",
  "credentials": {
    "personal": {
      "type": "github",
      "name": "personal",
      "credential": "credentials/github/personal.age",
      "description": "Token globale per i miei repo",
      "scope": ["*"],
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    "cliente-a": {
      "type": "github",
      "name": "cliente-a",
      "credential": "credentials/github/cliente-a.age",
      "description": "Token per repo cliente A",
      "scope": ["cliente-a-repo1", "cliente-a-repo2"],
      "org": "nome-org-cliente",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    "prod-server": {
      "type": "ssh",
      "name": "prod-server",
      "credential": "credentials/ssh/prod-server.age",
      "description": "Accesso SSH server produzione",
      "host": "prod.example.com",
      "user": "deploy",
      "port": 22,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    "prod-db": {
      "type": "database",
      "name": "prod-db",
      "credential": "credentials/database/prod-db.age",
      "description": "Database produzione",
      "db_type": "postgresql",
      "host": "db.example.com",
      "port": 5432,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    "backup-ftp": {
      "type": "ftp",
      "name": "backup-ftp",
      "credential": "credentials/ftp/backup-ftp.age",
      "description": "FTP per backup",
      "host": "ftp.backup.com",
      "port": 21,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    "openai-key": {
      "type": "api",
      "name": "openai-key",
      "credential": "credentials/api/openai-key.age",
      "description": "API key OpenAI",
      "provider": "openai",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  }
}
```

---

## Tipo: GitHub

### Campi

| Campo | Tipo | Richiesto | Descrizione |
|-------|------|-----------|--------------|
| `token` | string | Sì | Personal Access Token GitHub |
| `scope` | array | Sì | Lista repo accessibili, `["*"]` per tutti |
| `org` | string | No | Organizzazione (se token org) |
| `description` | string | No | Descrizione del credential |

### Wizard Interattivo

```
? Tipo credential: GitHub
? Nome del credential: personal
? Descrizione: Token globale per i miei repo
? Scope (repo separati da virgola, * per tutti): *
? Organizzazione (opzionale):
? Token GitHub: ************************
🔐 Cifratura in corso...
✅ Credential 'personal' aggiunto!
```

### CLI

```bash
# Solo token con scope *
am config add github --name personal --token ghp_xxxx --scope "*" --description "Token globale"

# Token per organizzazione
am config add github --name my-org --token ghp_xxxx --org nome-org --scope "*"

# Token per repo specifici
am config add github --name cliente-a --token ghp_xxxx --scope "repo1,repo2"
```

### JSON Cifrato (contenuto in .age)

```json
{
  "type": "github",
  "token": "ghp_xxxxxxxxxxxxxxxxxxxx",
  "scope": ["*"],
  "org": null
}
```

### Runtime

- Token decifrato salvato in: `/workspace/runtime/credentials/github/<name>.token`
- Git credential helper configurato con token

---

## Tipo: SSH

### Campi

| Campo | Tipo | Richiesto | Descrizione |
|-------|------|-----------|--------------|
| `private_key` | string | Sì | Chiave privata SSH |
| `public_key` | string | No | Chiave pubblica SSH |
| `passphrase` | string | No | Passphrase chiave (se presente) |
| `host` | string | Sì | Host SSH |
| `user` | string | Sì | Utente SSH |
| `port` | int | No | Porta SSH (default 22) |
| `description` | string | No | Descrizione |

### Wizard Interattivo

```
? Tipo credential: SSH
? Nome del credential: prod-server
? Descrizione: Accesso SSH server produzione
? Host: prod.example.com
? Utente: deploy
? Porta (default 22):
? Path chiave privata (o contenuto inline): /path/to/id_ed25519
? Passphrase (vuoto se nessuna):
🔐 Cifratura in corso...
✅ Credential 'prod-server' aggiunto!
```

### CLI

```bash
am config add ssh --name prod-server --host prod.example.com --user deploy --port 22 --private-key /path/to/key --passphrase ""
```

### JSON Cifrato (contenuto in .age)

```json
{
  "type": "ssh",
  "private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n...",
  "public_key": "ssh-ed25519 AAAA...",
  "passphrase": null,
  "host": "prod.example.com",
  "user": "deploy",
  "port": 22
}
```

### Runtime

- Chiave privata: `/workspace/runtime/credentials/ssh/<name>.key`
- Chiave pubblica: `/workspace/runtime/credentials/ssh/<name>.pub`
- Configurazione SSH: `/workspace/runtime/credentials/ssh/config`
- Opzionale: aggiunta a ssh-agent

---

## Tipo: Database

### Campi

| Campo | Tipo | Richiesto | Descrizione |
|-------|------|-----------|--------------|
| `db_type` | string | Sì | Tipo database: mysql, postgresql, mongodb, sqlite |
| `host` | string | Sì | Host database |
| `port` | int | Sì | Porta database |
| `database` | string | Sì | Nome database |
| `user` | string | Sì | Username |
| `password` | string | Sì | Password |
| `description` | string | No | Descrizione |

### Wizard Interattivo

```
? Tipo credential: Database
? Nome del credential: prod-db
? Descrizione: Database produzione
? Tipo database: postgresql
? Host: db.example.com
? Porta: 5432
? Database: myapp
? Utente: admin
? Password: ************************
🔐 Cifratura in corso...
✅ Credential 'prod-db' aggiunto!
```

### CLI

```bash
am config add database --name prod-db --db-type postgresql --host db.example.com --port 5432 --database myapp --user admin --password "xxx"
```

### JSON Cifrato (contenuto in .age)

```json
{
  "type": "database",
  "db_type": "postgresql",
  "host": "db.example.com",
  "port": 5432,
  "database": "myapp",
  "user": "admin",
  "password": "secretpassword"
}
```

### Runtime

- File di configurazione: `/workspace/runtime/credentials/database/<name>.json`
- Supporto per `.env` generation per applicazioni

---

## Tipo: FTP

### Campi

| Campo | Tipo | Richiesto | Descrizione |
|-------|------|-----------|--------------|
| `host` | string | Sì | Host FTP |
| `port` | int | No | Porta FTP (default 21) |
| `user` | string | Sì | Username FTP |
| `password` | string | Sì | Password FTP |
| `description` | string | No | Descrizione |

### Wizard Interattivo

```
? Tipo credential: FTP
? Nome del credential: backup-ftp
? Descrizione: FTP per backup
? Host: ftp.backup.com
? Porta (default 21):
? Utente: backup_user
? Password: ************************
🔐 Cifratura in corso...
✅ Credential 'backup-ftp' aggiunto!
```

### CLI

```bash
am config add ftp --name backup-ftp --host ftp.backup.com --user backup_user --password "xxx"
```

### JSON Cifrato (contenuto in .age)

```json
{
  "type": "ftp",
  "host": "ftp.backup.com",
  "port": 21,
  "user": "backup_user",
  "password": "secretpassword"
}
```

### Runtime

- File config: `/workspace/runtime/credentials/ftp/<name>.json`

---

## Tipo: API

### Campi

| Campo | Tipo | Richiesto | Descrizione |
|-------|------|-----------|--------------|
| `provider` | string | Sì | Provider: openai, anthropic, aws, azure, google, custom |
| `api_key` | string | Sì | API key |
| `endpoint` | string | No | Endpoint custom (se diverso da default) |
| `model` | string | No | Modello di default (per LLM) |
| `description` | string | No | Descrizione |

### Wizard Interattivo

```
? Tipo credential: API
? Nome del credential: openai-key
? Descrizione: API key OpenAI
? Provider: openai
? API Key: sk-xxxxxxxxxxxxxxxx
? Endpoint (opzionale, default):
? Modello di default (opzionale):
🔐 Cifratura in corso...
✅ Credential 'openai-key' aggiunto!
```

### CLI

```bash
am config add api --name openai-key --provider openai --api-key sk-xxx --model gpt-4
am config add api --name anthropic-key --provider anthropic --api-key sk-ant-xxx
```

### JSON Cifrato (contenuto in .age)

```json
{
  "type": "api",
  "provider": "openai",
  "api_key": "sk-xxxxxxxxxxxxxxxx",
  "endpoint": null,
  "model": "gpt-4"
}
```

### Runtime

- File config: `/workspace/runtime/credentials/api/<name>.json`
- Per LLM: variabili d'ambiente per opencode/tool

---

## Comandi

### Wizard (interattivo)

```bash
am config add              # Menu per scelta tipo → wizard
am config add github      # Wizard specifico GitHub
am config add ssh        # Wizard specifico SSH
am config add database   # Wizard specifico Database
am config add ftp        # Wizard specifico FTP
am config add api        # Wizard specifico API
```

### CLI (non interattivo)

```bash
# GitHub
am config add --type github --name <name> [opzioni...]

# SSH
am config add --type ssh --name <name> [opzioni...]

# Database
am config add --type database --name <name> [opzioni...]

# FTP
am config add --type ftp --name <name> [opzioni...]

# API
am config add --type api --name <name> [opzioni...]
```

### Altri comandi

```bash
am config list                    # Lista tutti i credential
am config list github            # Lista solo GitHub
am config list ssh              # Lista solo SSH
am config status                # Status unlock/blocco
am config unlock                 # Unlock con passphrase
am config lock                   # Lock (logout)
am config remove <nome>         # Rimuovi credential
am config show <nome>           # Mostra dettagli (decifrato)
am config export <nome>        # Esporta credential decifrato
```

---

## Sicurezza

### Regole

1. **Mai committare file .age su Git** - sono cifrati ma non sicuri
2. **Mai committare la passphrase** - solo nel password manager
3. **Non committare secrets/ in chiaro** - devono essere sempre .age
4. **Il volume Docker dei credentials è persistente** - non perderlo

### Workflow Cifratura

1. L'utente inserisce i dati nel wizard
2. I dati vengono serializzati in JSON
3. Il JSON viene cifrato con `age --passphrase -p`
4. Il file .age viene salvato in `credentials/<tipo>/`
5. L'indice in accounts.json viene aggiornato (NON contiene dati sensibili)

### Workflow Decifrazione (unlock)

1. L'utente inserisce la passphrase
2. Per ogni .age, age decifra il contenuto
3. Il JSON decifrato viene parsato
4. I file vengono scritti in `/workspace/runtime/credentials/<tipo>/`
5. Il git credential helper viene configurato

---

## TODO

- [ ] Implementare GitHub (priorità alta)
- [ ] Implementare SSH (con ssh-agent)
- [ ] Implementare Database
- [ ] Implementare FTP
- [ ] Implementare API
- [ ] Implementare `am config remove`
- [ ] Implementare `am config show`
- [ ] Implementare export credential
- [ ] Aggiornare entrypoint per nuovi tipi
- [ ] Aggiornare main.py per nuovi comandi

---

## Note

- La passphrase è unica per tutti i credential
- Il volume Docker `amstero-credentials` persiste i dati runtime
- I credential sono accessibili in `/workspace/runtime/credentials/` quando sbloccati
- Il file `accounts.json` NON contiene dati sensibili, solo metadati