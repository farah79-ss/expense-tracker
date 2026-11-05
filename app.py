"""واجهة Tkinter لتطبيق Expense Tracker."""
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from database import CATEGORIES, ExpenseDB


class ExpenseApp(tk.Tk):
    def __init__(self, db: ExpenseDB):
        super().__init__()
        self.title("Expense Tracker")
        self.geometry("900x560")
        self.db = db
        self.selected_id = None

        self._build_form()
        self._build_table()
        self._build_summary()
        self.refresh()

    # ---------- UI ----------
    def _build_form(self):
        form = ttk.LabelFrame(self, text="Expense")
        form.pack(fill="x", padx=10, pady=8)

        self.title_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.note_var = tk.StringVar()

        fields = [
            ("Title", ttk.Entry(form, textvariable=self.title_var, width=22)),
            ("Amount", ttk.Entry(form, textvariable=self.amount_var, width=12)),
            ("Category", ttk.Combobox(form, textvariable=self.category_var, values=CATEGORIES, state="readonly", width=16)),
            ("Date (YYYY-MM-DD)", ttk.Entry(form, textvariable=self.date_var, width=14)),
            ("Note", ttk.Entry(form, textvariable=self.note_var, width=30)),
        ]
        for i, (label, widget) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i, padx=5, pady=(6, 0), sticky="w")
            widget.grid(row=1, column=i, padx=5, pady=(0, 8))

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=5, pady=(0, 8))
        ttk.Button(buttons, text="Add", command=self.add_expense).pack(side="left", padx=4)
        ttk.Button(buttons, text="Update", command=self.update_expense).pack(side="left", padx=4)
        ttk.Button(buttons, text="Delete", command=self.delete_expense).pack(side="left", padx=4)
        ttk.Button(buttons, text="Clear", command=self.clear_form).pack(side="left", padx=4)

    def _build_table(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10)
        ttk.Label(top, text="Filter by category:").pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        flt = ttk.Combobox(top, textvariable=self.filter_var, values=["All"] + CATEGORIES, state="readonly", width=16)
        flt.pack(side="left", padx=6)
        flt.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        cols = ("id", "title", "amount", "category", "date", "note")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        widths = {"id": 40, "title": 200, "amount": 90, "category": 110, "date": 100, "note": 280}
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def _build_summary(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=10, pady=(0, 10))
        self.summary_label = ttk.Label(bar, text="")
        self.summary_label.pack(side="left")
        ttk.Button(bar, text="Report", command=self.show_report).pack(side="right")

    # ---------- Actions ----------
    def _read_form(self):
        try:
            amount = float(self.amount_var.get())
        except ValueError:
            raise ValueError("Amount must be a number")
        return (
            self.title_var.get(),
            amount,
            self.category_var.get(),
            self.date_var.get(),
            self.note_var.get(),
        )

    def add_expense(self):
        try:
            self.db.add(*self._read_form())
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return
        self.clear_form()
        self.refresh()

    def update_expense(self):
        if self.selected_id is None:
            messagebox.showinfo("Update", "Select an expense first")
            return
        try:
            self.db.update(self.selected_id, *self._read_form())
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return
        self.clear_form()
        self.refresh()

    def delete_expense(self):
        if self.selected_id is None:
            messagebox.showinfo("Delete", "Select an expense first")
            return
        if messagebox.askyesno("Delete", "Delete this expense?"):
            self.db.delete(self.selected_id)
            self.clear_form()
            self.refresh()

    def clear_form(self):
        self.selected_id = None
        self.title_var.set("")
        self.amount_var.set("")
        self.note_var.set("")
        self.date_var.set(date.today().isoformat())
        self.category_var.set(CATEGORIES[0])
        self.tree.selection_remove(self.tree.selection())

    def on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])["values"]
        self.selected_id = values[0]
        self.title_var.set(values[1])
        self.amount_var.set(values[2])
        self.category_var.set(values[3])
        self.date_var.set(values[4])
        self.note_var.set(values[5])

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for e in self.db.get_all(self.filter_var.get()):
            self.tree.insert("", "end", values=(e["id"], e["title"], f'{e["amount"]:.2f}', e["category"], e["date"], e["note"]))
        s = self.db.stats()
        self.summary_label.config(
            text=f'Total: {s["total"]:.2f}   |   Count: {s["count"]}   |   Average: {s["average"]:.2f}   |   Max: {s["maximum"]:.2f}'
        )

    def show_report(self):
        win = tk.Toplevel(self)
        win.title("Report")
        win.geometry("420x420")
        text = tk.Text(win, font=("Courier", 11))
        text.pack(fill="both", expand=True, padx=8, pady=8)

        text.insert("end", "Spending by category\n" + "-" * 36 + "\n")
        total = self.db.total() or 1
        for r in self.db.totals_by_category():
            pct = r["total"] / total * 100
            text.insert("end", f'{r["category"]:<15}{r["total"]:>10.2f}  {pct:5.1f}%\n')
        text.insert("end", "\nSpending by month\n" + "-" * 36 + "\n")
        for r in self.db.totals_by_month():
            text.insert("end", f'{r["month"]:<15}{r["total"]:>10.2f}\n')
        text.config(state="disabled")


if __name__ == "__main__":
    ExpenseApp(ExpenseDB()).mainloop()
