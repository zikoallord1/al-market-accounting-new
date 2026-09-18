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
    ("الموردون", "suppliers"), ("المالية", "finance"), ("الموظفون", "employees"), ("المستخدمون والصلاحيات", "users"),
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
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE,role TEXT NOT NULL,active INTEGER DEFAULT 1,created_at TEXT);
    CREATE TABLE IF NOT EXISTS market_info(id INTEGER PRIMARY KEY CHECK(id=1),market_name TEXT,owner_name TEXT,phone TEXT,address TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY,value TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS undo_log(id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL,details TEXT,created_at TEXT);
    """)
    c.commit(); c.close()

def setting_get(key, default=""):
    c=db(); r=c.execute("SELECT value FROM system_settings WHERE key=?",(key,)).fetchone(); c.close()
    return r["value"] if r else default

def setting_set(key,value):
    c=db(); c.execute("INSERT INTO system_settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",(key,value,now())); c.commit(); c.close()

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
        self.build(); self.show("sales")

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

    def sales_page(self,_):
        self.title_block("المبيعات","واجهة البيع الرئيسية — إنشاء فاتورة وإتمام البيع من شاشة واحدة")

        root=tk.Frame(self.content,bg="#f4f6f8"); root.pack(fill="both",expand=True,padx=22,pady=5)

        # بيانات الفاتورة
        top=tk.Frame(root,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb")
        top.pack(fill="x",pady=(0,8))
        customer=tk.StringVar()
        payment=tk.StringVar(value="نقدي")
        tk.Label(top,text="العميل",bg="#fff",fg="#374151",font=("Tahoma",9)).pack(side="right",padx=(12,4),pady=12)
        customer_entry=tk.Entry(top,textvariable=customer,width=22,justify="right",font=("Tahoma",10))
        customer_entry.pack(side="right",pady=10)
        tk.Label(top,text="طريقة الدفع",bg="#fff",fg="#374151",font=("Tahoma",9)).pack(side="right",padx=(18,4))
        ttk.Combobox(top,textvariable=payment,values=["نقدي","آجل","بطاقة"],state="readonly",width=12,justify="right").pack(side="right",pady=10)
        invoice_no=tk.StringVar(value=datetime.now().strftime("فاتورة-%Y%m%d-%H%M%S"))
        tk.Label(top,textvariable=invoice_no,bg="#fff",fg="#6b7280",font=("Tahoma",9,"bold")).pack(side="left",padx=16)

        main=tk.Frame(root,bg="#f4f6f8"); main.pack(fill="both",expand=True)

        # قائمة الأصناف
        products=tk.Frame(main,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb")
        products.pack(side="left",fill="both",expand=True,padx=(0,7))
        tk.Label(products,text="الأصناف",bg="#fff",fg="#172033",font=("Tahoma",13,"bold")).pack(anchor="e",padx=14,pady=(12,6))
        search=tk.StringVar()
        search_entry=tk.Entry(products,textvariable=search,justify="right",font=("Tahoma",10))
        search_entry.pack(fill="x",padx=12,pady=(0,8))
        search_entry.insert(0,"ابحث باسم الصنف أو الباركود")
        search_entry.bind("<FocusIn>",lambda e: search_entry.delete(0,"end") if search_entry.get()=="ابحث باسم الصنف أو الباركود" else None)
        pcols=("id","name","barcode","price","qty")
        ptree=ttk.Treeview(products,columns=pcols,show="headings",height=15)
        for c,h,w in [("id","الرقم",55),("name","الصنف",190),("barcode","الباركود",120),("price","سعر البيع",95),("qty","المخزون",85)]:
            ptree.heading(c,text=h,anchor="e"); ptree.column(c,width=w,anchor="e")
        ptree.pack(fill="both",expand=True,padx=10,pady=5)

        controls=tk.Frame(products,bg="#fff"); controls.pack(fill="x",padx=10,pady=8)
        qty=tk.StringVar(value="1"); discount=tk.StringVar(value="0")
        tk.Label(controls,text="الكمية",bg="#fff").pack(side="right",padx=4)
        tk.Entry(controls,textvariable=qty,width=8,justify="right").pack(side="right",padx=4)
        tk.Label(controls,text="الخصم",bg="#fff").pack(side="right",padx=4)
        tk.Entry(controls,textvariable=discount,width=8,justify="right").pack(side="right",padx=4)
        invoice=[]

        # الفاتورة الحالية
        bill=tk.Frame(main,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb",width=480)
        bill.pack(side="right",fill="both",padx=(7,0)); bill.pack_propagate(False)
        tk.Label(bill,text="الفاتورة الحالية",bg="#fff",fg="#172033",font=("Tahoma",13,"bold")).pack(anchor="e",padx=14,pady=(12,6))
        bcols=("name","qty","price","discount","total")
        btree=ttk.Treeview(bill,columns=bcols,show="headings",height=13)
        for c,h,w in [("name","الصنف",145),("qty","الكمية",55),("price","السعر",75),("discount","الخصم",65),("total","الإجمالي",85)]:
            btree.heading(c,text=h,anchor="e"); btree.column(c,width=w,anchor="e")
        btree.pack(fill="both",expand=True,padx=10,pady=5)

        totals=tk.Frame(bill,bg="#fff"); totals.pack(fill="x",padx=14,pady=6)
        subtotal=tk.StringVar(value="0.00"); total_discount=tk.StringVar(value="0.00"); grand=tk.StringVar(value="0.00")
        for label,var in [("المجموع",subtotal),("الخصم",total_discount),("الإجمالي المستحق",grand)]:
            r=tk.Frame(totals,bg="#fff"); r.pack(fill="x",pady=2)
            tk.Label(r,text=label,bg="#fff",fg="#4b5563",font=("Tahoma",10,"bold" if label=="الإجمالي المستحق" else "normal")).pack(side="right")
            tk.Label(r,textvariable=var,bg="#fff",fg="#172033",font=("Tahoma",11,"bold")).pack(side="left")

        def refresh_products(*_):
            ptree.delete(*ptree.get_children())
            q=search.get().strip()
            c=db()
            rows=c.execute("SELECT id,name,barcode,sale_price,quantity FROM items WHERE name LIKE ? OR barcode LIKE ? ORDER BY name",(f"%{q}%",f"%{q}%")).fetchall() if q and q!="ابحث باسم الصنف أو الباركود" else c.execute("SELECT id,name,barcode,sale_price,quantity FROM items ORDER BY name").fetchall()
            for r in rows: ptree.insert("", "end",values=(r["id"],r["name"],r["barcode"] or "",r["sale_price"],r["quantity"]))
            c.close()

        def refresh_bill():
            btree.delete(*btree.get_children())
            sub=disc=0
            for i in invoice:
                btree.insert("", "end",values=(i["name"],i["qty"],f'{i["price"]:,.2f}',f'{i["discount"]:,.2f}',f'{i["total"]:,.2f}'))
                sub += i["qty"]*i["price"]; disc += i["discount"]
            subtotal.set(f"{sub:,.2f}"); total_discount.set(f"{disc:,.2f}"); grand.set(f"{sub-disc:,.2f}")

        def add_selected(event=None):
            sel=ptree.selection()
            if not sel: return
            vals=ptree.item(sel[0],"values")
            try:
                q=float(qty.get() or 0); d=float(discount.get() or 0)
            except ValueError:
                messagebox.showwarning("تنبيه","تحقق من الكمية والخصم."); return
            if q<=0 or d<0: messagebox.showwarning("تنبيه","الكمية والخصم يجب أن يكونا صحيحين."); return
            stock=float(vals[4]); price=float(vals[3])
            if q>stock: messagebox.showwarning("تنبيه","الكمية المطلوبة أكبر من المخزون المتاح."); return
            total=q*price-d
            if total<0: messagebox.showwarning("تنبيه","الخصم أكبر من قيمة الصنف."); return
            invoice.append({"id":int(vals[0]),"name":vals[1],"qty":q,"price":price,"discount":d,"total":total})
            refresh_bill(); qty.set("1"); discount.set("0")

        def remove_line():
            sel=btree.selection()
            if not sel: return
            idx=btree.index(sel[0]); invoice.pop(idx); refresh_bill()

        def clear_bill():
            invoice.clear(); refresh_bill(); customer.set(""); payment.set("نقدي")
            invoice_no.set(datetime.now().strftime("فاتورة-%Y%m%d-%H%M%S"))

        def complete_sale():
            if not invoice:
                messagebox.showwarning("تنبيه","الفاتورة فارغة."); return
            c=db()
            try:
                # التحقق مرة ثانية من المخزون داخل المعاملة قبل الحفظ
                for i in invoice:
                    row=c.execute("SELECT quantity FROM items WHERE id=?",(i["id"],)).fetchone()
                    if not row or float(row["quantity"])<i["qty"]:
                        raise ValueError(f"المخزون غير كافٍ للصنف: {i['name']}")
                inv=invoice_no.get(); party=customer.get().strip() or "عميل نقدي"
                total=sum(i["total"] for i in invoice)
                for i in invoice:
                    c.execute("UPDATE items SET quantity=quantity-? WHERE id=?",(i["qty"],i["id"]))
                    c.execute("INSERT INTO transactions(kind,party,item,quantity,total,created_at) VALUES(?,?,?,?,?,?)",("بيع",party,i["name"],i["qty"],i["total"],now()))
                if payment.get()=="نقدي":
                    c.execute("INSERT INTO finance(kind,description,amount,created_at) VALUES(?,?,?,?)",("قبض",inv,total,now()))
                c.commit()
                audit("إتمام بيع",f"{inv} | {party} | {total:,.2f} | {payment.get()}")
                messagebox.showinfo("تم الحفظ",f"تم إتمام الفاتورة بنجاح\\nالإجمالي: {total:,.2f}")
                clear_bill(); refresh_products()
            except ValueError as e:
                c.rollback(); messagebox.showwarning("تنبيه",str(e))
            except Exception as e:
                c.rollback(); messagebox.showerror("خطأ","تعذر حفظ الفاتورة.\\n"+str(e))
            finally:
                c.close()

        search.trace_add("write",refresh_products)
        ptree.bind("<Double-1>",add_selected)
        tk.Button(controls,text="إضافة للفاتورة",command=add_selected,bg="#172033",fg="#fff",relief="flat",font=("Tahoma",9,"bold"),padx=14,pady=7).pack(side="left",padx=4)
        tk.Button(bill,text="حذف السطر المحدد",command=remove_line,bg="#6b7280",fg="#fff",relief="flat",padx=12,pady=7).pack(side="left",padx=10,pady=6)
        tk.Button(bill,text="تفريغ الفاتورة",command=clear_bill,bg="#9ca3af",fg="#fff",relief="flat",padx=12,pady=7).pack(side="left",padx=4,pady=6)
        tk.Button(bill,text="إتمام البيع وحفظ الفاتورة",command=complete_sale,bg="#15803d",fg="#fff",relief="flat",font=("Tahoma",10,"bold"),padx=18,pady=9).pack(fill="x",padx=10,pady=(4,12))
        refresh_products()

    def purchases_page(self,_):
        self.title_block("المشتريات","إنشاء عملية شراء وتحديث المخزون تلقائياً")
        form=tk.Frame(self.content,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); form.pack(fill="x",padx=28,pady=6)
        supplier=tk.StringVar(); item=tk.StringVar(); qty=tk.StringVar(value="1"); total=tk.StringVar(value="0")
        fields=[("المورد",supplier,22),("الصنف",item,22),("الكمية",qty,10),("الإجمالي",total,14)]
        for label,var,w in fields:
            r=tk.Frame(form,bg="#fff"); r.pack(side="right",padx=7,pady=12)
            tk.Label(r,text=label,bg="#fff",font=("Tahoma",9)).pack(anchor="e")
            tk.Entry(r,textvariable=var,width=w,justify="right").pack(pady=4)
        tree=ttk.Treeview(self.content,columns=("date","supplier","item","qty","total"),show="headings")
        for c,h,w in [("date","التاريخ",180),("supplier","المورد",170),("item","الصنف",200),("qty","الكمية",100),("total","الإجمالي",130)]:
            tree.heading(c,text=h,anchor="e"); tree.column(c,width=w,anchor="e")
        tree.pack(fill="both",expand=True,padx=28,pady=10)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT created_at,party,item,quantity,total FROM transactions WHERE kind='شراء' ORDER BY id DESC").fetchall():
                tree.insert("","end",values=tuple(r))
            c.close()
        def save():
            name=item.get().strip()
            try: q=float(qty.get() or 0); amount=float(total.get() or 0)
            except ValueError: messagebox.showwarning("تنبيه","تحقق من الكمية والإجمالي."); return
            if not name or q<=0: messagebox.showwarning("تنبيه","أدخل الصنف والكمية."); return
            c=db(); row=c.execute("SELECT id FROM items WHERE name=?",(name,)).fetchone()
            if row: c.execute("UPDATE items SET quantity=quantity+? WHERE id=?",(q,row["id"]))
            else:
                c.execute("INSERT INTO items(name,barcode,sale_price,purchase_price,quantity,created_at) VALUES(?,?,?,?,?,?)",(name,"",0,amount/q,q,now()))
            c.execute("INSERT INTO transactions(kind,party,item,quantity,total,created_at) VALUES(?,?,?,?,?,?)",("شراء",supplier.get().strip() or "مورد غير محدد",name,q,amount,now()))
            c.commit(); c.close(); audit("إتمام شراء",f"{name} - {q} - {amount:,.2f}")
            supplier.set(""); item.set(""); qty.set("1"); total.set("0"); refresh()
        tk.Button(form,text="حفظ عملية الشراء",command=save,bg="#172033",fg="#fff",relief="flat",font=("Tahoma",10,"bold"),padx=20,pady=8).pack(side="left",padx=18,pady=18)
        refresh()
    def customers_page(self,_): self.entity_page("العملاء","customers",[("اسم العميل","name"),("الهاتف","phone"),("العنوان","address")])
    def suppliers_page(self,_): self.entity_page("الموردون","suppliers",[("اسم المورد","name"),("الهاتف","phone"),("العنوان","address")])
    def employees_page(self,_): self.entity_page("الموظفون","employees",[("اسم الموظف","name"),("الهاتف","phone"),("الوظيفة","job")])

    def users_page(self,_):
        self.title_block("المستخدمون والصلاحيات","إدارة المستخدمين والأدوار الأساسية")
        form=tk.Frame(self.content,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); form.pack(fill="x",padx=28,pady=6)
        name=tk.StringVar(); role=tk.StringVar(value="مدير النظام")
        tk.Label(form,text="اسم المستخدم",bg="#fff").pack(side="right",padx=6,pady=15)
        tk.Entry(form,textvariable=name,width=22,justify="right").pack(side="right",padx=6,pady=15)
        tk.Label(form,text="الصلاحية",bg="#fff").pack(side="right",padx=6)
        ttk.Combobox(form,textvariable=role,values=["مدير النظام","محاسب","مبيعات","مخزون"],state="readonly",width=16).pack(side="right",padx=6)
        tree=ttk.Treeview(self.content,columns=("id","name","role","active","date"),show="headings")
        for c,h in [("id","الرقم"),("name","المستخدم"),("role","الصلاحية"),("active","الحالة"),("date","تاريخ الإضافة")]:
            tree.heading(c,text=h,anchor="e"); tree.column(c,width=180,anchor="e")
        tree.pack(fill="both",expand=True,padx=28,pady=10)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT id,name,role,active,created_at FROM users ORDER BY id DESC").fetchall():
                tree.insert("","end",values=(r["id"],r["name"],r["role"],"فعال" if r["active"] else "موقوف",r["created_at"]))
            c.close()
        def save():
            n=name.get().strip()
            if not n: messagebox.showwarning("تنبيه","أدخل اسم المستخدم."); return
            try:
                c=db(); c.execute("INSERT INTO users(name,role,created_at) VALUES(?,?,?)",(n,role.get(),now())); c.commit(); c.close()
            except sqlite3.IntegrityError: messagebox.showwarning("تنبيه","اسم المستخدم موجود مسبقاً."); return
            audit("إضافة مستخدم",f"{n} - {role.get()}"); name.set(""); refresh()
        tk.Button(form,text="إضافة مستخدم",command=save,bg="#172033",fg="#fff",relief="flat",padx=18,pady=8).pack(side="left",padx=18,pady=15)
        refresh()

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
        self.title_block("التقارير","تقارير قابلة للتصفية حسب النوع والفترة")
        bar=tk.Frame(self.content,bg="#fff"); bar.pack(fill="x",padx=28,pady=6)
        typ=tk.StringVar(value="الكل"); frm=tk.StringVar(); to=tk.StringVar()
        tk.Label(bar,text="النوع",bg="#fff").pack(side="right",padx=5)
        ttk.Combobox(bar,textvariable=typ,values=["الكل","بيع","شراء"],state="readonly",width=12).pack(side="right",padx=5)
        tk.Label(bar,text="من (YYYY-MM-DD)",bg="#fff").pack(side="right",padx=5)
        tk.Entry(bar,textvariable=frm,width=14,justify="right").pack(side="right",padx=5)
        tk.Label(bar,text="إلى",bg="#fff").pack(side="right",padx=5)
        tk.Entry(bar,textvariable=to,width=14,justify="right").pack(side="right",padx=5)
        box=tk.Frame(self.content,bg="#fff"); box.pack(fill="both",expand=True,padx=28,pady=10)
        tree=ttk.Treeview(box,columns=("date","kind","party","item","qty","total"),show="headings")
        for c,h,w in [("date","التاريخ",180),("kind","النوع",100),("party","الطرف",160),("item","الصنف",180),("qty","الكمية",90),("total","الإجمالي",120)]:
            tree.heading(c,text=h,anchor="e"); tree.column(c,width=w,anchor="e")
        tree.pack(fill="both",expand=True,padx=10,pady=10)
        summary=tk.StringVar(value=""); tk.Label(box,textvariable=summary,bg="#fff",fg="#172033",font=("Tahoma",11,"bold")).pack(anchor="e",padx=12,pady=6)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            sql="SELECT created_at,kind,party,item,quantity,total FROM transactions WHERE 1=1"; args=[]
            if typ.get()!="الكل": sql+=" AND kind=?"; args.append(typ.get())
            if frm.get().strip(): sql+=" AND date(created_at)>=date(?)"; args.append(frm.get().strip())
            if to.get().strip(): sql+=" AND date(created_at)<=date(?)"; args.append(to.get().strip())
            sql+=" ORDER BY id DESC"; rows=c.execute(sql,args).fetchall()
            total_sum=0
            for r in rows: tree.insert("","end",values=tuple(r)); total_sum+=float(r["total"] or 0)
            c.close(); summary.set(f"عدد العمليات: {len(rows)}    |    الإجمالي: {total_sum:,.2f}")
        tk.Button(bar,text="عرض التقرير",command=refresh,bg="#172033",fg="#fff",relief="flat",padx=18,pady=7).pack(side="left",padx=15)
        refresh()

    def audit_page(self,_):
        self.title_block("سجل الحركة والتدقيق","سجل فعلي للعمليات التي ينفذها المستخدم داخل النظام")
        tree=ttk.Treeview(self.content,columns=("date","action","details"),show="headings")
        for c,h,w in [("date","التاريخ والوقت",180),("action","العملية",220),("details","التفاصيل",650)]:
            tree.heading(c,text=h,anchor="e"); tree.column(c,width=w,anchor="e")
        tree.pack(fill="both",expand=True,padx=28,pady=10)
        def refresh():
            tree.delete(*tree.get_children()); c=db()
            for r in c.execute("SELECT created_at,action,details FROM audit ORDER BY id DESC").fetchall():
                tree.insert("","end",values=tuple(r))
            c.close()
        tk.Button(self.content,text="تحديث السجل",command=refresh,bg="#172033",fg="#fff",relief="flat",padx=18,pady=7).pack(anchor="e",padx=28)
        refresh()

    def settings_page(self,_):
        self.title_block("الإعدادات وتهيئة النظام","بيانات السوق الأساسية وأدوات التهيئة")
        box=tk.Frame(self.content,bg="#fff",highlightthickness=1,highlightbackground="#e5e7eb"); box.pack(fill="both",expand=True,padx=28,pady=10)
        market=tk.StringVar(value=setting_get("market_name","")); owner=tk.StringVar(value=setting_get("owner_name",""))
        phone=tk.StringVar(value=setting_get("phone","")); address=tk.StringVar(value=setting_get("address",""))
        for label,var in [("اسم السوق",market),("اسم المالك",owner),("رقم الهاتف",phone),("العنوان",address)]:
            r=tk.Frame(box,bg="#fff"); r.pack(fill="x",padx=25,pady=8)
            tk.Label(r,text=label,bg="#fff",width=18,anchor="e",font=("Tahoma",10,"bold")).pack(side="right",padx=8)
            tk.Entry(r,textvariable=var,width=45,justify="right").pack(side="right")
        def save_info():
            for k,v in [("market_name",market.get()),("owner_name",owner.get()),("phone",phone.get()),("address",address.get())]: setting_set(k,v)
            audit("حفظ بيانات السوق",market.get()); messagebox.showinfo("تم الحفظ","تم حفظ بيانات السوق بنجاح.")
        def init_system():
            init_db(); audit("تهيئة النظام","تم فحص وإنشاء جداول النظام دون حذف البيانات")
            messagebox.showinfo("تهيئة النظام","تمت التهيئة والفحص مع الحفاظ على البيانات الحالية.")
        tk.Button(box,text="حفظ بيانات السوق",command=save_info,bg="#172033",fg="#fff",relief="flat",padx=20,pady=9).pack(anchor="e",padx=25,pady=12)
        tk.Button(box,text="تهيئة النظام",command=init_system,bg="#15803d",fg="#fff",relief="flat",padx=20,pady=9).pack(anchor="e",padx=25,pady=8)
        tk.Label(box,text="مسار قاعدة البيانات:",bg="#fff",fg="#374151",font=("Tahoma",10,"bold")).pack(anchor="e",padx=25,pady=(25,4))
        tk.Label(box,text=str(DB_PATH),bg="#fff",fg="#6b7280",font=("Tahoma",9)).pack(anchor="e",padx=25)

    def placeholder(self,title):
        self.title_block(title)
        tk.Label(self.content,text="الوحدة غير متاحة حالياً.",bg="#fff",fg="#6b7280",font=("Tahoma",13)).pack(fill="both",expand=True,padx=28,pady=10)

if __name__=="__main__":
    App().mainloop()
