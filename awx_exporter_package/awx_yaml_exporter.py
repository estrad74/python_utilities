#!/usr/bin/env python3
"""
Exportador especializado para generar archivos YAML compatibles con Ansible
desde inventarios de AWX.
"""

import yaml
import logging
from typing import Dict, List, Any, Optional
from awx_base import AWXBase

logger = logging.getLogger(__name__)

# Constante para indicar progreso cada N hosts
NUM_HOSTS_BLOQUE = 20

class AWXInventoryYAMLExporter(AWXBase):
    """Clase para exportar inventarios de AWX a YAML"""
    
    def get_inventory_structure(self, inventory_id: int) -> Dict[str, Any]:
        """Obtiene la estructura completa del inventario (sin variables de hosts)
        
        Args:
            inventory_id: ID del inventario a exportar
            
        Returns:
            Dict[str, Any]: Estructura del inventario en formato dict
        """
        logger.info(f"Obteniendo estructura del inventario {inventory_id}")
        
        # Verificar que el inventario existe y obtener su información
        inventory_info = self.get_inventory_info(inventory_id)
        logger.info(f"Exportando inventario: {inventory_info.get('name', 'N/A')}")
        
        # Inicializar la estructura de exportación
        inventory_structure = {
            "all": {
                "children": {},
                "vars": {}
            }
        }
        
        # Obtener variables del inventario
        inventory_vars = inventory_info.get("variables", "")
        if inventory_vars:
            try:
                vars_dict = yaml.safe_load(inventory_vars)
                if isinstance(vars_dict, dict):
                    inventory_structure["all"]["vars"] = vars_dict
            except yaml.YAMLError as e:
                logger.warning(f"Error parseando variables del inventario: {e}")
        
        # Obtener todos los grupos
        groups_url = f"{self.awx_url}/api/v2/inventories/{inventory_id}/groups/"
        groups = self._get_all_pages(groups_url, "grupos")
        
        # Obtener hosts que no están en ningún grupo (ungrouped)
        ungrouped_hosts_url = f"{self.awx_url}/api/v2/inventories/{inventory_id}/hosts/?not__groups__isnull=False"
        ungrouped_hosts = self._get_all_pages(ungrouped_hosts_url, "hosts sin grupo")
        
        # Procesar hosts sin grupo
        if ungrouped_hosts:
            logger.info(f"Encontrados {len(ungrouped_hosts)} hosts sin grupo")
            ungrouped_dict = {"hosts": [host["name"] for host in ungrouped_hosts]}
            inventory_structure["all"]["children"]["ungrouped"] = ungrouped_dict
        
        # Procesar grupos (solo nombres de hosts, sin variables)
        logger.info(f"Procesando {len(groups)} grupos")
        for group in groups:
            group_data = self._get_group_data(group, include_host_vars=False)
            inventory_structure["all"]["children"][group["name"]] = group_data
        
        return inventory_structure
    
    def _get_group_data(self, group: Dict[str, Any], include_host_vars: bool = True) -> Dict[str, Any]:
        """Obtiene los datos de un grupo específico
        
        Args:
            group: Datos del grupo desde AWX
            include_host_vars: Si incluir variables de hosts en el grupo
            
        Returns:
            Dict[str, Any]: Datos del grupo estructurados
        """
        group_name = group["name"]
        logger.debug(f"Procesando grupo: {group_name}")
        
        group_data = {
            "hosts": [],
            "vars": {},
            "children": {}
        }
        
        # Procesar las variables del grupo
        group_vars = group.get("variables", "")
        if group_vars:
            try:
                vars_dict = yaml.safe_load(group_vars)
                if isinstance(vars_dict, dict):
                    group_data["vars"] = vars_dict
            except yaml.YAMLError as e:
                logger.warning(f"Error parseando variables del grupo {group_name}: {e}")
        
        # Obtener hosts del grupo
        hosts_url = f"{self.awx_url}/api/v2/groups/{group['id']}/hosts/"
        hosts = self._get_all_pages(hosts_url, f"hosts del grupo {group_name}")
        
        if include_host_vars:
            # Modo antiguo: incluir variables de host en cada grupo
            group_data["hosts"] = {}
            for host in hosts:
                host_data = self.get_host_data(host)
                group_data["hosts"][host["name"]] = host_data
        else:
            # Modo nuevo: solo nombres de hosts
            group_data["hosts"] = [host["name"] for host in hosts]
        
        # Obtener subgrupos
        children_url = f"{self.awx_url}/api/v2/groups/{group['id']}/children/"
        children = self._get_all_pages(children_url, f"subgrupos del grupo {group_name}")
        
        for child in children:
            child_data = self._get_group_data(child, include_host_vars)
            group_data["children"][child["name"]] = child_data
        
        # Limpiar secciones vacías
        if not group_data["hosts"]:
            del group_data["hosts"]
        if not group_data["vars"]:
            del group_data["vars"]
        if not group_data["children"]:
            del group_data["children"]
        
        return group_data
    
    def _write_all_hosts_to_file(self, file_handle, inventory_id: int):
        """Escribe el grupo de todos los hosts con sus variables de manera paginada
        
        Args:
            file_handle: Handle del archivo donde escribir
            inventory_id: ID del inventario
        """
        logger.info("Escribiendo grupo all_hosts con variables de hosts")
        
        # Escribir encabezado del grupo all_hosts
        file_handle.write("    all_hosts:\n      hosts:\n")
        
        host_count = 0
        
        # Procesar hosts usando el generador paginado
        for hosts_page in self.get_inventory_hosts_paginated(inventory_id):
            for host in hosts_page:
                host_count += 1
                host_name = host["name"]
                logger.debug(f"Procesando host {host_count}: {host_name}")
                
                # Escribir nombre del host
                file_handle.write(f"        {host_name}:\n")
                
                # Obtener y escribir variables del host
                host_vars = self.get_host_data(host)
                if host_vars:
                    # Convertir variables a YAML y escribir con indentación
                    host_yaml = yaml.dump(host_vars, default_flow_style=False, indent=2)
                    for line in host_yaml.splitlines():
                        if line.strip():  # Evitar líneas vacías
                            file_handle.write(f"          {line}\n")
                
                # Flush periódico para evitar acumulación en buffer
                if host_count % NUM_HOSTS_BLOQUE == 0:
                    file_handle.flush()
                    logger.info(f"Escritos {host_count} hosts en el archivo...")
        
        logger.info(f"Completado grupo all_hosts con {host_count} hosts")
        file_handle.flush()

    def _write_group_recursively(self, file_handle, group_name: str, 
                                group_data: Dict[str, Any], indent_level: int = 2):
        """Escribe un grupo y sus subgrupos de manera recursiva
        
        Args:
            file_handle: Handle del archivo donde escribir
            group_name: Nombre del grupo
            group_data: Datos del grupo
            indent_level: Nivel de indentación
        """
        indent = "  " * indent_level
        
        # Escribir nombre del grupo
        file_handle.write(f"{indent}{group_name}:\n")
        
        # Escribir hosts si existen
        if "hosts" in group_data and group_data["hosts"]:
            file_handle.write(f"{indent}  hosts:\n")
            for host in group_data["hosts"]:
                file_handle.write(f"{indent}    {host}:\n")
        
        # Escribir variables del grupo si existen
        if "vars" in group_data and group_data["vars"]:
            file_handle.write(f"{indent}  vars:\n")
            vars_yaml = yaml.dump(
                group_data["vars"], 
                default_flow_style=False, 
                indent=2
            )
            for line in vars_yaml.splitlines():
                if line.strip():
                    file_handle.write(f"{indent}    {line}\n")
        
        # Escribir subgrupos de manera recursiva
        if "children" in group_data and group_data["children"]:
            file_handle.write(f"{indent}  children:\n")
            for child_name, child_data in group_data["children"].items():
                self._write_group_recursively(file_handle, child_name, child_data, indent_level + 2)

    def export(self, inventory_id: int, output_file: str, include_metadata: bool = True):
        """Exporta el inventario a un archivo YAML
        
        Args:
            inventory_id: ID del inventario a exportar
            output_file: Ruta y nombre del fichero de exportación
        """
        try:
            # Obtener estructura básica (sin variables de hosts)
            inventory_structure = self.get_inventory_structure(inventory_id)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Escribir estructura básica hasta llegar a children
                f.write("all:\n")
                
                # Escribir variables globales si existen
                if inventory_structure["all"].get("vars"):
                    f.write("  vars:\n")
                    vars_yaml = yaml.dump(
                        inventory_structure["all"]["vars"], 
                        default_flow_style=False, 
                        indent=2
                    )
                    for line in vars_yaml.splitlines():
                        if line.strip():
                            f.write(f"    {line}\n")
                
                # Escribir encabezado de children
                f.write("  children:\n")
                
                # Escribir grupos usando el método recursivo
                for group_name, group_data in inventory_structure["all"]["children"].items():
                    self._write_group_recursively(f, group_name, group_data, indent_level=2)
            
                # Escribir grupo all_hosts procesando hosts de uno en uno
                self._write_all_hosts_to_file(f, inventory_id)
            
            logger.info(f"Inventario exportado exitosamente a: {output_file}")
            
        except Exception as e:
            logger.error(f"Error exportando inventario: {e}")
            raise
        