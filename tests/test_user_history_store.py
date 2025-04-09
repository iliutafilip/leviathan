import os
import unittest

from store.user_history_store import UserHistoryStore


class TestUserHistoryStore(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "store/test_user_history.db"
        self.store = UserHistoryStore(db_path=self.test_db_path)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_add_load_history(self):
        username = "test"
        history = [
            {"role": "user", "message": "test"},
            {"role": "assistant", "message": "test"}
        ]
        self.store.add_to_user_history(username, history)
        loaded = self.store.load_user_history(username)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["role"], "user")
        self.assertEqual(loaded[0]["message"], "test")

    def test_load_expired_data(self):
        username = "test"
        with self.store.lock:
            self.store.conn.execute("""
                        INSERT INTO history (username, role, message, expire_at) VALUES (?, ?, ?, datetime('now', '-1 hour'))
                    """, (username, "user", "test"))
            self.store.conn.commit()

        result = self.store.load_user_history(username)
        self.assertEqual(len(result), 0)

    def test_cleanup(self):
        username = "test"
        with self.store.lock:
            self.store.conn.execute("""
                INSERT INTO history (username, role, message, expire_at) VALUES (?, ?, ?, datetime('now', '-1 hour'))
            """, (username, "user", "test"))
            self.store.conn.commit()

        self.store.cleanup()
        result = self.store.load_user_history(username)
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    unittest.main()
