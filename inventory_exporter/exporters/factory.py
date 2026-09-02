# Clase para crear instancias de los exportadores según el formato especificado.
from exporters.ansible_yaml_exporter import AnsibleYamlExporter
from exporters.csv_exporter import CsvExporter
from exporters.json_exporter import JsonExporter
from exporters.rundeck_exporter import RundeckExporter


class ExporterFactory:

    # Función estática para crear una instancia del exportador según el formato especificado.
    @staticmethod
    def create(format_name, **kwargs):

        if format_name.lower() == "csv":
            return CsvExporter(**kwargs)

        if format_name.lower() == "json":
            return JsonExporter(**kwargs)

        if format_name.lower() == "ansible":
            return AnsibleYamlExporter(**kwargs)

        if format_name.lower() == "rundeck":
            return RundeckExporter(**kwargs)

        raise ValueError(
            f"Unsupported format: {format_name}"
        )