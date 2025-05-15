import sqlite3
import threading
from datetime import datetime, timedelta


class UserHistoryStore:

    def __init__(self, db_path = "store/user_history.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    username TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    expire_at TEXT
                )
            """)
            self.conn.commit()

    def add_to_user_history(self, username, data):
        expire_at = (datetime.now() + timedelta(hours=1)).isoformat()
        with self.lock:
            for entry in data:
                self.conn.execute("""
                    INSERT INTO history (username, role, message, expire_at)
                    VALUES (?, ?, ?, ?)
                """, (username, entry["role"], entry["message"], expire_at))
            self.conn.commit()

    def load_user_history(self, username):
        with self.lock:
            now = datetime.now().isoformat()
            cursor = self.conn.execute("""
                SELECT role, message FROM history
                WHERE username = ? AND (expire_at IS NULL OR expire_at > ?)
                ORDER BY id
            """, (username, now))
            return [{"role": role, "message": message} for role, message in cursor.fetchall()]

    def cleanup(self):
        with self.lock:
            now = datetime.now().isoformat()
            self.conn.execute("DELETE FROM history WHERE expire_at IS NOT NULL AND expire_at <= ?", (now,))
            self.conn.commit()

    def close(self):
        with self.lock:
            self.conn.close()