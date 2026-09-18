import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime
import hashlib
import json
import traceback

APP_NAME = "نظام الماركت المحاسبي"
APP_DIR = Path.home() / "Documents" / APP_NAME
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
    ("المستخدمون والصلاحيات", "users"),
    ("التقارير", "reports"),
    ("سجل الحركة والتدقيق", "audit"),
    ("الإعدادات وتهيئة النظام", "settings"),
    ("الدليل والمساعدة", "guide"),
]

ROLES = {
    "مدير النظام": set(k for _, k in MODULES),
    "محاسب": {"dashboard", "sales", "purchases", "customers", "suppliers", "finance", "reports", "audit", "guide"},
    "مبيعات": {"dashboard", "sales", "customers", "reports", "guide"},
    "مخزون": {"dashboard", "purchases", "items", "inventory", "suppliers", "reports", "guide"},
}

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def db():
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def hash_password(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def audit(action, details="", user="النظام"):
    try:
        c = db()
        c.execute("INSERT INTO audit(action,details,created_at,user_name) VALUES(?,?,?,?)",
                  (action, details, now(), user))
        c.commit()
        c.close()
    except Exception:
        pass

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS items(
      id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,barcode TEXT,
      sale_price REAL DEFAULT 0,purchase_price REAL DEFAULT 0,quantity REAL DEFAULT 0,
      category TEXT DEFAULT '',unit TEXT DEFAULT '',min_quantity REAL DEFAULT 0,created_at TEXT);
    CREATE TABLE IF NOT EXISTS customers(
      id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT,address TEXT,
      balance REAL DEFAULT 0,created_at TEXT);
    CREATE TABLE IF NOT EXISTS suppliers(
      id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT,address TEXT,
      balance REAL DEFAULT 0,created_at TEXT);
    CREATE TABLE IF NOT EXISTS employees(
      id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT,job TEXT,
      salary REAL DEFAULT 0,created_at TEXT);
    CREATE TABLE IF NOT EXISTS transactions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,party TEXT,item TEXT,
      quantity REAL DEFAULT 0,total REAL DEFAULT 0,invoice_no TEXT DEFAULT '',
      payment TEXT DEFAULT 'نقدي',created_at TEXT,user_name TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS finance(
      id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,description TEXT,
      amount REAL DEFAULT 0,created_at TEXT,user_name TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS audit(
      id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL,details TEXT,
      created_at TEXT,user_name TEXT DEFAULT 'النظام');
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE,role TEXT NOT NULL,
      active INTEGER DEFAULT 1,created_at TEXT,password_hash TEXT DEFAULT '',
      permissions TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS market_info(
      id INTEGER PRIMARY KEY CHECK(id=1),market_name TEXT,owner_name TEXT,phone TEXT,
      address TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS system_settings(
      key TEXT PRIMARY KEY,value TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS undo_log(
      id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL,details TEXT,
      created_at TEXT,user_name TEXT DEFAULT '',payload TEXT DEFAULT '',undone INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS invoices(
      id INTEGER PRIMARY KEY AUTOINCREMENT,invoice_no TEXT UNIQUE,customer TEXT,
      payment TEXT,total REAL DEFAULT 0,created_at TEXT,user_name TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS invoice_lines(
      id INTEGER PRIMARY KEY AUTOINCREMENT,invoice_id INTEGER NOT NULL,item_id INTEGER,
      item_name TEXT,quantity REAL DEFAULT 0,price REAL DEFAULT 0,discount REAL DEFAULT 0,
      total REAL DEFAULT 0,FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE);
    """)
    # ترقية قواعد البيانات القديمة دون حذف بياناتها.
    columns = {r["name"] for r in c.execute("PRAGMA table_info(audit)").fetchall()}
    if "user_name" not in columns:
        c.execute("ALTER TABLE audit ADD COLUMN user_name TEXT DEFAULT 'النظام'")
    columns = {r["name"] for r in c.execute("PRAGMA table_info(transactions)").fetchall()}
    for col, typ in [("invoice_no","TEXT DEFAULT ''"),("payment","TEXT DEFAULT 'نقدي'"),("user_name","TEXT DEFAULT ''")]:
        if col not in columns:
            c.execute(f"ALTER TABLE transactions ADD COLUMN {col} {typ}")
    columns = {r["name"] for r in c.execute("PRAGMA table_info(users)").fetchall()}
    for col, typ in [("password_hash","TEXT DEFAULT ''"),("permissions","TEXT DEFAULT ''")]:
        if col not in columns:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
    columns = {r["name"] for r in c.execute("PRAGMA table_info(items)").fetchall()}
    for col, typ in [("category","TEXT DEFAULT ''"),("unit","TEXT DEFAULT ''"),("min_quantity","REAL DEFAULT 0")]:
        if col not in columns:
            c.execute(f"ALTER TABLE items ADD COLUMN {col} {typ}")
    user_count = c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
    if user_count == 0:
        c.execute("INSERT INTO users(name,role,active,created_at,password_hash,permissions) VALUES(?,?,?,?,?,?)",
                  ("admin","مدير النظام",1,now(),hash_password("1234"),json.dumps(sorted(ROLES["مدير النظام"]), ensure_ascii=False)))
    c.commit()
    c.close()

def setting_get(key, default=""):
    c = db()
    r = c.execute("SELECT value FROM system_settings WHERE key=?", (key,)).fetchone()
    c.close()
    return r["value"] if r else default

def setting_set(key, value):
    c = db()
    c.execute("""INSERT INTO system_settings(key,value,updated_at) VALUES(?,?,?)
                 ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at""",
              (key, value, now()))
    c.commit()
    c.close()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title(APP_NAME)
        self.geometry("1280x800")
        self.minsize(1050, 680)
        self.configure(bg="#f4f6f8")
        init_db()
        self.current_user = None
        self.current_role = None
        self.login()

    def login(self):
        win = tk.Toplevel(self)
        win.title("تسجيل الدخول")
        win.geometry("430x330")
        win.resizable(False, False)
        win.configure(bg="#f4f6f8")
        win.protocol("WM_DELETE_WINDOW", self.destroy)
        tk.Label(win,text=APP_NAME,bg="#f4f6f8",fg="#172033",font=("Tahoma",20,"bold")).pack(pady=(28,8))
        tk.Label(win,text="تسجيل الدخول إلى النظام",bg="#f4f6f8",fg="#6b7280",font=("Tahoma",11)).pack(pady=(0,18))
        frm=tk.Frame(win,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb")
        frm.pack(fill="both",expand=True,padx=28,pady=5)
        user=tk.StringVar(); password=tk.StringVar()
        for label,var,show in [("اسم المستخدم",user,None),("كلمة المرور",password,"*")]:
            r=tk.Frame(frm,bg="#fff"); r.pack(fill="x",padx=22,pady=9)
            tk.Label(r,text=label,bg="#fff",font=("Tahoma",10)).pack(anchor="e")
            tk.Entry(r,textvariable=var,show=show,width=32,justify="right",font=("Tahoma",11)).pack(anchor="e",pady=4)
        def do_login(event=None):
            c=db()
            row=c.execute("SELECT * FROM users WHERE name=? AND active=1",(user.get().strip(),)).fetchone()
            c.close()
            if not row or row["password_hash"] != hash_password(password.get()):
                messagebox.showwarning("تنبيه","اسم المستخدم أو كلمة المرور غير صحيحة.",parent=win); return
            self.current_user=row["name"]; self.current_role=row["role"]
            audit("تسجيل الدخول",f"المستخدم: {self.current_user}",self.current_user)
            win.destroy(); self.deiconify(); self.build(); self.show("sales")
        tk.Button(frm,text="دخول",command=do_login,bg="#172033",fg="#fff",relief="flat",
                  font=("Tahoma",11,"bold"),padx=40,pady=9).pack(pady=16)
        tk.Label(win,text="المستخدم الافتراضي: admin  |  كلمة المرور: 1234",bg="#f4f6f8",fg="#9ca3af",
                 font=("Tahoma",8)).pack(pady=5)
        win.bind("<Return>",do_login)
        user.set("admin"); password.set("1234")
        win.grab_set()

    def build(self):
        s=ttk.Style(self)
        try: s.theme_use("clam")
        except tk.TclError: pass
        s.configure("Treeview",rowheight=31,font=("Tahoma",10))
        s.configure("Treeview.Heading",font=("Tahoma",10,"bold"))
        h=tk.Frame(self,bg="#fff",height=74); h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h,text=APP_NAME,bg="#fff",fg="#172033",font=("Tahoma",20,"bold")).pack(side="right",padx=25,pady=12)
        tk.Label(h,text=f"المستخدم: {self.current_user} | الصلاحية: {self.current_role}",bg="#fff",fg="#6b7280",
                 font=("Tahoma",10)).pack(side="right",padx=5)
        tk.Button(h,text="مساعد النظام",command=self.ai_assistant,bg="#334155",fg="#fff",relief="flat",
                  padx=12,pady=6).pack(side="left",padx=8)
        tk.Button(h,text="تراجع",command=self.undo_last,bg="#9a3412",fg="#fff",relief="flat",
                  padx=12,pady=6).pack(side="left",padx=5)
        tk.Button(h,text="خروج",command=self.logout,bg="#6b7280",fg="#fff",relief="flat",
                  padx=12,pady=6).pack(side="left",padx=5)
        body=tk.Frame(self,bg="#f4f6f8"); body.pack(fill="both",expand=True)
        self.sidebar=tk.Frame(body,bg="#172033",width=250); self.sidebar.pack(side="left",fill="y"); self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar,text="القائمة الرئيسية",bg="#172033",fg="#fff",font=("Tahoma",13,"bold")).pack(anchor="e",padx=22,pady=(20,10))
        self.buttons={}
        allowed=ROLES.get(self.current_role,set())
        for label,key in MODULES:
            if key not in allowed: continue
            b=tk.Button(self.sidebar,text=label,command=lambda k=key:self.show(k),bg="#172033",fg="#e5e7eb",
                        activebackground="#263552",activeforeground="#fff",relief="flat",bd=0,font=("Tahoma",10),
                        anchor="e",padx=18,pady=8,cursor="hand2")
            b.pack(fill="x",padx=10,pady=1); self.buttons[key]=b
        self.content=tk.Frame(body,bg="#f4f6f8"); self.content.pack(side="right",fill="both",expand=True)
        f=tk.Frame(self,bg="#fff",height=54); f.pack(fill="x"); f.pack_propagate(False)
        tk.Label(f,text="تصميم وتنفيذ المهندس : زكريا الحاج",bg="#fff",fg="#4b5563",font=("Tahoma",9,"bold")).pack(side="right",padx=15)
        tk.Label(f,text="لطلب البرنامج أو تصميم برامج أخرى: 772233564",bg="#fff",fg="#4b5563",font=("Tahoma",9)).pack(side="right")
        tk.Label(f,text="☎ 772233564    واتساب: 772233564",bg="#fff",fg="#15803d",font=("Tahoma",9,"bold")).pack(side="left",padx=15)

    def logout(self):
        audit("تسجيل الخروج",f"المستخدم: {self.current_user}",self.current_user)
        for w in self.winfo_children(): w.destroy()
        self.withdraw(); self.current_user=None; self.current_role=None; self.login()

    def allowed(self,key):
        return key in ROLES.get(self.current_role,set())

    def clear(self):
        for w in self.content.winfo_children(): w.destroy()

    def title_block(self,title,sub=""):
        x=tk.Frame(self.content,bg="#f4f6f8"); x.pack(fill="x",padx=28,pady=(18,8))
        tk.Label(x,text=title,bg="#f4f6f8",fg="#172033",font=("Tahoma",19,"bold")).pack(anchor="e")
        if sub: tk.Label(x,text=sub,bg="#f4f6f8",fg="#6b7280",font=("Tahoma",10)).pack(anchor="e",pady=2)

    def show(self,key):
        if not self.allowed(key):
            messagebox.showwarning("صلاحية مرفوضة","ليس لديك صلاحية لتنفيذ هذه الوحدة."); return
        self.clear()
        for k,b in self.buttons.items(): b.configure(bg="#263552" if k==key else "#172033")
        title=next((x for x,k in MODULES if k==key),key)
        page=getattr(self,key+"_page",self.placeholder)
        try: page(title)
        except Exception as e:
            audit("خطأ في الشاشة",f"{key}: {e}",self.current_user)
            traceback.print_exc()
            messagebox.showerror("خطأ","حدث خطأ في الشاشة. تم تسجيله في سجل التدقيق.")
    def card(self,p,text,value):
        x=tk.Frame(p,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); x.pack(side="right",fill="both",expand=True,padx=5)
        tk.Label(x,text=text,bg="#fff",fg="#6b7280",font=("Tahoma",10)).pack(anchor="e",padx=15,pady=(13,3))
        tk.Label(x,text=value,bg="#fff",fg="#172033",font=("Tahoma",18,"bold")).pack(anchor="e",padx=15,pady=(0,13))

    def dashboard_page(self,_):
        self.title_block("لوحة التحكم","ملخص حي لحالة النظام")
        c=db()
        vals=[
            c.execute("SELECT COUNT(*) n FROM items").fetchone()["n"],
            c.execute("SELECT COALESCE(SUM(quantity),0) n FROM items").fetchone()["n"],
            c.execute("SELECT COUNT(DISTINCT invoice_no) n FROM transactions WHERE kind='بيع' AND invoice_no<>''").fetchone()["n"],
            c.execute("SELECT COUNT(*) n FROM audit").fetchone()["n"],
        ]
        low=c.execute("SELECT COUNT(*) n FROM items WHERE quantity<=min_quantity").fetchone()["n"]
        c.close()
        row=tk.Frame(self.content,bg="#f4f6f8"); row.pack(fill="x",padx=22,pady=8)
        for t,v in zip(["عدد الأصناف","كمية المخزون","عدد الفواتير","سجل التدقيق"],vals): self.card(row,t,str(v))
        box=tk.Frame(self.content,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb")
        box.pack(fill="both",expand=True,padx=28,pady=12)
        tk.Label(box,text="حالة النظام",bg="#fff",fg="#172033",font=("Tahoma",15,"bold")).pack(anchor="e",padx=22,pady=(20,8))
        tk.Label(box,text=f"الأصناف التي وصلت إلى حد إعادة الطلب: {low}",bg="#fff",fg="#9a3412",
                 font=("Tahoma",11,"bold")).pack(anchor="e",padx=22,pady=6)
        tk.Label(box,text="تم حفظ العمليات مع المستخدم والتاريخ في سجل الحركة. يمكن استخدام زر التراجع للعمليات القابلة للعكس.",
                 bg="#fff",fg="#6b7280",font=("Tahoma",10)).pack(anchor="e",padx=22,pady=6)

    def entity_page(self,title,table,fields):
        self.title_block(title,"إضافة وعرض وتحديث البيانات")
        form=tk.Frame(self.content,bg="#fff"); form.pack(fill="x",padx=28,pady=6)
        entries={}
        for label,col in fields:
            r=tk.Frame(form,bg="#fff"); r.pack(side="right",padx=7,pady=10)
            tk.Label(r,text=label,bg="#fff",font=("Tahoma",9)).pack(anchor="e")
            e=tk.Entry(r,width=17,justify="right"); e.pack(pady=4); entries[col]=e
        tree=tk.Frame(self.content,bg="#fff"); tree.pack(fill="both",expand=True,padx=28,pady=10)
        cols=["id"]+[x[1] for x in fields]; view=ttk.Treeview(tree,columns=cols,show="headings")
        for col in cols:
            view.heading(col,text="الرقم" if col=="id" else next(x[0] for x in fields if x[1]==col),anchor="e"); view.column(col,width=150,anchor="e")
        view.pack(fill="both",expand=True)
        def refresh():
            view.delete(*view.get_children()); c=db()
            rows=c.execute("SELECT "+",".join(cols)+" FROM "+table+" ORDER BY id DESC").fetchall(); c.close()
            for r in rows: view.insert("","end",values=tuple(r))
        def save():
            vals=[entries[col].get().strip() for _,col in fields]
            if not vals[0]: messagebox.showwarning("تنبيه","أدخل البيانات المطلوبة."); return
            c=db(); c.execute("INSERT INTO "+table+"("+",".join(x[1] for x in fields)+",created_at) VALUES("+",".join("?" for _ in fields)+",?)",vals+[now()]); new_id=c.execute("SELECT last_insert_rowid()").fetchone()[0]
            c.commit(); c.close()
            self.push_undo("حذف السجل",{"table":table,"id":new_id})
            audit("إضافة "+title,vals[0],self.current_user); [e.delete(0,"end") for e in entries.values()]; refresh()
        tk.Button(form,text="حفظ",command=save,bg="#172033",fg="#fff",relief="flat",font=("Tahoma",10,"bold"),padx=25,pady=8).pack(side="left",padx=18,pady=16)
        refresh()

    def items_page(self,_):
        self.title_block("الأصناف","الاسم والباركود والأسعار والكمية والتصنيف والوحدة وحد إعادة الطلب")
        form=tk.Frame(self.content,bg="#fff"); form.pack(fill="x",padx=28,pady=6)
        names=[("اسم الصنف","name"),("الباركود","barcode"),("سعر البيع","sale_price"),("سعر الشراء","purchase_price"),("الكمية","quantity"),("التصنيف","category"),("الوحدة","unit"),("حد الطلب","min_quantity")]
        e={}
        for label,col in names:
            r=tk.Frame(form,bg="#fff"); r.pack(side="right",padx=4,pady=9)
            tk.Label(r,text=label,bg="#fff",font=("Tahoma",8)).pack(anchor="e"); z=tk.Entry(r,width=12,justify="right"); z.pack(pady=3); e[col]=z
        cols=("id","name","barcode","sale_price","purchase_price","quantity","category","unit","min_quantity")
        box=tk.Frame(self.content,bg="#fff"); box.pack(fill="both",expand=True,padx=28,pady=10)
        tree=ttk.Treeview(box,columns=cols,show="headings")
        heads={"id":"الرقم","name":"الصنف","barcode":"الباركود","sale_price":"سعر البيع","purchase_price":"سعر الشراء","quantity":"الكمية","category":"التصنيف","unit":"الوحدة","min_quantity":"حد الطلب"}
        for col in cols: tree.heading(col,text=heads[col],anchor="e"); tree.column(col,width=110,anchor="e")
        tree.pack(fill="both",expand=True)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT "+",".join(cols)+" FROM items ORDER BY id DESC").fetchall(): tree.insert("","end",values=tuple(r))
            c.close()
        def save():
            if not e["name"].get().strip(): messagebox.showwarning("تنبيه","أدخل اسم الصنف."); return
            try:
                vals=[e["name"].get().strip(),e["barcode"].get().strip(),float(e["sale_price"].get() or 0),float(e["purchase_price"].get() or 0),
                      float(e["quantity"].get() or 0),e["category"].get().strip(),e["unit"].get().strip(),float(e["min_quantity"].get() or 0)]
            except ValueError: messagebox.showwarning("تنبيه","تحقق من القيم الرقمية."); return
            c=db(); c.execute("""INSERT INTO items(name,barcode,sale_price,purchase_price,quantity,category,unit,min_quantity,created_at)
                                VALUES(?,?,?,?,?,?,?,?,?)""",vals+[now()]); new_id=c.execute("SELECT last_insert_rowid()").fetchone()[0]; c.commit(); c.close()
            self.push_undo("حذف السجل",{"table":"items","id":new_id}); audit("إضافة صنف",vals[0],self.current_user)
            [z.delete(0,"end") for z in e.values()]; refresh()
        tk.Button(form,text="حفظ الصنف",command=save,bg="#172033",fg="#fff",relief="flat",padx=18,pady=8).pack(side="left",padx=12,pady=15); refresh()

    def sales_page(self,_):
        self.title_block("المبيعات","واجهة البيع الرئيسية — إنشاء فاتورة كاملة وتحديث المخزون والحسابات")
        root=tk.Frame(self.content,bg="#f4f6f8"); root.pack(fill="both",expand=True,padx=22,pady=5)
        top=tk.Frame(root,bg="#fff"); top.pack(fill="x",pady=(0,8))
        customer=tk.StringVar(); payment=tk.StringVar(value="نقدي"); invoice_no=tk.StringVar(value=self.new_invoice_no())
        tk.Label(top,text="العميل",bg="#fff").pack(side="right",padx=5,pady=10); tk.Entry(top,textvariable=customer,width=20,justify="right").pack(side="right",pady=10)
        tk.Label(top,text="الدفع",bg="#fff").pack(side="right",padx=5); ttk.Combobox(top,textvariable=payment,values=["نقدي","آجل","بطاقة"],state="readonly",width=10).pack(side="right")
        tk.Label(top,textvariable=invoice_no,bg="#fff",fg="#6b7280",font=("Tahoma",9,"bold")).pack(side="left",padx=15)
        main=tk.Frame(root,bg="#f4f6f8"); main.pack(fill="both",expand=True)
        products=tk.Frame(main,bg="#fff"); products.pack(side="left",fill="both",expand=True,padx=(0,7))
        tk.Label(products,text="الأصناف",bg="#fff",font=("Tahoma",13,"bold")).pack(anchor="e",padx=12,pady=8)
        search=tk.StringVar(); se=tk.Entry(products,textvariable=search,justify="right"); se.pack(fill="x",padx=10,pady=5)
        pcols=("id","name","barcode","price","qty"); pt=ttk.Treeview(products,columns=pcols,show="headings")
        for c,h,w in [("id","الرقم",55),("name","الصنف",190),("barcode","الباركود",110),("price","السعر",90),("qty","المخزون",85)]: pt.heading(c,text=h); pt.column(c,width=w,anchor="e")
        pt.pack(fill="both",expand=True,padx=10,pady=5)
        controls=tk.Frame(products,bg="#fff"); controls.pack(fill="x",padx=10,pady=7)
        qty=tk.StringVar(value="1"); disc=tk.StringVar(value="0")
        tk.Label(controls,text="الكمية",bg="#fff").pack(side="right"); tk.Entry(controls,textvariable=qty,width=8,justify="right").pack(side="right",padx=5)
        tk.Label(controls,text="الخصم",bg="#fff").pack(side="right"); tk.Entry(controls,textvariable=disc,width=8,justify="right").pack(side="right",padx=5)
        invoice=[]
        bill=tk.Frame(main,bg="#fff",width=470); bill.pack(side="right",fill="both",padx=(7,0)); bill.pack_propagate(False)
        tk.Label(bill,text="الفاتورة الحالية",bg="#fff",font=("Tahoma",13,"bold")).pack(anchor="e",padx=12,pady=8)
        bt=ttk.Treeview(bill,columns=("name","qty","price","discount","total"),show="headings")
        for c,h,w in [("name","الصنف",140),("qty","الكمية",55),("price","السعر",70),("discount","الخصم",65),("total","الإجمالي",85)]: bt.heading(c,text=h); bt.column(c,width=w,anchor="e")
        bt.pack(fill="both",expand=True,padx=10,pady=5)
        grand=tk.StringVar(value="0.00")
        tk.Label(bill,textvariable=grand,bg="#fff",fg="#172033",font=("Tahoma",15,"bold")).pack(anchor="e",padx=15,pady=7)
        def refresh_products(*_):
            pt.delete(*pt.get_children()); q=search.get().strip(); c=db()
            if q: rows=c.execute("SELECT id,name,barcode,sale_price,quantity FROM items WHERE name LIKE ? OR barcode LIKE ? ORDER BY name",(f"%{q}%",f"%{q}%")).fetchall()
            else: rows=c.execute("SELECT id,name,barcode,sale_price,quantity FROM items ORDER BY name").fetchall()
            c.close()
            for r in rows: pt.insert("","end",values=(r["id"],r["name"],r["barcode"] or "",r["sale_price"],r["quantity"]))
        def refresh_bill():
            bt.delete(*bt.get_children()); total=0
            for i in invoice: bt.insert("","end",values=(i["name"],i["qty"],f'{i["price"]:,.2f}',f'{i["discount"]:,.2f}',f'{i["total"]:,.2f}')); total+=i["total"]
            grand.set(f"الإجمالي المستحق: {total:,.2f}")
        def add():
            sel=pt.selection()
            if not sel: return
            v=pt.item(sel[0],"values")
            try: q=float(qty.get() or 0); d=float(disc.get() or 0)
            except ValueError: messagebox.showwarning("تنبيه","الكمية أو الخصم غير صحيح."); return
            if q<=0 or d<0 or q>float(v[4]): messagebox.showwarning("تنبيه","تحقق من الكمية والمخزون والخصم."); return
            price=float(v[3]); total=q*price-d
            if total<0: messagebox.showwarning("تنبيه","الخصم أكبر من قيمة السطر."); return
            invoice.append({"id":int(v[0]),"name":v[1],"qty":q,"price":price,"discount":d,"total":total}); refresh_bill()
        def remove():
            s=bt.selection()
            if s: invoice.pop(bt.index(s[0])); refresh_bill()
        def clear_bill():
            invoice.clear(); refresh_bill(); customer.set(""); payment.set("نقدي"); invoice_no.set(self.new_invoice_no())
        def complete():
            if not invoice: messagebox.showwarning("تنبيه","الفاتورة فارغة."); return
            c=db()
            try:
                for i in invoice:
                    r=c.execute("SELECT quantity FROM items WHERE id=?",(i["id"],)).fetchone()
                    if not r or float(r["quantity"])<i["qty"]: raise ValueError("المخزون تغير وأصبح غير كافٍ.")
                inv=invoice_no.get(); party=customer.get().strip() or "عميل نقدي"; pay=payment.get(); total=sum(i["total"] for i in invoice)
                c.execute("INSERT INTO invoices(invoice_no,customer,payment,total,created_at,user_name) VALUES(?,?,?,?,?,?)",(inv,party,pay,total,now(),self.current_user))
                iid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
                for i in invoice:
                    c.execute("UPDATE items SET quantity=quantity-? WHERE id=?",(i["qty"],i["id"]))
                    c.execute("INSERT INTO invoice_lines(invoice_id,item_id,item_name,quantity,price,discount,total) VALUES(?,?,?,?,?,?,?)",(iid,i["id"],i["name"],i["qty"],i["price"],i["discount"],i["total"]))
                    c.execute("INSERT INTO transactions(kind,party,item,quantity,total,invoice_no,payment,created_at,user_name) VALUES(?,?,?,?,?,?,?,?,?)",("بيع",party,i["name"],i["qty"],i["total"],inv,pay,now(),self.current_user))
                if pay in ("نقدي","بطاقة"):
                    c.execute("INSERT INTO finance(kind,description,amount,created_at,user_name) VALUES(?,?,?,?,?)",("قبض",inv,total,now(),self.current_user))
                elif party!="عميل نقدي":
                    c.execute("UPDATE customers SET balance=balance+? WHERE name=?",(total,party))
                c.commit()
                self.push_undo("عكس فاتورة بيع",{"invoice_no":inv})
                audit("إتمام بيع",f"{inv} | {party} | {total:,.2f} | {pay}",self.current_user)
                messagebox.showinfo("تم الحفظ",f"تم حفظ الفاتورة {inv}\nالإجمالي: {total:,.2f}")
                clear_bill(); refresh_products()
            except Exception as e:
                c.rollback(); messagebox.showerror("خطأ",str(e))
            finally: c.close()
        search.trace_add("write",refresh_products); pt.bind("<Double-1>",lambda e:add())
        tk.Button(controls,text="إضافة للفاتورة",command=add,bg="#172033",fg="#fff",relief="flat",padx=13,pady=7).pack(side="left")
        tk.Button(bill,text="حذف السطر",command=remove,bg="#6b7280",fg="#fff",relief="flat",padx=10,pady=6).pack(side="left",padx=8,pady=5)
        tk.Button(bill,text="تفريغ",command=clear_bill,bg="#9ca3af",fg="#fff",relief="flat",padx=10,pady=6).pack(side="left",pady=5)
        tk.Button(bill,text="إتمام البيع وحفظ الفاتورة",command=complete,bg="#15803d",fg="#fff",relief="flat",font=("Tahoma",10,"bold"),padx=18,pady=9).pack(fill="x",padx=10,pady=8)
        refresh_products()

    def purchases_page(self,_):
        self.title_block("المشتريات","تسجيل شراء وتحديث المخزون وحساب المورد")
        form=tk.Frame(self.content,bg="#fff"); form.pack(fill="x",padx=28,pady=6)
        supplier=tk.StringVar(); item=tk.StringVar(); qty=tk.StringVar(value="1"); total=tk.StringVar(value="0")
        for label,var,w in [("المورد",supplier,20),("الصنف",item,20),("الكمية",qty,10),("الإجمالي",total,14)]:
            r=tk.Frame(form,bg="#fff"); r.pack(side="right",padx=6,pady=10); tk.Label(r,text=label,bg="#fff").pack(anchor="e"); tk.Entry(r,textvariable=var,width=w,justify="right").pack(pady=4)
        tree=ttk.Treeview(self.content,columns=("date","supplier","item","qty","total"),show="headings")
        for c,h in [("date","التاريخ"),("supplier","المورد"),("item","الصنف"),("qty","الكمية"),("total","الإجمالي")]: tree.heading(c,text=h); tree.column(c,width=180,anchor="e")
        tree.pack(fill="both",expand=True,padx=28,pady=10)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT created_at,party,item,quantity,total FROM transactions WHERE kind='شراء' ORDER BY id DESC").fetchall(): tree.insert("","end",values=tuple(r))
            c.close()
        def save():
            try: q=float(qty.get() or 0); amount=float(total.get() or 0)
            except ValueError: messagebox.showwarning("تنبيه","تحقق من الأرقام."); return
            if not item.get().strip() or q<=0: messagebox.showwarning("تنبيه","أدخل الصنف والكمية."); return
            sup=supplier.get().strip() or "مورد غير محدد"; name=item.get().strip(); c=db()
            try:
                row=c.execute("SELECT id FROM items WHERE name=?",(name,)).fetchone()
                if row: c.execute("UPDATE items SET quantity=quantity+?,purchase_price=? WHERE id=?",(q,amount/q if q else 0,row["id"]))
                else: c.execute("INSERT INTO items(name,purchase_price,quantity,created_at) VALUES(?,?,?,?)",(name,amount/q if q else 0,q,now()))
                c.execute("INSERT INTO transactions(kind,party,item,quantity,total,created_at,user_name) VALUES(?,?,?,?,?,?,?)",("شراء",sup,name,q,amount,now(),self.current_user))
                c.execute("UPDATE suppliers SET balance=balance+? WHERE name=?",(amount,sup))
                c.commit(); self.push_undo("عكس عملية شراء",{"supplier":sup,"item":name,"quantity":q,"total":amount})
                audit("إتمام شراء",f"{name} - {q} - {amount:,.2f}",self.current_user); supplier.set(""); item.set(""); qty.set("1"); total.set("0"); refresh()
            except Exception as e: c.rollback(); messagebox.showerror("خطأ",str(e))
            finally: c.close()
        tk.Button(form,text="حفظ عملية الشراء",command=save,bg="#172033",fg="#fff",relief="flat",padx=18,pady=8).pack(side="left",padx=15,pady=15); refresh()

    def customers_page(self,_): self.entity_page("العملاء","customers",[("اسم العميل","name"),("الهاتف","phone"),("العنوان","address")])
    def suppliers_page(self,_): self.entity_page("الموردون","suppliers",[("اسم المورد","name"),("الهاتف","phone"),("العنوان","address")])
    def employees_page(self,_): self.entity_page("الموظفون","employees",[("اسم الموظف","name"),("الهاتف","phone"),("الوظيفة","job")])

    def users_page(self,_):
        self.title_block("المستخدمون والصلاحيات","حسابات فعلية وتطبيق الصلاحية على الوصول إلى الوحدات")
        form=tk.Frame(self.content,bg="#fff"); form.pack(fill="x",padx=28,pady=6)
        name=tk.StringVar(); role=tk.StringVar(value="مبيعات"); password=tk.StringVar(value="1234")
        for label,var,w,show in [("اسم المستخدم",name,16,None),("كلمة المرور",password,12,"*")]:
            r=tk.Frame(form,bg="#fff"); r.pack(side="right",padx=5,pady=10); tk.Label(r,text=label,bg="#fff").pack(anchor="e"); tk.Entry(r,textvariable=var,width=w,show=show,justify="right").pack(pady=3)
        tk.Label(form,text="الصلاحية",bg="#fff").pack(side="right",padx=5); ttk.Combobox(form,textvariable=role,values=list(ROLES),state="readonly",width=15).pack(side="right",padx=5)
        tree=ttk.Treeview(self.content,columns=("id","name","role","active","date"),show="headings")
        for c,h in [("id","الرقم"),("name","المستخدم"),("role","الصلاحية"),("active","الحالة"),("date","تاريخ الإضافة")]: tree.heading(c,text=h); tree.column(c,width=170,anchor="e")
        tree.pack(fill="both",expand=True,padx=28,pady=10)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT id,name,role,active,created_at FROM users ORDER BY id DESC").fetchall(): tree.insert("","end",values=(r["id"],r["name"],r["role"],"فعال" if r["active"] else "موقوف",r["created_at"]))
            c.close()
        def save():
            n=name.get().strip()
            if not n: messagebox.showwarning("تنبيه","أدخل اسم المستخدم."); return
            try:
                c=db(); c.execute("INSERT INTO users(name,role,active,created_at,password_hash,permissions) VALUES(?,?,?,?,?,?)",
                                  (n,role.get(),1,now(),hash_password(password.get()),json.dumps(sorted(ROLES[role.get()]),ensure_ascii=False))); c.commit(); c.close()
            except sqlite3.IntegrityError: messagebox.showwarning("تنبيه","اسم المستخدم موجود مسبقاً."); return
            audit("إضافة مستخدم",f"{n} - {role.get()}",self.current_user); name.set(""); password.set("1234"); refresh()
        tk.Button(form,text="إضافة مستخدم",command=save,bg="#172033",fg="#fff",relief="flat",padx=18,pady=8).pack(side="left",padx=15,pady=15); refresh()

    def inventory_page(self,_):
        self.title_block("المخزون","الرصيد والقيمة والتنبيهات")
        bar=tk.Frame(self.content,bg="#fff"); bar.pack(fill="x",padx=28,pady=6)
        low=tk.BooleanVar(value=False); search=tk.StringVar()
        tk.Label(bar,text="بحث",bg="#fff").pack(side="right",padx=5); tk.Entry(bar,textvariable=search,width=24,justify="right").pack(side="right")
        tk.Checkbutton(bar,text="منخفض المخزون",variable=low,bg="#fff",command=lambda:refresh()).pack(side="right",padx=15)
        tree=ttk.Treeview(self.content,columns=("name","category","qty","purchase","value","status"),show="headings")
        for c,h in [("name","الصنف"),("category","التصنيف"),("qty","الكمية"),("purchase","سعر الشراء"),("value","قيمة المخزون"),("status","الحالة")]: tree.heading(c,text=h); tree.column(c,width=160,anchor="e")
        tree.pack(fill="both",expand=True,padx=28,pady=10)
        def refresh(*_):
            tree.delete(*tree.get_children()); c=db(); rows=c.execute("SELECT name,category,quantity,purchase_price,quantity*purchase_price value,min_quantity FROM items WHERE name LIKE ? ORDER BY name",(f"%{search.get().strip()}%",)).fetchall(); c.close()
            for r in rows:
                if low.get() and float(r["quantity"])>float(r["min_quantity"]): continue
                tree.insert("","end",values=(r["name"],r["category"],r["quantity"],r["purchase_price"],r["value"],"منخفض" if r["quantity"]<=r["min_quantity"] else "طبيعي"))
        search.trace_add("write",refresh); refresh()

    def finance_page(self,_):
        self.title_block("المالية","المقبوضات والمصروفات مع رصيد مالي مباشر")
        form=tk.Frame(self.content,bg="#fff"); form.pack(fill="x",padx=28,pady=6)
        typ=tk.StringVar(value="قبض"); desc=tk.StringVar(); amount=tk.StringVar()
        tk.Label(form,text="النوع",bg="#fff").pack(side="right"); ttk.Combobox(form,textvariable=typ,values=["قبض","صرف"],state="readonly",width=10).pack(side="right",padx=6)
        tk.Label(form,text="البيان",bg="#fff").pack(side="right"); tk.Entry(form,textvariable=desc,width=28,justify="right").pack(side="right",padx=6)
        tk.Label(form,text="المبلغ",bg="#fff").pack(side="right"); tk.Entry(form,textvariable=amount,width=14,justify="right").pack(side="right",padx=6)        tree=ttk.Treeview(self.content,columns=("date","kind","desc","amount","user"),show="headings")
        for c,h in [("date","التاريخ"),("kind","النوع"),("desc","البيان"),("amount","المبلغ"),("user","المستخدم")]: tree.heading(c,text=h); tree.column(c,width=170,anchor="e")
        tree.pack(fill="both",expand=True,padx=28,pady=10)
        summary=tk.StringVar()
        tk.Label(self.content,textvariable=summary,bg="#f4f6f8",fg="#172033",font=("Tahoma",11,"bold")).pack(anchor="e",padx=28)
        def refresh():
            tree.delete(*tree.get_children()); c=db(); rows=c.execute("SELECT created_at,kind,description,amount,user_name FROM finance ORDER BY id DESC").fetchall()
            plus=c.execute("SELECT COALESCE(SUM(amount),0) n FROM finance WHERE kind='قبض'").fetchone()["n"]; minus=c.execute("SELECT COALESCE(SUM(amount),0) n FROM finance WHERE kind='صرف'").fetchone()["n"]; c.close()
            for r in rows: tree.insert("","end",values=tuple(r))
            summary.set(f"إجمالي القبض: {plus:,.2f}   |   إجمالي الصرف: {minus:,.2f}   |   الرصيد: {plus-minus:,.2f}")
        def save():
            try: a=float(amount.get() or 0)
            except ValueError: messagebox.showwarning("تنبيه","المبلغ غير صحيح."); return
            if a<=0: return
            c=db(); c.execute("INSERT INTO finance(kind,description,amount,created_at,user_name) VALUES(?,?,?,?,?)",(typ.get(),desc.get().strip(),a,now(),self.current_user)); c.commit(); c.close()
            self.push_undo("حذف العملية المالية",{"kind":typ.get(),"description":desc.get().strip(),"amount":a})
            audit("عملية مالية",f"{typ.get()} - {a:,.2f}",self.current_user); desc.set(""); amount.set(""); refresh()
        tk.Button(form,text="حفظ",command=save,bg="#172033",fg="#fff",relief="flat",padx=20,pady=7).pack(side="left",padx=12); refresh()

    def reports_page(self,_):
        self.title_block("التقارير","فلترة بالفترة والنوع والتصنيف والطرف، مع اختيار الأعمدة")
        bar=tk.Frame(self.content,bg="#fff"); bar.pack(fill="x",padx=28,pady=6)
        typ=tk.StringVar(value="الكل"); frm=tk.StringVar(); to=tk.StringVar(); cat=tk.StringVar(value="الكل")
        for label,var,values,w in [("النوع",typ,["الكل","بيع","شراء"],10),("التصنيف",cat,["الكل"],14)]:
            tk.Label(bar,text=label,bg="#fff").pack(side="right",padx=4); ttk.Combobox(bar,textvariable=var,values=values,state="readonly",width=w).pack(side="right",padx=4)
        tk.Label(bar,text="من",bg="#fff").pack(side="right"); tk.Entry(bar,textvariable=frm,width=12,justify="right").pack(side="right",padx=4)
        tk.Label(bar,text="إلى",bg="#fff").pack(side="right"); tk.Entry(bar,textvariable=to,width=12,justify="right").pack(side="right",padx=4)
        tree=ttk.Treeview(self.content,columns=("date","kind","party","item","qty","total","user"),show="headings")
        for c,h,w in [("date","التاريخ",170),("kind","النوع",80),("party","الطرف",150),("item","الصنف",170),("qty","الكمية",80),("total","الإجمالي",110),("user","المستخدم",110)]: tree.heading(c,text=h); tree.column(c,width=w,anchor="e")
        tree.pack(fill="both",expand=True,padx=28,pady=10)
        summary=tk.StringVar(); tk.Label(self.content,textvariable=summary,bg="#f4f6f8",font=("Tahoma",11,"bold")).pack(anchor="e",padx=28)
        def load_categories():
            c=db(); cats=[r["category"] for r in c.execute("SELECT DISTINCT category FROM items WHERE category<>'' ORDER BY category").fetchall()]; c.close()
            # إعادة بناء قائمة التصنيف.
            bar.winfo_children()[2] if False else None
            for w in bar.winfo_children(): 
                if isinstance(w, ttk.Combobox) and str(w.cget("textvariable"))==str(cat): w.configure(values=["الكل"]+cats)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            sql="SELECT t.created_at,t.kind,t.party,t.item,t.quantity,t.total,t.user_name FROM transactions t WHERE 1=1"; args=[]
            if typ.get()!="الكل": sql+=" AND t.kind=?"; args.append(typ.get())
            if frm.get().strip(): sql+=" AND date(t.created_at)>=date(?)"; args.append(frm.get().strip())
            if to.get().strip(): sql+=" AND date(t.created_at)<=date(?)"; args.append(to.get().strip())
            if cat.get()!="الكل": sql+=" AND EXISTS(SELECT 1 FROM items i WHERE i.name=t.item AND i.category=?)"; args.append(cat.get())
            sql+=" ORDER BY t.id DESC"; rows=c.execute(sql,args).fetchall(); c.close(); total=0
            for r in rows: tree.insert("","end",values=tuple(r)); total+=float(r["total"] or 0)
            summary.set(f"عدد العمليات: {len(rows)}   |   الإجمالي: {total:,.2f}")
        tk.Button(bar,text="تحديث التقرير",command=refresh,bg="#172033",fg="#fff",relief="flat",padx=16,pady=7).pack(side="left",padx=12)
        load_categories(); refresh()

    def audit_page(self,_):
        self.title_block("سجل الحركة والتدقيق","كل دخول وعمليات الحفظ والأخطاء مسجلة بالمستخدم والتاريخ")
        tree=ttk.Treeview(self.content,columns=("date","user","action","details"),show="headings")
        for c,h,w in [("date","التاريخ والوقت",175),("user","المستخدم",120),("action","العملية",210),("details","التفاصيل",650)]: tree.heading(c,text=h); tree.column(c,width=w,anchor="e")
        tree.pack(fill="both",expand=True,padx=28,pady=10)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT created_at,user_name,action,details FROM audit ORDER BY id DESC").fetchall(): tree.insert("","end",values=tuple(r))
            c.close()
        tk.Button(self.content,text="تحديث السجل",command=refresh,bg="#172033",fg="#fff",relief="flat",padx=18,pady=7).pack(anchor="e",padx=28); refresh()

    def settings_page(self,_):
        self.title_block("الإعدادات وتهيئة النظام","بيانات السوق، الفحص، والنسخ الاحتياطي المنطقي")
        box=tk.Frame(self.content,bg="#fff"); box.pack(fill="both",expand=True,padx=28,pady=10)
        vals={k:tk.StringVar(value=setting_get(k,"")) for k in ["market_name","owner_name","phone","address"]}
        for label,key in [("اسم السوق","market_name"),("اسم المالك","owner_name"),("رقم الهاتف","phone"),("العنوان","address")]:
            r=tk.Frame(box,bg="#fff"); r.pack(fill="x",padx=25,pady=7); tk.Label(r,text=label,bg="#fff",width=18,anchor="e").pack(side="right",padx=7); tk.Entry(r,textvariable=vals[key],width=48,justify="right").pack(side="right")
        def save():
            for k,v in vals.items(): setting_set(k,v.get())
            audit("حفظ بيانات السوق",vals["market_name"].get(),self.current_user); messagebox.showinfo("تم الحفظ","تم حفظ بيانات السوق.")
        def init_system():
            init_db(); audit("تهيئة النظام","فحص الجداول مع الحفاظ على البيانات",self.current_user); messagebox.showinfo("تهيئة النظام","تم فحص وتهيئة قاعدة البيانات دون حذف البيانات.")
        def backup():
            target=APP_DIR/(f"نسخة_احتياطية_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            src=db(); dst=sqlite3.connect(target); src.backup(dst); dst.close(); src.close(); audit("نسخة احتياطية",str(target),self.current_user)
            messagebox.showinfo("النسخ الاحتياطي",f"تم إنشاء نسخة احتياطية:\n{target}")
        tk.Button(box,text="حفظ بيانات السوق",command=save,bg="#172033",fg="#fff",relief="flat",padx=20,pady=8).pack(anchor="e",padx=25,pady=10)
        tk.Button(box,text="تهيئة النظام",command=init_system,bg="#15803d",fg="#fff",relief="flat",padx=20,pady=8).pack(anchor="e",padx=25,pady=6)
        tk.Button(box,text="إنشاء نسخة احتياطية الآن",command=backup,bg="#334155",fg="#fff",relief="flat",padx=20,pady=8).pack(anchor="e",padx=25,pady=6)
        tk.Label(box,text=f"قاعدة البيانات: {DB_PATH}",bg="#fff",fg="#6b7280",font=("Tahoma",9)).pack(anchor="e",padx=25,pady=20)

    def guide_page(self,_):
        self.title_block("الدليل والمساعدة","دليل عملي داخل البرنامج")
        txt=tk.Text(self.content,wrap="word",font=("Tahoma",11),bg="#fff",fg="#172033",padx=25,pady=20)
        txt.pack(fill="both",expand=True,padx=28,pady=10)
        guide="""دليل استخدام نظام الماركت المحاسبي

1) تسجيل الدخول
المستخدم الافتراضي: admin
كلمة المرور الافتراضية: 1234
يمكن لمدير النظام إضافة مستخدمين بصلاحيات مختلفة من شاشة المستخدمين والصلاحيات.

2) المبيعات
افتح المبيعات، ابحث عن الصنف، حدّد الكمية، أضفه إلى الفاتورة، ثم اختر العميل وطريقة الدفع وأتمم البيع.
عند إتمام البيع يتم تخفيض المخزون وحفظ الفاتورة وتسجيل العملية في سجل التدقيق.

3) المشتريات
سجل المورد والصنف والكمية والإجمالي. يتم تحديث المخزون وحساب المورد.

4) المخزون
يمكن البحث عن صنف وعرض الأصناف منخفضة المخزون وقيمة المخزون.

5) التقارير
يمكن تحديد نوع العملية والفترة والتصنيف ثم تحديث التقرير.

6) التراجع
زر التراجع يعكس آخر عملية قابلة للعكس نفذها المستخدم. لا يحذف سجل التدقيق، بل يسجل عملية العكس.

