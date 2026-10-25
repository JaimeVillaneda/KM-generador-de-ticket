import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import re

class ClientModule:
    def __init__(self, parent_frame, data_manager, refresh_callback=None, use_in_ticket_callback=None):
        self.parent = parent_frame
        self.data_manager = data_manager
        self.refresh_callback = refresh_callback
        self.use_in_ticket_callback = use_in_ticket_callback
        self._sort_reverse = {}
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de gestión de clientes"""
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Lista de clientes
        self.list_frame = ttk.LabelFrame(self.main_frame, text="Clientes Registrados")
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        top_bar = ttk.Frame(self.list_frame)
        top_bar.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top_bar, text="Buscar:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top_bar, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind("<KeyRelease>", lambda e: self.load_clients())

        self.tree = ttk.Treeview(self.list_frame, columns=('name', 'nit', 'email', 'phone', 'location'), show='headings')
        self.tree.heading('name', text='Nombre', command=lambda: self.sort_tree('name'))
        self.tree.heading('nit', text='NIT/CC', command=lambda: self.sort_tree('nit'))
        self.tree.heading('email', text='Correo', command=lambda: self.sort_tree('email'))
        self.tree.heading('phone', text='Teléfono', command=lambda: self.sort_tree('phone'))
        self.tree.heading('location', text='Ubicación', command=lambda: self.sort_tree('location'))
        self.tree.pack(fill=tk.BOTH, expand=True)
        self._enable_tree_hover(self.tree)

        # Botones de acción
        btn_frame = ttk.Frame(self.list_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Nuevo", command=self.new_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editar", command=self.edit_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Usar en Ticket", command=self.use_in_ticket).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Exportar", command=self.export_clients).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Importar", command=self.import_clients).pack(side=tk.RIGHT, padx=5)
        self.load_clients()

    def _enable_tree_hover(self, tree: ttk.Treeview):
        hover_tag = "__hover__"
        tree.tag_configure(hover_tag, background="#d9d9d9")
        state = {"last": None}

        def _remove_hover(item_id):
            if not item_id:
                return
            tags = list(tree.item(item_id, "tags"))
            if hover_tag in tags:
                tags.remove(hover_tag)
                tree.item(item_id, tags=tuple(tags))

        def _add_hover(item_id):
            if not item_id:
                return
            tags = list(tree.item(item_id, "tags"))
            if hover_tag not in tags:
                tags.append(hover_tag)
                tree.item(item_id, tags=tuple(tags))

        def on_motion(event):
            item = tree.identify_row(event.y)
            if item == state["last"]:
                return
            _remove_hover(state["last"])
            state["last"] = item
            _add_hover(item)

        def on_leave(_event):
            _remove_hover(state["last"])
            state["last"] = None

        tree.bind("<Motion>", on_motion, add="+")
        tree.bind("<Leave>", on_leave, add="+")

    def load_clients(self):
        """Carga los clientes en el treeview"""
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        clients = self.data_manager.load_clients()
        query = (self.search_var.get() if hasattr(self, "search_var") else "").strip().lower()
        for client in clients:
            if query:
                haystack = " ".join([
                    str(client.get("nombre", "")),
                    str(client.get("nit", "")),
                    str(client.get("correo", "")),
                    str(client.get("telefono", "")),
                    str(client.get("departamento", "")),
                    str(client.get("municipio", "")),
                ]).lower()
                if query not in haystack:
                    continue
            location = f"{client.get('departamento', '')} - {client.get('municipio', '')}".strip(' - ')
            self.tree.insert('', tk.END, values=(
                client['nombre'],
                client.get('nit', ''),
                client.get('correo', ''),
                client.get('telefono', ''),
                location
            ))

    def sort_tree(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        reverse = self._sort_reverse.get(col, False)

        def _key(val):
            try:
                return float(str(val).replace(".", "").replace(",", "."))
            except Exception:
                return str(val).lower()

        items.sort(key=lambda t: _key(t[0]), reverse=reverse)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, '', index)
        self._sort_reverse[col] = not reverse

    def new_client(self):
        ClientFormModal(self.parent, self.data_manager, client=None, index=-1, on_saved=self._after_saved)

    def edit_client(self):
        """Carga el cliente seleccionado para editar"""
        index, client = self.get_selected_client_with_index()
        if client is None:
            messagebox.showwarning("Advertencia", "Seleccione un cliente para editar")
            return
        ClientFormModal(self.parent, self.data_manager, client=client, index=index, on_saved=self._after_saved)

    def delete_client(self):
        """Elimina el cliente seleccionado"""
        index, client = self.get_selected_client_with_index()
        if client is None:
            messagebox.showwarning("Advertencia", "Seleccione un cliente para eliminar")
            return

        if client.get("nombre") == "Mostrador":
            messagebox.showwarning("Advertencia", "No se puede eliminar el cliente Mostrador")
            return

        if messagebox.askyesno("Confirmar", f"¿Eliminar el cliente '{client.get('nombre', '')}'?"):
            if self.data_manager.delete_client(index):
                self._after_saved()

    def get_selected_client_name(self):
        selection = self.tree.selection()
        if not selection:
            return ""
        item = self.tree.item(selection[0])
        values = item.get("values", [])
        return values[0] if values else ""

    def get_selected_client_with_index(self):
        selection = self.tree.selection()
        if not selection:
            return -1, None
        item = self.tree.item(selection[0])
        values = item.get("values", [])
        nit = values[1] if len(values) > 1 else ""
        name = values[0] if values else ""
        clients = self.data_manager.load_clients()
        index = next((i for i, c in enumerate(clients) if (nit and c.get("nit", "") == nit) or (not nit and c.get("nombre", "") == name)), -1)
        if 0 <= index < len(clients):
            return index, clients[index]
        return -1, None

    def _after_saved(self):
        self.load_clients()
        if self.refresh_callback:
            self.refresh_callback()

    def use_in_ticket(self):
        name = self.get_selected_client_name()
        if not name:
            messagebox.showwarning("Advertencia", "Seleccione un cliente")
            return
        if self.use_in_ticket_callback:
            self.use_in_ticket_callback(name)

    def export_clients(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Exportar clientes",
        )
        if not path:
            return
        try:
            clients = self.data_manager.load_clients()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(clients, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", "Clientes exportados correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

    def import_clients(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json")],
            title="Importar clientes",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                incoming = json.load(f)
            if not isinstance(incoming, list):
                raise ValueError("Formato inválido (se esperaba una lista)")

            clients = self.data_manager.load_clients()
            existing_nits = {str(c.get("nit", "")).strip() for c in clients if str(c.get("nit", "")).strip()}
            existing_names = {str(c.get("nombre", "")).strip().lower() for c in clients}
            added = 0
            for c in incoming:
                if not isinstance(c, dict):
                    continue
                nit = str(c.get("nit", "")).strip()
                name = str(c.get("nombre", "")).strip()
                if nit and nit in existing_nits:
                    continue
                if not nit and name.lower() in existing_names:
                    continue
                clients.append(c)
                if nit:
                    existing_nits.add(nit)
                existing_names.add(name.lower())
                added += 1

            self.data_manager.save_clients(clients)
            self.load_clients()
            if self.refresh_callback:
                self.refresh_callback()
            messagebox.showinfo("Importar", f"Clientes importados: {added}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar:\n{e}")


class ClientFormModal:
    def __init__(self, parent, data_manager, client=None, index=-1, on_saved=None):
        self.parent = parent
        self.data_manager = data_manager
        self.client = client or {}
        self.index = index
        self.on_saved = on_saved

        self._all_departamentos = self.data_manager.get_departamentos()
        self._all_municipios = self.data_manager.get_municipios(self.client.get("departamento", ""))

        self.win = tk.Toplevel(parent)
        self.win.title("Nuevo Cliente" if index == -1 else "Editar Cliente")
        self.win.resizable(False, False)
        try:
            self.win.transient(parent.winfo_toplevel())
        except Exception:
            pass
        self.win.grab_set()
        self.win.bind("<Escape>", lambda e: self.win.destroy())

        frame = ttk.Frame(self.win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        self.name_var = tk.StringVar(value=self.client.get("nombre", ""))
        self.nit_var = tk.StringVar(value=self.client.get("nit", ""))
        self.phone_var = tk.StringVar(value=self.client.get("telefono", ""))
        self.email_var = tk.StringVar(value=self.client.get("correo", ""))
        self.dep_var = tk.StringVar(value=self.client.get("departamento", ""))
        self.mun_var = tk.StringVar(value=self.client.get("municipio", ""))

        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)
        name_entry = ttk.Entry(frame, textvariable=self.name_var, width=45)
        name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=4)

        ttk.Label(frame, text="NIT/CC:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Entry(frame, textvariable=self.nit_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=4)

        ttk.Label(frame, text="Teléfono:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Entry(frame, textvariable=self.phone_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=4)

        ttk.Label(frame, text="Correo:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Entry(frame, textvariable=self.email_var).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=4)

        ttk.Label(frame, text="Departamento:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=4)
        self.dep_combo = ttk.Combobox(frame, textvariable=self.dep_var, values=self._all_departamentos)
        self.dep_combo.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=4)
        self.dep_combo.bind("<KeyRelease>", self._on_dep_type)
        self.dep_combo.bind("<<ComboboxSelected>>", self._on_dep_selected)

        ttk.Label(frame, text="Municipio:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=4)
        self.mun_combo = ttk.Combobox(frame, textvariable=self.mun_var, values=self._all_municipios)
        self.mun_combo.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=4)
        self.mun_combo.bind("<KeyRelease>", self._on_mun_type)

        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, columnspan=2, sticky=tk.E, padx=5, pady=(10, 0))
        save_btn = ttk.Button(buttons, text="Guardar", command=self.save)
        save_btn.pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons, text="Cancelar", command=self.win.destroy).pack(side=tk.RIGHT, padx=5)

        frame.columnconfigure(1, weight=1)
        name_entry.focus_set()
        self.win.bind("<Return>", lambda e: self.save())

    def _post_combobox(self, combo: ttk.Combobox, values):
        if not values:
            try:
                combo.tk.call("ttk::combobox::Unpost", combo)
            except Exception:
                pass
            return
        try:
            combo.tk.call("ttk::combobox::Post", combo)
        except Exception:
            pass

    def _on_dep_selected(self, event=None):
        dep = self.dep_var.get().strip()
        self._all_municipios = self.data_manager.get_municipios(dep)
        self.mun_combo["values"] = self._all_municipios
        self.mun_var.set("")

    def _on_dep_type(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "Shift_L", "Shift_R"):
            return
        q = self.dep_var.get().strip().lower()
        values = self._all_departamentos if not q else [d for d in self._all_departamentos if q in d.lower()]
        self.dep_combo["values"] = values
        self._post_combobox(self.dep_combo, values)

    def _on_mun_type(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "Shift_L", "Shift_R"):
            return
        q = self.mun_var.get().strip().lower()
        values = self._all_municipios if not q else [m for m in self._all_municipios if q in m.lower()]
        self.mun_combo["values"] = values
        self._post_combobox(self.mun_combo, values)

    def save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Advertencia", "El nombre es obligatorio", parent=self.win)
            return

        email = self.email_var.get().strip()
        if email and not re.match(r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", email):
            messagebox.showwarning("Advertencia", "Correo inválido", parent=self.win)
            return

        nit = self.nit_var.get().strip()
        phone = self.phone_var.get().strip()
        departamento = self.dep_var.get().strip()
        municipio = self.mun_var.get().strip()

        clients = self.data_manager.load_clients()
        for idx, c in enumerate(clients):
            if idx == self.index:
                continue
            if nit and str(c.get("nit", "")).strip() == nit:
                messagebox.showwarning("Advertencia", "Ya existe un cliente con ese NIT/CC", parent=self.win)
                return
            if not nit and str(c.get("nombre", "")).strip().lower() == name.lower():
                messagebox.showwarning("Advertencia", "Ya existe un cliente con ese nombre", parent=self.win)
                return

        client_data = {
            "nombre": name,
            "nit": nit,
            "telefono": phone,
            "correo": email,
            "departamento": departamento,
            "municipio": municipio,
        }

        if self.index == -1:
            self.data_manager.add_client(client_data)
        else:
            if not self.data_manager.update_client(self.index, client_data):
                messagebox.showerror("Error", "No se pudo actualizar el cliente", parent=self.win)
                return

        self.data_manager.remember_location(departamento, municipio)

        if callable(self.on_saved):
            try:
                self.on_saved()
            except Exception:
                pass
        self.win.destroy()
