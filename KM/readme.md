SistemaTicketsPOS/
│
├── assets/
│   └── icon.ico          # Icono para la aplicación
│
├── data/
│   ├── empresas.json     # Datos de empresas
│   └── data_manager.py   # Manejo de datos
│
├── modules/
│   ├── __init__.py
│   ├── ticket_module.py  # Módulo de tickets
│   └── company_module.py # Módulo de empresas
│
├── templates/
│   └── ticket_template.py # Plantilla de tickets
│
├── main.py               # Entrada principal
├── build.spec            # Configuración de PyInstaller
└── requirements.txt      # Dependencias



pyinstaller==5.13.0
reportlab==4.0.4



con este codigo compilas

python -m PyInstaller build.spec

Nota: si al abrir el `.exe` aparece `ModuleNotFoundError: No module named 'tkinter'`, el Python/entorno con el que compilaste no tiene Tcl/Tk (tkinter). En Anaconda suele solucionarse con:

conda install tk
