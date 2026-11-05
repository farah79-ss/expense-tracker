import unittest

from database import ExpenseDB


class TestExpenseDB(unittest.TestCase):
    def setUp(self):
        self.db = ExpenseDB(":memory:")

    def test_add_and_get(self):
        eid = self.db.add("Lunch", 25.5, "Food", "2026-11-01", "burger")
        row = self.db.get(eid)
        self.assertEqual(row["title"], "Lunch")
        self.assertAlmostEqual(row["amount"], 25.5)

    def test_invalid_amount(self):
        with self.assertRaises(ValueError):
            self.db.add("Bad", -5, "Food", "2026-11-01")

    def test_empty_title(self):
        with self.assertRaises(ValueError):
            self.db.add("  ", 10, "Food", "2026-11-01")

    def test_update(self):
        eid = self.db.add("Taxi", 30, "Transport", "2026-11-02")
        self.assertTrue(self.db.update(eid, "Taxi ride", 35, "Transport", "2026-11-02"))
        self.assertEqual(self.db.get(eid)["title"], "Taxi ride")
        self.assertAlmostEqual(self.db.get(eid)["amount"], 35)

    def test_delete(self):
        eid = self.db.add("Coffee", 12, "Food", "2026-11-03")
        self.assertTrue(self.db.delete(eid))
        self.assertIsNone(self.db.get(eid))
        self.assertFalse(self.db.delete(eid))

    def test_filter_by_category(self):
        self.db.add("A", 10, "Food", "2026-11-01")
        self.db.add("B", 20, "Bills", "2026-11-01")
        self.assertEqual(len(self.db.get_all("Food")), 1)
        self.assertEqual(len(self.db.get_all("All")), 2)

    def test_reports(self):
        self.db.add("A", 10, "Food", "2026-10-01")
        self.db.add("B", 30, "Food", "2026-11-01")
        self.db.add("C", 60, "Bills", "2026-11-05")
        self.assertAlmostEqual(self.db.total(), 100)
        by_cat = {r["category"]: r["total"] for r in self.db.totals_by_category()}
        self.assertAlmostEqual(by_cat["Food"], 40)
        self.assertAlmostEqual(by_cat["Bills"], 60)
        by_month = {r["month"]: r["total"] for r in self.db.totals_by_month()}
        self.assertAlmostEqual(by_month["2026-11"], 90)
        s = self.db.stats()
        self.assertEqual(s["count"], 3)
        self.assertAlmostEqual(s["maximum"], 60)

    def test_persistence(self):
        import os
        import tempfile

        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            ExpenseDB(path).add("Saved", 5, "Other", "2026-11-05")
            rows = ExpenseDB(path).get_all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "Saved")
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
