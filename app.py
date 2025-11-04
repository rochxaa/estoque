# app.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import db, utils
from datetime import datetime

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login - Controle de Estoque")
        self.geometry("300x160")
        self.resizable(False, False)
        self.build()

    def build(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(expand=True, fill=tk.BOTH)

        ttk.Label(frm, text="Usuário:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.username = ttk.Entry(frm)
        self.username.grid(row=0, column=1, pady=4)

        ttk.Label(frm, text="Senha:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.password = ttk.Entry(frm, show="*")
        self.password.grid(row=1, column=1, pady=4)

        btn = ttk.Button(frm, text="Entrar", command=self.do_login)
        btn.grid(row=2, column=0, columnspan=2, pady=12)

    def do_login(self):
        user = self.username.get().strip()
        pwd = self.password.get()
        if not user or not pwd:
            messagebox.showerror("Erro", "Usuário e senha obrigatórios.")
            return
        row = db.get_user_by_username(user)
        if not row:
            messagebox.showerror("Erro", "Usuário não encontrado.")
            return
        if db.verify_password(row["password_hash"], row["salt"], pwd):
            self.destroy()
            MainWindow(user_id=row["id"], username=row["username"], role=row["role"]).mainloop()
        else:
            messagebox.showerror("Erro", "Senha incorreta.")

class MainWindow(tk.Tk):
    def __init__(self, user_id, username, role):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.role = role
        self.title(f"Controle de Estoque - Usuário: {username} ({role})")
        self.geometry("800x500")
        self.build()

    def build(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Sair", command=self.quit)
        menubar.add_cascade(label="Arquivo", menu=filemenu)

        if self.role == "admin":
            usermenu = tk.Menu(menubar, tearoff=0)
            usermenu.add_command(label="Gerenciar Usuários", command=self.open_user_mgmt)
            menubar.add_cascade(label="Usuários", menu=usermenu)

        prodmenu = tk.Menu(menubar, tearoff=0)
        prodmenu.add_command(label="Novo Produto", command=self.open_new_product)
        menubar.add_cascade(label="Produtos", menu=prodmenu)

        # Search bar
        frm_top = ttk.Frame(self, padding=8)
        frm_top.pack(fill=tk.X)
        ttk.Label(frm_top, text="Buscar:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        ent_search = ttk.Entry(frm_top, textvariable=self.search_var)
        ent_search.pack(side=tk.LEFT, padx=6)
        ttk.Button(frm_top, text="Pesquisar", command=self.refresh_products).pack(side=tk.LEFT)

        # Treeview products
        cols = ("id","name","description","quantity","unit_price","created_at")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, anchor=tk.W)
        self.tree.pack(expand=True, fill=tk.BOTH, padx=8, pady=8)

        # Buttons
        frm_btn = ttk.Frame(self, padding=8)
        frm_btn.pack(fill=tk.X)
        ttk.Button(frm_btn, text="Editar", command=self.edit_selected).pack(side=tk.LEFT)
        ttk.Button(frm_btn, text="Excluir", command=self.delete_selected).pack(side=tk.LEFT)
        ttk.Button(frm_btn, text="Atualizar", command=self.refresh_products).pack(side=tk.RIGHT)

        self.refresh_products()

    def refresh_products(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        q = self.search_var.get().strip().lower()
        rows = db.list_products()
        for row in rows:
            if q and q not in (str(row["name"]).lower() + " " + str(row["description"] or "")).lower():
                continue
            self.tree.insert("", tk.END, values=(row["id"], row["name"], row["description"] or "", row["quantity"], f"{row['unit_price']:.2f}", row["created_at"] or ""))

    def open_user_mgmt(self):
        UserMgmtDialog(self)

    def open_new_product(self):
        ProductDialog(self, mode="create", user_id=self.user_id, callback=self.refresh_products)

    def get_selected_product_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        item = self.tree.item(sel[0])
        return int(item["values"][0])

    def edit_selected(self):
        pid = self.get_selected_product_id()
        if not pid:
            messagebox.showinfo("Info", "Selecione um produto para editar.")
            return
        ProductDialog(self, mode="edit", prod_id=pid, callback=self.refresh_products)

    def delete_selected(self):
        pid = self.get_selected_product_id()
        if not pid:
            messagebox.showinfo("Info", "Selecione um produto para excluir.")
            return
        if messagebox.askyesno("Confirmar", "Deseja realmente excluir o produto selecionado?"):
            db.delete_product(pid)
            messagebox.showinfo("Ok", "Produto excluído.")
            self.refresh_products()

class ProductDialog(tk.Toplevel):
    def __init__(self, parent, mode="create", prod_id=None, user_id=None, callback=None):
        super().__init__(parent)
        self.mode = mode
        self.prod_id = prod_id
        self.user_id = user_id
        self.callback = callback
        self.title("Produto" if mode=="create" else "Editar Produto")
        self.transient(parent)
        self.grab_set()
        self.build()
        if mode == "edit" and prod_id:
            self.load_product(prod_id)

    def build(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="Nome:").grid(row=0, column=0, sticky=tk.W)
        self.ent_name = ttk.Entry(frm, width=50)
        self.ent_name.grid(row=0, column=1, pady=4)

        ttk.Label(frm, text="Descrição:").grid(row=1, column=0, sticky=tk.W)
        self.ent_desc = ttk.Entry(frm, width=50)
        self.ent_desc.grid(row=1, column=1, pady=4)

        ttk.Label(frm, text="Quantidade:").grid(row=2, column=0, sticky=tk.W)
        self.ent_qty = ttk.Entry(frm)
        self.ent_qty.grid(row=2, column=1, pady=4, sticky=tk.W)

        ttk.Label(frm, text="Preço unitário:").grid(row=3, column=0, sticky=tk.W)
        self.ent_price = ttk.Entry(frm)
        self.ent_price.grid(row=3, column=1, pady=4, sticky=tk.W)

        btn_text = "Criar" if self.mode=="create" else "Salvar"
        ttk.Button(frm, text=btn_text, command=self.save).grid(row=4, column=0, columnspan=2, pady=8)

    def load_product(self, prod_id):
        row = db.get_product_by_id(prod_id)
        if not row:
            messagebox.showerror("Erro", "Produto não encontrado.")
            self.destroy()
            return
        self.ent_name.insert(0, row["name"])
        if row["description"]:
            self.ent_desc.insert(0, row["description"])
        self.ent_qty.insert(0, str(row["quantity"]))
        self.ent_price.insert(0, f"{row['unit_price']:.2f}")

    def save(self):
        name = self.ent_name.get().strip()
        desc = self.ent_desc.get().strip()
        qty = self.ent_qty.get().strip()
        price = self.ent_price.get().strip()
        if not name:
            messagebox.showerror("Erro", "Nome é obrigatório.")
            return
        if not utils.is_int(qty):
            messagebox.showerror("Erro", "Quantidade deve ser um número inteiro.")
            return
        if not utils.is_float(price):
            messagebox.showerror("Erro", "Preço unitário deve ser um número (ex: 12.50).")
            return
        qty_i = int(qty)
        price_f = float(price)
        if self.mode == "create":
            db.create_product(name, desc, qty_i, price_f, created_by=self.user_id)
            messagebox.showinfo("Ok", "Produto criado.")
        else:
            db.update_product(self.prod_id, name, desc, qty_i, price_f)
            messagebox.showinfo("Ok", "Produto atualizado.")
        if self.callback:
            self.callback()
        self.destroy()

class UserMgmtDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gerenciar Usuários")
        self.transient(parent)
        self.grab_set()
        self.build()
        self.refresh_users()

    def build(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(frm, columns=("id","username","role","created_at"), show="headings")
        for c in ("id","username","role","created_at"):
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, anchor=tk.W)
        self.tree.pack(expand=True, fill=tk.BOTH)

        frm_btn = ttk.Frame(self, padding=6)
        frm_btn.pack(fill=tk.X)
        ttk.Button(frm_btn, text="Novo Usuário", command=self.create_user).pack(side=tk.LEFT)
        ttk.Button(frm_btn, text="Remover", command=self.delete_selected).pack(side=tk.LEFT)
        ttk.Button(frm_btn, text="Atualizar", command=self.refresh_users).pack(side=tk.RIGHT)

    def refresh_users(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        rows = db.list_users()
        for row in rows:
            self.tree.insert("", tk.END, values=(row["id"], row["username"], row["role"], row["created_at"] or ""))

    def create_user(self):
        # popup para username, senha, role
        username = simpledialog.askstring("Novo usuário", "Nome de usuário (login):", parent=self)
        if not username:
            return
        password = simpledialog.askstring("Senha", "Senha:", parent=self, show="*")
        if not password:
            return
        role = simpledialog.askstring("Role", "Role ('admin' ou 'common'):", parent=self)
        if role not in ("admin","common"):
            messagebox.showerror("Erro", "Role inválida. Use 'admin' ou 'common'.")
            return
        pwd_hash, salt = utils.hash_password(password)
        try:
            db.create_user(username, pwd_hash, salt, role)
            messagebox.showinfo("Ok", "Usuário criado.")
            self.refresh_users()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível criar usuário: {e}")

    def get_selected_user_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        item = self.tree.item(sel[0])
        return int(item["values"][0])

    def delete_selected(self):
        uid = self.get_selected_user_id()
        if not uid:
            messagebox.showinfo("Info", "Selecione um usuário para remover.")
            return
        if messagebox.askyesno("Confirmar", "Deseja realmente remover o usuário?"):
            db.delete_user_by_id(uid)
            messagebox.showinfo("Ok", "Usuário removido.")
            self.refresh_users()

if __name__ == "__main__":
    LoginWindow().mainloop()
