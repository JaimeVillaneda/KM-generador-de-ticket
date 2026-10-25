import json
import shutil
from datetime import datetime
from typing import Any
from config import DATA_DIR, LEGACY_DATA_DIR

class DataManager:
    def __init__(self, filename="empresas.json"):
        self.data_dir = DATA_DIR
        self.legacy_data_dir = LEGACY_DATA_DIR

        self.filepath = self.data_dir / filename
        self.tickets_filepath = self.data_dir / "tickets.json"
        self.clients_filepath = self.data_dir / "clientes.json"
        self.settings_filepath = self.data_dir / "settings.json"
        self.draft_filepath = self.data_dir / "ticket_draft.json"
        self.locations_filepath = self.data_dir / "locations.json"

        self.migrate_legacy_data()
        self.ensure_data_file()
        self.ensure_tickets_file()
        self.ensure_clients_file()
        self.ensure_settings_file()
        self.ensure_locations_file()

        # Migraciones de esquema (sin romper datos existentes)
        self.migrate_companies_schema()
        self.migrate_clients_schema()
        self.migrate_tickets_schema()
        self.sync_locations_from_data()

    def migrate_legacy_data(self):
        """Copia datos del directorio legacy (junto al código) al nuevo directorio de usuario."""
        try:
            legacy_files = {
                "empresas.json": self.legacy_data_dir / "empresas.json",
                "clientes.json": self.legacy_data_dir / "clientes.json",
                "tickets.json": self.legacy_data_dir / "tickets.json",
                "settings.json": self.legacy_data_dir / "settings.json",
            }

            self.data_dir.mkdir(parents=True, exist_ok=True)

            for name, legacy_path in legacy_files.items():
                new_path = self.data_dir / name
                if new_path.exists():
                    continue
                if legacy_path.exists():
                    shutil.copy2(legacy_path, new_path)
        except Exception:
            # Si la migración falla, no debe impedir que la app arranque.
            pass

    def _read_json(self, path, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _write_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)

        # Backup simple antes de sobrescribir
        if path.exists():
            try:
                backup = path.with_suffix(path.suffix + ".bak")
                shutil.copy2(path, backup)
            except Exception:
                pass

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def ensure_data_file(self):
        """Crea el archivo si no existe"""
        if not self.filepath.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, 'w') as f:
                json.dump([], f)

    def ensure_tickets_file(self):
        """Crea el archivo de tickets si no existe"""
        if not self.tickets_filepath.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.tickets_filepath, 'w') as f:
                json.dump([], f)

    def load_data(self):
        """Carga datos del archivo JSON"""
        return self._read_json(self.filepath, [])

    def save_data(self, data):
        """Guarda datos en el archivo JSON"""
        self._write_json(self.filepath, data)

    def add_company(self, company_data):
        """Añade una nueva empresa al archivo"""
        data = self.load_data()
        data.append(company_data)
        self.save_data(data)

    def update_company(self, index, company_data):
        """Actualiza una empresa existente"""
        data = self.load_data()
        if 0 <= index < len(data):
            data[index] = company_data
            self.save_data(data)
            return True
        return False

    def load_tickets(self):
        """Carga tickets del archivo JSON"""
        return self._read_json(self.tickets_filepath, [])

    def save_tickets(self, tickets):
        """Guarda la lista completa de tickets (con backup)."""
        self._write_json(self.tickets_filepath, tickets)

    def save_ticket(self, ticket_data):
        """Guarda un ticket en el historial de tickets"""
        tickets = self.load_tickets()

        if isinstance(ticket_data, dict):
            ticket_data.setdefault("estado", "ACTIVA")
            ticket_data.setdefault("creado_en", datetime.now().isoformat(timespec="seconds"))

        tickets.append(ticket_data)
        self.save_tickets(tickets)

    def ensure_clients_file(self):
        """Crea el archivo de clientes si no existe"""
        if not self.clients_filepath.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.clients_filepath, 'w') as f:
                # Cliente por defecto "Mostrador"
                json.dump([{
                    "nombre": "Mostrador",
                    "nit": "",
                    "telefono": "",
                    "correo": "",
                    "departamento": "",
                    "municipio": ""
                }], f)

    def load_clients(self):
        """Carga clientes del archivo JSON"""
        return self._read_json(self.clients_filepath, [])

    def save_clients(self, data):
        """Guarda clientes en el archivo JSON"""
        self._write_json(self.clients_filepath, data)

    def add_client(self, client_data):
        """Añade un nuevo cliente al archivo"""
        data = self.load_clients()
        data.append(client_data)
        self.save_clients(data)

    def update_client(self, index, client_data):
        """Actualiza un cliente existente"""
        data = self.load_clients()
        if 0 <= index < len(data):
            data[index] = client_data
            self.save_clients(data)
            return True
        return False

    def delete_client(self, index):
        """Elimina un cliente"""
        data = self.load_clients()
        if 0 <= index < len(data) and data[index]["nombre"] != "Mostrador":
            del data[index]
            self.save_clients(data)
            return True
        return False

    def ensure_settings_file(self):
        if not self.settings_filepath.exists():
            self._write_json(self.settings_filepath, {})

    def ensure_locations_file(self):
        if not self.locations_filepath.exists():
            departamentos = [
                "Amazonas",
                "Antioquia",
                "Arauca",
                "Atlántico",
                "Bogotá D.C.",
                "Bolívar",
                "Boyacá",
                "Caldas",
                "Caquetá",
                "Casanare",
                "Cauca",
                "Cesar",
                "Chocó",
                "Córdoba",
                "Cundinamarca",
                "Guainía",
                "Guaviare",
                "Huila",
                "La Guajira",
                "Magdalena",
                "Meta",
                "Nariño",
                "Norte de Santander",
                "Putumayo",
                "Quindío",
                "Risaralda",
                "San Andrés y Providencia",
                "Santander",
                "Sucre",
                "Tolima",
                "Valle del Cauca",
                "Vaupés",
                "Vichada",
            ]
            self._write_json(self.locations_filepath, {"departamentos": departamentos, "municipios": {}})

    def load_settings(self) -> dict[str, Any]:
        return self._read_json(self.settings_filepath, {})

    def save_settings(self, settings: dict[str, Any]):
        self._write_json(self.settings_filepath, settings)

    def get_setting(self, key: str, default=None):
        settings = self.load_settings()
        return settings.get(key, default)

    def set_setting(self, key: str, value):
        settings = self.load_settings()
        settings[key] = value
        self.save_settings(settings)

    def load_draft_ticket(self) -> dict[str, Any]:
        return self._read_json(self.draft_filepath, {})

    def save_draft_ticket(self, draft: dict[str, Any]):
        self._write_json(self.draft_filepath, draft or {})

    def clear_draft_ticket(self):
        try:
            if self.draft_filepath.exists():
                self.draft_filepath.unlink()
        except Exception:
            pass

    def load_locations(self) -> dict[str, Any]:
        return self._read_json(self.locations_filepath, {"departamentos": [], "municipios": {}})

    def save_locations(self, data: dict[str, Any]):
        self._write_json(self.locations_filepath, data)

    def get_departamentos(self) -> list[str]:
        loc = self.load_locations()
        values = [d for d in (loc.get("departamentos") or []) if isinstance(d, str) and d.strip()]
        return sorted(set(values), key=lambda s: s.lower())

    def get_municipios(self, departamento: str) -> list[str]:
        dep = (departamento or "").strip()
        if not dep:
            return []
        loc = self.load_locations()
        municipios = (loc.get("municipios") or {}).get(dep, [])
        values = [m for m in municipios if isinstance(m, str) and m.strip()]
        return sorted(set(values), key=lambda s: s.lower())

    def remember_location(self, departamento: str, municipio: str):
        dep = (departamento or "").strip()
        mun = (municipio or "").strip()
        if not dep and not mun:
            return

        loc = self.load_locations()
        departamentos = loc.get("departamentos") or []
        if dep and dep not in departamentos:
            departamentos.append(dep)
            loc["departamentos"] = departamentos

        municipios_by_dep = loc.get("municipios") or {}
        if dep and mun:
            current = municipios_by_dep.get(dep) or []
            if mun not in current:
                current.append(mun)
                municipios_by_dep[dep] = current
        loc["municipios"] = municipios_by_dep

        self.save_locations(loc)

    def sync_locations_from_data(self):
        """Agrega ubicaciones encontradas en empresas/clientes al archivo de sugerencias."""
        try:
            for c in self.load_data():
                self.remember_location(c.get("departamento", ""), c.get("municipio", ""))
            for c in self.load_clients():
                self.remember_location(c.get("departamento", ""), c.get("municipio", ""))
        except Exception:
            pass

    def migrate_companies_schema(self):
        companies = self.load_data()
        changed = False
        for c in companies:
            if "iva" not in c:
                c["iva"] = "19"
                changed = True
            if "departamento" not in c:
                c["departamento"] = ""
                changed = True
            if "municipio" not in c:
                c["municipio"] = ""
                changed = True
            if "direccion" not in c:
                c["direccion"] = ""
                changed = True
        if changed:
            self.save_data(companies)

    def migrate_clients_schema(self):
        clients = self.load_clients()
        changed = False
        for c in clients:
            if "correo" not in c:
                c["correo"] = ""
                changed = True
            if "telefono" not in c:
                c["telefono"] = ""
                changed = True
            if "departamento" not in c:
                c["departamento"] = ""
                changed = True
            if "municipio" not in c:
                c["municipio"] = ""
                changed = True
            if "nit" not in c:
                c["nit"] = ""
                changed = True
        if changed:
            self.save_clients(clients)

    def migrate_tickets_schema(self):
        tickets = self.load_tickets()
        changed = False
        for t in tickets:
            if "estado" not in t:
                t["estado"] = "ACTIVA"
                changed = True
            if "creado_en" not in t:
                t["creado_en"] = ""
                changed = True
            if "cliente" in t and isinstance(t["cliente"], dict) and "correo" not in t["cliente"]:
                t["cliente"]["correo"] = ""
                changed = True
        if changed:
            self.save_tickets(tickets)

    def update_ticket(self, numero: str, updates: dict[str, Any]) -> bool:
        tickets = self.load_tickets()
        for t in tickets:
            if t.get("numero") == numero:
                t.update(updates)
                self.save_tickets(tickets)
                return True
        return False
