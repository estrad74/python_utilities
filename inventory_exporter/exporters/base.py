# Clase base para todos los exportadores de inventario.
from abc import ABC, abstractmethod


class InventoryExporter(ABC):

    # Definición de la interfaz para exportar hosts a un archivo.
    @abstractmethod
    def export(self, hosts, filename):
        pass