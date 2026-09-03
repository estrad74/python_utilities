# Clase para exportar inventario en formato compatible con Ansible YAML.
import yaml
from exporters.base import InventoryExporter

class AnsibleYamlExporter(InventoryExporter):

    # Función para exportar la lista de hosts a un archivo YAML compatible con Ansible.
    def export(self, hosts, filename):

        inventory = {
            "all": {
                "children": {},
                "hosts": {}
            }
        }

        for host in hosts:
            host_entry = {
                "ansible_host": host.hostname
            }
            
            host_entry.update(host.metadata)
            inventory[
                "all"
            ][
                "hosts"
            ][
                host.name
            ] = host_entry

            for group in host.groups:
                if (
                    group
                    not in inventory[
                        "all"
                    ][
                        "children"
                    ]
                ):

                    inventory[
                        "all"
                    ][
                        "children"
                    ][
                        group
                    ] = {
                        "hosts": {}
                    }

                inventory[
                    "all"
                ][
                    "children"
                ][
                    group
                ][
                    "hosts"
                ][
                    host.name
                ] = {}

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            yaml.dump(
                inventory,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