7) سجل الحركة والتدقيق
كل دخول وحفظ وبيع وشراء ومالية وتهيئة وأخطاء شاشة تسجل بالمستخدم والتاريخ والتفاصيل.

8) النسخ الاحتياطي
من الإعدادات يمكن إنشاء نسخة احتياطية من قاعدة البيانات دون حذف الأصل.

9) المساعد الذكي
زر مساعد النظام يعرض تشخيصاً أولياً مبنياً على بيانات النظام، مثل نقص المخزون وعدد العمليات وحالة قاعدة البيانات."""
        txt.insert("1.0",guide); txt.configure(state="disabled")

    def ai_assistant(self):
        c=db()
        items=c.execute("SELECT COUNT(*) n FROM items").fetchone()["n"]; low=c.execute("SELECT COUNT(*) n FROM items WHERE quantity<=min_quantity").fetchone()["n"]
        sales=c.execute("SELECT COUNT(*) n FROM transactions WHERE kind='بيع'").fetchone()["n"]; purchases=c.execute("SELECT COUNT(*) n FROM transactions WHERE kind='شراء'").fetchone()["n"]
        audits=c.execute("SELECT COUNT(*) n FROM audit").fetchone()["n"]; c.close()
        messagebox.showinfo("مساعد النظام",f"""تشخيص النظام الحالي

