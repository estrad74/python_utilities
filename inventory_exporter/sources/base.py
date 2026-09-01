# Clase base para todas las fuentes de inventario.
from abc import ABC, abstractmethod


class InventorySource(ABC):

    # Definición de la interfaz para obtener hosts desde una fuente de inventario.
    @abstractmethod
    def get_hosts(self):
        pass