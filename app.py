import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime

APP_NAME = "نظام الماركت المحاسبي"
APP_DIR = Path.home() / "Documents" / "نظام الماركت المحاسبي"
DB_PATH = APP_DIR / "market.db"

APP_DIR.mkdir(parents=True, exist_ok=True)

MODULES = [
    ("لوحة التحكم", "dashboard"),
    ("المبيعات", "sales"),
    ("المشتريات", "purchases"),
    ("الأصناف", "items"),
    ("المخزون", "inventory"),
    ("العملاء", "customers"),
    ("الموردون", "suppliers"),
    ("المالية", "finance"),
    ("الموظفون", "employees"),
    ("التقارير", "reports"),
    ("سجل الحركة والتدقيق", "audit"),
    ("الإعدادات", "settings"),
]

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        barcode TEXT DEFAULT '',
        sale_price REAL DEFAULT 0,
        purchase_price REAL DEFAULT 0,
        quantity REAL DEFAULT 0,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        details TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );
    """)
    con.commit()
    con.close()

def audit(action, details=""):
    con = db()
    con.execute(
        "INSERT INTO audit(action, details, created_at) VALUES(?,?,?)",
        (action, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    con.commit()
    con.close()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1200x760")
        self.minsize(1000, 650)
        self.configure(bg="#f4f6f8")
        init_db()
        audit("تشغيل النظام", "تم فتح البرنامج")
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Treeview", rowheight=34, font=("Tahoma", 10))
        self.style.configure("Treeview.Heading", font=("Tahoma", 10, "bold"))
        self.build()
        self.show("dashboard")

    def build(self):
        header = tk.Frame(self, bg="#ffffff", height=72)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=APP_NAME, bg="#ffffff", fg="#172033",
                 font=("Tahoma", 20, "bold")).pack(side="right", padx=28, pady=17)
        tk.Label(header, text="إدارة المبيعات والمخزون والحسابات", bg="#ffffff",
                 fg="#6b7280", font=("Tahoma", 10)).pack(side="right", padx=5, pady=22)

        body = tk.Frame(self, bg="#f4f6f8")
        body.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(body, bg="#172033", width=245)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="القائمة الرئيسية", bg="#172033", fg="#ffffff",
                 font=("Tahoma", 13, "bold")).pack(anchor="e", padx=22, pady=(24, 14))

        self.buttons = {}
        for label, key in MODULES:
            b = tk.Button(
                self.sidebar, text=label, command=lambda k=key: self.show(k),
                bg="#172033", fg="#e5e7eb", activebackground="#263552",
                activeforeground="#ffffff", relief="flat", bd=0,
                font=("Tahoma", 10), anchor="e", padx=20, pady=11,
                cursor="hand2"
            )
            b.pack(fill="x", padx=10, pady=2)
            self.buttons[key] = b

        content = tk.Frame(body, bg="#f4f6f8")
        content.pack(side="right", fill="both", expand=True)
        self.content = content

        footer = tk.Frame(self, bg="#ffffff", height=58)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)
        tk.Label(footer, text="تصميم وتنفيذ المهندس : زكريا الحاج",
                 bg="#ffffff", fg="#4b5563", font=("Tahoma", 9, "bold")).pack(side="right", padx=24, pady=7)
        tk.Label(footer, text="لطلب البرنامج او تصميم برامج اخرى التواصل على الرقم 772233564",
                 bg="#ffffff", fg="#4b5563", font=("Tahoma", 9)).pack(side="right", padx=10, pady=7)
        tk.Label(footer, text="☎  772233564    واتساب: 772233564",
                 bg="#ffffff", fg="#15803d", font=("Tahoma", 9, "bold")).pack(side="left", padx=24, pady=7)

    def clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def title_block(self, title, subtitle=""):
        top = tk.Frame(self.content, bg="#f4f6f8")
        top.pack(fill="x", padx=28, pady=(25, 10))
        tk.Label(top, text=title, bg="#f4f6f8", fg="#172033",
                 font=("Tahoma", 19, "bold")).pack(anchor="e")
        if subtitle:
            tk.Label(top, text=subtitle, bg="#f4f6f8", fg="#6b7280",
                     font=("Tahoma", 10)).pack(anchor="e", pady=4)

    def card(self, parent, text, value):
        f = tk.Frame(parent, bg="#ffffff", bd=0, highlightthickness=1, highlightbackground="#e5e7eb")
        f.pack(side="right", fill="both", expand=True, padx=6)
        tk.Label(f, text=text, bg="#ffffff", fg="#6b7280",
                 font=("Tahoma", 10)).pack(anchor="e", padx=18, pady=(18, 5))
        tk.Label(f, text=value, bg="#ffffff", fg="#172033",
                 font=("Tahoma", 20, "bold")).pack(anchor="e", padx=18, pady=(0, 18))

    def show(self, key):
        self.clear()
        for k, b in self.buttons.items():
            b.configure(bg="#263552" if k == key else "#172033")
        handlers = {
            "dashboard": self.dashboard,
            "items": self.items_page,
            "inventory": self.inventory_page,
            "audit": self.audit_page,
        }
        if key in handlers:
            handlers[key]()
        else:
            self.placeholder(dict(MODULES)[key])

    def dashboard(self):
        self.title_block("لوحة التحكم", "ملخص سريع للنظام")
        con = db()
        items = con.execute("SELECT COUNT(*) c FROM items").fetchone()["c"]
        qty = con.execute("SELECT COALESCE(SUM(quantity),0) q FROM items").fetchone()["q"]
        audits = con.execute("SELECT COUNT(*) c FROM audit").fetchone()["c"]
        con.close()
        row = tk.Frame(self.content, bg="#f4f6f8")
        row.pack(fill="x", padx=22, pady=10)
        self.card(row, "عدد الأصناف", str(items))
        self.card(row, "إجمالي الكمية", f"{qty:g}")
        self.card(row, "عمليات السجل", str(audits))
        self.card(row, "حالة النظام", "يعمل")

        box = tk.Frame(self.content, bg="#ffffff", highlightthickness=1, highlightbackground="#e5e7eb")
        box.pack(fill="both", expand=True, padx=28, pady=18)
        tk.Label(box, text="مرحباً بك في نظام الماركت المحاسبي",
                 bg="#ffffff", fg="#172033", font=("Tahoma", 16, "bold")).pack(anchor="e", padx=24, pady=(25, 8))
        tk.Label(box, text="اختر إحدى القوائم من الجانب الأيسر للبدء بإدارة عمليات النظام.",
                 bg="#ffffff", fg="#6b7280", font=("Tahoma", 11)).pack(anchor="e", padx=24)

    def items_page(self):
        self.title_block("الأصناف", "إضافة وعرض بيانات الأصناف")
        form = tk.Frame(self.content, bg="#ffffff", highlightthickness=1, highlightbackground="#e5e7eb")
        form.pack(fill="x", padx=28, pady=8)
        fields = {}
        for label in ["اسم الصنف", "الباركود", "سعر البيع", "سعر الشراء", "الكمية"]:
            r = tk.Frame(form, bg="#ffffff")
            r.pack(side="right", padx=8, pady=15)
            tk.Label(r, text=label, bg="#ffffff", fg="#374151", font=("Tahoma", 9)).pack(anchor="e")
            e = tk.Entry(r, width=18, justify="right", font=("Tahoma", 10))
            e.pack(pady=5)
            fields[label] = e

        def add():
            name = fields["اسم الصنف"].get().strip()
            if not name:
                messagebox.showwarning("تنبيه", "أدخل اسم الصنف.")
                return
            try:
                sale = float(fields["سعر البيع"].get() or 0)
                purchase = float(fields["سعر الشراء"].get() or 0)
                quantity = float(fields["الكمية"].get() or 0)
            except ValueError:
                messagebox.showwarning("تنبيه", "تأكد من صحة الأسعار والكمية.")
                return
            con = db()
            con.execute("INSERT INTO items(name,barcode,sale_price,purchase_price,quantity,created_at) VALUES(?,?,?,?,?,?)",
                        (name, fields["الباركود"].get().strip(), sale, purchase, quantity,
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            con.commit()
            con.close()
            audit("إضافة صنف", name)
            for e in fields.values(): e.delete(0, "end")
            self.refresh_items(tree)

        tk.Button(form, text="حفظ الصنف", command=add, bg="#172033", fg="white",
                  relief="flat", font=("Tahoma", 10, "bold"), padx=22, pady=9).pack(side="left", padx=18, pady=20)

        table_box = tk.Frame(self.content, bg="#ffffff")
        table_box.pack(fill="both", expand=True, padx=28, pady=12)
        tree = ttk.Treeview(table_box, columns=("id","name","barcode","sale","purchase","qty"),
                            show="headings")
        heads = {"id":"الرقم","name":"اسم الصنف","barcode":"الباركود","sale":"سعر البيع","purchase":"سعر الشراء","qty":"الكمية"}
        for c, h in heads.items():
            tree.heading(c, text=h, anchor="e")
            tree.column(c, width=130, anchor="e")
        tree.pack(fill="both", expand=True)
        self.refresh_items(tree)

    def refresh_items(self, tree):
        for x in tree.get_children(): tree.delete(x)
        con = db()
        rows = con.execute("SELECT id,name,barcode,sale_price,purchase_price,quantity FROM items ORDER BY id DESC").fetchall()
        con.close()
        for r in rows:
            tree.insert("", "end", values=(r["id"], r["name"], r["barcode"], f"{r['sale_price']:g}", f"{r['purchase_price']:g}", f"{r['quantity']:g}"))

    def inventory_page(self):
        self.title_block("المخزون", "عرض الكميات الحالية للأصناف")
        box = tk.Frame(self.content, bg="#ffffff")
        box.pack(fill="both", expand=True, padx=28, pady=10)
        tree = ttk.Treeview(box, columns=("name","qty","value"), show="headings")
        for c,h in [("name","الصنف"),("qty","الكمية"),("value","قيمة المخزون بسعر الشراء")]:
            tree.heading(c, text=h, anchor="e"); tree.column(c, width=220, anchor="e")
        tree.pack(fill="both", expand=True)
        con=db()
        rows=con.execute("SELECT name,quantity,purchase_price FROM items ORDER BY name").fetchall()
        con.close()
        for r in rows:
            tree.insert("", "end", values=(r["name"], f"{r['quantity']:g}", f"{r['quantity']*r['purchase_price']:,.2f}"))

    def audit_page(self):
        self.title_block("سجل الحركة والتدقيق", "تسجيل عمليات النظام للمراجعة والمتابعة")
        box = tk.Frame(self.content, bg="#ffffff")
        box.pack(fill="both", expand=True, padx=28, pady=10)
        tree=ttk.Treeview(box, columns=("date","action","details"), show="headings")
        for c,h,w in [("date","التاريخ والوقت",170),("action","العملية",180),("details","التفاصيل",500)]:
            tree.heading(c,text=h,anchor="e"); tree.column(c,width=w,anchor="e")
        tree.pack(fill="both",expand=True)
        con=db()
        rows=con.execute("SELECT created_at,action,details FROM audit ORDER BY id DESC").fetchall()
        con.close()
        for r in rows: tree.insert("", "end", values=(r["created_at"],r["action"],r["details"]))

    def placeholder(self, title):
        self.title_block(title)
        box=tk.Frame(self.content,bg="#ffffff",highlightthickness=1,highlightbackground="#e5e7eb")
        box.pack(fill="both",expand=True,padx=28,pady=10)
        tk.Label(box,text="هذه الوحدة جاهزة للتوسعة ضمن نفس تصميم النظام.",
                 bg="#ffffff",fg="#4b5563",font=("Tahoma",13)).pack(expand=True)

if __name__ == "__main__":
    App().mainloop()
