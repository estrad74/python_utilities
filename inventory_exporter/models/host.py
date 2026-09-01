# Clase Host que representa un host en el inventario. 
# Contiene información como el nombre, hostname, familia del sistema operativo, 
# nombre de usuario, descripción, etiquetas y metadatos adicionales.
from dataclasses import dataclass, field


@dataclass
class Host:
    name: str
    hostname: str
    os_family: str
    username: str

    description: str = ""

    tags: list = field(default_factory=list)

    metadata: dict = field(default_factory=dict)