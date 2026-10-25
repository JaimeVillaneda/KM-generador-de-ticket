def _show_fatal_error(title: str, message: str) -> "None":
    """Muestra un error fatal (ideal para ejecutables windowed) y sale."""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # MB_ICONERROR
    except Exception:
        # Si no se puede mostrar MessageBox, igual salimos.
        pass
    raise SystemExit(1)

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Tickets Profesional")
        self.root.geometry("1100x750")
        self.root.minsize(1000, 700)
        
        # Configurar DataManager
        self.data_manager = DataManager()
        
        # Frame principal
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear notebook (pestañas)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Pestaña de Tickets
        self.tab_ticket = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_ticket, text="Generar Ticket")
        self.ticket_module = TicketModule(self.tab_ticket, self.data_manager)
        
        # Pestaña de Empresas
        self.tab_company = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_company, text="Gestionar Empresas")
        self.company_module = CompanyModule(
            self.tab_company,
            self.data_manager,
            refresh_callback=self.refresh_ticket_module,
            use_in_ticket_callback=self.select_company_in_ticket,
        )
        
        # Pestaña de Clientes
        self.tab_client = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_client, text="Gestionar Clientes")
        self.client_module = ClientModule(
            self.tab_client,
            self.data_manager,
            refresh_callback=self.refresh_ticket_module,
            use_in_ticket_callback=self.select_client_in_ticket,
        )
        
        # Pestaña de Historial
        self.tab_history = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_history, text="Historial de Facturas")
        self.history_module = HistoryModule(self.tab_history, self.data_manager)
        
        # Footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            footer_frame, 
            text="Desarrollado con ❤️ por JAVU, para KIL", 
            font=('Arial', 9), 
            foreground='gray'
        ).pack(side=tk.RIGHT, padx=10)
        
        # Configurar tema
        self.setup_theme()

    def on_tab_changed(self, event=None):
        """Refresca datos al cambiar de pestaña (sin botones de 'Actualizar')."""
        current_tab = self.notebook.select()
        if current_tab == str(self.tab_ticket):
            self.ticket_module.refresh_data()
        elif current_tab == str(self.tab_company):
            self.company_module.load_companies()
        elif current_tab == str(self.tab_client):
            self.client_module.load_clients()
        elif current_tab == str(self.tab_history):
            self.history_module.load_tickets()

    def select_client_in_ticket(self, client_name: str):
        try:
            self.notebook.select(self.tab_ticket)
            self.ticket_module.refresh_data()
            self.ticket_module.client_var.set(client_name)
            self.ticket_module.check_ready()
        except Exception:
            pass

    def select_company_in_ticket(self, company_name: str):
        try:
            self.notebook.select(self.tab_ticket)
            self.ticket_module.refresh_data()
            self.ticket_module.empresa_var.set(company_name)
            self.ticket_module.check_ready()
        except Exception:
            pass

    def setup_theme(self):
        """Configura el aspecto visual de la aplicación"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configuraciones generales
        style.configure('.', font=('Arial', 10))
        style.configure('TNotebook.Tab', padding=(10, 5), font=('Arial', 10, 'bold'))
        style.configure('TLabelFrame', font=('Arial', 10, 'bold'))
        style.configure('TButton', padding=5)
        
        # Colores
        style.map('TButton',
                foreground=[('active', 'black'), ('!active', 'black')],
                background=[('active', '#e6e6e6'), ('!active', '#f0f0f0')])

    def refresh_ticket_module(self):
        """Actualiza empresas y clientes en el módulo de tickets"""
        self.ticket_module.refresh_data()

if __name__ == "__main__":
    try:
        import tkinter as tk  # type: ignore
        from tkinter import ttk  # type: ignore
    except ModuleNotFoundError:
        _show_fatal_error(
            "Falta Tkinter",
            "No se encontró el módulo 'tkinter'.\n\n"
            "Si estás abriendo un .exe generado con PyInstaller: vuelve a compilarlo con un Python que tenga Tcl/Tk instalado.\n"
            "En Anaconda: conda install tk\n"
            "En Python oficial (python.org): reinstala y marca 'tcl/tk and IDLE'.",
        )

    # Importaciones que dependen de tkinter (se dejan aquí para poder mostrar un error amigable arriba).
    from data.data_manager import DataManager
    from modules.ticket_module import TicketModule
    from modules.company_module import CompanyModule
    from modules.client_module import ClientModule
    from modules.history_module import HistoryModule

    try:
        root = tk.Tk()
    except Exception as exc:
        _show_fatal_error(
            "Error inicializando Tk",
            "Tkinter está instalado, pero no se pudo inicializar Tcl/Tk.\n\n"
            "Esto suele pasar cuando falta el archivo 'init.tcl' (Tcl no instalado correctamente).\n\n"
            f"Detalle: {exc}",
        )

    app = MainApplication(root)
    root.mainloop()
