import sqlite3
from datetime import datetime
import json
import os


class Database:
    def __init__(self, db_path):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                input_data TEXT,
                output_data TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER,
                step TEXT,
                level TEXT DEFAULT 'info',
                message TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (execution_id) REFERENCES executions(id)
            );
            CREATE TABLE IF NOT EXISTS workflow_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS proxy_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                caller TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                service TEXT,
                subject TEXT,
                message TEXT NOT NULL,
                ai_response TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                sent_at TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS hunt_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                recipient TEXT,
                subject TEXT,
                source TEXT,
                body_preview TEXT,
                created_at TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

    def create_execution(self, workflow, input_data=None):
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        cur = conn.execute(
            "INSERT INTO executions (workflow, status, input_data, created_at) VALUES (?, ?, ?, ?)",
            (workflow, "running", json.dumps(input_data) if input_data else None, now),
        )
        exec_id = cur.lastrowid
        conn.commit()
        conn.close()
        return exec_id

    def complete_execution(self, exec_id, status, output=None):
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE executions SET status=?, output_data=?, completed_at=? WHERE id=?",
            (status, json.dumps(output) if output else None, now, exec_id),
        )
        conn.commit()
        conn.close()

    def add_log(self, exec_id, step, message, level="info"):
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO logs (execution_id, step, level, message, timestamp) VALUES (?, ?, ?, ?, ?)",
            (exec_id, step, level, message, now),
        )
        conn.commit()
        conn.close()

    def save_data(self, workflow, key, value):
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO workflow_data (workflow, key, value, created_at) VALUES (?, ?, ?, ?)",
            (workflow, key, json.dumps(value) if not isinstance(value, str) else value, now),
        )
        conn.commit()
        conn.close()

    def get_executions(self, workflow=None, limit=20):
        conn = self._get_conn()
        if workflow:
            rows = conn.execute(
                "SELECT * FROM executions WHERE workflow=? ORDER BY id DESC LIMIT ?",
                (workflow, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM executions ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def log_proxy_call(self, provider, model, tokens_used=0, caller="unknown"):
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO proxy_calls (provider, model, tokens_used, caller, created_at) VALUES (?, ?, ?, ?, ?)",
            (provider, model, tokens_used, caller, now),
        )
        conn.commit()
        conn.close()

    def get_proxy_stats(self, since_days=7):
        conn = self._get_conn()
        from datetime import datetime, timedelta
        since = (datetime.utcnow() - timedelta(days=since_days)).isoformat()
        rows = conn.execute(
            """SELECT provider, model, COUNT(*) as calls, SUM(tokens_used) as total_tokens
               FROM proxy_calls WHERE created_at >= ? GROUP BY provider, model
               ORDER BY calls DESC""",
            (since,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def create_contact(self, name, email, service, message, subject=None):
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        cur = conn.execute(
            """INSERT INTO contacts (name, email, service, subject, message, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
            (name, email, service, subject, message, now),
        )
        contact_id = cur.lastrowid
        conn.commit()
        conn.close()
        return contact_id

    def save_ai_response(self, contact_id, ai_response):
        conn = self._get_conn()
        conn.execute(
            "UPDATE contacts SET ai_response=? WHERE id=?",
            (ai_response, contact_id),
        )
        conn.commit()
        conn.close()

    def list_contacts(self, pending_only=True, limit=50):
        conn = self._get_conn()
        if pending_only:
            rows = conn.execute(
                "SELECT * FROM contacts WHERE status='pending' ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM contacts ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_contact(self, contact_id):
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM contacts WHERE id=?", (contact_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def mark_contact_sent(self, contact_id, sent_response):
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE contacts SET status='sent', ai_response=?, sent_at=? WHERE id=?",
            (sent_response, now, contact_id),
        )
        conn.commit()
        conn.close()

    def log_hunt_event(self, item_type, recipient, subject, source, body_preview=""):
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        conn.execute(
            """INSERT INTO hunt_events (item_type, recipient, subject, source, body_preview, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (item_type, recipient, subject, source, body_preview, now),
        )
        conn.commit()
        conn.close()

    def list_hunt_events(self, limit=50):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM hunt_events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
