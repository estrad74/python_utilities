# Clase para crear instancias de los sources según la fuente especificada.
from sources.proxmox import ProxmoxSource
from sources.vsphere import VsphereSource
from sources.awx import AwxSource

class SourceFactory:

    # Función estática para crear una instancia del source según la fuente especificada.
    @staticmethod
    def create(source, **kwargs):

        if source.lower() == "proxmox":

            return ProxmoxSource(
                host=kwargs["host"],
                user=kwargs["user"],
                password=kwargs["password"]
            )

        if source.lower() == "vsphere":

            return VsphereSource(
                host=kwargs["host"],
                user=kwargs["user"],
                password=kwargs["password"],
                port=kwargs.get("port", 443),
                ignore_ssl=kwargs.get(
                    "ignore_ssl",
                    False
                ),
                only_powered_on=kwargs.get(
                    "only_powered_on",
                    False
                )
            )

        if source.lower() == "awx":

            return AwxSource(
                host=kwargs["host"],
                user=kwargs["user"],
                password=kwargs["password"],
                inventory_id=kwargs["inventory_id"],
                ignore_ssl=kwargs.get(
                    "ignore_ssl",
                    False
                )
            )

        raise ValueError(
            f"Unsupported source: {source}"
        )    
