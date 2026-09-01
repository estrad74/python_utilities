#!/usr/bin/env python3
"""
Paquete para exportar inventarios de AWX a diferentes formatos y subirlos a GitLab.

Módulos disponibles:
- awx_base: Clase base para conexión con AWX
- gitlab_uploader: Clase para subir archivos a GitLab
- awx_csv_exporter: Exportador especializado en formato CSV con info de SO
- awx_yaml_exporter: Exportador especializado en formato YAML compatible con Ansible
- config: Configuración y constantes comunes
"""

from .awx_base import AWXBase
from .gitlab_uploader import GitLabUploader
from .awx_csv_exporter import AWXInventoryCSVExporter
from .awx_yaml_exporter import AWXInventoryYAMLExporter
from .config import DEFAULT_PAGE_SIZE, NUM_HOSTS_BLOQUE, LOGGING_CONFIG

__version__ = "1.0.0"
__author__ = "Ignacio Estrada Cáceres"

__all__ = [
    'AWXBase',
    'GitLabUploader', 
    'AWXInventoryCSVExporter',
    'AWXInventoryYAMLExporter',
    'DEFAULT_PAGE_SIZE',
    'NUM_HOSTS_BLOQUE',
    'LOGGING_CONFIG'
]