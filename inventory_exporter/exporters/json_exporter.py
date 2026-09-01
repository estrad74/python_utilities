#Clase para exportar inventario en formato JSON.
from dataclasses import asdict
import json
from exporters.base import InventoryExporter

class JsonExporter(InventoryExporter):

    # Función para exportar la lista de hosts a un archivo JSON.
    def export(self, hosts, filename):

        inventory = {
            host.name: asdict(host)
            for host in hosts
        }

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                inventory,
                f,
                indent=4,
                ensure_ascii=False
            )