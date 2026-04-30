# Auto-Switch Git Credentials - Specifiche

## Panoramica

Il sistema di auto-switch permette di usare credenziali Git diverse automaticamente in base all'owner del repository. Non richiede configurazione manuale - funziona come git standard.

## Struttura Credential

### GitHub HTTPS

```json
{
  "name": "personal",
  "type": "github",
  "auth_type": "https",
  "github_user": "mio-username",
  "github_email": "mio@email.com",
  "token": "ghp_xxxxxxxxxxxx",
  "owners": ["mio-username", "mia-organizzazione"],
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Campi:**
- `name` - nome identificativo del credential
- `type` - sempre "github"
- `auth_type` - "https" o "ssh"
- `github_user` - username GitHub per configurare git user.name
- `github_email` - email GitHub per configurare git user.email
- `token` - Personal Access Token GitHub
- `owners` - lista di owner (username GitHub o organizzazioni) gestiti da questo credential

### SSH

```json
{
  "name": "server-prod",
  "type": "ssh",
  "private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n...",
  "public_key": "ssh-ed25519 AAAA...",
  "passphrase": "optional",
  "hosts": ["github.com", "gitlab.com", "ssh.dev.azure.com"],
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Campi:**
- `name` - nome identificativo del credential
- `type` - sempre "ssh"
- `private_key` - chiave privata SSH
- `public_key` - chiave pubblica SSH
- `passphrase` - passphrase per la chiave (opzionale)
- `hosts` - lista di host per cui usare questa chiave

## Wrapper Git

### Percorso
`/usr/local/bin/git`

### Logica di Funzionamento

```
1. Prima di ogni comando git:
   a. Determina la directory corrente
   b. Se è un repository git:
      - Leggi il remote URL
      - Estrai l'owner (es. da https://github.com/owner/repo → owner)
      - Estrai l'host (es. github.com, gitlab.com)

2. Cerca il credential appropriato:
   a. HTTPS: cerca in credentials.github quello con owner nell'elenco owners
   b. SSH: cerca in credentials.ssh quello con host nell'elenco hosts

3. Se trovato, configura per questa sessione:
   a. git config user.name = <github_user>
   b. git config user.email = <github_email>
   c. HTTPS: configura credential helper con token
   d. SSH: esporta chiave temporanea e configura GIT_SSH_COMMAND

4. Esegue il comando git originale

5. Pulizia (opzionale)
```

### Installazione

Nel Dockerfile:
```dockerfile
# Copia wrapper git
COPY bin/git-wrapper.sh /usr/local/bin/git
RUN chmod +x /usr/local/bin/git

# Backup git originale
RUN mv /usr/bin/git /usr/bin/git-bin
```

### Matching Priority

L'ordine di ricerca del credential:
1. HTTPS: owner esatto dal remote URL
2. SSH: host esatto dal remote URL
3. Se non trovato → errore

## CLI Commands

### Aggiungere Credential GitHub

```bash
am config add github --name <nome> \
  --token <token> \
  --github-user <username> \
  --github-email <email> \
  --owners "owner1,owner2" \
  --auth-type https
```

**Esempio:**
```bash
am config add github --name cliente-a \
  --token ghp_xxxxxxxxxxxx \
  --github-user cliente-user \
  --github-email cliente@azienda.it \
  --owners "cliente-a,azienda-cliente" \
  --auth-type https
```

### Aggiungere Credential SSH

```bash
am config add ssh --name <nome> \
  --private-key-path /path/to/private_key \
  --public-key-path /path/to/public_key \
  --hosts "github.com,gitlab.com"
```

**Esempio:**
```bash
am config add ssh --name mia-key \
  --private-key-path ~/.ssh/id_ed25519 \
  --public-key-path ~/.ssh/id_ed25519.pub \
  --hosts "github.com"
```

### CLI Wizard

```bash
am config add github
? Tipo credential: GitHub
? Nome: cliente-a
? Token GitHub: ********************
? Username GitHub: cliente-user
? Email GitHub: cliente@email.com
? Owner (account/organizzazioni separati da virgola): cliente-a,azienda-cliente
? Auth type (https/ssh): https
🔐 Cifratura...
✅ Credential aggiunto!
```

## Comportamento

### Clone

```bash
cd /workspace/repos
git clone https://github.com/cliente-a/repo.git
```

Risultato:
1. Wrapper estrae owner: `cliente-a`
2. Trova credential con `cliente-a` negli owners
3. Configura git con user/email/token di quel credential
4. Clone funziona con credenziali giuste

### Push/Pull

```bash
cd /workspace/repos/progetto-cliente
git push
```

Risultato:
1. Wrapper legge remote
2. Estrae owner
3. Applica credential corretto
4. Push usa le credenziali giuste

### Cambiare Repository

```bash
cd /workspace/repos/progetto-cliente
# usa credential cliente-a

cd /workspace/repos/progetto-personale
# usa credential personal
```

## Gestione Errori

### Owner Sconosciuto

```
fatal: Unknown GitHub owner. Add credential with:
  am config add github --owners <owner>
```

### Auth Fallita

```
fatal: Authentication failed for owner 'owner-name'.
Check token or add correct credential with:
  am config add github --name <name> --owners <owner>
```

### Chiave SSH Mancante

```
fatal: No SSH credential found for host 'github.com'.
Add SSH credential with:
  am config add ssh --hosts github.com
```

## Runtime

### Credential Sbloccati

Quando si fa `am config unlock`, tutti i credential vengono decifrati e resi disponibili in:
- `/workspace/runtime/credentials/github/` - token HTTPS
- `/workspace/runtime/credentials/ssh/` - chiavi SSH

### File Temporanei SSH

Le chiavi SSH vengono esportate temporaneamente in:
- `/workspace/runtime/credentials/ssh/keys/<name>.key`
- `/workspace/runtime/credentials/ssh/keys/<name>.pub`

## Sicurezza

1. **Credential cifrati** - tutti i token e chiavi sono cifrati nel repo
2. **Passphrase richiesta** - per sbloccare serve la passphrase
3. **Token runtime** - i token decifrati stanno solo in memoria/volume
4. **Nessun fallback** - se non c'è credential, errore chiaro

## TODO

- [ ] Aggiornare accounts.json schema
- [ ] Implementare add_credential per SSH
- [ ] Aggiornare add_credential per GitHub con nuovi campi
- [ ] Creare git wrapper script
- [ ] Aggiornare Dockerfile per wrapper
- [ ] Aggiornare unlock/lock per gestire SSH
- [ ] Testare clone/push/pull con credential diversi