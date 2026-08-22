<div align="center">

  <a href="https://www.graxonrag.com/">
    <img src="img/graxon-logo.png" alt="Graxon Logo" width="400">
  </a>
  <h1 style="font-size: 46px;">Graxon</h1>

  <br>
  <br>

  <!-- Badges -->
  <a href="https://github.com/Graxon-rag/graxon/stargazers">
    <img src="https://img.shields.io/github/stars/Graxon-rag/graxon?style=flat-square&logo=github&color=0969da" alt="GitHub stars">
  </a>
  <a href="https://pypi.org/project/graxon/">
    <img src="https://img.shields.io/pypi/v/graxon?style=flat-square&logo=pypi&color=blue" alt="PyPI version">
  </a>
  <a href="https://github.com/Graxon-rag/python">
    <img src="https://img.shields.io/badge/Python-SDK-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python SDK">
  </a>

<a href="https://www.npmjs.com/package/graxon">
  <img src="https://img.shields.io/npm/v/graxon?style=flat-square&logo=npm&color=CB3837" alt="npm version">
</a>
<a href="https://github.com/Graxon-rag/js">
  <img src="https://img.shields.io/badge/JavaScript--TypeScript-SDK-F7DF1E?style=flat-square&logo=javascript&logoColor=black" alt="JavaScript TypeScript SDK">
</a>
  <a href="https://www.linkedin.com/company/115924256">
    <img src="https://img.shields.io/badge/LinkedIn-Follow-0A66C2?style=flat-square&logo=linkedin" alt="LinkedIn Follow">
  </a>
  <a href="https://www.youtube.com/@graxonrag">
    <img src="https://img.shields.io/badge/YouTube-Subscribe-FF0000?style=flat-square&logo=youtube" alt="YouTube Subscribe">
  </a>

  <br>
  <br>

