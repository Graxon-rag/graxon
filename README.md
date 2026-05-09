# Graxon

## Prerequisites

Make sure the following are running before proceeding:

- PostgreSQL
- PgBouncer
- Neo4j

---

## First Time Setup

### 1. Clone the repository and install dependencies

```bash
git clone https://github.com/Graxon-rag/graxon.git
cd graxon
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Errors

1. If you encounter error regarding the `psycopg2` then remove `psycopg2==2.9.12` from `requirements.txt`
2. If you encounter error regarding the `pypdf` then update it's version to `pypdf==6.4.9` in `requirements.txt`

### 2. Configure environment variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Required variables:

| Variable              | Description                               |
| --------------------- | ----------------------------------------- |
| `POSTGRESQL_HOST`     | Direct PostgreSQL host (e.g. `localhost`) |
| `POSTGRESQL_PORT`     | Direct PostgreSQL port (e.g. `5432`)      |
| `PGBOUNCER_HOST`      | PgBouncer host (e.g. `localhost`)         |
| `PGBOUNCER_PORT`      | PgBouncer port (e.g. `5433`)              |
| `POSTGRESQL_USERNAME` | PostgreSQL username                       |
| `POSTGRESQL_PASSWORD` | PostgreSQL password                       |

### 3. Run Alembic migrations

> **Important:** Migrations must be run manually before starting the server.
> The application does **not** run migrations automatically on startup.

```bash
cd graxon
alembic upgrade head
```

You should see output like:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 37dc4a863ca1, init_schema
INFO  [alembic.runtime.migration] Running upgrade 37dc4a863ca1 -> c2dd6dc1f8dc, sparse_text_model
...
INFO  [alembic.runtime.migration] Running upgrade 74b2e9477c08 -> 0f85cfaf0f05, document
```

### 4. Start the server

```bash
chmod +x dev.sh
```

Run

```bash
./dev.sh
```

On first startup, the application will automatically seed default data into PostgreSQL and Neo4j — this happens only once.

---

## Adding New Migrations

When you make changes to SQLAlchemy models, generate a new migration:

```bash
alembic revision --autogenerate -m "your_migration_description"
```

Then apply it:

```bash
alembic upgrade head
```

> Only modify tables listed in `GRAXON_OWNED_TABLES` inside `migrations/env.py`.
> Do not add tables owned by other services.

---

## Rolling Back Migrations

Roll back the last migration:

```bash
alembic downgrade -1
```

Roll back to a specific revision:

```bash
alembic downgrade <revision_id>
```

---

## Checking Migration Status

```bash
alembic current   # shows current revision
alembic history   # shows full migration history
```

---

## Seeding

Seeding runs automatically on first startup — no manual step needed.

It inserts:

- Default organization (`dev`)
- LLM models (OpenAI, Claude, Gemini, DeepSeek)
- Embedding models (OpenAI, Voyage, Gemini)
- Reranker models
- Sparse text models
- Default Neo4j organization node

If you need to re-seed (e.g. after wiping the database), delete the `seed_tracker` table row:

```sql
DELETE FROM seed_tracker;
```

Then restart the server.

## Spacy

```py
spacy download en_core_web_sm
```

## Lexical Engine

Entity Extraction (NER) — Detects shared named entities like people, organizations, products, and technologies across chunks to build high-confidence semantic relationships.
Concept Extraction (Noun Phrases) — Extracts meaningful noun phrases and technical concepts shared between chunks to connect semantically related ideas.
TF-IDF Keyword Linking — Uses TF-IDF scoring to identify rare but important keywords that appear across multiple chunks while filtering common noise words.
Phrase Bridge Detection — Generates exact n-gram phrase matches between chunks to capture strong lexical overlap and repeated terminology.
Acronym Resolution — Detects acronym definitions and links them to later acronym usage across the document for better contextual understanding.
Edge Construction — Converts shared entities, concepts, keywords, phrases, and acronyms into graph edges connecting related chunks.
Edge Deduplication — Removes duplicate or weaker edges to keep the graph cleaner, more meaningful, and efficient for traversal.

Entity Extraction (NER) — Identifies shared named entities such as people, organizations, technologies, and products across chunks. This helps create strong semantic links between chunks discussing the same real-world subject and improves graph-based retrieval accuracy.
Concept Extraction (Noun Phrases) — Extracts meaningful noun phrases and technical concepts shared between chunks. It helps connect semantically related ideas even when exact keywords differ, improving topic grouping and contextual understanding.
TF-IDF Keyword Linking — Uses TF-IDF scoring to detect rare but informative keywords that appear across multiple chunks while filtering common noise words. This highlights statistically important terms that help strengthen semantic relationships.
Phrase Bridge Detection — Detects exact shared n-gram phrases between chunks to capture repeated terminology and strong lexical overlap. This is especially useful for technical, scientific, and domain-specific documents where repeated phrases carry important meaning.
Acronym Resolution — Detects acronym definitions and links them to later acronym usage throughout the document. This improves long-document comprehension by connecting abbreviated references back to their original meaning.
Edge Construction — Converts all detected lexical relationships into graph edges connecting related chunks. These edges form the foundation of the semantic document graph used for retrieval, traversal, and contextual reasoning.
Edge Deduplication — Removes duplicate or weaker relationships while preserving the strongest semantic connections. This keeps the graph cleaner, more efficient, and easier to traverse during retrieval and ranking operations.
