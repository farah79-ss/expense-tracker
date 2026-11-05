"""طبقة قاعدة البيانات (SQLite) لتطبيق Expense Tracker."""
import sqlite3
from contextlib import contextmanager
from typing import Optional

DEFAULT_DB = "expenses.db"

CATEGORIES = ["Food", "Transport", "Bills", "Shopping", "Health", "Entertainment", "Other"]


class ExpenseDB:
    def __init__(self, path: str = DEFAULT_DB):
        self.path = path
        self._memory_conn = None
        if path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:")
            self._memory_conn.row_factory = sqlite3.Row
        self._create_table()

    @contextmanager
    def _connect(self):
        if self._memory_conn is not None:
            conn = self._memory_conn
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            return
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _create_table(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    amount REAL NOT NULL CHECK (amount > 0),
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    note TEXT DEFAULT ''
                )
                """
            )

    # ---------- CRUD ----------
    def add(self, title: str, amount: float, category: str, date: str, note: str = "") -> int:
        if not title.strip():
            raise ValueError("Title is required")
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO expenses (title, amount, category, date, note) VALUES (?, ?, ?, ?, ?)",
                (title.strip(), amount, category, date, note),
            )
            return cur.lastrowid

    def get_all(self, category: Optional[str] = None):
        query = "SELECT * FROM expenses"
        params: tuple = ()
        if category and category != "All":
            query += " WHERE category = ?"
            params = (category,)
        query += " ORDER BY date DESC, id DESC"
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def get(self, expense_id: int):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
            return dict(row) if row else None

    def update(self, expense_id: int, title: str, amount: float, category: str, date: str, note: str = "") -> bool:
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE expenses SET title=?, amount=?, category=?, date=?, note=? WHERE id=?",
                (title.strip(), amount, category, date, note, expense_id),
            )
            return cur.rowcount > 0

    def delete(self, expense_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return cur.rowcount > 0

    # ---------- Reports ----------
    def total(self) -> float:
        with self._connect() as conn:
            return conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses").fetchone()[0]

    def totals_by_category(self):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT category, SUM(amount) AS total, COUNT(*) AS count "
                "FROM expenses GROUP BY category ORDER BY total DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def totals_by_month(self):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT substr(date, 1, 7) AS month, SUM(amount) AS total "
                "FROM expenses GROUP BY month ORDER BY month DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def stats(self):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count, COALESCE(SUM(amount),0) AS total, "
                "COALESCE(AVG(amount),0) AS average, COALESCE(MAX(amount),0) AS maximum "
                "FROM expenses"
            ).fetchone()
            return dict(row)
