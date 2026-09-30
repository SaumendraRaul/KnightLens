import io, os, shutil
import chess, chess.pgn, chess.engine
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="KnightLens API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class ReviewRequest(BaseModel):
    pgn: str
    depth: int = 14

def engine_path():
    configured = os.getenv("STOCKFISH_PATH")
    if configured and os.path.exists(configured): return configured
    found = shutil.which("stockfish")
    if found: return found
    for p in ["stockfish.exe", "./stockfish/stockfish.exe", "./stockfish/stockfish"]:
        if os.path.exists(p): return p
    raise HTTPException(500, "Stockfish not found. Set STOCKFISH_PATH or put Stockfish on PATH.")

def pov_cp(score, turn):
    s = score.pov(turn)
    if s.is_mate():
        m = s.mate()
        return 100000 if (m or 0) > 0 else -100000
    return s.score(mate_score=100000) or 0

def classify(cpl: int, best: bool, book=False):
    if book: return "book"
    if best or cpl <= 8: return "best"
    if cpl <= 25: return "excellent"
    if cpl <= 60: return "good"
    if cpl <= 120: return "inaccuracy"
    if cpl <= 250: return "mistake"
    return "blunder"

@app.get("/health")
def health(): return {"ok": True}

@app.post("/review")
def review(req: ReviewRequest):
    game = chess.pgn.read_game(io.StringIO(req.pgn))
    if not game: raise HTTPException(400, "Could not parse PGN")
    board = game.board()
    moves = list(game.mainline_moves())
    if not moves: raise HTTPException(400, "PGN contains no moves")
    out=[]
    white_losses=[]; black_losses=[]
    with chess.engine.SimpleEngine.popen_uci(engine_path()) as eng:
        for ply, move in enumerate(moves, start=1):
            mover = board.turn
            san = board.san(move)
            before = eng.analyse(board, chess.engine.Limit(depth=max(8,min(req.depth,22))), multipv=1)
            best_move = before.get("pv", [None])[0]
            best_san = board.san(best_move) if best_move else None
            best_eval = pov_cp(before["score"], mover)
            pv_sans=[]; tmp=board.copy()
            for pv_move in before.get("pv", [])[:6]:
                if pv_move not in tmp.legal_moves: break
                pv_sans.append(tmp.san(pv_move)); tmp.push(pv_move)
            board.push(move)
            after = eng.analyse(board, chess.engine.Limit(depth=max(8,min(req.depth,22))))
            played_eval = pov_cp(after["score"], mover)
            cpl = max(0, min(2000, best_eval - played_eval))
            is_best = move == best_move
            label = classify(cpl, is_best)
            (white_losses if mover==chess.WHITE else black_losses).append(cpl)
            out.append({"ply":ply,"move_number":(ply+1)//2,"color":"white" if mover else "black","san":san,"uci":move.uci(),"fen":board.fen(),"evaluation_cp":played_eval,"best_move":best_san,"centipawn_loss":cpl,"classification":label,"pv":pv_sans})
    def accuracy(losses):
        if not losses: return 100.0
        avg=sum(losses)/len(losses)
        return round(max(0.0, 100.0 * (2.718281828 ** (-avg/260.0))),1)
    return {"headers":dict(game.headers),"initial_fen":game.board().fen(),"moves":out,"summary":{"white_accuracy":accuracy(white_losses),"black_accuracy":accuracy(black_losses),"plies":len(out)}}
