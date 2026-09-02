# Clase para crear instancias de los sources según la fuente especificada.
from sources.proxmox import ProxmoxSource
from sources.vsphere import VsphereSource



class SourceFactory:

    # Función estática para crear una instancia del source según la fuente especificada.
    @staticmethod
    def create(source, **kwargs):

        if source.lower() == "proxmox":
            return ProxmoxSource(**kwargs)

        if source.lower() == "vsphere":
            return VsphereSource(**kwargs)

        raise ValueError(
            f"Unsupported source: {source}"
        )