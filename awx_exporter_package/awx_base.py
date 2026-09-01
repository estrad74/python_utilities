#!/usr/bin/env python3
"""
Clase base para conectarse y trabajar con la API de AWX.
Proporciona funcionalidad común para exportadores especializados.
"""

import requests
import yaml
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import urllib3

logger = logging.getLogger(__name__)

class AWXBase(ABC):
    """Clase base para interactuar con la API de AWX"""
    
    def __init__(self, awx_url: str, awx_token: str, verify_ssl: bool = False, page_size: int = 50):
        """Constructor base para AWX
        
        Args:
            awx_url: URL de la API de AWX
            awx_token: Token de autenticación para acceder a AWX
            verify_ssl: Verificar certificados SSL
            page_size: Número de elementos por página
        """
        self.awx_url = awx_url.rstrip('/')
        self.headers = {"Authorization": f"Bearer {awx_token}"}
        self.verify_ssl = verify_ssl
        self.page_size = min(page_size, 200)  # AWX tiene límite de 200
        self.session = requests.Session()
        
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    @abstractmethod
    def export(self, inventory_id: int, output_file: str, include_metadata: bool = True):
        """
        Método que debe implementar cualquier clase hija.
        """
        pass

     
    def _make_request(self, url: str) -> Dict[str, Any]:
        """Realiza una petición HTTP con manejo de errores"""
        try:
            logger.debug(f"Haciendo petición a: {url}")
            response = self.session.get(url, headers=self.headers, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en la petición a {url}: {e}")
            raise
    
    def _add_page_size_to_url(self, url: str) -> str:
        """Añade el parámetro page_size a la URL si no existe"""
        if 'page_size=' not in url:
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}page_size={self.page_size}"
        return url
    
    def _get_all_pages(self, url: str, resource_name: str = "elementos") -> List[Dict[str, Any]]:
        """Obtiene todos los resultados paginados de una URL"""
        all_results = []
        page_count = 0
        
        url = self._add_page_size_to_url(url)
        
        while url:
            page_count += 1
            data = self._make_request(url)
            results = data.get("results", [])
            all_results.extend(results)
            
            total_count = data.get("count", 0)
            current_page_size = len(results)
            
            logger.info(f"Recuperada página {page_count}: obtenidos {current_page_size} {resource_name} (total acumulado: {len(all_results)}/{total_count})")
            
            # Manejar URLs relativas en paginación
            next_url = data.get("next")
            if next_url:
                if next_url.startswith('/'):
                    url = f"{self.awx_url}{next_url}"
                elif next_url.startswith('http'):
                    url = next_url
                else:
                    url = f"{self.awx_url}/{next_url}"
            else:
                url = None
        
        logger.info(f"Paginación completada: {len(all_results)} {resource_name} obtenidos en {page_count} páginas")
        return all_results
    
    def get_inventory_info(self, inventory_id: int) -> Dict[str, str]:
        """Obtiene información básica del inventario"""
        try:
            inventory_url = f"{self.awx_url}/api/v2/inventories/{inventory_id}/"
            inventory_info = self._make_request(inventory_url)
            return {
                'name': inventory_info.get('name', f'Inventory-{inventory_id}'),
                'description': inventory_info.get('description', ''),
                'organization': inventory_info.get('organization', ''),
                'variables': inventory_info.get('variables', '')
            }
        except Exception as e:
            logger.warning(f"No se pudo obtener información del inventario {inventory_id}: {e}")
            return {
                'name': f'Inventory-{inventory_id}', 
                'description': '', 
                'organization': '',
                'variables': ''
            }
    
    def get_host_data(self, host: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de un host específico"""
        host_name = host["name"]
        logger.debug(f"Procesando host: {host_name}")
        
        # Obtener detalles del host para las variables
        host_detail_url = f"{self.awx_url}/api/v2/hosts/{host['id']}/"
        host_detail = self._make_request(host_detail_url)
        
        host_vars = host_detail.get("variables", "")
        if not host_vars:
            return None
        
        try:
            vars_dict = yaml.safe_load(host_vars)
            return vars_dict if isinstance(vars_dict, dict) else None
        except yaml.YAMLError as e:
            logger.warning(f"Error parseando variables del host {host_name}: {e}")
            return None
    
    def get_inventory_hosts_paginated(self, inventory_id: int):
        """Generador que devuelve hosts paginados de un inventario"""
        hosts_url = f"{self.awx_url}/api/v2/inventories/{inventory_id}/hosts/"
        hosts_url = self._add_page_size_to_url(hosts_url)
        page_count = 0
        
        while hosts_url:
            page_count += 1
            logger.info(f"Recuperando página {page_count} de hosts del inventario...")
            
            data = self._make_request(hosts_url)
            hosts = data.get("results", [])
            
            total_hosts = data.get("count", 0)
            current_page_size = len(hosts)
            logger.info(f"Página {page_count}: procesando {current_page_size} hosts de {total_hosts} totales")
            
            yield hosts
            
            # Obtener siguiente página
            next_url = data.get("next")
            if next_url:
                if next_url.startswith('/'):
                    hosts_url = f"{self.awx_url}{next_url}"
                elif next_url.startswith('http'):
                    hosts_url = next_url
                else:
                    hosts_url = f"{self.awx_url}/{next_url}"
            else:
                hosts_url = None