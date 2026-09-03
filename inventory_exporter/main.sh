#!/bin/bash
set -euo pipefail

# Constantes
DEFAULT_PROXMOX_HOST="proxmox.ced.junta-andalucia.es"
DEFAULT_VSPHERE_HOST="sscc-vcsa.ced.junta-andalucia.es"
DEFAULT_AWX_HOST="sv0078.ced.junta-andalucia.es"

# Comprobación de secrets
: "${SOURCE_USER:?La variable SOURCE_USER no está definida}"
: "${SOURCE_PASSWORD:?La variable SOURCE_PASSWORD no está definida}"
: "${AWX_TOKEN:?La variable AWX_TOKEN no está definida}"

# Función de ayuda
usage() {
    cat <<EOF
Uso:
  $0 --source <proxmox|vsphere|awx> \
     --format <csv|yaml|ansible|rundeck> \
     --output <fichero> \
     [opciones]

Parámetros obligatorios:
  --source <valor>        Fuente de inventario (proxmox, vsphere, awx)
  --format <valor>        Formato de salida
  --output <fichero>      Fichero generado

Parámetros opcionales:
  --host <host>           Host de la plataforma origen o url de AWX
  --port <puerto>         Puerto de conexión
  --only-powered-on       Exportar solo máquinas encendidas
  --ignore-ssl            Ignorar validación SSL
  --awx-token <token>     Token de acceso a la instancia AWX  
  --inventory-id <id>     ID del inventario en AWX

Variables obligatorias:
  SOURCE_USER             Usuario de la plataforma origen
  SOURCE_PASSWORD         Contraseña de la plataforma origen
  AWX_TOKEN               Token de acceso a la instancia AWX

Ejemplos:

  Proxmox:
  $0 \
    --source proxmox \
    --host pve01.midominio.com \
    --format rundeck \
    --output inventario.yaml

  vSphere:
  $0 \
    --source vsphere \
    --host vcenter.midominio.com \
    --format csv \
    --output inventario.csv \
    --ignore-ssl \
    --only-powered-on

  AWX:
  $0 \
    --source awx \
    --host awx.midominio.com \
    --format ansible \
    --output inventario.yaml \
    --ignore-ssl \
    --only-powered-on
    --inventory-id 2

EOF
    exit 1
}


# Comprobación de parámetros
while [ $# -gt 0 ]; do
    case "$1" in
        --source)
            SOURCE="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --inventory-id)
            INVENTORY_ID="$2"
            shift 2
            ;;
        --only-powered-on)
            ONLY_POWERED_ON="--only-powered-on"
            shift 1
            ;;
        --ignore-ssl)
            IGNORE_SSL="--ignore-ssl"
            shift 1
            ;;
        *)
            echo "ERROR: Parámetro desconocido: $1"
            usage
            ;;
    esac
done

[ -z "$SOURCE" ]    && { echo "ERROR: falta --source"; exit 1; }
[ -z "$FORMAT" ]    && { echo "ERROR: falta --format"; exit 1; }
[ -z "$OUTPUT" ]    && { echo "ERROR: falta --output"; exit 1; }

if [ -z "${HOST+x}" ]; then
    if [ "$SOURCE" == "proxmox" ]; then
        HOST=$DEFAULT_PROXMOX_HOST
    elif [ "$SOURCE" == "vsphere" ]; then
        HOST=$DEFAULT_VSPHERE_HOST
    elif [ "$SOURCE" == "awx" ]; then
        HOST=$DEFAULT_AWX_HOST
    else
        echo "ERROR: falta --host y no se puede determinar un valor por defecto para la fuente $SOURCE"
        exit 1
    fi
fi

# Si la fuente es AWX, usar el token de AWX como contraseña
if [ "$SOURCE" == "awx" ]; then
    PASSWORD="$AWX_TOKEN"
else
    PASSWORD="$SOURCE_PASSWORD"
fi

# Ejecutar el script de exportación de inventario
python3 "inventory_exporter/inventory-exporter.py" \
            --source "$SOURCE" \
            --host "$HOST" \
            --user "$SOURCE_USER" \
            --password "$PASSWORD" \
            --format "$FORMAT" \
            --output "$OUTPUT" \
            ${INVENTORY_ID:+--inventory-id "$INVENTORY_ID"} \
            ${PORT:+--port "$PORT"} \
            ${IGNORE_SSL:-} \
            ${ONLY_POWERED_ON:-}


echo "Exportación completada. Archivo generado: $OUTPUT"


