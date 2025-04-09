import sqlite3
import threading
import time
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



def start_cleanup_loop(store: UserHistoryStore, period: int = 1800):
    '''
    starts a loop which periodically cleans up the user's history
    default period is 30 minutes
    :param store: user history store
    :param period: period length in seconds; default is 1800s = 30min
    :return:
    '''
    def cleanup_loop():
        while True:
            try:
                store.cleanup()
            except Exception as e:
                print(f"[-] Cleanup error: {e}")
            time.sleep(period)

    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()