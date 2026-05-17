# Graxon

## Clone the repository

```bash
git clone https://github.com/Graxon-rag/graxon.git
cd graxon
```

## Execution Choices

### 1. Local Development (Native)

Best if you prefer to run the app directly on your host machine without containerization.

1. Create a `.env` from `.env.example`
   ```bash
   cp .env.example .env
   ```
2. Create a `Virtual Env` and `enable` it
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install all dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Up all the engines/ databases/ store
   ```bash
   docker compose up -d
   ```
5. Run the migration
   ```bash
   alembic upgrade head
   ```
6. Run the server
   ```bash
    chmod +x dev.sh
    ./dev.sh
   ```

### 2. Docker Development (With Container HMR)

Best for keeping your host machine clean while maintaining instant hot-reloading (Hot Module Replacement) as you change your code.

1. Create a `.env.docker` from `.env.docker.example`

   ```bash
   cp .env.docker.example .env.docker
   ```

2. Build the image
   ```bash
   docker compose -f docker-compose-dev.yaml build
   ```
3. Run Container

   ```bash
   docker compose -f docker-compose-dev.yaml up -d
   ```

   The server will be accessible at http://localhost:8888

   #### To view live container logs:

   ```bash
   docker compose -f docker-compose-dev.yaml logs -f
   ```

### 3. Docker Production

Run the images from `docker-hub`

1. Create a `.env.docker` from `.env.docker.example`

   ```bash
   cp .env.docker.example .env.docker
   ```

2. Run Container

   ```bash
   docker compose -f docker-compose-prod.yaml up -d
   ```

   The server will be accessible at http://localhost:8888

   #### To view live container logs:

   ```bash
   docker compose -f docker-compose-prod.yaml logs -f
   ```

### Stopping Containers

If you are running either of the Docker variations, you can spin down the environments using:

- #### For Development:
  docker compose -f docker-compose-dev.yaml down
- #### For Production:
  docker compose -f docker-compose-prod.yaml down

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
