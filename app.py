from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Cơ sở dữ liệu key với device_id
keys_db = {
    "ABC123": {
        "expires_at": datetime(2025, 12, 31),
        "device_id": None
    }
}

@app.route("/")
def index():
    return render_template("index.html", keys=keys_db)

@app.route("/add", methods=["POST"])
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
def extend_key(key):
    days = int(request.form["days"])
    if key in keys_db:
        keys_db[key]["expires_at"] += timedelta(days=days)
    return redirect(url_for("index"))

@app.route("/delete/<key>", methods=["POST"])
def delete_key(key):
    if key in keys_db:
        del keys_db[key]
    return redirect(url_for("index"))

# ✅ Gỡ thiết bị khỏi key
@app.route("/unassign/<key>", methods=["POST"])
def unassign_key(key):
    if key in keys_db:
        keys_db[key]["device_id"] = None
    return redirect(url_for("index"))

# ✅ Kiểm tra key + device_id
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
