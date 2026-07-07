# cloud_endpoint.py
# Adaptive calibration server for StampedeShield.
# Before hackathon: run locally  → python cloud_endpoint.py
# Hackathon day:    deploy to Qualcomm Cloud AI 100 environment
#
# Test locally:
#   curl http://localhost:5000/health
#   curl -X POST http://localhost:5000/calibrate \
#     -H "Content-Type: application/json" \
#     -d '{"sensors":[500,600,700,800,900,600,500,400],"risk":75}'

from flask import Flask, jsonify, request
import numpy as np
import time

app   = Flask(__name__)
store = {
    "history":   [],   # list of normalised sensor vectors
    "start_time": time.time()
}

MAX_HISTORY = 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":          "ok",
        "samples_seen":    len(store["history"]),
        "uptime_seconds":  int(time.time() - store["start_time"])
    })


@app.route("/calibrate", methods=["POST"])
def calibrate():
    """
    Receives out-of-distribution sensor pattern from Snapdragon PC.
    Returns updated SPC thresholds based on historical distribution.
    """
    body = request.get_json(silent=True)
    if not body or "sensors" not in body:
        return jsonify({"error": "Missing 'sensors' field"}), 400

    sensors = body["sensors"]
    if len(sensors) != 8:
        return jsonify({"error": f"Expected 8 sensors, got {len(sensors)}"}), 400

    # Normalise and store
    normalised = [max(0.0, min(1.0, v / 1023.0)) for v in sensors]
    store["history"].append(normalised)
    if len(store["history"]) > MAX_HISTORY:
        store["history"].pop(0)

    n = len(store["history"])
    if n < 30:
        return jsonify({
            "ucl_sigma": 3.0, "alpha": 0.3,
            "status": "warmup", "samples": n
        })

    hist          = np.array(store["history"])
    mean_variance = float(np.mean(np.var(hist, axis=0)))

    # Wider threshold in naturally high-variance environments
    ucl_sigma = round(min(5.0, 3.0 + mean_variance * 4), 3)

    # Faster EWMA when high-risk events are frequent
    recent_high_risk = sum(
        1 for r in store["history"][-50:] if sum(r) / 8 > 0.6
    ) / 50
    alpha = round(min(0.6, 0.3 + recent_high_risk * 0.3), 3)

    return jsonify({
        "ucl_sigma":     ucl_sigma,
        "alpha":         alpha,
        "status":        "recalibrated",
        "samples":       n,
        "mean_variance": round(mean_variance, 4)
    })


@app.route("/reset", methods=["POST"])
def reset():
    """Clear all history — call at start of each new event deployment."""
    store["history"].clear()
    return jsonify({"status": "reset", "samples": 0})


if __name__ == "__main__":
    print("Cloud AI 100 calibration server on port 5000")
    print("Test: curl http://localhost:5000/health")
    app.run(host="0.0.0.0", port=5000, debug=False)
