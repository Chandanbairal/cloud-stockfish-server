from flask import Flask, request, jsonify
import chess
import chess.engine

app = Flask(__name__)

STOCKFISH_PATH = "/usr/games/stockfish" # Railway uses this path for binaries

@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    fen = data.get("fen")
    if not fen:
        return jsonify({"error": "No FEN provided"}), 400

    board = chess.Board(fen)
    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            best_score = None
            best_line = []

            for depth in range(20, 31):  # depth 20 to 30
                try:
                    result = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=1)
                    line = result["pv"]
                    score = result["score"].relative.score(mate_score=10000)

                    if best_score is None or score > best_score:
                        best_score = score
                        best_line = [move.uci() for move in line]

                except Exception as e:
                    continue

            return jsonify({
                "moves": best_line,
                "score": best_score
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "♟️ Stockfish Cloud Server Running"

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=8000)
