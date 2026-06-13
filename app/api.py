"""A tiny Flask API wrapping the calculator. This is our 'app under test'.

Run locally:  flask --app app.api run   (or: python -m app.api)
"""
from flask import Flask, jsonify, request

from app import calculator

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/calculate")
def calculate():
    data = request.get_json(silent=True) or {}
    op = data.get("op")
    try:
        a = float(data["a"])
        b = float(data["b"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Provide numeric 'a' and 'b'"), 400

    ops = {
        "add": calculator.add,
        "subtract": calculator.subtract,
        "multiply": calculator.multiply,
        "divide": calculator.divide,
    }
    if op not in ops:
        return jsonify(error=f"Unknown op '{op}'"), 400

    try:
        return jsonify(result=ops[op](a, b))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
