# Chess Analyzer ♟️

Analyze your Chess.com games with Stockfish, then get plain-English move reviews from an LLM grounded in opening theory via RAG.

## Features
- Fetch and store game archives from the Chess.com API
- Per-move Stockfish evaluation with classification (blunder, mistake, inaccuracy, best, etc.)
- Mate-in detection and best-move suggestions
- Interactive eval chart — click a point to jump to that position on the board
- Move-quality, accuracy, opening, and result-distribution dashboards
- LLM-generated review of any move, grounded in an opening-theory RAG index
- Per-opponent filtering

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL 15, python-chess, Stockfish
- **LLM / RAG**: LangChain + Groq, ChromaDB, sentence-transformers
- **Frontend**: Next.js 16, React 19, Tailwind v4, react-chessboard, Recharts
- **Infra**: Docker Compose

## Setup

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for the frontend dev server)
- A [Groq API key](https://console.groq.com/) for LLM reviews

### 1. Configure environment
Copy the example file and fill it in:
```bash
cp .env.example .env
```
Edit `.env`:
```env
POSTGRES_USER=chess
POSTGRES_PASSWORD=change_me
POSTGRES_DB=chess_db
STOCKFISH_PATH=/usr/games/stockfish
GROQ_API_KEY=your_groq_key_here
```

### 2. Start backend + database
```bash
docker-compose up --build -d
```
The API is served at `http://localhost:8000`.

### 3. Start frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000`.

## Usage
1. Enter your Chess.com username on the home page.
2. Click **Analyze** — recent games are fetched and queued for Stockfish analysis in the background.
3. Refresh after a minute or two. Browse games, click a game to see the eval chart and per-move classification.
4. Click any move and request an **AI review** for an LLM explanation grounded in opening theory.

## Key API endpoints
- `POST /analyze/{username}?limit=5&opponent=...` — kick off analysis
- `GET /games/{username}` — list analyzed games
- `GET /game/{game_id}` — game + per-move analysis
- `GET /stats/{username}` — aggregate dashboard stats
- `GET /moves/{username}/{classification}` — filter moves by classification
- `GET /review/move/{move_id}` — LLM review for a single move

## Project layout
```
backend/app/
  api.py                 # FastAPI routes
  batch.py               # Background analysis pipeline
  game_analysis.py       # Stockfish-driven per-move analysis
  feature_extraction.py  # Aggregated stats / features
  player_stats.py        # Dashboard stats
  llm_reviewer.py        # LLM review with RAG retrieval
  rag.py                 # Chroma vector store for opening theory
  chesscom.py            # Chess.com API client
  models.py / database.py / crud.py
frontend/app/
  page.tsx               # Main dashboard
  components/            # Board, charts, lists, etc.
```

## Security note
`.env` is gitignored. Never commit real API keys. If a key has been exposed, rotate it in the Groq console.
