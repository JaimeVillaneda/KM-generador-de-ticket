import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from templates.ticket_template import generate_ticket_pdf, format_number

class TicketModule:
    def __init__(self, parent_frame, data_manager):
        self.parent = parent_frame
        self.data_manager = data_manager
        self._draft_after_id = None
        self._company_all_values = []
        self._client_all_values = []
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de generación de tickets"""
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Variables
        self.empresa_var = tk.StringVar()
        self.ancho_var = tk.StringVar(value="80")
        self.pagado_var = tk.StringVar()
        self.numero_var = tk.StringVar()
        self.fecha_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        self.hora_var = tk.StringVar(value=datetime.now().strftime("%H:%M"))
        self.cajero_var = tk.StringVar(value="ADMIN")
        self.usuario_var = tk.StringVar(value="USUARIO")
        self.cliente_frame = None
        self.productos = []
        
        # Estilos para botones
        self.style = ttk.Style()
        self.style.configure("Ready.TButton", background="green", foreground="white")
        self.style.configure("NotReady.TButton", background="gray", foreground="black")
        
        self.generate_ticket_number()

        # Sección de empresa
        company_frame = ttk.LabelFrame(self.main_frame, text="Información de Empresa")
        company_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(company_frame, text="Empresa:").grid(row=0, column=0, sticky=tk.W)
        self.company_combo = ttk.Combobox(company_frame, textvariable=self.empresa_var)
        self.company_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        self.company_combo.bind("<<ComboboxSelected>>", lambda e: (self.update_totals(), self.check_ready()))
        self.company_combo.bind("<KeyRelease>", self._on_company_type)
        ttk.Label(company_frame, text="Buscar:").grid(row=0, column=2, sticky=tk.E, padx=5)
        self.company_search_var = tk.StringVar()
        company_search = ttk.Entry(company_frame, textvariable=self.company_search_var, width=18)
        company_search.grid(row=0, column=3, sticky=tk.EW, padx=5, pady=2)
        company_search.bind("<KeyRelease>", lambda e: self._filter_company_values(self.company_search_var.get()))
        
        # Sección de configuración
        config_frame = ttk.Frame(company_frame)
        config_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW)

        ttk.Label(config_frame, text="Fecha:").pack(side=tk.LEFT)
        ttk.Entry(config_frame, textvariable=self.fecha_var, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Label(config_frame, text="Hora:").pack(side=tk.LEFT)
        ttk.Entry(config_frame, textvariable=self.hora_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(config_frame, text="Ancho:").pack(side=tk.LEFT)
        ttk.Combobox(config_frame, textvariable=self.ancho_var, values=["80", "56"], width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(config_frame, text="Cajero:").pack(side=tk.LEFT)
        ttk.Entry(config_frame, textvariable=self.cajero_var, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Label(config_frame, text="Usuario:").pack(side=tk.LEFT)
        ttk.Entry(config_frame, textvariable=self.usuario_var, width=10).pack(side=tk.LEFT, padx=2)

        company_frame.columnconfigure(1, weight=1)

        # Sección de cliente
        client_frame = ttk.LabelFrame(self.main_frame, text="Cliente")
        client_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(client_frame, text="Cliente:").grid(row=0, column=0, sticky=tk.W)
        self.client_var = tk.StringVar()
        self.client_combo = ttk.Combobox(client_frame, textvariable=self.client_var)
        self.client_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        self.client_combo.bind("<<ComboboxSelected>>", lambda e: self.check_ready())
        self.client_combo.bind("<KeyRelease>", self._on_client_type)
        
        ttk.Button(client_frame, text="Nuevo Cliente", command=self.new_client).grid(row=0, column=2, padx=5)
        ttk.Label(client_frame, text="Buscar:").grid(row=0, column=3, sticky=tk.E, padx=5)
        self.client_search_var = tk.StringVar()
        client_search = ttk.Entry(client_frame, textvariable=self.client_search_var, width=18)
        client_search.grid(row=0, column=4, sticky=tk.EW, padx=5, pady=2)
        client_search.bind("<KeyRelease>", lambda e: self._filter_client_values(self.client_search_var.get()))

        client_frame.columnconfigure(1, weight=1)
        client_frame.columnconfigure(4, weight=1)

        # Sección de productos
        products_frame = ttk.LabelFrame(self.main_frame, text="Productos/Servicios")
        products_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Cabeceras de productos
        headers_frame = ttk.Frame(products_frame)
        headers_frame.pack(fill=tk.X)
        
        ttk.Label(headers_frame, text="Descripción").pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Label(headers_frame, text="Cant", width=5).pack(side=tk.LEFT)
        ttk.Label(headers_frame, text="Valor unitario", width=12).pack(side=tk.LEFT)
        ttk.Label(headers_frame, text="Total", width=10).pack(side=tk.LEFT)
        ttk.Label(headers_frame, width=3).pack(side=tk.LEFT)

        # Área de productos con scroll
        self.canvas = tk.Canvas(products_frame)
        self.scrollbar = ttk.Scrollbar(products_frame, orient="vertical", command=self.canvas.yview)
        self.products_inner_frame = ttk.Frame(self.canvas)

        self.products_inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.products_inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Botón para agregar productos
        ttk.Button(products_frame, text="➕ Agregar Producto", command=self.add_product).pack(pady=5)

        # Totales
        totals_frame = ttk.Frame(products_frame)
        totals_frame.pack(fill=tk.X, pady=5)

        self.subtotal_sin_iva_var = tk.StringVar(value="$0")
        self.iva_incluido_var = tk.StringVar(value="$0")
        self.total_var = tk.StringVar(value="$0")

        ttk.Label(totals_frame, text="Subtotal (sin IVA):", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(totals_frame, textvariable=self.subtotal_sin_iva_var, font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky=tk.E)
        ttk.Label(totals_frame, text="IVA incluido:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(totals_frame, textvariable=self.iva_incluido_var, font=('Arial', 10, 'bold')).grid(row=1, column=1, sticky=tk.E)
        ttk.Label(totals_frame, text="Total:", font=('Arial', 12, 'bold')).grid(row=2, column=0, sticky=tk.W)
        ttk.Label(totals_frame, textvariable=self.total_var, font=('Arial', 12, 'bold')).grid(row=2, column=1, sticky=tk.E)
        totals_frame.columnconfigure(0, weight=1)

        # Sección de pago
        payment_frame = ttk.LabelFrame(self.main_frame, text="Información de Pago")
        payment_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(payment_frame, text="FACTURA DE VENTA Nº:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(payment_frame, textvariable=self.numero_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(payment_frame, text="Pagado con:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(payment_frame, textvariable=self.pagado_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        self.cambio_var = tk.StringVar(value="$0")
        ttk.Label(payment_frame, text="Cambio:", font=('Arial', 10, 'bold')).grid(row=1, column=2, sticky=tk.E, padx=5)
        ttk.Label(payment_frame, textvariable=self.cambio_var, font=('Arial', 10, 'bold')).grid(row=1, column=3, sticky=tk.W, padx=5)

        payment_frame.columnconfigure(3, weight=1)

        # Botones de acción
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Vista Previa", command=self.show_preview).pack(side=tk.LEFT, padx=5)
        self.generate_button = ttk.Button(btn_frame, text="Generar Ticket", command=self.generate_ticket)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpiar", command=self.clear_form).pack(side=tk.LEFT, padx=5)

        # Cargar empresas y clientes
        self.load_companies()
        self.load_clients()
        self.add_product()

        self._setup_draft_autosave()
        self._load_draft_if_any()
        self.update_totals()

    def _setup_draft_autosave(self):
        vars_to_watch = [
            self.empresa_var,
            self.client_var,
            self.ancho_var,
            self.pagado_var,
            self.fecha_var,
            self.hora_var,
            self.cajero_var,
            self.usuario_var,
        ]
        for v in vars_to_watch:
            try:
                if v is self.pagado_var or v is self.empresa_var:
                    v.trace_add("write", lambda *args: (self.update_totals(), self.schedule_draft_save()))
                else:
                    v.trace_add("write", lambda *args: self.schedule_draft_save())
            except Exception:
                pass

    def schedule_draft_save(self):
        if self._draft_after_id is not None:
            try:
                self.parent.after_cancel(self._draft_after_id)
            except Exception:
                pass
        self._draft_after_id = self.parent.after(600, self._save_draft_now)

    def _save_draft_now(self):
        self._draft_after_id = None
        try:
            draft = {
                "empresa_nombre": self.empresa_var.get(),
                "cliente_nombre": self.client_var.get(),
                "fecha": self.fecha_var.get(),
                "hora": self.hora_var.get(),
                "ancho": self.ancho_var.get(),
                "cajero": self.cajero_var.get(),
                "usuario": self.usuario_var.get(),
                "pagado": self.pagado_var.get(),
                "productos": [
                    {
                        "nombre": p["name"].get(),
                        "cantidad": p["quantity"].get(),
                        "precio": p["price"].get(),
                    }
                    for p in self.productos
                    if p["name"].get().strip() or p["price"].get().strip() or p["quantity"].get().strip()
                ],
            }
            self.data_manager.save_draft_ticket(draft)
        except Exception:
            pass

    def _load_draft_if_any(self):
        try:
            draft = self.data_manager.load_draft_ticket()
        except Exception:
            return
        if not isinstance(draft, dict) or not draft:
            return

        # No restauramos el número para evitar duplicados.
        if draft.get("fecha"):
            self.fecha_var.set(draft["fecha"])
        if draft.get("hora"):
            self.hora_var.set(draft["hora"])
        if draft.get("ancho"):
            self.ancho_var.set(str(draft["ancho"]))
        if draft.get("cajero"):
            self.cajero_var.set(draft["cajero"])
        if draft.get("usuario"):
            self.usuario_var.set(draft["usuario"])
        if draft.get("pagado") is not None:
            self.pagado_var.set(str(draft.get("pagado", "")))

        if draft.get("empresa_nombre"):
            self.empresa_var.set(draft["empresa_nombre"])
        if draft.get("cliente_nombre"):
            self.client_var.set(draft["cliente_nombre"])

        products = draft.get("productos") or []
        if isinstance(products, list) and products:
            # Asegurar filas suficientes
            while len(self.productos) < len(products):
                self.add_product()
            for i, p in enumerate(products):
                if i >= len(self.productos):
                    break
                self.productos[i]["name"].set(str(p.get("nombre", "")))
                self.productos[i]["quantity"].set(str(p.get("cantidad", "1")))
                self.productos[i]["price"].set(str(p.get("precio", "")))

        self.check_ready()

    def load_companies(self):
        """Carga las empresas en el combobox"""
        selected = self.empresa_var.get()
        companies = self.data_manager.load_data()
        values = [c.get('nombre', '') for c in companies if c.get('nombre')]
        self._company_all_values = values[:]
        self.company_combo['values'] = values

        default_name = self.data_manager.get_setting("default_company_nombre")
        default_nit = self.data_manager.get_setting("default_company_nit")
        if not selected:
            if default_nit:
                match = next((c for c in companies if c.get("nit") == default_nit), None)
                if match and match.get("nombre") in values:
                    self.company_combo.set(match["nombre"])
            elif default_name and default_name in values:
                self.company_combo.set(default_name)

        if self.empresa_var.get() in values:
            self.company_combo.set(self.empresa_var.get())
        elif values:
            self.company_combo.current(0)

        self.check_ready()

    def load_clients(self):
        """Carga los clientes en el combobox"""
        selected = self.client_var.get()
        clients = self.data_manager.load_clients()
        values = [c['nombre'] for c in clients]
        self._client_all_values = values[:]
        self.client_combo['values'] = values
        if selected in values:
            self.client_combo.set(selected)
        elif values:
            # Seleccionar "Mostrador" por defecto
            mostrador_index = next((i for i, c in enumerate(clients) if c['nombre'] == 'Mostrador'), 0)
            self.client_combo.current(mostrador_index)
        self.check_ready()

    def _filter_company_values(self, query: str):
        query = (query or "").strip().lower()
        if not query:
            self.company_combo["values"] = self._company_all_values
            return
        values = [v for v in self._company_all_values if query in v.lower()]
        self.company_combo["values"] = values
        self._post_combobox(self.company_combo, values)

    def _filter_client_values(self, query: str):
        query = (query or "").strip().lower()
        if not query:
            self.client_combo["values"] = self._client_all_values
            return
        values = [v for v in self._client_all_values if query in v.lower()]
        self.client_combo["values"] = values
        self._post_combobox(self.client_combo, values)

    def _post_combobox(self, combo: ttk.Combobox, values):
        """Abre la lista de opciones para selección mientras se escribe."""
        if not values:
            try:
                combo.tk.call("ttk::combobox::Unpost", combo)
            except Exception:
                pass
            return
        try:
            combo.tk.call("ttk::combobox::Post", combo)
        except Exception:
            try:
                combo.event_generate("<Down>")
            except Exception:
                pass

    def _on_company_type(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "Shift_L", "Shift_R"):
            return
        typed = self.empresa_var.get()
        if typed:
            self._filter_company_values(typed)
        else:
            self._filter_company_values(self.company_search_var.get() if hasattr(self, "company_search_var") else "")
        self.update_totals()
        self.check_ready()
        self.schedule_draft_save()

    def _on_client_type(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "Shift_L", "Shift_R"):
            return
        typed = self.client_var.get()
        if typed:
            self._filter_client_values(typed)
        else:
            self._filter_client_values(self.client_search_var.get() if hasattr(self, "client_search_var") else "")
        self.check_ready()
        self.schedule_draft_save()

    def new_client(self):
        """Abre una ventana para crear un nuevo cliente"""
        from modules.client_module import ClientFormModal  # Importar aquí para evitar circular import

        ClientFormModal(
            parent=self.parent,
            data_manager=self.data_manager,
            client=None,
            index=-1,
            on_saved=self.load_clients,
        )

    def refresh_data(self):
        """Actualiza empresas y clientes"""
        self.load_companies()
        self.load_clients()

    def add_product(self):
        """Agrega una nueva fila de producto"""
        # Variables
        name_var = tk.StringVar()
        qty_var = tk.StringVar(value="1")
        price_var = tk.StringVar()
        total_var = tk.StringVar()

        # Widgets
        frame = ttk.Frame(self.products_inner_frame)
        frame.pack(fill=tk.X, pady=2)

        name_entry = ttk.Entry(frame, textvariable=name_var)
        name_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        qty_entry = ttk.Entry(frame, textvariable=qty_var, width=8)
        qty_entry.pack(side=tk.LEFT, padx=2)
        price_entry = ttk.Entry(frame, textvariable=price_var, width=12)
        price_entry.pack(side=tk.LEFT, padx=2)
        ttk.Label(frame, textvariable=total_var, width=10).pack(side=tk.LEFT, padx=2)
        
        btn = ttk.Button(frame, text="✖", width=3, command=lambda f=frame: self.remove_product_by_frame(f))
        btn.pack(side=tk.LEFT)

        def on_enter(_event=None):
            # Si estamos en la última fila, agrega una nueva
            if frame == self.productos[-1]["frame"]:
                self.add_product()
            # Enfocar el nombre de la última fila
            try:
                self.productos[-1]["name_entry"].focus_set()
            except Exception:
                pass
            return "break"

        for w in (name_entry, qty_entry, price_entry):
            w.bind("<Return>", on_enter)
            w.bind("<Control-BackSpace>", lambda e, f=frame: (self.remove_product_by_frame(f), "break")[1])

        # Configurar cálculo automático
        def calculate_total(*args):
            try:
                qty = float(qty_var.get()) if qty_var.get() else 0
                price = float(price_var.get()) if price_var.get() else 0
                total_var.set(f"{qty * price:.2f}")
                self.update_totals()
            except ValueError:
                total_var.set("0.00")
                self.update_totals()
            self.schedule_draft_save()

        qty_var.trace_add("write", calculate_total)
        price_var.trace_add("write", calculate_total)
        name_var.trace_add("write", lambda *args: self.schedule_draft_save())

        self.productos.append({
            "frame": frame,
            "name": name_var,
            "quantity": qty_var,
            "price": price_var,
            "total": total_var
            ,
            "name_entry": name_entry,
            "qty_entry": qty_entry,
            "price_entry": price_entry,
            "remove_button": btn,
        })
        self.update_totals()

    def remove_product_by_frame(self, frame):
        for i, p in enumerate(self.productos):
            if p.get("frame") == frame:
                self.remove_product(i)
                return

    def remove_product(self, index):
        """Elimina un producto de la lista"""
        if 0 <= index < len(self.productos):
            self.productos[index]["frame"].destroy()
            del self.productos[index]
            
            # Reindexar los productos restantes
            for prod in self.productos:
                prod["remove_button"].config(command=lambda f=prod["frame"]: self.remove_product_by_frame(f))
            self.update_totals()
            self.schedule_draft_save()

    def update_totals(self):
        """Actualiza totales en tiempo real (asume IVA incluido en precios)."""
        total = 0.0
        for prod in self.productos:
            try:
                total += float(prod["total"].get())
            except ValueError:
                pass

        iva_percent = 0.0
        company_name = self.empresa_var.get()
        companies = self.data_manager.load_data()
        company = next((c for c in companies if c.get('nombre') == company_name), None)
        if company:
            try:
                iva_percent = float(company.get("iva", 0) or 0)
            except ValueError:
                iva_percent = 0.0

        iva_incl = total * (iva_percent / (100.0 + iva_percent)) if iva_percent > 0 else 0.0
        subtotal_sin_iva = total - iva_incl

        self.subtotal_sin_iva_var.set(f"${format_number(subtotal_sin_iva)}")
        self.iva_incluido_var.set(f"${format_number(iva_incl)}")
        self.total_var.set(f"${format_number(total)}")

        try:
            pagado = float(self.pagado_var.get()) if self.pagado_var.get() else 0.0
        except ValueError:
            pagado = 0.0
        cambio = pagado - total
        self.cambio_var.set(f"${format_number(cambio)}")

        self.check_ready()

    def check_ready(self):
        """Verifica si el formulario está listo para generar ticket"""
        # Verificar empresa
        company_name = self.empresa_var.get()
        companies = self.data_manager.load_data()
        company = next((c for c in companies if c['nombre'] == company_name), None)
        if not company:
            self.generate_button.config(text="Generar Ticket", state="disabled")
            return
        
        # Verificar cliente
        client_name = self.client_var.get()
        clients = self.data_manager.load_clients()
        client = next((c for c in clients if c['nombre'] == client_name), None)
        if not client:
            self.generate_button.config(text="Generar Ticket", state="disabled")
            return
        
        # Verificar productos
        products = []
        for prod in self.productos:
            name = prod["name"].get()
            if name:
                try:
                    qty = float(prod["quantity"].get())
                    price = float(prod["price"].get())
                    if qty > 0 and price > 0:
                        products.append(True)
                except ValueError:
                    pass
        if not products:
            self.generate_button.config(text="Generar Ticket", state="disabled")
            return
        
        # Listo
        self.generate_button.config(text="Generar Ticket ✅", state="normal")

    def generate_ticket_number(self):
        """Genera un número de ticket único"""
        now = datetime.now()
        self.numero_var.set(f"T-{now.strftime('%Y%m%d-%H%M%S')}")

    def get_ticket_data(self):
        """Obtiene los datos del formulario para el ticket"""
        company_name = self.empresa_var.get()
        companies = self.data_manager.load_data()
        company = next((c for c in companies if c['nombre'] == company_name), None)
        
        if not company:
            messagebox.showwarning("Entrada inválida", "Seleccione una empresa válida antes de generar el ticket.")
            return None

        client_name = self.client_var.get()
        clients = self.data_manager.load_clients()
        client = next((c for c in clients if c['nombre'] == client_name), None)
        
        if not client:
            messagebox.showwarning("Entrada inválida", "Seleccione un cliente válido antes de generar el ticket.")
            return None

        products = []
        for prod in self.productos:
            name = prod["name"].get()
            if name:
                try:
                    products.append({
                        "nombre": name,
                        "cantidad": float(prod["quantity"].get()),
                        "precio": float(prod["price"].get())
                    })
                except ValueError:
                    continue

        if not products:
            messagebox.showwarning("Advertencia", "Agregue al menos un producto")
            return None

        try:
            paid = float(self.pagado_var.get()) if self.pagado_var.get() else 0
        except ValueError:
            paid = 0

        ticket_data = {
            "empresa": company,
            "cliente": client,
            "productos": products,
            "pagado": paid,
            "numero": self.numero_var.get(),
            "fecha": self.fecha_var.get(),
            "hora": self.hora_var.get(),
            "ancho": self.ancho_var.get(),
            "cajero": self.cajero_var.get(),
            "usuario": self.usuario_var.get(),
            "estado": "ACTIVA"
        }

        return ticket_data

    def show_preview(self):
        """Muestra una vista previa del ticket"""
        data = self.get_ticket_data()
        if not data:
            return

        preview = self.format_ticket_text(data)
        
        win = tk.Toplevel(self.parent)
        win.title("Vista Previa del Ticket")
        
        text = scrolledtext.ScrolledText(win, width=60, height=30, font=("Courier New", 10))
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, preview)
        text.config(state=tk.DISABLED)

    def format_ticket_text(self, data):
        """Formatea los datos del ticket como texto"""
        company = data["empresa"]
        products = data["productos"]
        
        # Calcular totales
        subtotal = sum(p["cantidad"] * p["precio"] for p in products)
        iva_percent = float(company.get('iva', 19))
        iva_value = subtotal * (iva_percent / (100 + iva_percent))  # IVA incluido
        subtotal_sin_iva = subtotal - iva_value
        total = subtotal
        cambio = data["pagado"] - total if data["pagado"] else 0

        # Formatear ticket
        lines = [
            "=" * 50,
            company["nombre"].center(50),
            company["direccion"].center(50),
            f"Tel: {company['telefono']} | IVA: {iva_percent}%",
            "=" * 50,
            f"FACTURA DE VENTA Nº: {data['numero']}",
            f"Fecha: {data['fecha']} {data['hora']}",
            f"Cajero: {data.get('cajero', 'ADMIN')}",
            f"Usuario: {data.get('usuario', 'USUARIO')}",
            f"Cliente: {data['cliente'].get('nombre', '')}",
            (f"Correo: {data['cliente'].get('correo', '')}" if data.get('cliente', {}).get('correo') else ""),
            "-" * 50,
            f"{'PRODUCTO'.ljust(30)} {'CANT'.rjust(5)} {'TOTAL'.rjust(10)}",
            "-" * 50
        ]

        for p in products:
            name = p["nombre"][:28] + "..." if len(p["nombre"]) > 28 else p["nombre"]
            lines.append(f"{name.ljust(30)} {str(p['cantidad']).rjust(5)} ${format_number(p['cantidad'] * p['precio'])}")

        lines.extend([
            "-" * 50,
            f"{'Subtotal:'.rjust(38)} ${format_number(subtotal)}",
            f"{'Subtotal (sin IVA):'.rjust(38)} ${format_number(subtotal_sin_iva)}",
            f"{'IVA incluido:'.rjust(38)} ${format_number(iva_value)}",
            f"{'TOTAL:'.rjust(38)} ${format_number(total)}",
            f"{'PAGADO:'.rjust(38)} ${format_number(data['pagado'])}",
            f"{'CAMBIO:'.rjust(38)} ${format_number(cambio)}",
            "=" * 50,
            "¡GRACIAS POR SU COMPRA!".center(50),
            "=" * 50,
            "Sistema de Tickets v1.0".center(50)
        ])

        return "\n".join(lines)

    

    def generate_ticket(self):
        """Genera el ticket PDF"""
        data = self.get_ticket_data()
        if not data:
            return

        try:
            file_path = generate_ticket_pdf(data)
            
            # Guardar el ticket en el historial
            self.data_manager.save_ticket(data)
            self.data_manager.clear_draft_ticket()
            
            messagebox.showinfo("Ticket generado", f"El ticket se generó correctamente y se guardó en el historial.\n\nRuta:\n{file_path}")
            
            # Abrir el ticket generado
            import os
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            else:  # macOS o Linux
                os.system(f'open "{file_path}"')
                
        except AttributeError as e:
            messagebox.showerror("Error interno", "No se pudo guardar el ticket en el historial. Por favor reinicie la aplicación.")
        except Exception as e:
            messagebox.showerror("Error al generar ticket", f"Ocurrió un error al generar el ticket:\n{str(e)}")

    def clear_form(self):
        """Limpia el formulario"""
        # Eliminar todos los productos excepto el primero
        while len(self.productos) > 1:
            self.remove_product(len(self.productos)-1)
        
        # Limpiar campos del primer producto
        first = self.productos[0]
        first["name"].set("")
        first["quantity"].set("1")
        first["price"].set("")
        
        # Limpiar otros campos
        self.pagado_var.set("")
        self.load_clients()  # Resetear cliente a Mostrador
        self.generate_ticket_number()
        self.update_totals()
        self.data_manager.clear_draft_ticket()
