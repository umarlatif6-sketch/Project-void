"""
void-engine-sdk — Basic Flask Example
Drop this into any Flask app in under 10 lines.
"""

from flask import Flask, request, jsonify
from void_sdk import VoidSDK

app = Flask(__name__)
sdk = VoidSDK()  # FREE tier — local .void_memory.db, no license key needed


@app.route("/encode", methods=["POST"])
def encode():
    data = request.json or {}
    message = data.get("message", "")

    result = sdk.track(
        entity=f"user:{request.remote_addr}",
        condition=f"frequency:432hz chars:{len(message)}",
        action="encode",
        codon="voidecho",
        meta={"message_length": len(message)},
    )

    if not result["ok"]:
        return jsonify({"error": result["reason"]}), 429

    return jsonify({
        "digest": result["digest"],
        "formation_score": result["formation_score"],
        "tier": result["tier"],
    })


@app.route("/stats")
def stats():
    return jsonify(sdk.stats())


@app.route("/recall")
def recall():
    entity = request.args.get("entity")
    codon = request.args.get("codon")
    return jsonify(sdk.recall(entity=entity, codon=codon, limit=20))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
