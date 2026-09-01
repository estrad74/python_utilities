#!/usr/bin/env python3
"""
Script para exportar inventarios de AWX a Gitlab
"""

import argparse
import sys
import logging

from config import DEFAULT_PAGE_SIZE, LOGGING_CONFIG
from awx_yaml_exporter import AWXInventoryYAMLExporter
from awx_csv_exporter import AWXInventoryCSVExporter
from gitlab_uploader import GitLabUploader

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Exportar inventarios de AWX a Gitlab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso

Exportación YAML:

%(prog)s \
  --awx-url https://awx.example.com \
  --awx-token TOKEN123 \
  --inventory-id 5 \
  --format yaml \
  --output inventory.yml

Exportación CSV:

%(prog)s \
  --awx-url https://awx.example.com \
  --awx-token TOKEN123 \
  --inventory-id 5 \
  --format CSV \
  --output inventory.csv \
  --include-metadata

Exportación y subida a GitLab:

%(prog)s \
  --awx-url https://awx.example.com \
  --awx-token TOKEN123 \
  --inventory-id 5 \
  --format YAML \
  --output inventory.yml \
  --gitlab-url https://gitlab.com \
  --gitlab-project-id 12345 \
  --gitlab-token GITLAB_TOKEN \
  --gitlab-path inventories/production.yml \
  --gitlab-branch main
  --verify-ssl false
"""
    )
    
    # Argumentos para AWX
    parser.add_argument(
        "--awx-url",
        required=True,
        help="URL base de la API de AWX (ej: https://awx.example.com)"
    )
    parser.add_argument(
        "--awx-token",
        required=True,
        help="Token de autenticación de AWX"
    )
    parser.add_argument(
        "--inventory-id",
        required=True,
        type=int,
        help="ID del inventario a exportar"
    )

    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=f"Tamaño de página para consultas API (por defecto: {DEFAULT_PAGE_SIZE})"
    )

    #
    # Parámetros de exportación
    #
    parser.add_argument(
        "--format",
        required=True,
        choices=["YAML", "CSV"],
        help="Formato de exportación"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Fichero de salida"
    )

    parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="Incluir metadatos adicionales en exportaciones CSV"
    )

    #
    # Parámetros GitLab
    #
    parser.add_argument(
        "--gitlab-url",
        required=True,
        help="URL de GitLab"
    )

    parser.add_argument(
        "--gitlab-project-id",
        type=int,
        required=True,
        help="ID del proyecto GitLab"
    )

    parser.add_argument(
        "--gitlab-token",
        required=True,
        help="Token de acceso a GitLab"
    )

    parser.add_argument(
        "--gitlab-path",
        required=True,
        help="Ruta destino dentro del repositorio GitLab"
    )

    parser.add_argument(
        "--gitlab-branch",
        default="main",
        help="Rama destino en GitLab (por defecto: main)"
    )

    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        help="Verificar certificados SSL (por defecto: False)"
    )

    return parser.parse_args()


def create_exporter(args):
    """
    Crea el exportador adecuado según el formato solicitado.
    """

    common_args = {
        "awx_url": args.awx_url,
        "awx_token": args.awx_token,
        "page_size": args.page_size
    }

    if args.format == "YAML":
        return AWXInventoryYAMLExporter(**common_args)

    if args.format == "CSV":
        return AWXInventoryCSVExporter(**common_args)

    raise ValueError(f"Formato no soportado: {args.format}")


def export_inventory(exporter, args):
    """
    Ejecuta la exportación.
    """

    logger.info(
        "Exportando inventario %s en formato %s",
        args.inventory_id,
        args.format.upper()
    )

    exporter.export(
        inventory_id=args.inventory_id,
        output_file=args.output,
        include_metadata=args.include_metadata
    )

    logger.info("Exportación completada: %s", args.output)


def upload_to_gitlab(args):
    """
    Sube el fichero generado a GitLab si se han proporcionado
    todos los parámetros necesarios.
    """

    gitlab_configured = any([
        args.gitlab_url,
        args.gitlab_project_id,
        args.gitlab_token,
        args.gitlab_path
    ])

    if not gitlab_configured:
        logger.info("No se ha solicitado subida a GitLab")
        return

    required_params = [
        args.gitlab_url,
        args.gitlab_project_id,
        args.gitlab_token,
        args.gitlab_path
    ]

    if not all(required_params):
        raise ValueError(
            "Para subir a GitLab deben especificarse todos los parámetros: "
            "--gitlab-url, "
            "--gitlab-project-id, "
            "--gitlab-token y "
            "--gitlab-path"
        )

    logger.info(
        "Subiendo '%s' a GitLab (%s)",
        args.output,
        args.gitlab_path
    )

    uploader = GitLabUploader(
            args.gitlab_url,
            args.gitlab_project_id,
            args.gitlab_token,
            args.gitlab_branch,
            args.verify_ssl
        )

    success = uploader.upload_file(
                args.output,
                args.gitlab_path
            )

    if success:
        logger.info("¡Proceso completado exitosamente! Inventario exportado y subido a GitLab.")
    else:
        logger.error("El inventario se exportó correctamente, pero falló la subida a GitLab.")
        sys.exit(1)

def main():
    """
    Función principal.
    """

    try:
        args = parse_arguments()

        exporter = create_exporter(args)

        export_inventory(
            exporter=exporter,
            args=args
        )

        upload_to_gitlab(args)

        logger.info("Proceso finalizado correctamente")

    except KeyboardInterrupt:
        logger.warning("Proceso cancelado por el usuario")
        sys.exit(1)

    except Exception as exc:
        logger.error("Error durante la ejecución: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()