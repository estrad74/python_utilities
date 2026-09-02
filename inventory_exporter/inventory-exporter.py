# Programa principal para exportar inventario desde diferentes fuentes a varios formatos.
#!/usr/bin/env python3

import os
import argparse

from exporters.factory import ExporterFactory
from sources.factory import SourceFactory
import sources.base
import exporters.base

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
        type=str,
        default=None,
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
        action="store_false",
        help="Exportar solo VMs encendidas"
    )


    args = parser.parse_args()


    # Creación del uploader según la fuente especificada.
    source = SourceFactory.create(
        source=args.source,
        host=args.host,
        user=args.user,
        password=args.password,
        port=args.port,
        ignore_ssl=args.ignore_ssl,
        only_powered_on=args.only_powered_on
    )

    # Creación del exportador según el formato especificado.
    exporter = ExporterFactory.create(
        format_name=args.format
    )
    
    hosts = source.get_hosts()

    exporter.export(hosts,args.output)

    print(
        f"Exportados {len(hosts)} hosts "
        f"a {args.output}"
    )

if __name__ == "__main__":
    main()
