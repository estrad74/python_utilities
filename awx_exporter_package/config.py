#!/usr/bin/env python3
"""
Configuración y constantes comunes para los exportadores de AWX.
"""

# Constantes de configuración
DEFAULT_PAGE_SIZE = 50
NUM_HOSTS_BLOQUE = 20

# Configuración de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s'
}