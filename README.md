# Amstero Core
<!-- amstero:quick-start -->

## Quick Start

### Prerequisiti

- **macOS**: [OrbStack](https://orbstack.dev/) (consigliato)
- **Windows**: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux**: segui la [guida ufficiale](https://docs.docker.com/engine/install/), oppure su Ubuntu:
  ```bash
  curl -fsSL https://get.docker.com | sh
  ```

### Setup

1. Crea una cartella per il workspace (es. `amstero-workspace`)

2. Scarica lo ZIP da GitHub:
   https://github.com/cdario79/amstero-core/archive/refs/heads/main.zip

3. Estrai il contenuto in `amstero-workspace/repos/`

4. La cartella in cui si troverà il contenuto del repo si dovrà chiamare `amstero-core` nel caso non avesse questo nome rinominarla

5. Il risultato finale sarà:
   ```
   amstero-workspace/
   └── repos/
       └── amstero-core/
           └── ...
   ```

6. Apri il terminale in `repos/amstero-core` e avvia:
   ```bash
   docker compose up --build -d
   ```

Oppure se hai `git` sul tuo computer:
   ```bash
   mkdir -p amstero-workspace/repos
   cd amstero-workspace
   git clone https://github.com/cdario79/amstero-core.git repos/amstero-core
   cd repos/amstero-core
   docker compose up --build -d
  ```

<!-- amstero:quick-start:end -->

Amstero Core è il cuore operativo del sistema Amstero.

Non è un progetto applicativo e non contiene i progetti dell’utente.  
È il motore che prepara, orchestra e rende utilizzabile un workspace Amstero basato su repository separati, container Docker, OpenCode e strumenti di automazione.

---

## 1. Cos’è Amstero Core

Amstero Core serve a trasformare una cartella locale in un ambiente di lavoro strutturato, portabile e adatto allo sviluppo assistito da AI.

Il suo compito è fornire:

- CLI centrale `am`
- ambiente Docker per gli strumenti
- integrazione con OpenCode
- gestione della vista virtuale dei progetti
- collegamento tra repository `code`, `spec` e `config`
- automazioni per wiki, specifiche, task e modifiche multi-repo

---

## 2. Modello mentale

Amstero separa chiaramente i ruoli.

```text
SPEC       → governa
CODE       → contiene il sorgente
CONFIG     → personalizza l’ambiente utente
TOOLS      → automatizzano
CONTAINER  → esegue strumenti, test, build e processi
RUNTIME    → mantiene stato temporaneo
```

Il codice sorgente non “esegue” direttamente.  
Il repo `code` contiene i file dell’applicazione.  
L’esecuzione avviene dentro container, immagini o ambienti collegati.

---

## 3. Workspace Amstero

Un workspace Amstero è una cartella locale che contiene repository separati e una struttura minima di supporto.

Struttura fisica consigliata su host:

```text
workspace/
├── repos/
│   ├── amstero-core-code/
│   ├── amstero-core-spec/
│   ├── amstero-bootstrap-code/
│   ├── amstero-bootstrap-spec/
│   ├── config/
│   ├── gestionale-code/
│   ├── gestionale-spec/
│   ├── servizio-email-code/
│   ├── servizio-email-spec/
│   └── servizio-sms-code/
│
├── shared/
├── runtime/
└── .amstero-workspace
```

La cartella fondamentale è:

```text
repos/
```

Qui vivono tutti i repository reali.

---

## 4. Repository nel workspace

Ogni elemento sviluppabile può avere almeno due repo:

```text
nome-progetto-code
nome-progetto-spec
```

Esempio:

```text
gestionale-code  → codice sorgente del gestionale
gestionale-spec  → wiki, specifiche, task, regole, decisioni
```

Anche Amstero stesso segue questa regola:

```text
amstero-core-code  → codice di Amstero Core
amstero-core-spec  → specifiche e documentazione evolutiva di Amstero Core
```

In questo modo Amstero può essere sviluppato usando Amstero.

---

## 5. Repo config utente

Il workspace può contenere un repository di configurazione personale:

```text
repos/config/
```

Questo repo non appartiene ad Amstero Core in modo rigido.  
Viene creato o inizializzato dal bootstrap, ma l’utente può collegarlo al proprio repository GitHub, GitLab, Bitbucket o mantenerlo solo locale.

Serve a contenere:

- registry dei progetti
- preferenze utente
- configurazioni locali
- provider AI
- riferimenti ai repository
- secrets cifrati
- chiavi SSH cifrate
- file `.env` cifrati

Esempio:

```text
repos/config/
├── registry/
│   └── projects.json
├── user/
│   ├── profile.json
│   └── preferences.json
├── secrets/
│   ├── providers.age
│   └── clients/
├── ssh/
│   └── keys.age
├── env/
│   └── global.env.age
└── README.md
```

Regola importante:

```text
Mai salvare password, token o chiavi private in chiaro su Git.
```

Per i segreti si useranno strumenti come:

```text
sops + age
```

---

## 6. Shared e Runtime

`shared/` e `runtime/` non contengono verità del sistema.

Sono cartelle sacrificabili, non versionate e rigenerabili.

### shared/

Contiene dati temporanei o persistenti ma non critici:

```text
shared/
├── logs/
├── cache/
└── tmp/
```

Esempi:

- log CLI
- log OpenCode
- cache parsing
- cache LLM
- file temporanei

### runtime/

Contiene stato vivo dell’esecuzione:

```text
runtime/
├── mounts/
├── sessions/
├── locks/
└── execution/
```

Esempi:

- symlink generati
- vista virtuale dei repo
- sessioni agenti
- lock file
- stato task in corso

Se `shared/` e `runtime/` vengono cancellate, il sistema deve poterle ricreare.

---

## 7. Vista virtuale Docker

Sul filesystem host i repo restano separati.

Dentro Docker, Amstero Core può creare una vista logica più comoda, simile a un mega-repo, ma senza trasformare i repo in un monorepo reale.

Host:

```text
workspace/repos/
├── gestionale-code/
├── gestionale-spec/
├── servizio-email-code/
└── servizio-email-spec/
```

Vista nel container:

```text
/workspace/projects/
├── gestionale/
│   ├── code/  -> /host-workspace/repos/gestionale-code
│   └── spec/  -> /host-workspace/repos/gestionale-spec
│
└── servizio-email/
    ├── code/  -> /host-workspace/repos/servizio-email-code
    └── spec/  -> /host-workspace/repos/servizio-email-spec
```

Questa vista permette a OpenCode e agli altri strumenti di lavorare come se tutto fosse ordinato in un’unica struttura, mantenendo però repository Git separati.

---

## 8. Registry dei progetti

Il file principale di configurazione dei progetti vive nel repo config:

```text
repos/config/registry/projects.json
```

Esempio:

```json
{
  "projects": {
    "gestionale": {
      "code_repo": "repos/gestionale-code",
      "spec_repo": "repos/gestionale-spec",
      "type": "application",
      "role": "Gestionale principale",
      "linked_projects": [
        "servizio-email",
        "servizio-sms"
      ]
    },
    "servizio-email": {
      "code_repo": "repos/servizio-email-code",
      "spec_repo": "repos/servizio-email-spec",
      "type": "service",
      "role": "Servizio invio email",
      "linked_projects": [
        "gestionale"
      ]
    }
  }
}
```

Questo registry consente ad Amstero Core di sapere:

- quali progetti esistono
- dove si trovano i repo code
- dove si trovano i repo spec
- quali progetti sono collegati
- quali repo possono essere coinvolti in modifiche multi-repo

---

## 9. Spec repo

Ogni progetto ha un proprio repository `spec`.

Esempio:

```text
repos/gestionale-spec/
├── .amstero-project.json
├── config/
├── wiki/
├── specs/
├── tasks/
├── decisions/
└── README.md
```

Il repo `spec` contiene:

- conoscenza del progetto
- wiki
- richieste
- decisioni
- specifiche operative
- task eseguibili
- riferimenti ad altri progetti collegati

Non contiene il codice sorgente dell’applicazione.

---

## 10. Code repo

Ogni progetto ha un proprio repository `code`.

Esempio:

```text
repos/gestionale-code/
├── src/
├── config/
├── templates/
├── public/
├── composer.json
└── ...
```

Il repo `code` contiene il sorgente dell’applicazione o del servizio.

Non deve contenere la documentazione operativa principale, le specifiche di progetto o i secrets utente.

---

## 11. Modifiche multi-repo

Amstero Core deve supportare modifiche che coinvolgono più progetti.

Esempio:

```text
gestionale
servizio-email
servizio-sms
sistema-cron
```

Una specifica multi-repo può vivere nel repo spec del progetto da cui parte la richiesta:

```text
repos/gestionale-spec/specs/multi-repo/notifiche-scadenze.md
```

Esempio di frontmatter:

```yaml
---
type: multi-repo-change
owner_project: gestionale
target_projects:
  - gestionale
  - servizio-sms
  - sistema-cron
execution_order:
  - servizio-sms
  - sistema-cron
  - gestionale
---
```

Amstero Core dovrà:

1. leggere la spec
2. individuare i progetti coinvolti
3. consultare il registry
4. montare/risolvere i path dei repo
5. eseguire i task nell’ordine definito
6. aggiornare code e spec dei progetti coinvolti

---

## 12. OpenCode

OpenCode viene usato come agente operativo.

Il flusso tipico sarà:

```bash
am shell
cd /workspace/projects/gestionale/spec
opencode
```

Oppure tramite comando diretto:

```bash
am opencode gestionale
```

OpenCode lavorerà partendo dalla cartella `spec`, ma potrà leggere e modificare anche il relativo `code` e gli altri progetti collegati, secondo configurazione.

---

## 13. CLI am

La CLI `am` sarà il punto di ingresso unico.

Comandi previsti:

```bash
am workspace init
am workspace mount
am workspace status

am config init
am config connect
am config decrypt

am project add gestionale
am project list
am project open gestionale

am opencode gestionale

am wiki init gestionale
am wiki compile gestionale

am task run gestionale path/to/task.md
```

La CLI non deve contenere logica specifica dei singoli clienti.  
Deve leggere configurazioni e registry.

---

## 14. Struttura prevista di Amstero Core

Struttura evolutiva del repository:

```text
amstero-core/
├── README.md
├── setup.sh
├── bin/
│   └── am
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── cli/
├── opencode/
│   ├── commands/
│   ├── tools/
│   └── config/
├── wiki/
│   └── compiler/
├── templates/
│   ├── spec/
│   ├── config/
│   └── project/
└── docs/
```

---

## 15. Rapporto con Amstero Bootstrap

`amstero-bootstrap` serve solo ad avviare un workspace.

Il bootstrap:

- crea la struttura base
- inizializza `repos/`
- scarica o prepara Amstero Core
- inizializza eventualmente il repo config
- delega tutto il resto ad Amstero Core

Amstero Bootstrap deve restare minimale.

Amstero Core contiene invece l’evoluzione del sistema.

---

## 16. Principi architetturali

### 16.1 Repo separati

Amstero non impone un monorepo.

Usa repository separati e crea una vista virtuale di comodo.

### 16.2 Spec separata dal codice

Il sapere operativo non deve essere disperso dentro il codice.

```text
spec = governo del progetto
code = sorgente del progetto
```

### 16.3 Config personale separata

Le configurazioni dell’utente non appartengono ai progetti.

Devono stare in un repo config separato, eventualmente cifrato e sincronizzato.

### 16.4 Runtime sacrificabile

Tutto ciò che è in `shared/` e `runtime/` deve poter essere cancellato e ricreato.

### 16.5 AI guidata da specifiche

OpenCode e gli agenti non devono improvvisare.

Devono leggere:

- config
- wiki
- spec
- task
- registry

prima di lavorare.

---

## 17. Obiettivo finale

Amstero Core deve rendere possibile questo flusso:

```text
1. Creo workspace
2. Aggiungo repo code/spec/config
3. Creo vista virtuale Docker
4. Entro nel progetto
5. OpenCode legge le spec
6. L’AI modifica uno o più repo
7. Il sistema aggiorna wiki, task e decisioni
```

---

## 18. In sintesi

Amstero Core è:

- motore del workspace
- orchestratore dei tool
- ponte tra spec e code
- base per lavorare con AI su progetti multi-repo
- sistema portabile e replicabile
- fondazione tecnica del metodo Amstero

Non è:

- un monorepo
- un singolo progetto applicativo
- un contenitore di secrets in chiaro
- una cartella di file temporanei
- un sostituto dei repo code/spec

---

## 19. Prossimi step

Priorità iniziali:

1. creare CLI minimale `am`
2. inizializzare struttura workspace
3. inizializzare repo config
4. creare registry `projects.json`
5. generare vista virtuale Docker
6. integrare OpenCode
7. creare template spec
8. supportare prime operazioni multi-repo
