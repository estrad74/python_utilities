# Clase para exportar inventario en formato compatible con Rundeck.
import yaml
from exporters.base import InventoryExporter

class RundeckExporter(InventoryExporter):

    # Función para exportar la lista de hosts a un archivo YAML compatible con Rundeck.
    def export(self, hosts, filename):

        inventory = {}

        for host in hosts:

            node = {
                "nodename": host.name,
                "hostname": host.hostname,
                "description": host.description,
                "username": host.username,
                "osFamily": host.os_family,
                "tags": ",".join(host.tags)
            }

            node.update(host.metadata)

            inventory[host.name] = node

        with open(filename, "w") as f:
            yaml.dump(
                inventory,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )