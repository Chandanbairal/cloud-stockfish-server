from flask import Flask, request, jsonify
import chess
import chess.engine
import logging
import time
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STOCKFISH_PATH = "/usr/bin/stockfish"  # Now properly linked in Dockerfile
MIN_DEPTH = 20
MAX_DEPTH = 30
TIME_LIMIT = 10  # seconds

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
            engine.configure({"Threads": 4, "Hash": 128})  # Better configuration
            
            for depth in range(MIN_DEPTH, MAX_DEPTH + 1):
                if time.time() - start_time > TIME_LIMIT:
                    logger.info(f"Time limit reached at depth {depth}")
                    break
                
                try:
                    result = engine.analyse(
                        board,
                        chess.engine.Limit(depth=depth),
                        multipv=1
                    )
                    
                    # Keep the deepest analysis
                    if best_result is None or result.get("depth", 0) > best_result.get("depth", 0):
                        best_result = result
                        logger.info(f"New best depth: {depth}")
                        
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
            
            return jsonify({
                "moves": [move.uci() for move in best_result["pv"]],
                "score": score_value,
                "depth": best_result.get("depth", 0),
                "time_used": round(time.time() - start_time, 2),
                "nodes": best_result.get("nodes", 0)
            })
            
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            return jsonify({
                "status": "healthy",
                "engine": engine.id["name"],
                "protocol": engine.id["protocol"]
            }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "expected_path": STOCKFISH_PATH
        }), 500

@app.route('/')
def home():
    return "♟️ Stockfish Cloud Server (Depth 20-30 Analysis)"

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=8000)