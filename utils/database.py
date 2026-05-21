import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "data/smartresolve.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint TEXT NOT NULL,
            category TEXT,
            priority TEXT,
            summary TEXT,
            risk_level TEXT,
            risk_score INTEGER,
            resolution TEXT,
            customer_reply TEXT,
            should_escalate BOOLEAN,
            latency_ms INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] Database initialized.")

def save_ticket(data: dict, latency_ms: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tickets (
            complaint, category, priority, summary,
            risk_level, risk_score, resolution,
            customer_reply, should_escalate,
            latency_ms, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.get("complaint", ""),
        data.get("category", ""),
        data.get("priority", ""),
        data.get("summary", ""),
        data.get("risk_level", ""),
        data.get("risk_score", 0),
        data.get("resolution", ""),
        data.get("customer_reply", ""),
        data.get("should_escalate", False),
        latency_ms,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_all_tickets():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def save_policy_upload(filename: str, chunks: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policy_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            chunks INTEGER,
            uploaded_at TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO policy_uploads (filename, chunks, uploaded_at)
        VALUES (?, ?, ?)
    """, (filename, chunks, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_policy_uploads():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM policy_uploads ORDER BY uploaded_at DESC")
        rows = [dict(row) for row in cursor.fetchall()]
    except:
        rows = []
    conn.close()
    return rows

def get_analytics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tickets")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category")
    categories = dict(cursor.fetchall())

    cursor.execute("SELECT risk_level, COUNT(*) FROM tickets GROUP BY risk_level")
    risks = dict(cursor.fetchall())

    cursor.execute("SELECT AVG(latency_ms) FROM tickets")
    avg_latency = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE should_escalate=1")
    escalations = cursor.fetchone()[0]

    conn.close()
    return {
        "total_tickets": total,
        "categories": categories,
        "risk_distribution": risks,
        "avg_latency_ms": round(avg_latency),
        "total_escalations": escalations
    }