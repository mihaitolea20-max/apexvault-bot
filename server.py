"""
LSFD Market License Server
Porneste cu: python server.py
"""

from flask import Flask, request, jsonify
import sqlite3, secrets, hashlib, json
from datetime import datetime, timedelta
from functools import wraps
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH      = "licenses.db"
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "123456789D")  # folosit de bot

PLANS = {
    "1d":       timedelta(days=1),
    "7d":       timedelta(days=7),
    "1m":       timedelta(days=30),
    "lifetime": None,
}

# ── Database ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                key         TEXT UNIQUE NOT NULL,
                plan        TEXT NOT NULL,
                expires     TEXT,
                hwid        TEXT,
                token       TEXT,
                created     TEXT NOT NULL,
                activated   TEXT,
                revoked     INTEGER DEFAULT 0,
                note        TEXT,
                ip_address  TEXT,
                pc_name     TEXT,
                os_info     TEXT,
                username    TEXT
            )
        """)
        db.commit()

# ── Helpers ───────────────────────────────────────────────────────────────────
def generate_key():
    """Genereaza un key de forma SM-XXXX-XXXX-XXXX-XXXX"""
    part = lambda: secrets.token_hex(2).upper()
    return f"SM-{part()}-{part()}-{part()}-{part()}"

def generate_token(key: str, hwid: str) -> str:
    raw = f"{key}:{hwid}:{secrets.token_hex(8)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")

def parse_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")

def days_left(expires_str: str | None) -> int | str:
    if expires_str is None:
        return "∞"
    exp = parse_dt(expires_str)
    diff = (exp - datetime.utcnow()).days
    return max(0, diff)

# ── Admin middleware ──────────────────────────────────────────────────────────
def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        secret = request.headers.get("X-Admin-Secret") or request.json.get("admin_secret", "")
        if secret != ADMIN_SECRET:
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# ════════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS PUBLICE (folosite de scriptul PS)
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/validate", methods=["POST"])
def validate():
    """Activare key pe un HWID."""
    data = request.get_json(force=True)
    key  = (data.get("key") or "").strip().upper()
    hwid = (data.get("hwid") or "").strip()

    if not key or not hwid:
        return jsonify({"valid": False, "reason": "Date lipsa."})

    with get_db() as db:
        row = db.execute("SELECT * FROM licenses WHERE key = ?", (key,)).fetchone()

        if not row:
            return jsonify({"valid": False, "reason": "Key inexistent."})
        if row["revoked"]:
            return jsonify({"valid": False, "reason": "Key revocat."})

        # Verifica expirare
        if row["expires"]:
            if datetime.utcnow() > parse_dt(row["expires"]):
                return jsonify({"valid": False, "reason": "Key expirat."})

        # Daca e deja activat pe alt HWID
        if row["hwid"] and row["hwid"] != hwid:
            return jsonify({"valid": False, "reason": "Key deja activat pe alt PC."})

        # Prima activare — legam HWID-ul
        token = row["token"]
        if not row["hwid"]:
            token = generate_token(key, hwid)
            db.execute(
                "UPDATE licenses SET hwid=?, token=?, activated=? WHERE key=?",
                (hwid, token, fmt_dt(datetime.utcnow()), key)
            )
            db.commit()

        expires_display = row["expires"] if row["expires"] else "Lifetime"
        return jsonify({
            "valid":     True,
            "token":     token,
            "plan":      row["plan"],
            "expires":   expires_display,
            "days_left": days_left(row["expires"]),
        })


@app.route("/check", methods=["POST"])
def check():
    """Verifica o licenta deja activata (token + key)."""
    data  = request.get_json(force=True)
    key   = (data.get("key") or "").strip().upper()
    token = (data.get("token") or "").strip()

    if not key or not token:
        return jsonify({"valid": False})

    with get_db() as db:
        row = db.execute(
            "SELECT * FROM licenses WHERE key = ? AND token = ?", (key, token)
        ).fetchone()

        if not row or row["revoked"]:
            return jsonify({"valid": False})

        if row["expires"]:
            if datetime.utcnow() > parse_dt(row["expires"]):
                return jsonify({"valid": False, "reason": "Expirat."})

        expires_display = row["expires"] if row["expires"] else "Lifetime"
        return jsonify({
            "valid":     True,
            "plan":      row["plan"],
            "expires":   expires_display,
            "days_left": days_left(row["expires"]),
        })


# ════════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS ADMIN (folosite de botul Discord)
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/admin/generate", methods=["POST"])
@require_admin
def admin_generate():
    """Genereaza un key nou.  Body: { plan, note, admin_secret }"""
    data = request.get_json(force=True)
    plan = data.get("plan", "").lower()

    if plan not in PLANS:
        return jsonify({"ok": False, "error": f"Plan invalid. Disponibile: {list(PLANS.keys())}"})

    delta   = PLANS[plan]
    expires = fmt_dt(datetime.utcnow() + delta) if delta else None
    key     = generate_key()
    note    = data.get("note", "")
    created = fmt_dt(datetime.utcnow())

    with get_db() as db:
        db.execute(
            "INSERT INTO licenses (key, plan, expires, created, note) VALUES (?,?,?,?,?)",
            (key, plan, expires, created, note)
        )
        db.commit()

    return jsonify({
        "ok":      True,
        "key":     key,
        "plan":    plan,
        "expires": expires if expires else "Lifetime",
    })


@app.route("/admin/revoke", methods=["POST"])
@require_admin
def admin_revoke():
    """Revocare key.  Body: { key, admin_secret }"""
    data = request.get_json(force=True)
    key  = (data.get("key") or "").strip().upper()

    with get_db() as db:
        cur = db.execute("UPDATE licenses SET revoked=1 WHERE key=?", (key,))
        db.commit()

    if cur.rowcount:
        return jsonify({"ok": True, "message": f"Key {key} revocat."})
    return jsonify({"ok": False, "error": "Key negasit."})


@app.route("/admin/info", methods=["POST"])
@require_admin
def admin_info():
    """Info despre un key.  Body: { key, admin_secret }"""
    data = request.get_json(force=True)
    key  = (data.get("key") or "").strip().upper()

    with get_db() as db:
        row = db.execute("SELECT * FROM licenses WHERE key=?", (key,)).fetchone()

    if not row:
        return jsonify({"ok": False, "error": "Key negasit."})

    return jsonify({
        "ok":         True,
        "key":        row["key"],
        "plan":       row["plan"],
        "expires":    row["expires"] or "Lifetime",
        "days_left":  days_left(row["expires"]),
        "hwid":       row["hwid"] or "Neactivat",
        "activated":  row["activated"] or "—",
        "created":    row["created"],
        "revoked":    bool(row["revoked"]),
        "note":       row["note"] or "",
        "ip_address": row["ip_address"] or "—",
        "pc_name":    row["pc_name"] or "—",
        "os_info":    row["os_info"] or "—",
        "username":   row["username"] or "—",
    })


@app.route("/admin/list", methods=["POST"])
@require_admin
def admin_list():
    """Lista toate cheile (ultimele 50).  Body: { admin_secret }"""
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM licenses ORDER BY id DESC LIMIT 50"
        ).fetchall()

    keys = []
    for r in rows:
        keys.append({
            "key":     r["key"],
            "plan":    r["plan"],
            "expires": r["expires"] or "Lifetime",
            "hwid":    r["hwid"] or "—",
            "revoked": bool(r["revoked"]),
            "note":    r["note"] or "",
        })
    return jsonify({"ok": True, "keys": keys})




@app.route("/admin/resethwid", methods=["POST"])
@require_admin
def admin_resethwid():
    """Reseteaza HWID-ul unui key (pt transfer PC).  Body: { key, admin_secret }"""
    data = request.get_json(force=True)
    key  = (data.get("key") or "").strip().upper()
    with get_db() as db:
        cur = db.execute("UPDATE licenses SET hwid=NULL, token=NULL, activated=NULL WHERE key=?", (key,))
        db.commit()
    if cur.rowcount:
        return jsonify({"ok": True, "message": f"HWID resetat pentru {key}."})
    return jsonify({"ok": False, "error": "Key negasit."})


@app.route("/admin/extend", methods=["POST"])
@require_admin
def admin_extend():
    """Extinde expirarea unui key.  Body: { key, days, admin_secret }"""
    data = request.get_json(force=True)
    key  = (data.get("key") or "").strip().upper()
    days = int(data.get("days", 0))
    if days <= 0:
        return jsonify({"ok": False, "error": "Numar de zile invalid."})
    with get_db() as db:
        row = db.execute("SELECT * FROM licenses WHERE key=?", (key,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Key negasit."})
        if row["expires"] is None:
            return jsonify({"ok": False, "error": "Key-ul e Lifetime, nu poate fi extins."})
        try:
            base = max(datetime.utcnow(), parse_dt(row["expires"]))
        except:
            base = datetime.utcnow()
        new_exp = fmt_dt(base + timedelta(days=days))
        db.execute("UPDATE licenses SET expires=? WHERE key=?", (new_exp, key))
        db.commit()
    return jsonify({"ok": True, "new_expires": new_exp, "days_added": days})


@app.route("/admin/stats", methods=["POST"])
@require_admin
def admin_stats():
    """Statistici generale.  Body: { admin_secret }"""
    with get_db() as db:
        total    = db.execute("SELECT COUNT(*) FROM licenses").fetchone()[0]
        active   = db.execute("SELECT COUNT(*) FROM licenses WHERE revoked=0 AND (expires IS NULL OR expires > ?)",
                              (fmt_dt(datetime.utcnow()),)).fetchone()[0]
        expired  = db.execute("SELECT COUNT(*) FROM licenses WHERE revoked=0 AND expires IS NOT NULL AND expires <= ?",
                              (fmt_dt(datetime.utcnow()),)).fetchone()[0]
        revoked  = db.execute("SELECT COUNT(*) FROM licenses WHERE revoked=1").fetchone()[0]
        activated= db.execute("SELECT COUNT(*) FROM licenses WHERE hwid IS NOT NULL AND revoked=0").fetchone()[0]
        by_plan  = {}
        for plan in ["1d","7d","1m","lifetime"]:
            by_plan[plan] = db.execute("SELECT COUNT(*) FROM licenses WHERE plan=? AND revoked=0", (plan,)).fetchone()[0]
    return jsonify({"ok": True, "total": total, "active": active, "expired": expired,
                    "revoked": revoked, "activated": activated, "by_plan": by_plan})


@app.route("/admin/search", methods=["POST"])
@require_admin
def admin_search():
    """Cauta keys dupa nota.  Body: { query, admin_secret }"""
    data  = request.get_json(force=True)
    query = (data.get("query") or "").strip()
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM licenses WHERE note LIKE ? OR key LIKE ? ORDER BY id DESC LIMIT 20",
            (f"%{query}%", f"%{query}%")
        ).fetchall()
    results = []
    for r in rows:
        results.append({
            "key": r["key"], "plan": r["plan"],
            "expires": r["expires"] or "Lifetime",
            "hwid": r["hwid"] or "—",
            "revoked": bool(r["revoked"]),
            "note": r["note"] or "",
            "days_left": days_left(r["expires"]),
        })
    return jsonify({"ok": True, "results": results})


@app.route("/admin/bulkgenerate", methods=["POST"])
@require_admin
def admin_bulk():
    """Genereaza mai multe keys.  Body: { plan, count, admin_secret }"""
    data  = request.get_json(force=True)
    plan  = data.get("plan", "").lower()
    count = min(int(data.get("count", 1)), 20)
    if plan not in PLANS:
        return jsonify({"ok": False, "error": "Plan invalid."})
    delta   = PLANS[plan]
    created = fmt_dt(datetime.utcnow())
    keys    = []
    with get_db() as db:
        for _ in range(count):
            expires = fmt_dt(datetime.utcnow() + delta) if delta else None
            key     = generate_key()
            db.execute("INSERT INTO licenses (key, plan, expires, created, note) VALUES (?,?,?,?,?)",
                       (key, plan, expires, created, f"bulk by {data.get('note','admin')}"))
            keys.append({"key": key, "expires": expires or "Lifetime"})
        db.commit()
    return jsonify({"ok": True, "plan": plan, "keys": keys})

# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("=" * 50)
    print("  LSFD Market pornit")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
