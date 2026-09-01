# Clase base para subir ficheros a un repositorio Git.
from abc import ABC, abstractmethod
from pathlib import Path


class GitUploader(ABC):

    # Constructor de la clase GitUploader.
    def __init__(
        self,
        file_name,
        repo_url,
        project_id,
        access_token,
        branch="main",
        verify_ssl=False,
        commit_message="File uploaded"
    ):
        self.file_name = file_name
        self.repo_url = repo_url.rstrip("/")
        self.project_id = project_id
        self.access_token = access_token
        self.branch = branch
        self.verify_ssl = verify_ssl
        self.commit_message = commit_message

    # Función para leer el contenido del fichero a subir.
    def read_file(self):
        path = Path(self.file_name)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {self.file_name}"
            )

        return path.read_bytes()

    # Función para obtener el nombre del fichero en el repositorio.
    def get_repo_filename(self):
        """
        Nombre con el que se almacenará en el repositorio.
        Por defecto se utiliza únicamente el nombre del fichero.
        """
        return Path(self.file_name).name

    # Función abstracta para subir el fichero al repositorio.
    @abstractmethod
    def upload(self):
        pass