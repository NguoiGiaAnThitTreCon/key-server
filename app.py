from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from datetime import datetime, timedelta
from functools import wraps
import os
import json

app = Flask(__name__)
DATA_FILE = "data.json"

# ==== Đọc / Ghi File JSON ====
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(keys_db, f, indent=4, default=str)

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)
        # Chuyển chuỗi ngày về datetime
        result = {}
        for key, data in raw.items():
            result[key] = {
                "expires_at": datetime.fromisoformat(data["expires_at"]),
                "device_id": data.get("device_id")
            }
        return result

# ==== Khởi tạo dữ liệu ====
keys_db = load_data()

# ==== Bảo vệ trang quản trị ====
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "123456")

def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def authenticate():
    return Response(
        "Bạn cần đăng nhập để truy cập.\n",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ==== Trang quản trị ====
@app.route("/")
@requires_auth
def index():
    return render_template("index.html", keys=keys_db)

@app.route("/add", methods=["POST"])
@requires_auth
def add_key():
    key = request.form["key"]
    days = int(request.form["days"])
    if key not in keys_db:
        keys_db[key] = {
            "expires_at": datetime.now() + timedelta(days=days),
            "device_id": None
        }
        save_data()
    return redirect(url_for("index"))

@app.route("/extend/<key>", methods=["POST"])
@requires_auth
def extend_key(key):
    days = int(request.form["days"])
    if key in keys_db:
        keys_db[key]["expires_at"] += timedelta(days=days)
        save_data()
    return redirect(url_for("index"))

@app.route("/delete/<key>", methods=["POST"])
@requires_auth
def delete_key(key):
    if key in keys_db:
        del keys_db[key]
        save_data()
    return redirect(url_for("index"))

@app.route("/unassign/<key>", methods=["POST"])
@requires_auth
def unassign_key(key):
    if key in keys_db:
        keys_db[key]["device_id"] = None
        save_data()
    return redirect(url_for("index"))

# ==== API cho phần mềm client ====
@app.route("/check/<key>", methods=["GET"])
def check_key(key):
    device_id = request.args.get("device_id")
    data = keys_db.get(key)

    if not data:
        return jsonify({"valid": False, "error": "Key không tồn tại"})

    if data["expires_at"] <= datetime.now():
        return jsonify({"valid": False, "error": "Key đã hết hạn"})

    if data["device_id"] is None:
        data["device_id"] = device_id
        save_data()
        return jsonify({"valid": True, "expires_at": data["expires_at"].isoformat()})

    if data["device_id"] == device_id:
        return jsonify({"valid": True, "expires_at": data["expires_at"].isoformat()})

    return jsonify({"valid": False, "error": "Key đã được sử dụng trên thiết bị khác."})

# ==== Chạy server ====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
