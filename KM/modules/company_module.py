import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json

class CompanyModule:
    def __init__(self, parent_frame, data_manager, refresh_callback=None, use_in_ticket_callback=None):
        self.parent = parent_frame
        self.data_manager = data_manager
        self.refresh_callback = refresh_callback
        self.use_in_ticket_callback = use_in_ticket_callback
        self._sort_reverse = {}
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de gestión de empresas"""
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Lista de empresas
        self.list_frame = ttk.LabelFrame(self.main_frame, text="Empresas Registradas")
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        top_bar = ttk.Frame(self.list_frame)
        top_bar.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top_bar, text="Buscar:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top_bar, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind("<KeyRelease>", lambda e: self.load_companies())

        self.tree = ttk.Treeview(self.list_frame, columns=('name', 'phone', 'nit', 'location'), show='headings')
        self.tree.heading('name', text='Nombre', command=lambda: self.sort_tree('name'))
        self.tree.heading('phone', text='Teléfono', command=lambda: self.sort_tree('phone'))
        self.tree.heading('nit', text='NIT', command=lambda: self.sort_tree('nit'))
        self.tree.heading('location', text='Ubicación', command=lambda: self.sort_tree('location'))
        self.tree.pack(fill=tk.BOTH, expand=True)
        self._enable_tree_hover(self.tree)

        # Botones de acción
        btn_frame = ttk.Frame(self.list_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Nueva", command=self.new_company).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editar", command=self.edit_company).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_company).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Usar en Ticket", command=self.use_in_ticket).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Predeterminada", command=self.set_default_company).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Exportar", command=self.export_companies).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Importar", command=self.import_companies).pack(side=tk.RIGHT, padx=5)
        self.load_companies()

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

    def load_companies(self):
        """Carga las empresas en el Treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        companies = self.data_manager.load_data()
        query = (self.search_var.get() if hasattr(self, "search_var") else "").strip().lower()
        default_nit = self.data_manager.get_setting("default_company_nit")
        default_name = self.data_manager.get_setting("default_company_nombre")

        self.tree.tag_configure("default", background="#e8f5e9")

        for company in companies:
            if query:
                haystack = " ".join([
                    str(company.get("nombre", "")),
                    str(company.get("nit", "")),
                    str(company.get("telefono", "")),
                    str(company.get("departamento", "")),
                    str(company.get("municipio", "")),
                ]).lower()
                if query not in haystack:
                    continue
            ubicacion = f"{company.get('departamento', '')}/{company.get('municipio', '')}"
            tags = ()
            if default_nit and company.get("nit") == default_nit:
                tags = ("default",)
            elif default_name and company.get("nombre") == default_name:
                tags = ("default",)

            self.tree.insert('', tk.END, values=(
                company.get('nombre', ''),
                company.get('telefono', ''),
                company.get('nit', ''),
                ubicacion
            ), tags=tags)

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

    def new_company(self):
        CompanyFormModal(
            parent=self.parent,
            data_manager=self.data_manager,
            company=None,
            index=-1,
            on_saved=self._after_saved,
        )

    def edit_company(self):
        """Carga la empresa seleccionada para edición"""
        index, company = self.get_selected_company_with_index()
        if company is None:
            messagebox.showwarning("Advertencia", "Seleccione una empresa para editar")
            return

        CompanyFormModal(
            parent=self.parent,
            data_manager=self.data_manager,
            company=company,
            index=index,
            on_saved=self._after_saved,
        )

    def delete_company(self):
        """Elimina la empresa seleccionada"""
        index, company = self.get_selected_company_with_index()
        if company is None:
            messagebox.showwarning("Advertencia", "Seleccione una empresa para eliminar")
            return

        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar esta empresa?"):
            companies = self.data_manager.load_data()
            
            if 0 <= index < len(companies):
                del companies[index]
                self.data_manager.save_data(companies)
                self.load_companies()
                self._after_saved()

    def _after_saved(self):
        self.load_companies()
        if self.refresh_callback:
            self.refresh_callback()

    def get_selected_company_with_index(self):
        selected = self.tree.selection()
        if not selected:
            return -1, None
        item = self.tree.item(selected[0])
        nit = str(item.get("values", ["", "", "", ""])[2]).strip()
        companies = self.data_manager.load_data()
        index = next((i for i, c in enumerate(companies) if str(c.get("nit", "")).strip() == nit), -1)
        if 0 <= index < len(companies):
            return index, companies[index]
        return -1, None

    def use_in_ticket(self):
        _, company = self.get_selected_company_with_index()
        if company is None:
            messagebox.showwarning("Advertencia", "Seleccione una empresa")
            return
        if self.use_in_ticket_callback:
            self.use_in_ticket_callback(company.get("nombre", ""))

    def set_default_company(self):
        _, company = self.get_selected_company_with_index()
        if company is None:
            messagebox.showwarning("Advertencia", "Seleccione una empresa")
            return
        self.data_manager.set_setting("default_company_nit", company.get("nit", ""))
        self.data_manager.set_setting("default_company_nombre", company.get("nombre", ""))
        self.load_companies()
        if self.refresh_callback:
            self.refresh_callback()

    def export_companies(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Exportar empresas",
        )
        if not path:
            return
        try:
            companies = self.data_manager.load_data()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(companies, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", "Empresas exportadas correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

    def import_companies(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json")],
            title="Importar empresas",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                incoming = json.load(f)
            if not isinstance(incoming, list):
                raise ValueError("Formato inválido (se esperaba una lista)")

            companies = self.data_manager.load_data()
            existing_nits = {str(c.get("nit", "")).strip() for c in companies}
            added = 0
            for c in incoming:
                if not isinstance(c, dict):
                    continue
                nit = str(c.get("nit", "")).strip()
                if nit and nit in existing_nits:
                    continue
                companies.append(c)
                if nit:
                    existing_nits.add(nit)
                added += 1

            self.data_manager.save_data(companies)
            self.load_companies()
            if self.refresh_callback:
                self.refresh_callback()
            messagebox.showinfo("Importar", f"Empresas importadas: {added}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar:\n{e}")


class CompanyFormModal:
    def __init__(self, parent, data_manager, company=None, index=-1, on_saved=None):
        self.parent = parent
        self.data_manager = data_manager
        self.company = company or {}
        self.index = index
        self.on_saved = on_saved

        self._all_departamentos = self.data_manager.get_departamentos()
        self._all_municipios = self.data_manager.get_municipios(self.company.get("departamento", ""))

        self.win = tk.Toplevel(parent)
        self.win.title("Nueva Empresa" if index == -1 else "Editar Empresa")
        self.win.resizable(False, False)
        try:
            self.win.transient(parent.winfo_toplevel())
        except Exception:
            pass
        self.win.grab_set()
        self.win.bind("<Escape>", lambda e: self.win.destroy())

        frame = ttk.Frame(self.win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        self.name_var = tk.StringVar(value=self.company.get("nombre", ""))
        self.address_var = tk.StringVar(value=self.company.get("direccion", ""))
        self.phone_var = tk.StringVar(value=self.company.get("telefono", ""))
        self.nit_var = tk.StringVar(value=self.company.get("nit", ""))
        self.departamento_var = tk.StringVar(value=self.company.get("departamento", ""))
        self.municipio_var = tk.StringVar(value=self.company.get("municipio", ""))
        self.iva_var = tk.StringVar(value=str(self.company.get("iva", "19")))

        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)
        name_entry = ttk.Entry(frame, textvariable=self.name_var, width=45)
        name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=4)

        ttk.Label(frame, text="Dirección:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Entry(frame, textvariable=self.address_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=4)

        ttk.Label(frame, text="Teléfono:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Entry(frame, textvariable=self.phone_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=4)

        ttk.Label(frame, text="NIT:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Entry(frame, textvariable=self.nit_var).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=4)

        ttk.Label(frame, text="Departamento:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=4)
        self.dep_combo = ttk.Combobox(frame, textvariable=self.departamento_var, values=self._all_departamentos)
        self.dep_combo.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=4)
        self.dep_combo.bind("<KeyRelease>", self._on_dep_type)
        self.dep_combo.bind("<<ComboboxSelected>>", self._on_dep_selected)

        ttk.Label(frame, text="Municipio:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=4)
        self.mun_combo = ttk.Combobox(frame, textvariable=self.municipio_var, values=self._all_municipios)
        self.mun_combo.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=4)
        self.mun_combo.bind("<KeyRelease>", self._on_mun_type)

        ttk.Label(frame, text="IVA (%):").grid(row=6, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Entry(frame, textvariable=self.iva_var, width=6).grid(row=6, column=1, sticky=tk.W, padx=5, pady=4)

        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, columnspan=2, sticky=tk.E, padx=5, pady=(10, 0))
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
        dep = self.departamento_var.get().strip()
        self._all_municipios = self.data_manager.get_municipios(dep)
        self.mun_combo["values"] = self._all_municipios
        self.municipio_var.set("")

    def _on_dep_type(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "Shift_L", "Shift_R"):
            return
        q = self.departamento_var.get().strip().lower()
        values = self._all_departamentos if not q else [d for d in self._all_departamentos if q in d.lower()]
        self.dep_combo["values"] = values
        self._post_combobox(self.dep_combo, values)

    def _on_mun_type(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "Shift_L", "Shift_R"):
            return
        q = self.municipio_var.get().strip().lower()
        values = self._all_municipios if not q else [m for m in self._all_municipios if q in m.lower()]
        self.mun_combo["values"] = values
        self._post_combobox(self.mun_combo, values)

    def save(self):
        name = self.name_var.get().strip()
        address = self.address_var.get().strip()
        phone = self.phone_var.get().strip()
        nit = self.nit_var.get().strip()
        departamento = self.departamento_var.get().strip()
        municipio = self.municipio_var.get().strip()
        iva = self.iva_var.get().strip()

        if not name:
            messagebox.showwarning("Advertencia", "El nombre es obligatorio", parent=self.win)
            return
        if not nit:
            messagebox.showwarning("Advertencia", "El NIT es obligatorio", parent=self.win)
            return

        try:
            iva_val = float(iva)
            if not (0 <= iva_val <= 100):
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Advertencia", "El IVA debe ser un número válido entre 0 y 100", parent=self.win)
            return

        companies = self.data_manager.load_data()
        for idx, c in enumerate(companies):
            if idx == self.index:
                continue
            if str(c.get("nit", "")).strip() == nit:
                messagebox.showwarning("Advertencia", "Ya existe una empresa con ese NIT", parent=self.win)
                return

        company_data = {
            "nombre": name,
            "direccion": address,
            "telefono": phone,
            "nit": nit,
            "departamento": departamento,
            "municipio": municipio,
            "iva": str(iva),
        }

        if self.index == -1:
            self.data_manager.add_company(company_data)
        else:
            if not self.data_manager.update_company(self.index, company_data):
                messagebox.showerror("Error", "No se pudo actualizar la empresa", parent=self.win)
                return

        self.data_manager.remember_location(departamento, municipio)

        if callable(self.on_saved):
            try:
                self.on_saved()
            except Exception:
                pass
        self.win.destroy()
