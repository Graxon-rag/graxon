# Format-Aware RAG Chunking Pipeline

A multi-format document chunking pipeline that transforms raw files into **semantically meaningful RAG chunks**, storing embeddings in a **Vector Database** for similarity search and relationships in **Neo4j** for graph-based retrieval.

Instead of blindly splitting every file into fixed-size chunks, each file format is routed through a processing strategy suited to its content — structured tabular data, plain text, PDFs/images, audio, and video are all handled differently before converging into a unified chunk + storage layer.

---

## Table of Contents

- [Overview](#overview)
- [Supported Formats](#supported-formats)
- [Architecture](#architecture)
- [Queue & Worker Model](#queue--worker-model)
- [Format-Aware Processing](#format-aware-processing)
- [Two-Level Chunking](#two-level-chunking)
- [Progress Tracking](#progress-tracking)
- [Storage Layer](#storage-layer)
- [End-to-End Flow](#end-to-end-flow)

---

## Overview

This system ingests heterogeneous documents at scale, processes them asynchronously via a message queue and worker pool, and produces semantically coherent chunks optimized for retrieval-augmented generation (RAG). Each chunk is dual-written to:

- **Vector Database** — for embedding-based similarity search
- **Neo4j** — for structural and contextual graph relationships (file → chunk → speaker/video, etc.)

---

## Supported Formats

| Category         | Formats                                          |
| ---------------- | ------------------------------------------------ |
| Structured       | CSV, Excel, JSON, HTML, XML, YAML, Code and more |
| Text             | TXT, Markdown, Docs and more                     |
| Media (Document) | PDF, Images                                      |
| Media (Audio)    | Audio files                                      |
| Media (Video)    | Video files                                      |

---

## Architecture

```text
Multiple File Types
        ↓
   RabbitMQ Queue
        ↓
    Worker Pool
        ↓
  Format Detection
        ↓
  Semantic Chunking
        ↓
  ┌───────┴───────┐
  ▼               ▼
Vector DB        Neo4j
```

---

## Queue & Worker Model

Files are published onto a **RabbitMQ** queue and consumed by a pool of parallel workers.

```text
                ┌──────────────┐
Files ─────────►│ RabbitMQ     │
                │ Queue        │
                └──────┬───────┘
                       │
                 ┌─────▼───────┐
                 │   Workers   │
                 └──────┬──────┘
                        │
                 File Processor
```

RabbitMQ provides:

- Asynchronous processing
- Parallel workers
- Retry / requeue support on failure
- Resumable processing (via progress tracking, see below)

Each queue message carries positional state so processing can resume mid-file:

```json
{
  "file_path": "/uploads/sales.csv",
  "file_chunk_number": 3,
  "rag_chunk_start_index": 150
}
```

---

## Format-Aware Processing

Each worker inspects the incoming file's type and branches into a specialized processor:

```text
Worker
  │
  ┌────────┴────────┐
  │   File Type?    │
  └────────┬────────┘
           │
  ┌────────────────┼─────────────────┐
  │                │                 │
Structured        Text             Media
  │                │                 │
CSV/Excel/JSON   TXT/Markdown     PDF/Image
HTML/XML/YAML                     Audio
                                   Video
```

### Structured data (CSV / Excel / JSON / HTML / XML / YAML)

```text
CSV / Excel / JSON and more
        ↓
 500-row IO buffer
        ↓
  TF-IDF + KMeans
        ↓
  Semantic chunks
```

### Text (TXT / Markdown)

```text
Text / Markdown / Docs and more
        ↓
  50MB IO buffer
        ↓
Sentence + heading detection
        ↓
  Semantic chunks
```

### Documents (PDF / Image)

```text
PDF / Image
     ↓
    OCR
     ↓
  Markdown
     ↓
Text processor
```

### Audio

```text
Audio
  ↓
Speech-to-Text
  ↓
Utterances
  ↓
Utterance groups
```

### Video

```text
Video
  ↓
TwelveLabs
  ↓
Scene segments
  ↓
Segment groups
```

---

## Two-Level Chunking

The pipeline uses **two levels of chunking**:

- **Level 1 — IO Buffer**: controls memory usage by reading only a bounded portion of the source at a time (e.g. 500 CSV rows, 50MB of text).
- **Level 2 — Semantic Chunking**: transforms that buffer into smaller, semantically coherent chunks optimized for retrieval.

```text
Large File
    │
    ▼
┌─────────────────┐
│     Level 1     │
│    IO Buffer    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Level 2     │
│    Semantic     │
│    Chunking     │
└────────┬────────┘
         │
         ▼
   RAG Documents
```

**Example — structured data:**

```text
500 CSV rows
      ↓
 TF-IDF vectors
      ↓
 KMeans clusters
      ↓
10–15 related rows
      ↓
   1 RAG chunk
```

**Example — text:**

```text
Text
  ↓
Sentences
  ↓
Sentence groups
  ↓
RAG chunk
```

---

## Progress Tracking

Two counters track progress at different granularities:

| Field                   | Meaning                                                                |
| ----------------------- | ---------------------------------------------------------------------- |
| `file_chunk_number`     | Position within the original source file (Level 1 IO buffer index)     |
| `rag_chunk_start_index` | Global position of semantic chunks across every batch processed so far |

```text
File
 │
 ├── Batch 0 ──► RAG chunks 0–49
 │
 ├── Batch 1 ──► RAG chunks 50–99
 │
 ├── Batch 2 ──► RAG chunks 100–149
 │
 └── Batch 3 ──► RAG chunks 150–...
```

Each subsequent RabbitMQ message advances both counters, enabling resumable, exactly-once-ish processing:

```json
{
  "file_chunk_number": 4,
  "rag_chunk_start_index": 200
}
```

---

## Storage Layer

Every generated `Document` (RAG chunk) is written to two destinations:

```text
RAG Documents
      │
┌─────┴─────┐
│           │
▼           ▼
Vector DB   Neo4j
│           │
Embeddings  Relationships
│           │
Similarity  Graph
Search      Traversal
```

- **Vector Database** — enables semantic similarity search over chunk embeddings.
- **Neo4j** — preserves structural and contextual relationships between files, chunks, speakers, and video content.

**Neo4j chunk relationships:**

```text
(File)
  │
  ├── HAS_CHUNK ──► (Chunk 0)
  │                     │
  │                     └── NEXT_CHUNK ──► (Chunk 1)
  │                                             │
  │                                             └──► (Chunk 2)
```

**Audio / video specific relationships:**

```text
(Chunk)
  │
  ├── SPOKEN_BY ──► (Speaker)
  │
  └── IN_VIDEO  ──► (Video)
```

---

## End-to-End Flow

```text
Files
  │
  ▼
RabbitMQ
  │
  ▼
Worker Pool
  │
  ▼
Format Detection
  │
  ├── Structured ──► IO Buffer ──► TF-IDF/KMeans
  │
  ├── Text ────────► IO Buffer ──► Sentence Chunking
  │
  ├── PDF/Image ───► OCR ───────► Markdown
  │
  ├── Audio ───────► STT ───────► Utterances
  │
  └── Video ───────► TwelveLabs ► Segments
  │
  ▼
Semantic RAG Chunks
  │
┌──────┴──────┐
▼             ▼
Vector DB     Neo4j
│             │
Similarity    Graph
Search        Retrieval
```

---

## Summary

| Stage                       | Purpose                                                                |
| --------------------------- | ---------------------------------------------------------------------- |
| RabbitMQ                    | Async, parallel, retryable file ingestion                              |
| Format Detection            | Route each file to the right processing strategy                       |
| Level 1 (IO Buffer)         | Bound memory usage while reading large files                           |
| Level 2 (Semantic Chunking) | Produce retrieval-optimized, semantically coherent chunks              |
| Progress Tracking           | Resumable processing via `file_chunk_number` / `rag_chunk_start_index` |
| Vector DB                   | Similarity search over embeddings                                      |
| Neo4j                       | Graph traversal over structural/contextual relationships               |