[**Website**](https://www.graxonrag.com/) &nbsp;|&nbsp;
[**Documentation**](https://www.graxonrag.com/docs) &nbsp;|&nbsp;
[**API Reference**](https://www.graxonrag.com/docs/api-reference) &nbsp;|&nbsp;
[**Python SDK**](https://github.com/Graxon-rag/python) &nbsp;|&nbsp;
[**Javascript SDK**](https://github.com/Graxon-rag/js) &nbsp;|&nbsp;
[**Python Examples**](https://github.com/Graxon-rag/python-examples)&nbsp;|&nbsp;
[**Javascript Examples**](https://github.com/Graxon-rag/js-examples)

</div>

<br>

> **First Open-Source Hybrid RAG to eliminate hallucinations through a persistent Knowledge Graph layer.**

Graxon combines dense vector search, sparse retrieval, and a structured Knowledge Graph to deliver accurate, traceable, and context-aware answers — at scale, across multiple organizations, projects, and documents.

---

## 🌟 Why Graxon?

- **Eliminate Hallucinations:** Ground your AI responses in a persistent, traceable Knowledge Graph.
- **Hybrid Retrieval:** Leverage the best of both dense (vector) and sparse search methodologies.
- **Built for Scale:** Designed to handle complex queries across multiple organizations, diverse projects, and massive document stores.
- **Developer Friendly:** Comprehensive [API](https://www.graxonrag.com/docs/api-reference) and robust [Python SDK](https://github.com/Graxon-rag/python) to get you building quickly.

---

## Table of Contents

- [Overview](#overview)
- [Quickstart](#-quickstart)
- [Images](#images)
- [Videos](#videos)
- [Architecture](#architecture)
- [Infrastructure](#infrastructure)
- [Data Model](#data-model)
- [Supported Formats](#supported-formats)
- [Chunking Engine](#chunking-engine)
- [Ingestion Pipeline](#ingestion-pipeline)
- [Lexical Engine](#lexical-engine)
- [Resilient Ingestion & Checkpointing](#resilient-ingestion--checkpointing)
- [Query Pipeline](#query-pipeline)
- [Multipart Upload & Resume](#multipart-upload--resume)
- [Graxon vs Microsoft GraphRAG](#graxon-vs-microsoft-graphrag)
- [Getting Started](#getting-started)
- [Execution Choices](#execution-choices)
- [Swagger](#swagger)
- [Docker Hub](#docker-hub)
- [Connect with Us](#-connect-with-us)

---

## Overview

Traditional RAG systems rely purely on vector similarity, which can retrieve plausible but semantically incorrect chunks. Graxon solves this by layering a **persistent Knowledge Graph** on top of hybrid vector retrieval — connecting chunks through typed, weighted edges that capture real semantic relationships.

**Key properties:**

- **Multi-Tenant** — isolated workspaces per organization
- **Multi-Project** — scoped retrieval within projects
- **Multi-Document** — fine-grained document management
- **Hybrid Retrieval** — dense vectors + sparse BM25 + graph traversal
- **Hallucination Reduction** — graph-grounded answers anchored to structured knowledge

---

## 🚀 Quickstart

### Python

Install the Graxon Python SDK using pip:

```bash
pip install graxon
```

Check out the [Python Examples Repository](https://github.com/Graxon-rag/python-examples) for complete examples and end-to-end use cases.

**Python SDK:**  
https://github.com/Graxon-rag/python

**PyPI:**  
https://pypi.org/project/graxon/

---

### JavaScript / TypeScript

Install the Graxon JavaScript SDK using your preferred package manager.

#### Bun

```bash
bun add graxon
```

#### npm

```bash
npm install graxon
```

#### yarn

```bash
yarn add graxon
```

#### pnpm

```bash
pnpm add graxon
```

The JavaScript SDK supports modern JavaScript and TypeScript applications and is designed to work seamlessly with **Bun**.

Check out the [JavaScript Examples Repository](https://github.com/Graxon-rag/js-examples) for complete examples and end-to-end use cases.

**JavaScript SDK:**  
https://github.com/Graxon-rag/javascript

**npm:**  
https://www.npmjs.com/package/graxon

---

## Images

!["graxon.png"](./img/graxon.png)

<br/>
<br/>

!["graxon1.png"](./img/graxon1.png)

<br/>
<br/>

!["graxon2.png"](./img/graxon2.png)

## Videos

### UI

https://drive.google.com/file/d/1Luv6NVNh1e1VJPmGp_eXtB1fy4n7NVey/view?usp=drive_link

### Graph DB

https://drive.google.com/file/d/1fi_lNDTBxRy3jGuS0spnw0dNXraPAbwf/view?usp=sharing

---

<br/>

## Architecture

```
Orgs
 └── Projects
      └── Documents
           └── Chunks
```

Each document is chunked, processed through a multi-agent pipeline, stored in a vector database and a knowledge graph, and wired with semantic edges for retrieval.

---

## Infrastructure

| Component      | Role                                             |
| -------------- | ------------------------------------------------ |
| **Qdrant**     | Vector database — dense + sparse embeddings      |
| **Neo4j**      | Graph database — chunk nodes, semantic edges     |
| **PostgreSQL** | Primary relational database                      |
| **PgBouncer**  | PostgreSQL connection pooler                     |
| **MinIO**      | Object storage — raw document files              |
| **RabbitMQ**   | Message broker — async pipeline orchestration    |
| **Redis**      | In-memory cache — sessions, queues, fast lookups |

---

## Data Model

### Hierarchy

```
Organization
  └── Project
        └── Document
              └── Chunk
```

### Graph Node: `Chunk`

Each chunk is stored as a node in Neo4j and a vector in Qdrant. Nodes are connected by typed, weighted edges:

| Edge Type        | Description                                     |
| ---------------- | ----------------------------------------------- |
| `PREV` / `NEXT`  | Sequential order within the document            |
| `HAS_TAG`        | LLM-extracted semantic tags                     |
| `HAS_KEYWORD`    | TF-IDF significant keywords                     |
| `HAS_PHRASE`     | Shared n-gram phrases                           |
| `HAS_ENTITY`     | Named entities (NER)                            |
| `HAS_CONCEPT`    | Extracted noun phrases / concepts               |
| `HAS_ACRONYM`    | Acronym-to-definition links                     |
| `VECTOR_SIMILAR` | High cosine similarity between chunk embeddings |

All edges carry a **weight** for ranked graph traversal during retrieval.

### Images

!["graph.png"](./img/graph.png)

<br/>
<br/>

!["graph1.png"](./img/graph1.png)

---

## Supported Formats

| Category         | Formats                                          |
| ---------------- | ------------------------------------------------ |
| Structured       | CSV, Excel, JSON, HTML, XML, YAML, Code and more |
| Text             | TXT, Markdown, PPT, Docs and more                |
| Media (Document) | PDF, Images                                      |
| Media (Audio)    | Audio files                                      |
| Media (Video)    | Video files                                      |

---

## Chunking Engine

A multi-format document chunking pipeline that transforms raw files into **semantically meaningful RAG chunks**.

Instead of blindly splitting every file into fixed-size chunks, each file format is routed through a processing strategy suited to its content — structured tabular data, plain text, PDFs/images, audio, and video are all handled differently before converging into a unified chunk + storage layer.

#### [Read more about chunking engine](md/chunking_engine.md)

<br/>

## !["chunking_engine.png"](./img/chunking_engine.png)

---

## Ingestion Pipeline

Graxon uses **LangGraph** to orchestrate a parallel multi-agent pipeline at ingestion time.

```
Document
   │
   ▼
Chunking
   │
   ▼
LangGraph Pipeline
   ├── LLM Agent          → tags, inter-chunk relations
   ├── Embedding Agent    → dense vectors (OpenAI / Gemini / Voyage)
   ├── Sparse Agent       → sparse vectors via FastEmbed (BM25 / Qdrant sparse)
   └── Lexical Engine     → entities, concepts, keywords, phrases, acronyms
   │
   ├── Vector Store Agent
   │     └── Qdrant ← dense + sparse embeddings
   │
   ├── Graph DB Agent
   │     └── Neo4j ← chunk nodes
   │                 ├── PREV / NEXT edges
   │                 ├── HAS_TAG, HAS_KEYWORD, HAS_PHRASE ...
   │                 └── (all with weights)
   │
   └── Vector Similarity Sync
         └── Top-K similar chunks from Qdrant
               └── Neo4j ← VECTOR_SIMILAR edges (with cosine weight)
```

### Images

!["ingestion.png"](./img/ingestion.png)

---

### Agents

**LLM Agent**
Sends chunks to an LLM to extract semantic tags and inter-chunk relationships. Results become typed edges in the knowledge graph.

**Embedding Agent**
Generates dense vector embeddings using pluggable providers — OpenAI, Google Gemini, or Voyage AI. Stored in Qdrant for ANN search.

**Sparse Embedding Agent**
Generates sparse vectors via **FastEmbed** for BM25-style retrieval and Qdrant's sparse vector support. Enables lexical precision alongside semantic recall.

**Lexical Engine**
SpaCy-powered linguistic analysis that extracts structured signals from each chunk. See [Lexical Engine](#lexical-engine) below.

### Vector Similarity Sync

After all chunks are stored in Qdrant, Graxon runs a post-ingestion pass: for each chunk, it fetches the top-K most similar chunks by embedding cosine similarity and writes `VECTOR_SIMILAR` edges into Neo4j with the similarity score as the edge weight. This bridges the vector and graph layers.

---

## Lexical Engine

Graxon uses **SpaCy** as its lexical engine to extract structured linguistic signals from chunks, which are then converted into graph edges.

### Entity Extraction (NER)

Detects shared named entities — people, organizations, products, and technologies — across chunks. Creates strong semantic links between chunks discussing the same real-world subject, improving graph-based retrieval accuracy.

### Concept Extraction (Noun Phrases)

Extracts meaningful noun phrases and technical concepts shared between chunks. Connects semantically related ideas even when exact keywords differ, improving topic grouping and contextual understanding.

### TF-IDF Keyword Linking

Uses TF-IDF scoring to detect rare but informative keywords appearing across multiple chunks, while filtering common noise words. Highlights statistically important terms that strengthen semantic relationships.

### Phrase Bridge Detection

Detects exact shared n-gram phrases between chunks to capture repeated terminology and strong lexical overlap. Especially useful for technical, scientific, and domain-specific documents where repeated phrases carry important meaning.

### Acronym Resolution

Detects acronym definitions and links them to later acronym usage throughout the document. Improves long-document comprehension by connecting abbreviated references back to their original meaning.

### Edge Construction

Converts all detected lexical relationships — entities, concepts, keywords, phrases, and acronyms — into typed, weighted graph edges connecting related chunks in Neo4j.

### Edge Deduplication

Removes duplicate or weaker relationships while preserving the strongest semantic connections. Keeps the graph cleaner and more efficient to traverse during retrieval and ranking.

---

## Resilient Ingestion & Checkpointing

Most RAG pipelines work great in a notebook. At enterprise scale, they fall apart.

Rate limits spike. Workers crash. If your ingestion fails at page 800 of a 1,000-page document, an all-or-nothing architecture forces a full restart — burning engineering time and duplicate LLM tokens.

Graxon is built with an **infrastructure-first mindset** to make ingestion deterministic, fault-tolerant, and resumable by design.

---

### Zero-Loss Macro & Micro Checkpointing

Graxon treats ingestion like a **transaction log**, decoupling graph state and persisting checkpoints across two layers:

| Layer                 | Store      | Role                                     |
| --------------------- | ---------- | ---------------------------------------- |
| **Micro checkpoints** | Redis      | Hot in-memory state tracking per chunk   |
| **Macro checkpoints** | MinIO (S3) | Cold artifact backups per document/batch |

If an API provider or worker node crashes mid-ingestion, Graxon **hot-boots and resumes from the exact chunk it left off** — no full restart, no wasted tokens.

---

### Ironclad Idempotency & Atomicity

Resuming a failed pipeline usually introduces duplicate vectors or corrupted graph linkages. Graxon guarantees a **zero-duplicate footprint** by design:

**Qdrant**

- Deterministic `uuid5` hashing seeded by structured `chunk_id`s
- Ensures every vector upsert is fully idempotent — re-ingesting a chunk overwrites cleanly, never duplicates

**Neo4j**

- Single-transaction bulk uploads via optimized Cypher `UNWIND` clauses
- Strict `ON CREATE` / `ON MATCH` state isolation preserves temporal metadata and guarantees ACID consistency

---

### Multi-Engine Parallel Fan-Out

Rather than sequential processing, Graxon uses LangGraph to run a parallelized scatter-gather pipeline across all storage layers simultaneously:

- **Dense vectors** → Qdrant (deep semantic similarity)
- **Sparse vectors** → FastEmbed / BM25 → Qdrant (lexical exact matching)
- **Knowledge Graph** → Neo4j (chunk nodes, entity tags, structural edges)
- **Lexical Analysis** → SpaCy (natural textual topology)

All four engines process each chunk concurrently — maximizing throughput and minimizing ingestion latency at scale.

---

## Checkpoints

```mermaid
graph TD
    %% =========================
    %% Styling
    %% =========================
    classDef database fill:#f2f2f2,stroke:#333,stroke-width:2px;
    classDef process fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef agent fill:#ede7f6,stroke:#512da8,stroke-width:2px;
    classDef storage fill:#fff3e0,stroke:#f57c00,stroke-width:2px;

    %% =========================
    %% Level 1: Message Processing
    %% =========================
    subgraph L1["Level 1: Message-Driven File Processing"]
        Raw[Raw File<br/>] --> Producer[RabbitMQ Producer]
        Producer --> Consumer[RabbitMQ Consumer]:::process

        Consumer -->|Validate & Check Status| DB[(State Database<br/>Checkpoint)]:::database
        DB -->|Ready for Processing| Chunking[File Chunking]:::process
        Chunking -->|Save Progress| DB
    end

    %% =========================
    %% Level 2: Resumable AI Pipeline
    %% =========================
    subgraph L2["Level 2: LangGraph Resumable Processing Pipeline"]

        Chunking --> Supervisor[Supervisor Agent]:::agent
        Supervisor --> Parser[Chunk Parser Agent]:::agent

        Parser --> LLM[LLM Agent]:::agent
        Parser --> Dense[Dense Embedding Agent]:::agent
        Parser --> Sparse[Sparse Embedding Agent]:::agent
        Parser --> Lexical[Lexical Processing Agent]:::agent

        %% Object Storage Checkpointing
        LLM -.->|Checkpoint| ObjectStorage[(MinIO / S3<br/>Object Storage)]:::storage
        Dense -.->|Checkpoint| ObjectStorage
        Sparse -.->|Checkpoint| ObjectStorage
        Lexical -.->|Checkpoint| ObjectStorage

        %% Processing Results
        LLM --> VectorDB[Vector Database Agent]:::agent
        Dense --> VectorDB
        Sparse --> VectorDB
        Lexical --> VectorDB

        VectorDB --> GraphDB[Graph Database Agent]:::agent
    end
```

### Images

!["image_1"](./img/checkponit/image_1.png)
<br/>>
!["image_2"](./img/checkponit/image_2.png)
<br/>
!["image_3"](./img/checkponit/image_3.png)
<br/>
!["image_4"](./img/checkponit/image_4.png)
<br/>
!["image_5"](./img/checkponit/image_5.png)

---

## Query Pipeline

Graxon uses a **LangGraph-orchestrated query pipeline** with 3 query types and 2 depth levels, giving fine-grained control over retrieval quality vs. speed.

---

### Flow Overview

```
__start__
    │
    ▼
supervisor_agent
    │
    ▼
query_expansion_agent
    ├── embedding_agent          (dense embedding of expanded query)
    └── sparse_embedding_agent   (sparse / BM25 embedding)
    │
    ▼
vector_database_agent            (hybrid retrieval from Qdrant)
    │
    ├── [expert] ──► expert_query_agent ──► expert_query_reranker_agent ──► expert_query_answer_agent
    ├── [quick]  ──► quick_query_agent  ──► quick_query_reranker_agent  ──► quick_query_answer_agent
    └── [smart]  ──► smart_query_agent  ──► smart_query_reranker_agent  ──► smart_query_answer_agent
    │
    ▼
__end__  (answer + metadata / sources)
```

Every query — regardless of mode or depth — begins with:

1. **Query expansion** via LLM
2. **Dense + sparse embedding** of the expanded query
3. **Hybrid retrieval** from Qdrant (dense + BM25 vectors)

<br/>
<br/>

!["query.png"](./img/query.png)

---

### Query Types & Depth

#### Quick

Lightweight retrieval with immediate document context.

| Depth        | Retrieval                                               |
| ------------ | ------------------------------------------------------- |
| **Standard** | Vector DB chunks + `PREV` / `NEXT` neighbors from Neo4j |
| **Advanced** | Same as Standard                                        |

---

#### Smart

Adds graph-based semantic expansion on top of Quick.

| Depth        | Retrieval                                                                      |
| ------------ | ------------------------------------------------------------------------------ |
| **Standard** | Quick (Standard) + `VECTOR_SIMILAR` chunks from Neo4j for each retrieved chunk |
| **Advanced** | Smart (Standard) + `PREV` / `NEXT` neighbors for each `VECTOR_SIMILAR` chunk   |

---

#### Expert

Full hybrid retrieval combining vector, graph, and lexical signals with a unified chunk scoring system.

| Depth        | Retrieval                                                                                                                                                 |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Standard** | Smart (Advanced) + embedding comparison of query against Tags, Keywords, Concepts, Entities, Phrases, Acronyms filtered by `EQ_GTE_LANE_WEIGHT_THRESHOLD` |
| **Advanced** | Expert (Standard) + Lexical Engine picks best lanes and top `EQ_MAX_LANE_ENTITY` matches per lane                                                         |

##### Expert Chunk Scoring

Every `chunk_id` accumulates a score across all retrieval signals:

| Signal                                                   | Score |
| -------------------------------------------------------- | ----- |
| Present in Vector DB results                             | `++`  |
| Present as `PREV` / `NEXT` or `VECTOR_SIMILAR` neighbor  | `++`  |
| Matched via query–tag / keyword / concept embedding      | `++`  |
| Matched via Lexical Engine lane _(Expert Advanced only)_ | `++`  |

Top `EQ_MAX_CHUNKS` chunks by final score are forwarded to the answer agent.

---

### Reranking & Answer Generation

After retrieval, every mode runs:

1. **Reranker agent** — reranks the retrieved chunk set, selects Top-K
2. **Answer agent** — passes expanded query + context window to LLM
3. **Response** — returns the answer with full **metadata and sources**

---

### Configuration

| Variable                       | Description                                                               |
| ------------------------------ | ------------------------------------------------------------------------- |
| `EQ_GTE_LANE_WEIGHT_THRESHOLD` | Minimum similarity score for tag / keyword / concept lane matching        |
| `EQ_MAX_CHUNKS`                | Maximum chunks selected after expert scoring                              |
| `EQ_MAX_LANE_ENTITY`           | Top entities picked per lane by the Lexical Engine (Expert Advanced only) |

---

## Multipart Upload & Resume

Graxon's zero-loss checkpointing extends all the way to the browser.

Most upload implementations are fire-and-forget — if the connection drops at 95%, you start over. Graxon's upload system is session-aware and part-level resumable on both the frontend and backend, mirroring the same checkpoint philosophy as the ingestion pipeline.

- bucket: {org_id}
- key: pro*{project_id}/doc*{document_id}/{filename}

Each organization gets its own bucket. Each document gets its own isolated path within the project scope.

---

### Upload Flow

```
Browser
│
├── 1. Check local session (documentId, uploadId, key, completedParts)
│
├── 2. POST /multipart/init  (if no session)
│         └── Backend: auto-creates org bucket if missing
│                       creates S3 multipart upload
│                       returns uploadId + key
│                       session persisted on frontend
│
├── 3. For each part:
│         ├── Skip if already in completedParts  ──► advance progress
│         ├── GET presigned URL from backend (1hr expiry)
│         └── PUT chunk directly to MinIO  (no data through app server)
│
├── 4. POST /multipart/complete
│         └── Backend: sorts parts by PartNumber (S3 requirement)
│                       calls S3 complete_multipart_upload
│                       registers document via DocumentService
│                       triggers ingestion pipeline
│
└── 5. Session deleted on success  /  preserved on failure for retry
```

---

### Backend: `MinioUploadClient`

**`multipart_upload_init`**
Ensures the org bucket exists (creates it if not), registers a new multipart upload with MinIO, and returns the `upload_id` and `key` to the frontend.

**`get_multipart_presigned_url`**
Generates a presigned `upload_part` URL per part with a 1-hour expiry. The browser uploads directly to MinIO — no file data passes through the application server.

**`complete_multipart_upload`**
Sorts completed parts by `PartNumber` (required by S3/MinIO), finalizes the multipart upload.

---

### Frontend: Session-Aware Resume

**Session Persistence**
Before every upload, the frontend checks for an existing session — `documentId`, `uploadId`, `key`, and all `completedParts`. If a previous attempt was interrupted, the session is still there.

**Part-Level Resume**
The file is split into fixed-size chunks. For each part, the frontend checks whether it was already uploaded. If so, it skips it and advances the progress bar. Only missing parts are re-uploaded.

**Local Part Tracking**
Completed parts are tracked in a local array during the session to avoid stale store reads. Parts are also persisted to the store for cross-session recovery.

---

### Failure & Retry Behavior

| Scenario                      | Behavior                                                            |
| ----------------------------- | ------------------------------------------------------------------- |
| Connection drops mid-upload   | Session preserved, retry resumes from last completed part           |
| Browser tab closed            | Session persisted, upload resumes on next open                      |
| Part upload fails             | Error surfaced, session intact, retry skips completed parts         |
| Upload completes successfully | Session deleted, document handed to `DocumentService` for ingestion |

---

## Graxon vs Microsoft GraphRAG

While Microsoft GraphRAG is a brilliant research methodology for complex offline data discovery, it requires expensive full-corpus re-indexing and lacks multi-tenancy.

**Graxon** is engineered to bring knowledge graph-grounded RAG into **production SaaS environments** — featuring zero-loss checkpointing, dynamic multi-tenant isolation, and real-time hybrid retrieval.

| Feature                  | Graxon                                             | Microsoft GraphRAG                              |
| :----------------------- | :------------------------------------------------- | :---------------------------------------------- |
| **Open Source Status**   | Fully open-source (GitHub, Docker Hub, Apache 2.0) | Fully open-source (GitHub, MIT license)         |
| **Primary Innovation**   | Persistent KG + Hybrid Retrieval + Checkpointing   | Community hierarchy + summarization             |
| **Graph Node Type**      | Chunk-level (Fine-grained topology)                | Entity-level (High-level extraction)            |
| **Edge Types**           | 8 typed edges with dynamic weights                 | Semantic relationships (LLM-only)               |
| **Hybrid Retrieval**     | Dense + Sparse (BM25) + Graph Traversal            | Community summaries + optional vector           |
| **Query Orchestration**  | LangGraph Multi-Agent (3 types × 2 depths)         | Linear pipeline; community/global search        |
| **Multi-Tenancy**        | ✅ Built-in (Org → Project → Doc → Chunk)          | ❌ Not supported natively                       |
| **Fault Tolerance**      | ✅ Zero-loss checkpointing (Redis + MinIO)         | ❌ All-or-nothing; full re-index on failure     |
| **Multipart Upload**     | ✅ Browser-side resumable uploads                  | ❌ Not supported                                |
| **Lexical Analysis**     | SpaCy-powered (NER, TF-IDF, n-grams, acronyms)     | LLM-only (No traditional NLP layer)             |
| **LLM Providers**        | OpenAI, Claude, Gemini, DeepSeek (Dynamic UI)      | OpenAI / Azure OpenAI default                   |
| **Embedding Providers**  | OpenAI, Gemini, Voyage AI                          | OpenAI / Azure OpenAI default                   |
| **Sparse Embeddings**    | ✅ FastEmbed (Native BM25 for Qdrant)              | ❌ Not supported                                |
| **Reranking**            | ✅ Dedicated pluggable reranker agent              | ❌ Relies on LLM community summarization        |
| **Production Readiness** | Enterprise-ready (Docker, Swagger, async workers)  | Research prototype ("not officially supported") |

---

## Getting Started

### Clone the repository

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

## Swagger

After running the Server you can read the `swagger`

http://localhost:8888/docs

- **Username**: admin
- **Password**: admin

---

## Docker Hub

https://hub.docker.com/u/graxon

---

<br/>

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

---

## 🤝 Connect with Us

Stay up to date with the latest features, tutorials, and community highlights!

- Follow us on [LinkedIn](https://www.linkedin.com/company/115924256/)

- Subscribe to our [YouTube Channel](https://www.youtube.com/@graxonrag) for tutorials and deep dives.

- Star us on [GitHub](https://github.com/Graxon-rag/graxon) to support open-source development!
