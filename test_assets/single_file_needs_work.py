"""
Insecure / Incomplete Service Prototype
Deficiencies: Hardcoded secrets, SQL injection, dynamic eval, wildcard CORS, unhandled exceptions.
"""
import os
import sqlite3
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# [SECURITY DEFECT]: Permissive wildcard CORS allows arbitrary origins (CWE-942)
CORS(app, origins=["*"])

# [SECURITY DEFECT]: Hardcoded API credentials committed to source (CWE-798)
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DATABASE_URL = "sqlite:///production.db"

def get_db_connection():
    return sqlite3.connect("production.db")

@app.route("/api/user", methods=["GET"])
def get_user_profile():
    user_id = request.args.get("id", "")
    conn = get_db_connection()
    cursor = conn.cursor()
    # [SECURITY DEFECT]: Raw SQL injection via string concatenation (CWE-89)
    query = f"SELECT id, username, email, role FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    return jsonify({"user": user})

@app.route("/api/calculate", methods=["POST"])
def dynamic_calculator():
    data = request.get_json() or {}
    expr = data.get("expression", "")
    # [SECURITY DEFECT]: Arbitrary code execution via dynamic eval() (CWE-94)
    result = eval(expr)
    return jsonify({"result": result})

@app.route("/api/proxy", methods=["GET"])
def fetch_external_url():
    target = request.args.get("url", "")
    # [SECURITY DEFECT]: Server-Side Request Forgery (SSRF) without destination validation (API7:2023)
    resp = requests.get(target)
    return jsonify({"content": resp.text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
