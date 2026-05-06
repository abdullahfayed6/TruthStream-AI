# TruthStream AI

**Real-time fake news detection system** powered by a DistilBERT/RoBERTa classifier, Apache Kafka + Spark streaming pipeline, and a modern Next.js analytics dashboard.

TruthStream AI continuously ingests news articles from **NewsAPI** and **GNews**, classifies them as **Fake** or **Real** using a fine-tuned transformer model, and displays the results on a live dashboard with GPT-powered explanations.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" />
  <img src="https://img.shields.io/badge/Spark-3.5-E25A1C?logo=apachespark" />
  <img src="https://img.shields.io/badge/Kafka-3.x-231F20?logo=apachekafka" />
  <img src="https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb" />
  <img src="https://img.shields.io/badge/GPT--4o--mini-OpenAI-412991?logo=openai" />
</p>

---

## Key Features

- **Real-Time Ingestion**: Fetches breaking news every 60 seconds from NewsAPI & GNews, with automatic deduplication.
- **AI Classification**: Uses fine-tuned DistilBERT/RoBERTa for Fake/Real detection with confidence scores and a deterministic fallback.
- **GPT Integration**: 1-click "Explain" and "Summarize" for any article using GPT-4o-mini.
- **Live Dashboard**: Real-time WebSocket updates, timelines, source breakdown charts, and summary statistics.
- **Zero-Config Demo Mode**: Runs locally without Docker/Kafka/Spark, providing instant UI testing and live news fetching.
- **Production-Ready API**: 9 endpoints (REST + WebSocket + SSE) with pagination, filtering, and CORS.
- **Full Docker Stack**: Single `docker-compose up` launches Next.js, FastAPI, Spark, Kafka, and MongoDB.
- **Tested & CI/CD**: Includes 22 API tests, unit tests, end-to-end smoke tests, and GitHub Actions integration.

---

## Architecture

```
NewsAPI / GNews
      │
      ▼
┌─────────────┐      ┌──────────────┐      ┌───────────┐      ┌──────────┐
│  Ingestion  │ ───▶ │  Kafka      │ ───▶ │  Spark    │ ───▶│ MongoDB  │
│  Producers  │      │  (news.raw)  │      │  Scoring  │      │ (scored) │
└─────────────┘      └──────────────┘      └───────────┘      └──────────┘
                                                                     │
                                                                     ▼
                                                  ┌──────────────────────────┐
                                                  │  FastAPI Backend (API)   │
                                                  │  /articles  /stats       │
                                                  │  /explain   /summarize   │
                                                  │ /ws/articles (WebSocket) │
                                                  └──────────────────────────┘
                                                                     │
                                                                     ▼
                                                  ┌──────────────────────────┐
                                                  │   Next.js Frontend       │
                                                  │  Dashboard • Articles    │
                                                  │  GPT Explain • Charts    │
                                                  └──────────────────────────┘
```

> **Local Dev Mode**: When Kafka/Spark/MongoDB are not running, the API starts in **demo mode** with a built-in live ingestion service that fetches real news directly from NewsAPI/GNews, classifies them in-memory, and pushes them to the frontend via WebSocket — no infrastructure required.

---

## Project Structure

