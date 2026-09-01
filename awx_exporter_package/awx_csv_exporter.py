#!/usr/bin/env python3
"""
Exportador especializado para generar archivos CSV con información 
de sistema operativo desde inventarios de AWX.
"""

import csv
import yaml
import logging
from typing import Dict, List, Any, Tuple, Optional
from awx_base import AWXBase

logger = logging.getLogger(__name__)

# Constante para indicar progreso cada N hosts
NUM_HOSTS_BLOQUE = 20

class AWXInventoryCSVExporter(AWXBase):
    """Clase para exportar inventarios de AWX a CSV con información de SO"""
    
    def _extract_os_info(self, host_vars: Dict[str, Any]) -> Tuple[str, str]:
        """Extrae información del sistema operativo de las variables del host
        
        Args:
            host_vars: Variables del host desde AWX
            
        Returns:
            Tuple[str, str]: (nombre_so, version_completa)
        """
        try:
            # Buscar en ansible_facts
            ansible_facts = host_vars.get('ansible_facts', {})
            
            if ansible_facts and isinstance(ansible_facts, dict):
                # Información del SO desde facts
                os_info = ansible_facts.get('os', {})
                if os_info:
                    os_name = os_info.get('name', 'Unknown')
                    os_version = os_info.get('version', '')
                    os_release = os_info.get('release', '')
                    
                    # Construir versión completa
                    version_parts = [str(part) for part in [os_version, os_release] if part]
                    version_full = ' '.join(version_parts) if version_parts else 'Unknown'
                    
                    return os_name, version_full
                
                # Fallback: buscar directamente en ansible_facts
                distribution = ansible_facts.get('distribution') or ansible_facts.get('name', 'Unknown')
                version = ansible_facts.get('distribution_version', '')
                release = ansible_facts.get('distribution_release', '')
                
                version_parts = [str(part) for part in [version, release] if part]
                version_full = ' '.join(version_parts) if version_parts else 'Unknown'
                
                return distribution, version_full
            
            # Buscar información de Proxmox
            proxmox_ostype = host_vars.get('proxmox_ostype', '')
            if proxmox_ostype:
                return f"Proxmox-{proxmox_ostype}", "From Proxmox metadata"
            
            # Buscar información de VMware
            vmware_guest_id = host_vars.get('guest.id', '')
            vmware_guest_fullname = host_vars.get('guest.fullname', '')
            if vmware_guest_fullname:
                return vmware_guest_fullname, "From VMware metadata"
            elif vmware_guest_id:
                return f"VMware-{vmware_guest_id}", "From VMware metadata"
            
            return "Unknown", "No OS information available"
            
        except Exception as e:
            logger.debug(f"Error extrayendo información de SO: {e}")
            return "Error", "Failed to parse OS info"
    
    def export(self, inventory_id: int, output_file: str, 
                     include_metadata: bool = True):
        """Exporta inventarios a un archivo CSV con información de SO
        
        Args:
            inventory_id: ID del inventario de AWX a exportar
            output_file: Ruta del archivo CSV de salida
            include_metadata: Si incluir metadatos adicionales o solo hostname y OS
        """
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                # Definir columnas según si se incluyen metadatos o no
                if include_metadata:
                    fieldnames = [
                        'inventory_name', 'hostname', 'os_name', 'os_version',
                        'last_updated', 'has_facts'
                    ]
                else:
                    fieldnames = ['hostname', 'os_name']
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                total_hosts = 0
                hosts_with_os = 0
                
                logger.info(f"Procesando inventario {inventory_id}...")
                    
                # Obtener información del inventario
                inventory_info = self.get_inventory_info(inventory_id)
                inventory_name = inventory_info['name']
                    
                # Procesar hosts usando el generador paginado
                for hosts_page in self.get_inventory_hosts_paginated(inventory_id):
                    for host in hosts_page:
                        total_hosts += 1
                        host_name = host["name"]
                            
                        # Obtener variables del host
                        host_vars = {}
                        if host.get("variables"):
                            try:
                                host_vars = yaml.safe_load(host["variables"])
                                if not isinstance(host_vars, dict):
                                    host_vars = {}
                            except yaml.YAMLError:
                                host_vars = {}
                            
                        # Extraer información del SO
                        os_name, os_version = self._extract_os_info(host_vars)
                            
                        # Determinar si tiene facts
                        has_facts = bool(host_vars.get('ansible_facts'))
                        if has_facts:
                            hosts_with_os += 1
                            
                        # Preparar fila para CSV
                        if include_metadata:
                            row = {
                                'inventory_name': inventory_name,
                                'hostname': host_name,
                                'os_name': os_name,
                                'os_version': os_version,
                                'last_updated': host_vars.get('ansible_facts', {}).get('collected_at', 'Never'),
                                'has_facts': 'Yes' if has_facts else 'No'
                            }
                        else:
                            row = {
                                'hostname': host_name,
                                'os_name': f"{os_name} {os_version}".strip()
                            }
                            
                        writer.writerow(row)
                            
                        # Log progreso cada cierto número de hosts
                        if total_hosts % NUM_HOSTS_BLOQUE == 0:
                            logger.info(f"Procesados {total_hosts} hosts...")
                    
                logger.info(f"Completado inventario {inventory_name}")
                
                # Estadísticas finales
                logger.info(f"""
=== RESUMEN DE EXPORTACIÓN ===
Total de hosts procesados: {total_hosts}
Hosts con información de SO: {hosts_with_os}
Hosts sin información de SO: {total_hosts - hosts_with_os}
Archivo generado: {output_file}
""")
        
        except Exception as e:
            logger.error(f"Error exportando a CSV: {e}")
            raise
