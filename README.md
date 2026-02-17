# ᚱ RUNE Playground

> "Every prompt is a spell"

Interactive web app for the [RUNE Framework](https://github.com/neurabytelabs/rune) — transform simple prompts into powerful, structured LLM instructions through 8 archetypal layers, then validate output quality with the Spinoza philosophical validator.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/neurabytelabs/rune-playground.git
cd rune-playground

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your Gemini API key and RUNE_PATH

# 4. Run
RUNE_PATH=/path/to/master-prompts RUNE_API_KEY=your-key uvicorn app:app --reload
```

Open http://localhost:8000

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RUNE_API_KEY` | Gemini API key | (required) |
| `RUNE_API_URL` | Gemini endpoint | gemini-2.0-flash |
| `RUNE_PATH` | Path to repo containing `rune/` package | `/opt/rune` |
| `RATE_LIMIT` | Casts per IP per day | `5` |

## Docker

```bash
docker build -t rune-playground .
docker run -p 8000:8000 -e RUNE_API_KEY=your-key rune-playground
```

## Stack

- **Backend:** Python FastAPI
- **Frontend:** Single HTML file (vanilla JS, zero dependencies)
- **AI:** RUNE 8-layer enhancer → Gemini API → Spinoza validator
- **Deploy:** Docker / Coolify ready

## License

MIT — Built by [NeuraByte Labs](https://neurabytelabs.com)
