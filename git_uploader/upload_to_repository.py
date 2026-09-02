# Script para subir un fichero a un repositorio GitLab o GitHub.
import argparse
from uploaders.factory import UploaderFactory


# Función para convertir un valor a booleano.
def str2bool(value):
    return str(value).lower() in (
        "true",
        "1",
        "yes",
        "y"
    )

# Función principal del script.
def main():

    # Definición de los argumentos de línea de comandos.
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--file-name",
        required=True
    )

    parser.add_argument(
        "--dest",
        choices=["gitlab", "github"],
        required=True
    )

    parser.add_argument(
        "--url",
        required=True
    )

    parser.add_argument(
        "--project-id",
        required=True
    )

    parser.add_argument(
        "--access-token",
        required=True
    )

    parser.add_argument(
        "--branch",
        default="main"
    )

    parser.add_argument(
        "--verify-ssl",
        default=False,
        type=str2bool
    )

    parser.add_argument(
        "--comment",
        default="Subida automática de fichero exportado"
    )

    args = parser.parse_args()

    # Creación del uploader según el destino especificado.
    uploader = UploaderFactory.create(
        dest=args.dest,
        file_name=args.file_name,
        repo_url=args.url,
        project_id=args.project_id,
        access_token=args.access_token,
        branch=args.branch,
        verify_ssl=args.verify_ssl,
        commit_message=args.comment
    )

    # Subida del fichero al repositorio.
    uploader.upload()

# Punto de entrada del script.
if __name__ == "__main__":
    main()