```
TruthStream-AI/
├── api/                     # FastAPI backend
│   ├── main.py              # App entry point, lifespan, CORS
│   ├── fallback_store.py    # In-memory demo data store
│   ├── live_ingestion.py    # Real-time news fetching & classification
│   ├── routers/
│   │   ├── articles.py      # GET /articles, GET /articles/{id}
│   │   ├── stats.py         # GET /stats, GET /stats/timeline
│   │   ├── explain.py       # POST /explain, POST /summarize (GPT)
│   │   └── websocket.py     # WS /ws/articles, SSE /articles/stream
│   ├── requirements.txt
│   └── Dockerfile
│
├── Frontend/                # Next.js 16 dashboard (App Router)
│   ├── app/                 # Pages (Dashboard, Articles, Architecture)
│   ├── components/          # Reusable UI components
│   │   └── dashboard/       # Stats cards, charts, article feed, etc.
│   ├── hooks/               # SWR & WebSocket custom hooks
│   ├── lib/                 # API client, types, utilities
│   ├── package.json
│   └── Dockerfile
│
├── ingestion/               # Kafka producers
│   ├── newsapi_producer.py  # NewsAPI ingestion → Kafka
│   ├── gnews_producer.py    # GNews ingestion → Kafka
│   ├── producer_base.py     # Base producer with dedup
│   └── schema.py            # Article data model
│
├── streaming/               # Spark Structured Streaming jobs
│   ├── clean_job.py         # Bronze → Silver (text cleaning)
│   ├── score_job.py         # Silver → Gold (ML classification)
│   ├── common.py            # Shared Spark session config
│   └── text_utils.py        # Text normalization utilities
│
├── ml/                      # Machine Learning
│   ├── inference.py         # DistilBERT Spark UDF + fallback
│   ├── fallback.py          # Hash-based deterministic classifier
│   ├── download_model.py    # HuggingFace model downloader
│   └── train/               # Training notebooks & scripts
│
├── sink/                    # Kafka → MongoDB connector
│   └── mongo_sink.py        # Consumes scored articles → MongoDB
│
├── scripts/                 # DevOps & utility scripts
│   ├── bootstrap.sh         # Initial setup
│   ├── create-topics.sh     # Kafka topic creation
│   ├── start-app.ps1        # Windows startup script
│   └── submit-jobs.sh       # Spark job submission
│
├── tests/                   # Test suite
│   ├── test_all.py          # Comprehensive integration tests
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── load/                # Load testing
│
├── docs/                    # Documentation
│   ├── architecture.md      # System architecture details
│   └── why-bigdata.md       # Big data design rationale
│
├── docker-compose.yml       # Full stack orchestration
├── .env.example             # Environment variables template
├── pyproject.toml           # Python tooling config
└── README.md                # This file
```

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for the frontend)
- API keys: [NewsAPI](https://newsapi.org/), [GNews](https://gnews.io/), [OpenAI](https://platform.openai.com/)

### 1. Clone & Configure

```bash
git clone https://github.com/your-username/TruthStream-AI.git
cd TruthStream-AI
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Run Locally (No Docker)

**Terminal 1 — Backend API:**
```bash
pip install -r api/requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd Frontend
npm install
npm run dev
```

Open **http://localhost:3000** — the system will automatically:
- Start in demo mode with sample articles
- Fetch real news from NewsAPI & GNews every 60 seconds
- Classify articles as Fake/Real
- Push updates to the dashboard in real-time via WebSocket

### 3. Run with Docker (Full Pipeline)

```bash
docker-compose up --build
```

This starts the complete stack: Zookeeper → Kafka → Spark → MongoDB → API → Frontend.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check + mode (live/demo) |
| `GET` | `/articles` | Paginated article list with filters |
| `GET` | `/articles/{id}` | Single article by ID |
| `GET` | `/stats` | System statistics (counts, sources, rates) |
| `GET` | `/stats/timeline` | Articles per hour (last 24h) |
| `POST` | `/explain` | GPT explanation of classification |
| `POST` | `/summarize` | GPT article summary |
| `WS` | `/ws/articles` | Real-time article stream |
| `GET` | `/articles/stream` | SSE fallback stream |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEWSAPI_KEY` | NewsAPI.org API key | — |
| `GNEWS_KEY` | GNews.io API key | — |
| `OPENAI_API_KEY` | OpenAI API key (for GPT explain) | — |
| `OPENAI_MODEL` | GPT model name | `gpt-4o-mini` |
| `POLL_INTERVAL_SECONDS` | News fetch interval | `60` |
| `NEWSAPI_QUERY` | NewsAPI search query | `politics OR election OR breaking` |
| `GNEWS_QUERY` | GNews search query | `politics` |
| `MONGO_URI_EXTERNAL` | MongoDB connection string | `mongodb://localhost:27017` |
| `NEXT_PUBLIC_API_URL` | Frontend → API base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | Frontend → WebSocket URL | `ws://localhost:8000` |

---

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | Next.js dashboard |
| `api` | 8000 | FastAPI backend |
| `mongo` | 27017 | MongoDB database |
| `kafka` | 29092 | Kafka broker |
| `spark-master` | 8080 | Spark master UI |
| `zookeeper` | 2181 | Kafka coordination |

---

## Testing

```bash
# Run the full test suite
pip install -r requirements-dev.txt
pytest

# Quick API smoke test (requires running server)
python test_api.py
```