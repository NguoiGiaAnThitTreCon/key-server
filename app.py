from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from datetime import datetime, timedelta
from functools import wraps
import os

app = Flask(__name__)

# ==== THÔNG TIN ĐĂNG NHẬP QUẢN TRỊ ====
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "121386925@"

def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def authenticate():
    return Response(
        "Bạn cần đăng nhập để truy cập khu vực này.\n",
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

# ==== CƠ SỞ DỮ LIỆU KEY (tạm trong RAM) ====
keys_db = {
    "ABC123": {
        "expires_at": datetime(2025, 12, 31),
        "device_id": None
    }
}

# ==== GIAO DIỆN WEB ====
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
    return redirect(url_for("index"))

@app.route("/extend/<key>", methods=["POST"])
@requires_auth
def extend_key(key):
    days = int(request.form["days"])
    if key in keys_db:
        keys_db[key]["expires_at"] += timedelta(days=days)
    return redirect(url_for("index"))

@app.route("/delete/<key>", methods=["POST"])
@requires_auth
def delete_key(key):
    if key in keys_db:
        del keys_db[key]
    return redirect(url_for("index"))

@app.route("/unassign/<key>", methods=["POST"])
@requires_auth
def unassign_key(key):
    if key in keys_db:
        keys_db[key]["device_id"] = None
    return redirect(url_for("index"))

# ==== API CHO CLIENT ====
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
        return jsonify({"valid": True, "expires_at": data["expires_at"].isoformat()})

    if data["device_id"] == device_id:
        return jsonify({"valid": True, "expires_at": data["expires_at"].isoformat()})

    return jsonify({"valid": False, "error": "Key đã được sử dụng trên thiết bị khác."})

# ==== CHẠY SERVER ====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # dùng biến PORT nếu có
    app.run(host="0.0.0.0", port=port)