الأصناف: {items}
أصناف منخفضة المخزون: {low}
عمليات البيع: {sales}
عمليات الشراء: {purchases}
سجل التدقيق: {audits}

اقتراحات تلقائية:
- راجع الأصناف منخفضة المخزون.
- أنشئ نسخة احتياطية دورية.
- راجع سجل التدقيق عند وجود عملية غير متوقعة.
- تأكد من صلاحيات كل مستخدم.""")
        audit("استخدام مساعد النظام","تم إجراء تشخيص أولي",self.current_user)

    def push_undo(self,action,payload):
        c=db(); c.execute("INSERT INTO undo_log(action,details,created_at,user_name,payload) VALUES(?,?,?,?,?)",
                          (action,json.dumps(payload,ensure_ascii=False),now(),self.current_user,json.dumps(payload,ensure_ascii=False))); c.commit(); c.close()

    def undo_last(self):
        c=db()
        row=c.execute("SELECT * FROM undo_log WHERE user_name=? AND undone=0 ORDER BY id DESC LIMIT 1",(self.current_user,)).fetchone()
        if not row:
            c.close(); messagebox.showinfo("التراجع","لا توجد عملية قابلة للتراجع."); return
        try:
            payload=json.loads(row["payload"]); action=row["action"]
            if action=="حذف السجل":
                table=payload["table"]; rid=int(payload["id"]); c.execute(f"DELETE FROM {table} WHERE id=?",(rid,))
            elif action=="حذف العملية المالية":
                c.execute("DELETE FROM finance WHERE kind=? AND description=? AND amount=? ORDER BY id DESC LIMIT 1",(payload["kind"],payload["description"],payload["amount"]))
            elif action=="عكس عملية شراء":
                r=c.execute("SELECT id,quantity FROM items WHERE name=?",(payload["item"],)).fetchone()
                if r: c.execute("UPDATE items SET quantity=quantity-? WHERE id=?",(payload["quantity"],r["id"]))
                c.execute("DELETE FROM transactions WHERE kind='شراء' AND party=? AND item=? AND quantity=? AND total=? ORDER BY id DESC LIMIT 1",(payload["supplier"],payload["item"],payload["quantity"],payload["total"]))
                c.execute("UPDATE suppliers SET balance=balance-? WHERE name=?",(payload["total"],payload["supplier"]))
            elif action=="عكس فاتورة بيع":
                inv=payload["invoice_no"]; lines=c.execute("SELECT item_id,quantity,total FROM invoice_lines WHERE invoice_id=(SELECT id FROM invoices WHERE invoice_no=?)",(inv,)).fetchall()
                for r in lines:
                    if r["item_id"]: c.execute("UPDATE items SET quantity=quantity+? WHERE id=?",(r["quantity"],r["item_id"]))
                c.execute("DELETE FROM transactions WHERE invoice_no=?",(inv,))
                c.execute("DELETE FROM finance WHERE description=?",(inv,))
                c.execute("DELETE FROM invoices WHERE invoice_no=?",(inv,))
            else:
                c.close(); messagebox.showwarning("التراجع","هذه العملية لا تدعم التراجع الآمن."); return
            c.execute("UPDATE undo_log SET undone=1 WHERE id=?",(row["id"],)); c.commit(); c.close()
            audit("تراجع عن عملية",action,self.current_user); messagebox.showinfo("التراجع","تم عكس آخر عملية قابلة للتراجع بنجاح.")
            self.show("dashboard")
        except Exception as e:
            c.rollback(); c.close(); messagebox.showerror("خطأ في التراجع",str(e))

    def new_invoice_no(self):
        return "فاتورة-"+datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]

    def placeholder(self,title):
        self.title_block(title); tk.Label(self.content,text="الوحدة غير متاحة حالياً.",bg="#fff",fg="#6b7280",font=("Tahoma",13)).pack(fill="both",expand=True,padx=28,pady=10)

if __name__=="__main__":
    try:
        App().mainloop()
    except Exception:
        try: audit("خطأ تشغيل عام",traceback.format_exc(),"النظام")
        finally: raise