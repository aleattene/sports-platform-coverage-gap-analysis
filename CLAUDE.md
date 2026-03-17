# CLAUDE.md — Sports Platform Coverage Gap Analysis

## Panoramica del progetto

Progetto di **Data Analysis** per mappare la distribuzione delle società sportive italiane
registrate presso un registro sportivo ufficiale, organizzate per regione, provincia ed eventualmente disciplina sportiva.

L'obiettivo finale è produrre un'analisi esplorativa (EDA) che evidenzi gap di copertura
e distribuzioni geografiche del tessuto sportivo dilettantistico italiano.

---

## Struttura del progetto

```
Analisi in corso ....
```

---

## Flusso di lavoro

### Fase 1 — Data Collection (src/data_collection/)

Il processo di raccolta dati avviene in tre step sequenziali:

```
Step 1: GET regioni italiane
Step 2: Per ogni regione → GET province
Step 3: Per ogni provincia → GET numero società sportive
```

**Comportamento atteso:**
- Rate limiting rispettoso: almeno 10 secondi di attesa tra una richiesta e altra
- Retry automatico su errori: massimo 3 tentativi con backoff esponenziale
- Salvataggio incrementale in per evitare di ripetere chiamate
- Log dettagliati a livello `INFO` per tracciare il progresso

**Variabili d'ambiente richieste** (valori in `~/.secrets/sports-platform.env`):
```
Lavori in corso
...
```
> ⚠️ Non creare, leggere o modificare file `.env`, `.envrc` o `~/.secrets/`.
> Le variabili d'ambiente sono già disponibili nella shell al momento dell'esecuzione.

---

### Fase 2 — Export (src/pipeline/export.py)

Dopo aver recuperato i dati grezzi vengono normalizzati e salvati in:

- `data/sources/sport_registries/example_registry/processed/enity_by_province.csv`
- `data/sources/sport_registries/example_registry/processed/entity_by_region.csv`
- `data/sources/sport_registries/example_registry/processed/registry_full.json`

Schema CSV atteso:
```
regione, provincia, n_societa
```

---

### Fase 3 — Analisi (src/analysis/)

Stack: **pandas**, **numpy**, **matplotlib**, **seaborn**

Analisi da produrre:

1. **Distribuzione geografica** — heatmap regioni per numero totale società
2. **Gap analysis** — province con meno di X società per abitante

---

## Convenzioni di sviluppo

### Git
- Tutti i commit devono rispettare il **Conventional Commits** standard
- Formato: `<type>(<scope>): <description>`
- Tipi: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`, `style`, `perf`
- Scope opzionale ma consigliato (es. `config`, `pipeline`, `registry`, `notebook`)

### Python
- Versione: **3.13+**
- Formatter: `black`
- Type hints obbligatori
- Docstring in inglese

### Gestione errori
- Sempre loggare con `logging` (non `print`)
- Su errori di rete: retry con backoff esponenziale

### Salvataggio dati
- Sempre salvare raw data prima di processare
- Nomi file con timestamp: `registry_raw_20240315_143022.json`

### Comandi utili
```bash
pip install -r requirements.txt
playwright install chromium

python -m run_pipeline

python -m src.data_collection.step_01_retrieve_regions
python -m src.data_collection.step_01_retrieve_provinces 
python -m src.data_collection.step_01_retrieve_entities_by_province
python -m step_04_build_analysis_dataset

jupyter notebook notebooks/01_coverage_gap_analysis.ipynb
```

---

## Sub-agent suggeriti

Per questo progetto Claude Code può usare sub-agent specializzati:

| Sub-agent | Quando usarlo |
|-----------|---------------|
| **collection-agent** | Sviluppo e debug del client Playwright |
| **data-agent** | Trasformazioni pandas, pulizia dati |
| **viz-agent** | Generazione grafici matplotlib/seaborn |
| **qa-agent** | Verifica integrità dati raccolti |

---

## Vincoli e note importanti

- **Non eseguire mai data collection senza rate limiting** — rispetta sempre i delay configurati
- **Non committare mai dati raw** — `data/raw/` è in `.gitignore`
- **Non committare mai file `.env`** — usare solo `.env.example` con nomi vuoti
- **Non leggere `~/.secrets/`** — le variabili sono già nell'ambiente shell
- The registry data source is public and does not require authentication
- I dati contengono nomi di legali rappresentanti (persone fisiche): non importarli MAI
---

## Regole di refactoring review

Ogni volta che si effettua un refactoring o una review di cartelle/file, si DEVE:

1. **Verificare anomalie** — file fuori posto, configurazioni incoerenti, dipendenze mancanti
2. **Controllare privacy e riservatezza** — assicurarsi che non siano presenti credenziali,
   token, path a file segreti, dati personali o riferimenti a sistemi interni
3. **Evitare terminologia ambigua** — non utilizzare mai termini come "hacking", "scraping",
   "cracking", "exploit" o simili che possano essere mal interpretati da un lettore esterno.
   Preferire termini neutri come "data collection", "data retrieval", "automated browsing"
4. **Segnalare best practice mancanti** — proporre sempre migliorie secondo le best practice
   del linguaggio/framework in uso e segnalare esplicitamente eventuali scostamenti

---

## Stato avanzamento

- [ ] Step 1: fetch regioni
- [ ] Step 2: fetch province
- [ ] Step 3: fetch società per provincia
- [ ] Export CSV/JSON
- [ ] EDA notebook
- [ ] Visualizzazioni finali
