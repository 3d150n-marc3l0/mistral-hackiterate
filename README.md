# 🎙️ Sentinel Daily — AI-Powered Tech Podcast Generator

> Transform the top stories from Hacker News into a fully produced, multilingual podcast episode — in minutes.

---

## Introduction

**Sentinel Daily** is an end-to-end AI pipeline that fetches the day's top tech stories, writes a natural two-host dialogue, synthesizes it into audio, and generates a matching cover image — all without human intervention.

It is powered by **Mistral Large** for scriptwriting and quality evaluation, **ElevenLabs** for voice synthesis, and **FLUX.1** (via Hugging Face) for cover art generation. The result is served through an interactive **Streamlit** web application.

---

## Overview

The system works in five sequential stages:

```
Hacker News API
      │
      ▼
 [1] News Ingestion      ← httpx + trafilatura (full article extraction)
      │
      ▼
 [2] Script Generation   ← Mistral Large 3 + Jinja2 prompt templates
      │
      ▼
 [2b] LLM-Judge          ← Mistral Small evaluates script quality (0–10)
      │
      ▼
 [3] Cover Art           ← Mistral Large (art direction) + FLUX.1-schnell (HF)
      │
      ▼
 [4] Voice Synthesis     ← ElevenLabs Multilingual v2 (Alex + Sam)
      │
      ▼
 [5] Streamlit UI        ← Generate, preview, save & browse episodes
```

**Hosts:**
| Host | Personality | Voice |
|------|-------------|-------|
| **Alex** | Senior Strategic Analyst — calm, authoritative, big-picture thinker | Deep, steady |
| **Sam** | Technical Explorer — energetic, curious, fast-paced | High-pitched, enthusiastic |

---

## Architecture Overview

```
mistral-hackiterate/
│
├── src/sentinel/                  # Main Python package
│   ├── app.py                     # Streamlit web application
│   │
│   ├── core/
│   │   └── pipeline.py            # Orchestrates all stages end-to-end
│   │
│   ├── services/
│   │   ├── news.py                # Hacker News ingestion + article extraction
│   │   ├── llm.py                 # Script generation, LLM-Judge & cover art prompt
│   │   └── audio.py              # ElevenLabs voice synthesis
│   │
│   ├── interfaces/
│   │   └── schemas.py             # Pydantic models (RawArticle, NewsScript, JudgeScore, …)
│   │
│   ├── prompts/
│   │   ├── podcast_script.jinja2  # Prompt: generate two-host dialogue from articles
│   │   ├── cover_art_prompt.jinja2# Prompt: Mistral as art director for FLUX.1
│   │   └── judge_script.jinja2   # Prompt: LLM-Judge quality evaluation
│   │
│   └── utils/
│       ├── config.py              # Loads .env via python-dotenv
│       └── logger.py              # Centralized rotating file + console logger
│
├── tests/
│   ├── test_api.py                # Mistral connectivity test
│   ├── test_eleven.py             # ElevenLabs connectivity test
│   └── test_judge.py              # LLM-Judge integration tests
│
├── outputs/                       # Saved podcast episodes (audio + cover + metadata)
├── logs/                          # Rotating log files (sentinel.log)
├── .env                           # Secret keys (not committed)
├── .env.example                   # Template with all required variables
└── pyproject.toml                 # Project dependencies (managed by uv)
```

---

## Environment Setup

### Prerequisites

- Python **3.12+**
- [`uv`](https://docs.astral.sh/uv/) package manager
- Accounts & API keys for: **Mistral AI**, **ElevenLabs**, **Hugging Face**

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd mistral-hackiterate

uv sync
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Mistral AI — script generation & LLM-Judge
MISTRAL_API_KEY=your_mistral_api_key_here

# ElevenLabs — voice synthesis
ELEVEN_API_KEY=your_elevenlabs_api_key_here
ELEVEN_MODEL_ID=eleven_multilingual_v2
VOICE_ID_ALEX=pNInz6obpgDQGcFma_JgB
VOICE_ID_SAM=EXAVITQu4vr4xnSDxMaL

# Hugging Face — cover image generation (FLUX.1)
HF_API_KEY=your_hf_token_here
HF_IMAGE_PROVIDER=together
HF_IMAGE_MODEL=black-forest-labs/FLUX.1-schnell

# LLM-Judge (optional quality scoring)
JUDGE_ENABLED=true
JUDGE_MODEL=mistral-small-latest

# Logging level: DEBUG | INFO | WARNING | ERROR
LOG_LEVEL=INFO
```

> **Note:** Voice IDs above are the ElevenLabs defaults for Adam and Rachel. You can swap them for any voice from the [ElevenLabs Voice Library](https://elevenlabs.io/voice-library).

---

## 🛠️ Makefile Commands

The project includes a `Makefile` to simplify common tasks both locally and with Docker.

### Local Development
- `make run`: Run the Streamlit app locally using `uv`.
- `make test`: Run all tests with `uv run pytest`.
- `make clean`: Remove generated logs, outputs, and `__pycache__` files.

### Docker Management
- `make build`: Build the Docker image (`sentinel-daily`).
- `make up`: Start the application in a detached Docker container.
- `make down`: Stop and remove the Docker container.
- `make logs`: View live logs from the running container.

---

## 🐳 Docker Deployment

To run the application inside a container:

1. **Build the image**:
   ```bash
   make build
   ```

2. **Run the container**:
   ```bash
   make up
   ```
   The app will be available at [http://localhost:8501](http://localhost:8501).

3. **Stop the container**:
   ```bash
   make down
   ```

---

## Running

### Start the web application (Local)

```bash
make run
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

**From the UI you can:**
- 🎛️ Choose the podcast language (English, Spanish, French, German, Italian)
- 📰 Set how many Hacker News stories to analyze (1–5)
- 🎙️ Fine-tune the voice parameters (stability, clarity, style) for each host
- 🚀 Generate a new episode and watch the live transcript
- 💾 Save the episode to `outputs/` with audio, cover image and metadata
- 📚 Browse and replay all previously saved episodes

### Run the tests

```bash
# All tests
uv run pytest tests/ -v

# LLM-Judge integration test only
uv run pytest tests/test_judge.py -v
```

### Logs

Application logs are written to `logs/sentinel.log` (rotating, 5 MB × 3 backups) and also printed to the console. Set `LOG_LEVEL=DEBUG` in `.env` to see the full Mistral prompts.

```bash
tail -f logs/sentinel.log
```
