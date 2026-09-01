# Clase para exportar inventario en formato CSV.
import csv

from exporters.base import InventoryExporter


class CsvExporter(InventoryExporter):

    # Función para exportar la lista de hosts a un archivo CSV.
    def export(self, hosts, filename):

        metadata_fields = set()

        for host in hosts:
            metadata_fields.update(
                host.metadata.keys()
            )

        metadata_fields = sorted(
            metadata_fields
        )

        headers = [
            "name",
            "hostname",
            "os_family",
            "username",
            "description",
            "tags"
        ] + metadata_fields

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
        ) as csvfile:

            writer = csv.writer(csvfile)

            writer.writerow(headers)

            for host in hosts:

                row = [
                    host.name,
                    host.hostname,
                    host.os_family,
                    host.username,
                    host.description,
                    ",".join(host.tags)
                ]

                for field in metadata_fields:

                    row.append(
                        host.metadata.get(
                            field,
                            ""
                        )
                    )

                writer.writerow(row)