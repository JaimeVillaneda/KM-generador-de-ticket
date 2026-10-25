# Sistema Tickets POS

Aplicación de escritorio en Python para gestionar empresas, clientes, tickets e historial.

## Requisitos

- Python 3
- Tkinter (incluido en la mayoría de instalaciones de Python)

## Ejecutar

Desde la carpeta del repositorio:

```powershell
cd KM
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Crear ejecutable en Windows

Con el entorno virtual activo y desde `KM`:

```powershell
python -m PyInstaller build.spec
```

El ejecutable se genera dentro de `KM/dist/`. Los archivos de compilación y los tickets PDF generados no se versionan.

La aplicación y sus archivos de datos están en [KM](./KM/). Para más detalles, consulta [la guía del proyecto](./KM/readme.md).
