# Clase para crear instancias de los uploaders según el destino especificado.
from uploaders.github import GithubUploader
from uploaders.gitlab import GitlabUploader


class UploaderFactory:

    # Función estática para crear una instancia del uploader según el destino especificado.
    @staticmethod
    def create(dest, **kwargs):

        if dest.lower() == "gitlab":
            return GitlabUploader(**kwargs)

        if dest.lower() == "github":
            return GithubUploader(**kwargs)

        raise ValueError(
            f"Unsupported destination: {dest}"
        )