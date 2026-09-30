# KnightLens ♞
Unlimited, local-first chess game review using Stockfish.

## Requirements
- Python 3.11+
- Node.js 20+
- Stockfish chess engine

## Windows setup
1. Download Stockfish and note the path to `stockfish-windows-x86-64-avx2.exe`.
2. Backend:
   ```powershell
   cd backend
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   $env:STOCKFISH_PATH="C:\path\to\stockfish.exe"
   uvicorn app.main:app --reload
   ```
3. Frontend, in another terminal:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
4. Open http://localhost:3000

Paste a PGN or upload a `.pgn`, then click **Review game**.

## V1 features
- PGN paste and upload
- Full legal position reconstruction
- Stockfish analysis per move
- Best move + principal variation
- Centipawn-loss based move labels
- White/Black accuracy estimate
- Interactive move navigation
- Responsive board/review UI

## Next upgrades
Evaluation graph, mate-aware/win-probability classifications, opening detection, brilliant/great/missed-win logic, AI coaching, batch PGNs, Chess.com URL import, saved review history.
