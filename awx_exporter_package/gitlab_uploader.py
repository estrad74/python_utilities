#!/usr/bin/env python3
"""
Clase para subir archivos a repositorios de GitLab.
Maneja la creación y actualización de archivos via API.
"""

import requests
import base64
import os
import logging
import urllib3
from datetime import datetime

logger = logging.getLogger(__name__)

class GitLabUploader:
    """Clase para subir archivos a GitLab"""
    
    def __init__(self, gitlab_url: str, project_id: str, access_token: str, 
                 branch: str = "main", verify_ssl: bool = False):
        """Constructor para GitLab uploader
        
        Args:
            gitlab_url: URL base de GitLab (ej: https://gitlab.com)
            project_id: ID del proyecto en GitLab
            access_token: Token de acceso personal de GitLab
            branch: Rama donde subir el archivo (por defecto: main)
            verify_ssl: Verificar certificados SSL (por defecto: False)
        """
        self.gitlab_url = gitlab_url.rstrip('/')
        self.project_id = project_id
        self.access_token = access_token
        self.branch = branch
        self.verify_ssl = verify_ssl
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def file_exists(self, file_path: str) -> bool:
        """Verifica si un archivo existe en el repositorio
        
        Args:
            file_path: Ruta del archivo en el repositorio
            
        Returns:
            bool: True si el archivo existe, False en caso contrario
        """
        url = f"{self.gitlab_url}/api/v4/projects/{self.project_id}/repository/files/{file_path.replace('/', '%2F')}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params={"ref": self.branch},
                verify=self.verify_ssl
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def upload_file(self, local_file_path: str, remote_file_path: str, 
                   custom_commit_message: str = None) -> bool:
        """Sube un archivo al repositorio de GitLab
        
        Args:
            local_file_path: Ruta del archivo local
            remote_file_path: Ruta donde se guardará en GitLab
            custom_commit_message: Mensaje personalizado de commit (opcional)
        
        Returns:
            bool: True si se subió correctamente, False en caso contrario
        """
        try:
            # Leer el contenido del archivo
            with open(local_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Codificar el contenido en base64
            content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            # Preparar el mensaje de commit
            if custom_commit_message:
                commit_message = custom_commit_message
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_message = f"Automated export from AWX: {os.path.basename(remote_file_path)} - {timestamp}"
            
            # URL de la API
            url = f"{self.gitlab_url}/api/v4/projects/{self.project_id}/repository/files/{remote_file_path.replace('/', '%2F')}"
            
            # Verificar si el archivo ya existe
            file_exists = self.file_exists(remote_file_path)
            
            # Preparar los datos
            data = {
                "branch": self.branch,
                "content": content_base64,
                "commit_message": commit_message,
                "encoding": "base64"
            }
            
            # Hacer la petición (POST para crear, PUT para actualizar)
            if file_exists:
                logger.info(f"Actualizando archivo existente: {remote_file_path}")
                response = requests.put(url, headers=self.headers, json=data, verify=self.verify_ssl)
            else:
                logger.info(f"Creando nuevo archivo: {remote_file_path}")
                response = requests.post(url, headers=self.headers, json=data, verify=self.verify_ssl)
            
            if response.status_code in [200, 201]:
                logger.info(f"Archivo subido exitosamente a GitLab: {remote_file_path}")
                return True
            else:
                logger.error(f"Error subiendo archivo a GitLab: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error al subir archivo a GitLab: {e}")
            return False
    
    def create_directory_structure(self, directory_path: str) -> bool:
        """Crea la estructura de directorios necesaria en GitLab
        
        Args:
            directory_path: Ruta del directorio a crear
            
        Returns:
            bool: True si se creó correctamente o ya existía
        """
        try:
            # GitLab crea directorios automáticamente al subir archivos
            # Esta función está aquí para futuras extensiones si se necesita
            logger.info(f"La estructura de directorios se creará automáticamente: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"Error creando estructura de directorios: {e}")
            return False