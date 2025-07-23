from flask import Flask, request, jsonify
import chess
import chess.engine
import logging
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STOCKFISH_PATH = "/usr/games/stockfish"
MAX_ANALYSIS_TIME = 10  # seconds
DEPTH_RANGE = (20, 30)  # Your requested depth range

@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    fen = data.get("fen")
    if not fen:
        return jsonify({"error": "No FEN provided"}), 400

    try:
        board = chess.Board(fen)
    except ValueError as e:
        return jsonify({"error": f"Invalid FEN: {str(e)}"}), 400

    start_time = time.time()
    best_result = None
    
    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            engine.configure({"Threads": 2})
            
            for depth in range(*DEPTH_RANGE):
                if time.time() - start_time > MAX_ANALYSIS_TIME:
                    break
                
                try:
                    result = engine.analyse(
                        board,
                        chess.engine.Limit(depth=depth),
                        multipv=1
                    )
                    
                    # Keep the deepest analysis we can get within time limits
                    if best_result is None or result.get("depth", 0) > best_result.get("depth", 0):
                        best_result = result
                        
                except chess.engine.EngineError as e:
                    logger.warning(f"Depth {depth} analysis failed: {str(e)}")
                    continue

            if not best_result:
                return jsonify({"error": "No successful analysis completed"}), 500
                
            # Process the best result
            score = best_result["score"]
            if score.is_mate():
                score_value = f"mate {score.mate()}"
            else:
                score_value = score.relative.score()
            
            best_line = [move.uci() for move in best_result["pv"]]
            
            return jsonify({
                "moves": best_line,
                "score": score_value,
                "depth": best_result.get("depth", 0),
                "time_used": round(time.time() - start_time, 2)
            })
            
    except chess.engine.EngineTerminatedError:
        logger.error("Stockfish engine terminated unexpectedly")
        return jsonify({"error": "Engine terminated"}), 500
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            return jsonify({"status": "healthy", "engine": "stockfish"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/')
def home():
    return "♟️ Stockfish Cloud Server Running (Depth 20-30 Analysis)"

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=8000)