import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime

APP_NAME = "نظام الماركت المحاسبي"
APP_DIR = Path.home() / "Documents" / APP_NAME
DB_PATH = APP_DIR / "market.db"
APP_DIR.mkdir(parents=True, exist_ok=True)

MODULES = [
    ("لوحة التحكم", "dashboard"), ("المبيعات", "sales"), ("المشتريات", "purchases"),
    ("الأصناف", "items"), ("المخزون", "inventory"), ("العملاء", "customers"),
    ("الموردون", "suppliers"), ("المالية", "finance"), ("الموظفون", "employees"),
    ("التقارير", "reports"), ("سجل الحركة والتدقيق", "audit"), ("الإعدادات", "settings")
]

def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def audit(action, details=""):
    c = db()
    c.execute("INSERT INTO audit(action,details,created_at) VALUES(?,?,?)",(action,details,now()))
    c.commit(); c.close()

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS items(
      id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,barcode TEXT,
      sale_price REAL DEFAULT 0,purchase_price REAL DEFAULT 0,quantity REAL DEFAULT 0,created_at TEXT);
    CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT,address TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS suppliers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT,address TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT,job TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,party TEXT,item TEXT,quantity REAL DEFAULT 0,total REAL DEFAULT 0,created_at TEXT);
    CREATE TABLE IF NOT EXISTS finance(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,description TEXT,amount REAL DEFAULT 0,created_at TEXT);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL,details TEXT,created_at TEXT);
    """)
    c.commit(); c.close()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME); self.geometry("1200x760"); self.minsize(1000,650); self.configure(bg="#f4f6f8")
        init_db(); audit("تشغيل النظام","تم فتح البرنامج")
        s=ttk.Style(self)
        try: s.theme_use("clam")
        except tk.TclError: pass
        s.configure("Treeview",rowheight=32,font=("Tahoma",10))
        s.configure("Treeview.Heading",font=("Tahoma",10,"bold"))
        self.build(); self.show("dashboard")

    def build(self):
        h=tk.Frame(self,bg="#fff",height=72); h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h,text=APP_NAME,bg="#fff",fg="#172033",font=("Tahoma",20,"bold")).pack(side="right",padx=28,pady=17)
        tk.Label(h,text="إدارة المبيعات والمشتريات والمخزون والحسابات",bg="#fff",fg="#6b7280",font=("Tahoma",10)).pack(side="right")
        body=tk.Frame(self,bg="#f4f6f8"); body.pack(fill="both",expand=True)
        self.sidebar=tk.Frame(body,bg="#172033",width=245); self.sidebar.pack(side="left",fill="y"); self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar,text="القائمة الرئيسية",bg="#172033",fg="#fff",font=("Tahoma",13,"bold")).pack(anchor="e",padx=22,pady=(22,12))
        self.buttons={}
        for label,key in MODULES:
            b=tk.Button(self.sidebar,text=label,command=lambda k=key:self.show(k),bg="#172033",fg="#e5e7eb",
                        activebackground="#263552",activeforeground="#fff",relief="flat",bd=0,font=("Tahoma",10),
                        anchor="e",padx=20,pady=9,cursor="hand2")
            b.pack(fill="x",padx=10,pady=1); self.buttons[key]=b
        self.content=tk.Frame(body,bg="#f4f6f8"); self.content.pack(side="right",fill="both",expand=True)
        f=tk.Frame(self,bg="#fff",height=58); f.pack(fill="x"); f.pack_propagate(False)
        tk.Label(f,text="تصميم وتنفيذ المهندس : زكريا الحاج",bg="#fff",fg="#4b5563",font=("Tahoma",9,"bold")).pack(side="right",padx=20,pady=8)
        tk.Label(f,text="لطلب البرنامج او تصميم برامج اخرى التواصل على الرقم 772233564",bg="#fff",fg="#4b5563",font=("Tahoma",9)).pack(side="right")
        tk.Label(f,text="☎ 772233564    واتساب: 772233564",bg="#fff",fg="#15803d",font=("Tahoma",9,"bold")).pack(side="left",padx=20)

    def clear(self):
        for w in self.content.winfo_children(): w.destroy()

    def title_block(self,title,sub=""):
        x=tk.Frame(self.content,bg="#f4f6f8"); x.pack(fill="x",padx=28,pady=(22,8))
        tk.Label(x,text=title,bg="#f4f6f8",fg="#172033",font=("Tahoma",19,"bold")).pack(anchor="e")
        if sub: tk.Label(x,text=sub,bg="#f4f6f8",fg="#6b7280",font=("Tahoma",10)).pack(anchor="e",pady=3)

    def card(self,p,text,value):
        x=tk.Frame(p,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); x.pack(side="right",fill="both",expand=True,padx=5)
        tk.Label(x,text=text,bg="#fff",fg="#6b7280",font=("Tahoma",10)).pack(anchor="e",padx=16,pady=(15,4))
        tk.Label(x,text=value,bg="#fff",fg="#172033",font=("Tahoma",19,"bold")).pack(anchor="e",padx=16,pady=(0,15))

    def show(self,key):
        self.clear()
        for k,b in self.buttons.items():
            b.configure(bg="#263552" if k==key else "#172033")
        title = next((label for label,module_key in MODULES if module_key == key), key)
        page = getattr(self, key + "_page", self.placeholder)
        page(title)

    def dashboard_page(self,_):
        self.title_block("لوحة التحكم","ملخص النظام في شاشة واحدة")
        c=db()
        counts=[c.execute("SELECT COUNT(*) n FROM items").fetchone()["n"],
                c.execute("SELECT COALESCE(SUM(quantity),0) n FROM items").fetchone()["n"],
                c.execute("SELECT COUNT(*) n FROM transactions").fetchone()["n"],
                c.execute("SELECT COUNT(*) n FROM audit").fetchone()["n"]]
        c.close()
        row=tk.Frame(self.content,bg="#f4f6f8"); row.pack(fill="x",padx=22,pady=8)
        for t,v in zip(["عدد الأصناف","كمية المخزون","عدد العمليات","سجل التدقيق"],counts): self.card(row,t,f"{v:g}" if isinstance(v,float) else str(v))
        box=tk.Frame(self.content,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); box.pack(fill="both",expand=True,padx=28,pady=15)
        tk.Label(box,text="مرحباً بك في نظام الماركت المحاسبي",bg="#fff",fg="#172033",font=("Tahoma",16,"bold")).pack(anchor="e",padx=24,pady=(28,8))
        tk.Label(box,text="كل تبويبات النظام تعمل بنفس التصميم، مع حفظ العمليات في قاعدة البيانات وسجل الحركة.",bg="#fff",fg="#6b7280",font=("Tahoma",11)).pack(anchor="e",padx=24)

    def entity_page(self,title,table,fields):
        self.title_block(title,"إضافة وعرض البيانات بنفس الواجهة")
        form=tk.Frame(self.content,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); form.pack(fill="x",padx=28,pady=6)
        entries={}
        for label,col in fields:
            r=tk.Frame(form,bg="#fff"); r.pack(side="right",padx=7,pady=12)
            tk.Label(r,text=label,bg="#fff",fg="#374151",font=("Tahoma",9)).pack(anchor="e")
            e=tk.Entry(r,width=18,justify="right",font=("Tahoma",10)); e.pack(pady=4); entries[col]=e
        box=tk.Frame(self.content,bg="#fff"); box.pack(fill="both",expand=True,padx=28,pady=10)
        cols=["id"]+[x[1] for x in fields]; tree=ttk.Treeview(box,columns=cols,show="headings")
        for col in cols:
            tree.heading(col,text="الرقم" if col=="id" else next(x[0] for x in fields if x[1]==col),anchor="e"); tree.column(col,width=140,anchor="e")
        tree.pack(fill="both",expand=True)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT "+",".join(cols)+" FROM "+table+" ORDER BY id DESC").fetchall(): tree.insert("", "end", values=tuple(r))
            c.close()
        def save():
            vals=[entries[col].get().strip() for _,col in fields]
            if not vals[0]: messagebox.showwarning("تنبيه","أدخل البيانات المطلوبة."); return
            c=db(); c.execute("INSERT INTO "+table+"("+",".join(x[1] for x in fields)+",created_at) VALUES("+",".join("?" for _ in fields)+",?)",vals+[now()]); c.commit(); c.close()
            audit("إضافة "+title,vals[0]); [e.delete(0,"end") for e in entries.values()]; refresh()
        tk.Button(form,text="حفظ",command=save,bg="#172033",fg="#fff",relief="flat",font=("Tahoma",10,"bold"),padx=25,pady=8).pack(side="left",padx=18,pady=18)
        refresh()

    def items_page(self,_):
        self.title_block("الأصناف","إدارة الأصناف والأسعار والكميات")
        form=tk.Frame(self.content,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); form.pack(fill="x",padx=28,pady=6)
        names=[("اسم الصنف","name"),("الباركود","barcode"),("سعر البيع","sale_price"),("سعر الشراء","purchase_price"),("الكمية","quantity")]
        e={}
        for label,col in names:
            r=tk.Frame(form,bg="#fff"); r.pack(side="right",padx=6,pady=12); tk.Label(r,text=label,bg="#fff",font=("Tahoma",9)).pack(anchor="e")
            z=tk.Entry(r,width=16,justify="right"); z.pack(pady=4); e[col]=z
        box=tk.Frame(self.content,bg="#fff"); box.pack(fill="both",expand=True,padx=28,pady=10)
        tree=ttk.Treeview(box,columns=("id","name","barcode","sale_price","purchase_price","quantity"),show="headings"); heads={"id":"الرقم","name":"اسم الصنف","barcode":"الباركود","sale_price":"سعر البيع","purchase_price":"سعر الشراء","quantity":"الكمية"}
        for c,h in heads.items(): tree.heading(c,text=h,anchor="e"); tree.column(c,width=125,anchor="e")
        tree.pack(fill="both",expand=True)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT id,name,barcode,sale_price,purchase_price,quantity FROM items ORDER BY id DESC").fetchall(): tree.insert("", "end",values=tuple(r))
            c.close()
        def save():
            if not e["name"].get().strip(): messagebox.showwarning("تنبيه","أدخل اسم الصنف."); return
            try: vals=[e["name"].get().strip(),e["barcode"].get().strip(),float(e["sale_price"].get() or 0),float(e["purchase_price"].get() or 0),float(e["quantity"].get() or 0)]
            except ValueError: messagebox.showwarning("تنبيه","تحقق من الأرقام."); return
            c=db(); c.execute("INSERT INTO items(name,barcode,sale_price,purchase_price,quantity,created_at) VALUES(?,?,?,?,?,?)",vals+[now()]); c.commit(); c.close()
            audit("إضافة صنف",vals[0]); [z.delete(0,"end") for z in e.values()]; refresh()
        tk.Button(form,text="حفظ الصنف",command=save,bg="#172033",fg="#fff",relief="flat",font=("Tahoma",10,"bold"),padx=20,pady=8).pack(side="left",padx=15,pady=18)
        refresh()

    def transaction_page(self,title,kind):
        self.title_block(title,"تسجيل العملية وتحديث المخزون تلقائياً")
        form=tk.Frame(self.content,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); form.pack(fill="x",padx=28,pady=6)
        labels=[("الطرف","party"),("الصنف","item"),("الكمية","quantity"),("الإجمالي","total")]; e={}
        for label,col in labels:
            r=tk.Frame(form,bg="#fff"); r.pack(side="right",padx=8,pady=13); tk.Label(r,text=label,bg="#fff",font=("Tahoma",9)).pack(anchor="e")
            z=tk.Entry(r,width=19,justify="right"); z.pack(pady=4); e[col]=z
        box=tk.Frame(self.content,bg="#fff"); box.pack(fill="both",expand=True,padx=28,pady=10)
        tree=ttk.Treeview(box,columns=("date","party","item","quantity","total"),show="headings")
        for c,h in [("date","التاريخ"),("party","الطرف"),("item","الصنف"),("quantity","الكمية"),("total","الإجمالي")]: tree.heading(c,text=h,anchor="e"); tree.column(c,width=150,anchor="e")
        tree.pack(fill="both",expand=True)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT created_at,party,item,quantity,total FROM transactions WHERE kind=? ORDER BY id DESC",(kind,)).fetchall(): tree.insert("", "end",values=tuple(r))
            c.close()
        def save():
            try: q=float(e["quantity"].get() or 0); total=float(e["total"].get() or 0)
            except ValueError: messagebox.showwarning("تنبيه","تحقق من الكمية والإجمالي."); return
            item=e["item"].get().strip(); party=e["party"].get().strip()
            if not item or q<=0: messagebox.showwarning("تنبيه","أدخل الصنف والكمية."); return
            c=db(); row=c.execute("SELECT id,quantity FROM items WHERE name=?",(item,)).fetchone()
            if not row: messagebox.showwarning("تنبيه","الصنف غير موجود. أضفه أولاً من تبويب الأصناف."); c.close(); return
            newq=row["quantity"] + (q if kind=="شراء" else -q)
            if kind=="بيع" and newq<0: messagebox.showwarning("تنبيه","الكمية المتاحة في المخزون غير كافية."); c.close(); return
            c.execute("UPDATE items SET quantity=? WHERE id=?",(newq,row["id"]))
            c.execute("INSERT INTO transactions(kind,party,item,quantity,total,created_at) VALUES(?,?,?,?,?,?)",(kind,party,item,q,total,now()))
            c.commit(); c.close(); audit("تسجيل "+kind,f"{item} - {q}"); [z.delete(0,"end") for z in e.values()]; refresh()
        tk.Button(form,text="حفظ العملية",command=save,bg="#172033",fg="#fff",relief="flat",font=("Tahoma",10,"bold"),padx=20,pady=8).pack(side="left",padx=18,pady=18)
        refresh()

    def sales_page(self,_): self.transaction_page("المبيعات","بيع")
    def purchases_page(self,_): self.transaction_page("المشتريات","شراء")
    def customers_page(self,_): self.entity_page("العملاء","customers",[("اسم العميل","name"),("الهاتف","phone"),("العنوان","address")])
    def suppliers_page(self,_): self.entity_page("الموردون","suppliers",[("اسم المورد","name"),("الهاتف","phone"),("العنوان","address")])
    def employees_page(self,_): self.entity_page("الموظفون","employees",[("اسم الموظف","name"),("الهاتف","phone"),("الوظيفة","job")])

    def inventory_page(self,_):
        self.title_block("المخزون","الرصيد الحالي وقيمة المخزون")
        box=tk.Frame(self.content,bg="#fff"); box.pack(fill="both",expand=True,padx=28,pady=10)
        tree=ttk.Treeview(box,columns=("name","qty","purchase","value"),show="headings")
        for c,h in [("name","الصنف"),("qty","الكمية"),("purchase","سعر الشراء"),("value","قيمة المخزون")]: tree.heading(c,text=h,anchor="e"); tree.column(c,width=190,anchor="e")
        tree.pack(fill="both",expand=True); c=db()
        for r in c.execute("SELECT name,quantity,purchase_price,quantity*purchase_price value FROM items ORDER BY name").fetchall(): tree.insert("", "end",values=tuple(r))
        c.close()

    def finance_page(self,_):
        self.title_block("المالية","تسجيل المقبوضات والمصروفات")
        form=tk.Frame(self.content,bg="#fff"); form.pack(fill="x",padx=28,pady=6)
        typ=tk.StringVar(value="قبض"); desc=tk.Entry(form,width=30,justify="right"); amount=tk.Entry(form,width=18,justify="right")
        tk.Label(form,text="نوع العملية",bg="#fff").pack(side="right",padx=5); ttk.Combobox(form,textvariable=typ,values=["قبض","صرف"],state="readonly",width=12).pack(side="right",padx=5)
        tk.Label(form,text="البيان",bg="#fff").pack(side="right"); desc.pack(side="right",padx=5); tk.Label(form,text="المبلغ",bg="#fff").pack(side="right"); amount.pack(side="right",padx=5)
        tree=ttk.Treeview(self.content,columns=("date","kind","desc","amount"),show="headings"); tree.pack(fill="both",expand=True,padx=28,pady=10)
        for c,h in [("date","التاريخ"),("kind","النوع"),("desc","البيان"),("amount","المبلغ")]: tree.heading(c,text=h,anchor="e"); tree.column(c,width=190,anchor="e")
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT created_at,kind,description,amount FROM finance ORDER BY id DESC").fetchall(): tree.insert("", "end",values=tuple(r))
            c.close()
        def save():
            try: a=float(amount.get() or 0)
            except ValueError: messagebox.showwarning("تنبيه","المبلغ غير صحيح."); return
            if a<=0: return
            c=db(); c.execute("INSERT INTO finance(kind,description,amount,created_at) VALUES(?,?,?,?)",(typ.get(),desc.get().strip(),a,now())); c.commit(); c.close()
            audit("عملية مالية",f"{typ.get()} - {a:g}"); desc.delete(0,"end"); amount.delete(0,"end"); refresh()
        tk.Button(form,text="حفظ",command=save,bg="#172033",fg="#fff",relief="flat",padx=20,pady=7).pack(side="left",padx=12)
        refresh()

    def reports_page(self,_):
        self.title_block("التقارير","ملخص قابل للعرض من قاعدة البيانات")
        box=tk.Frame(self.content,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); box.pack(fill="both",expand=True,padx=28,pady=10)
        c=db(); sales=c.execute("SELECT COALESCE(SUM(total),0) n FROM transactions WHERE kind='بيع'").fetchone()["n"]; purchases=c.execute("SELECT COALESCE(SUM(total),0) n FROM transactions WHERE kind='شراء'").fetchone()["n"]; cash=c.execute("SELECT COALESCE(SUM(CASE WHEN kind='قبض' THEN amount ELSE -amount END),0) n FROM finance").fetchone()["n"]; c.close()
        for text,val in [("إجمالي المبيعات",sales),("إجمالي المشتريات",purchases),("صافي الحركة المالية",cash)]:
            self.card(box,text,f"{val:,.2f}")
        tk.Label(box,text="يمكن توسيع التقارير لاحقاً بإضافة الفترات والتصفية والطباعة.",bg="#fff",fg="#6b7280",font=("Tahoma",11)).pack(anchor="e",padx=20,pady=25)

    def audit_page(self,_):
        self.title_block("سجل الحركة والتدقيق","كل عملية مهمة تسجل بتاريخها وتفاصيلها")
        tree=ttk.Treeview(self.content,columns=("date","action","details"),show="headings"); tree.pack(fill="both",expand=True,padx=28,pady=10)
        for c,h,w in [("date","التاريخ والوقت",180),("action","العملية",210),("details","التفاصيل",600)]: tree.heading(c,text=h,anchor="e"); tree.column(c,width=w,anchor="e")
        c=db()
        for r in c.execute("SELECT created_at,action,details FROM audit ORDER BY id DESC").fetchall(): tree.insert("", "end",values=tuple(r))
        c.close()

    def settings_page(self,_):
        self.title_block("الإعدادات","تهيئة البرنامج وبياناته الأساسية")
        box=tk.Frame(self.content,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); box.pack(fill="both",expand=True,padx=28,pady=10)
        tk.Label(box,text="مسار بيانات النظام:",bg="#fff",fg="#374151",font=("Tahoma",11,"bold")).pack(anchor="e",padx=25,pady=(30,5))
        tk.Label(box,text=str(DB_PATH),bg="#fff",fg="#6b7280",font=("Tahoma",10)).pack(anchor="e",padx=25)
        tk.Button(box,text="تسجيل عملية فحص النظام",command=lambda:(audit("فحص النظام","تم تنفيذ فحص يدوي"),messagebox.showinfo("تم","تم تسجيل الفحص في سجل الحركة.")),bg="#172033",fg="#fff",relief="flat",padx=20,pady=9).pack(anchor="e",padx=25,pady=25)

    def placeholder(self,title):
        self.title_block(title)
        tk.Label(self.content,text="الوحدة غير متاحة حالياً.",bg="#fff",fg="#6b7280",font=("Tahoma",13)).pack(fill="both",expand=True,padx=28,pady=10)

if __name__=="__main__":
    App().mainloop()
