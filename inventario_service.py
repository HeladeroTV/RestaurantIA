import requests
from typing import List, Dict, Any

class InventoryService:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def obtener_inventario(self) -> List[Dict[str, Any]]:
        r = requests.get(f"{self.base_url}/inventario")
        r.raise_for_status()
        return r.json()

    def agregar_item_inventario(self, nombre: str, cantidad: int, unidad: str = "unidad") -> Dict[str, Any]:
        payload = {
            "nombre": nombre,
            "cantidad_disponible": cantidad,
            "unidad_medida": unidad
        }
        r = requests.post(f"{self.base_url}/inventario", json=payload)
        r.raise_for_status()
        return r.json()

    def actualizar_item_inventario(self, item_id: int, cantidad: int, unidad: str = "unidad") -> Dict[str, Any]:
        payload = {
            "cantidad_disponible": cantidad,
            "unidad_medida": unidad
        }
        r = requests.put(f"{self.base_url}/inventario/{item_id}", json=payload)
        r.raise_for_status()
        return r.json()

    def eliminar_item_inventario(self, item_id: int) -> Dict[str, Any]:
        r = requests.delete(f"{self.base_url}/inventario/{item_id}")
        r.raise_for_status()
        return r.json()