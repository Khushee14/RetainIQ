import sqlite3
from datetime import datetime

import pandas as pd

DB_PATH = "retainiq.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS actions (
            action_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            risk_score INTEGER,
            suggested_action TEXT,
            status TEXT DEFAULT 'Pending',
            owner TEXT DEFAULT '',
            outcome TEXT DEFAULT '',
            created_date TEXT,
            updated_date TEXT
        )"""
    )
    return conn


def add_actions(entity_type, cases):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    added = 0
    conn = get_conn()
    try:
        for _, r in cases.iterrows():
            exists = conn.execute(
                "SELECT 1 FROM actions WHERE entity_type=? AND entity_id=?",
                (entity_type, str(r["entity_id"])),
            ).fetchone()
            if exists:
                continue
            conn.execute(
                """INSERT INTO actions
                   (entity_type, entity_id, risk_score, suggested_action, created_date, updated_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (entity_type, str(r["entity_id"]), int(r["RiskScore"]),
                 r["suggested_action"], now, now),
            )
            added += 1
        conn.commit()
    finally:
        conn.close()
    return added


def load_actions():
    conn = get_conn()
    try:
        return pd.read_sql("SELECT * FROM actions ORDER BY action_id DESC", conn)
    finally:
        conn.close()


def update_actions(df):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    df = df.fillna("")
    conn = get_conn()
    try:
        for _, r in df.iterrows():
            conn.execute(
                "UPDATE actions SET status=?, owner=?, outcome=?, updated_date=? WHERE action_id=?",
                (r["status"], str(r["owner"]), str(r["outcome"]), now, int(r["action_id"])),
            )
        conn.commit()
    finally:
        conn.close()


def clear_actions():
    conn = get_conn()
    try:
        conn.execute("DELETE FROM actions")
        conn.commit()
    finally:
        conn.close()


def apply_outcomes(id_to_outcome):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    updated = 0
    conn = get_conn()
    try:
        for eid, outcome in id_to_outcome.items():
            cur = conn.execute(
                "UPDATE actions SET outcome=?, status='Done', updated_date=? "
                "WHERE entity_id=? AND (outcome IS NULL OR outcome='')",
                (outcome, now, str(eid)),
            )
            updated += cur.rowcount
        conn.commit()
    finally:
        conn.close()
    return updated