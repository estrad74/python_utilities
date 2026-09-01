# Programa principal para exportar inventario desde diferentes fuentes a varios formatos.
#!/usr/bin/env python3

import os
import argparse

from sources.proxmox import ProxmoxSource
from sources.vsphere import VsphereSource

from exporters.rundeck_exporter import RundeckExporter
from exporters.csv_exporter import CsvExporter
from exporters.json_exporter import JsonExporter
from exporters.ansible_yaml_exporter import (
    AnsibleYamlExporter
)

# Función para obtener la fuente de datos según los argumentos proporcionados.
def get_source(args):

    if args.source == "proxmox":

        return ProxmoxSource(
            host=args.host,
            user=args.user,
            password=args.password
        )

    if args.source == "vsphere":

        return VsphereSource(
            host=args.host,
            user=args.user,
            password=args.password,
            port=args.port,
            ignore_ssl=args.ignore_ssl,
            only_powered_on=args.only_powered_on
        )

    raise ValueError(
        f"Fuente no soportada: {args.source}"
    )

# Función para obtener el exportador según el formato especificado.
def get_exporter(format_name):

    if format_name == "rundeck":
        return RundeckExporter()

    if format_name == "csv":
        return CsvExporter()

    if format_name == "ansible":
        return AnsibleYamlExporter()

    if format_name == "json":
        return JsonExporter()

    raise ValueError(
        f"Formato no soportado: {format_name}"
    )

# Función principal que maneja la lógica del programa.
def main():

    parser = argparse.ArgumentParser(
        description=(
            "Exportador de inventario desde Proxmox o VMware"
        )
    )

    parser.add_argument(
        "--source",
        required=True,
        choices=[
            "proxmox",
            "vsphere"
        ]
    )

    parser.add_argument(
        "--format",
        required=True,
        choices=[
            "csv",
            "json",
            "ansible",
            "rundeck"
        ]
    )

    parser.add_argument(
        "--host",
        required=True,
        help="Host Proxmox o vCenter"
    )

    parser.add_argument(
        "--user",
        required=True,
        help="Usuario de conexión"
    )

    parser.add_argument(
        "--password",
        required=True,
        help="Contraseña de conexión"
    )

    parser.add_argument(
        "--output",
        required=True
    )

    parser.add_argument(
        "--port",
        type=int,
        default=443,
        help="Puerto vCenter"
    )

    parser.add_argument(
        "--ignore-ssl",
        action="store_true",
        help="Ignorar validación SSL"
    )

    parser.add_argument(
        "--only-powered-on",
        action="store_true",
        help="Exportar solo VMs encendidas"
    )


    args = parser.parse_args()

    source = get_source(args)

    exporter = get_exporter(args.format)

    hosts = source.get_hosts()

    exporter.export(hosts,args.output)

    print(
        f"Exportados {len(hosts)} hosts "
        f"a {args.output}"
    )

if __name__ == "__main__":
    main()
