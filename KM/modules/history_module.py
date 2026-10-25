import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from templates.ticket_template import generate_ticket_pdf
from templates.ticket_template import format_number
import os
import json
from datetime import datetime

class HistoryModule:
    def __init__(self, parent_frame, data_manager):
        self.parent = parent_frame
        self.data_manager = data_manager
        self.audit_win = None
        self.audit_text = None
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del historial de facturas"""
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        filters = ttk.LabelFrame(self.main_frame, text="Filtros")
        filters.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filters, text="Buscar:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filters, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        search_entry.bind("<KeyRelease>", lambda e: self.load_tickets())

        ttk.Label(filters, text="Estado:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.estado_var = tk.StringVar(value="TODAS")
        estado_combo = ttk.Combobox(filters, textvariable=self.estado_var, values=["TODAS", "ACTIVA", "ANULADA"], width=10, state="readonly")
        estado_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        estado_combo.bind("<<ComboboxSelected>>", lambda e: self.load_tickets())

        ttk.Label(filters, text="Desde (dd/mm/aaaa):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.desde_var = tk.StringVar()
        ttk.Entry(filters, textvariable=self.desde_var, width=14).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(filters, text="Hasta (dd/mm/aaaa):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.hasta_var = tk.StringVar()
        ttk.Entry(filters, textvariable=self.hasta_var, width=14).grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Button(filters, text="Aplicar", command=self.load_tickets).grid(row=1, column=4, padx=5, pady=2)
        ttk.Button(filters, text="Limpiar", command=self.clear_filters).grid(row=0, column=4, padx=5, pady=2)

        filters.columnconfigure(1, weight=1)

        # Lista de tickets
        self.list_frame = ttk.LabelFrame(self.main_frame, text="Historial de Facturas")
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(self.list_frame, columns=('numero', 'fecha', 'empresa', 'cliente', 'total', 'estado'), show='headings', selectmode="extended")
        self.tree.heading('numero', text='Número')
        self.tree.heading('fecha', text='Fecha')
        self.tree.heading('empresa', text='Empresa')
        self.tree.heading('cliente', text='Cliente')
        self.tree.heading('total', text='Total')
        self.tree.heading('estado', text='Estado')
        self.tree.pack(fill=tk.BOTH, expand=True)
        self._enable_tree_hover(self.tree)
        self.tree.bind("<ButtonRelease-1>", self.show_audit_modal, add="+")

        # Botones de acción
        btn_frame = ttk.Frame(self.list_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Ver Factura", command=self.view_ticket).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reimprimir", command=self.reprint_ticket).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Anular", command=self.void_ticket).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Exportar", command=self.export_tickets).pack(side=tk.RIGHT, padx=5)

        self.load_tickets()

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

    def show_audit_modal(self, event=None):
        ticket = self.get_selected_ticket()
        if not ticket:
            return

        if self.audit_win is None or not self.audit_win.winfo_exists():
            self.audit_win = tk.Toplevel(self.parent)
            self.audit_win.title(f"Auditoría - {ticket.get('numero', '')}")
            self.audit_win.geometry("720x700")
            self.audit_win.bind("<Escape>", lambda e: self.audit_win.destroy())

            container = ttk.Frame(self.audit_win, padding=10)
            container.pack(fill=tk.BOTH, expand=True)

            self.audit_text = tk.Text(container, wrap=tk.WORD, font=("Consolas", 10))
            scrollbar = ttk.Scrollbar(container, command=self.audit_text.yview)
            self.audit_text.config(yscrollcommand=scrollbar.set)
            self.audit_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            btns = ttk.Frame(self.audit_win, padding=(10, 0, 10, 10))
            btns.pack(fill=tk.X)
            ttk.Button(btns, text="Copiar", command=self.copy_audit_to_clipboard).pack(side=tk.LEFT)
            ttk.Button(btns, text="Cerrar", command=self.audit_win.destroy).pack(side=tk.RIGHT)

            def _on_close():
                self.audit_win = None
                self.audit_text = None

            self.audit_win.protocol("WM_DELETE_WINDOW", lambda: (self.audit_win.destroy(), _on_close()))

        self.audit_win.title(f"Auditoría - {ticket.get('numero', '')}")
        self._render_audit(ticket)

    def copy_audit_to_clipboard(self):
        if not self.audit_win or not self.audit_text:
            return
        try:
            text = self.audit_text.get("1.0", tk.END)
            self.audit_win.clipboard_clear()
            self.audit_win.clipboard_append(text)
        except Exception:
            pass

    def _render_audit(self, ticket: dict):
        if not self.audit_text:
            return

        empresa = ticket.get("empresa", {}) or {}
        cliente = ticket.get("cliente", {}) or {}
        productos = ticket.get("productos", []) or []

        total = sum(float(p.get("cantidad", 0)) * float(p.get("precio", 0)) for p in productos)
        try:
            iva_percent = float(empresa.get("iva", 0) or 0)
        except ValueError:
            iva_percent = 0.0
        iva_incl = total * (iva_percent / (100.0 + iva_percent)) if iva_percent > 0 else 0.0
        subtotal_sin_iva = total - iva_incl

        try:
            pagado = float(ticket.get("pagado", 0) or 0)
        except ValueError:
            pagado = 0.0
        cambio = pagado - total

        lines = []
        lines.append("=== AUDITORÍA DE FACTURA ===")
        lines.append(f"FACTURA DE VENTA Nº: {ticket.get('numero', '')}")
        lines.append(f"Estado: {ticket.get('estado', 'ACTIVA')}")
        if ticket.get("creado_en"):
            lines.append(f"Creado en: {ticket.get('creado_en')}")
        if ticket.get("anulada_en"):
            lines.append(f"Anulada en: {ticket.get('anulada_en')}")
        if ticket.get("anulada_motivo"):
            lines.append(f"Motivo: {ticket.get('anulada_motivo')}")
        lines.append(f"Fecha/Hora: {ticket.get('fecha', '')} {ticket.get('hora', '')}")
        lines.append(f"Cajero: {ticket.get('cajero', '')} | Usuario: {ticket.get('usuario', '')}")
        lines.append("")

        lines.append("--- EMPRESA ---")
        lines.append(f"Nombre: {empresa.get('nombre', '')}")
        lines.append(f"NIT: {empresa.get('nit', '')}")
        lines.append(f"Tel: {empresa.get('telefono', '')}")
        lines.append(f"Dirección: {empresa.get('direccion', '')}")
        lines.append(f"Ubicación: {empresa.get('departamento', '')} - {empresa.get('municipio', '')}")
        lines.append(f"IVA: {empresa.get('iva', '')}%")
        lines.append("")

        lines.append("--- CLIENTE ---")
        lines.append(f"Nombre: {cliente.get('nombre', '')}")
        lines.append(f"NIT/CC: {cliente.get('nit', '')}")
        lines.append(f"Tel: {cliente.get('telefono', '')}")
        lines.append(f"Correo: {cliente.get('correo', '')}")
        lines.append(f"Ubicación: {cliente.get('departamento', '')} - {cliente.get('municipio', '')}")
        lines.append("")

        lines.append("--- PRODUCTOS ---")
        for p in productos:
            nombre = str(p.get("nombre", ""))
            cant = p.get("cantidad", 0)
            precio = p.get("precio", 0)
            try:
                row_total = float(cant) * float(precio)
            except Exception:
                row_total = 0.0
            lines.append(f"- {nombre} | Cant: {cant} | Unit: {format_number(precio)} | Total: {format_number(row_total)}")
        lines.append("")

        lines.append("--- TOTALES ---")
        lines.append(f"Subtotal: {format_number(total)}")
        lines.append(f"Subtotal (sin IVA): {format_number(subtotal_sin_iva)}")
        lines.append(f"IVA incluido: {format_number(iva_incl)}")
        lines.append(f"Pagado: {format_number(pagado)}")
        lines.append(f"Cambio: {format_number(cambio)}")

        self.audit_text.config(state=tk.NORMAL)
        self.audit_text.delete("1.0", tk.END)
        self.audit_text.insert(tk.END, "\n".join(lines))
        self.audit_text.config(state=tk.DISABLED)

    def clear_filters(self):
        self.search_var.set("")
        self.estado_var.set("TODAS")
        self.desde_var.set("")
        self.hasta_var.set("")
        self.load_tickets()

    def _parse_date(self, s: str):
        s = (s or "").strip()
        if not s:
            return None
        try:
            return datetime.strptime(s, "%d/%m/%Y").date()
        except ValueError:
            return None

    def load_tickets(self):
        """Carga los tickets en el treeview"""
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        tickets = self.data_manager.load_tickets()
        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        estado = self.estado_var.get().strip().upper() if hasattr(self, "estado_var") else "TODAS"
        desde = self._parse_date(self.desde_var.get()) if hasattr(self, "desde_var") else None
        hasta = self._parse_date(self.hasta_var.get()) if hasattr(self, "hasta_var") else None
        
        for ticket in tickets:
            if estado != "TODAS" and str(ticket.get("estado", "ACTIVA")).upper() != estado:
                continue

            if desde or hasta:
                d = self._parse_date(ticket.get("fecha", ""))
                if d is None:
                    continue
                if desde and d < desde:
                    continue
                if hasta and d > hasta:
                    continue

            if query:
                haystack = " ".join([
                    str(ticket.get("numero", "")),
                    str(ticket.get("empresa", {}).get("nombre", "")),
                    str(ticket.get("cliente", {}).get("nombre", "")),
                    str(ticket.get("cliente", {}).get("nit", "")),
                ]).lower()
                if query not in haystack:
                    continue

            total = sum(p["cantidad"] * p["precio"] for p in ticket.get("productos", []))
            self.tree.insert('', tk.END, values=(
                ticket["numero"],
                ticket["fecha"],
                ticket["empresa"]["nombre"],
                ticket.get("cliente", {}).get("nombre", ""),
                f"${format_number(total)}",
                ticket.get("estado", "ACTIVA")
            ))

    def get_selected_ticket(self):
        """Obtiene el ticket seleccionado"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un ticket")
            return None

        numero = self.tree.item(selection[0])['values'][0]
        tickets = self.data_manager.load_tickets()
        return next((t for t in tickets if t["numero"] == numero), None)

    def view_ticket(self):
        """Muestra la vista previa del ticket seleccionado"""
        ticket = self.get_selected_ticket()
        if not ticket:
            return

        # Crear una ventana para mostrar el ticket
        win = tk.Toplevel(self.parent)
        win.title(f"Factura {ticket['numero']}")
        win.geometry("600x800")

        text = tk.Text(win, wrap=tk.WORD, font=("Courier New", 10))
        scrollbar = ttk.Scrollbar(win, command=text.yview)
        text.config(yscrollcommand=scrollbar.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Formatear el ticket como texto
        ticket_text = self.format_ticket_text(ticket)
        text.insert(tk.END, ticket_text)
        text.config(state=tk.DISABLED)

    def reprint_ticket(self):
        """Reimprime el ticket seleccionado"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione al menos un ticket")
            return

        numeros = [self.tree.item(s)['values'][0] for s in selection]
        tickets = self.data_manager.load_tickets()
        to_print = [t for t in tickets if t.get("numero") in numeros]
        if not to_print:
            return

        try:
            last_path = None
            for t in to_print:
                last_path = generate_ticket_pdf(t)

            messagebox.showinfo("Éxito", f"Facturas reimpresas: {len(to_print)}")
            
            # Abrir el ticket
            if last_path and os.name == 'nt':  # Windows
                os.startfile(last_path)
            else:  # macOS o Linux
                if last_path:
                    os.system(f'open "{last_path}"')
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reimprimir el ticket:\n{str(e)}")

    def void_ticket(self):
        ticket = self.get_selected_ticket()
        if not ticket:
            return
        if str(ticket.get("estado", "ACTIVA")).upper() == "ANULADA":
            messagebox.showwarning("Advertencia", "La factura ya está anulada")
            return

        motivo = simpledialog.askstring("Anular factura", "Motivo de anulación (opcional):", parent=self.parent)
        if motivo is None:
            return

        ok = self.data_manager.update_ticket(ticket["numero"], {
            "estado": "ANULADA",
            "anulada_en": datetime.now().isoformat(timespec="seconds"),
            "anulada_motivo": motivo or "",
        })
        if ok:
            self.load_tickets()
        else:
            messagebox.showerror("Error", "No se pudo anular la factura")

    def export_tickets(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Exportar historial",
        )
        if not path:
            return
        try:
            tickets = self.data_manager.load_tickets()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(tickets, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", "Historial exportado correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

    def format_ticket_text(self, data):
        """Formatea los datos del ticket como texto para vista previa"""
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
            company.get("direccion", "").center(50),
            f"Tel: {company['telefono']} | IVA: {iva_percent}%",
            "=" * 50,
            f"FACTURA DE VENTA Nº: {data['numero']}",
            f"Fecha: {data['fecha']} {data['hora']}",
            f"Cajero: {data.get('cajero', 'ADMIN')}",
            f"Usuario: {data.get('usuario', 'USUARIO')}",
            f"Cliente: {data.get('cliente', {}).get('nombre', '')}",
            (f"Correo: {data.get('cliente', {}).get('correo', '')}" if data.get('cliente', {}).get('correo') else ""),
            "-" * 50,
            f"{'PRODUCTO'.ljust(30)} {'CANT'.rjust(5)} {'TOTAL'.rjust(10)}",
            "-" * 50
        ]

        for p in products:
            name = p["nombre"][:28] + "..." if len(p["nombre"]) > 28 else p["nombre"]
            lines.append(f"{name.ljust(30)} {str(p['cantidad']).rjust(5)} ${p['cantidad'] * p['precio']:.2f}")

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
