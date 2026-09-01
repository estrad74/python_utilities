#!/bin/bash
# Wrapper script para llamar al programa python de exportación de inventarios de hosts.

set -e

usage() {
    echo "Uso:"
    echo "  $0 --source <proxmox|vsphere> \\"
    echo "     --host <host> \\"
    echo "     --user <usuario> \\"
    echo "     --password <password> \\"
    echo "     --format <rundeck|csv|ansible|json> \\"
    echo "     --output <fichero> \\"
    echo "     [--port <puerto>] \\"
    echo "     [--only-powered-on] \\"
    echo "     [--ignore-ssl]"
    exit 1
}

if [ $# -eq 0 ]; then
    usage
fi

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
        --user)
            USER="$2"
            shift 2
            ;;
        --password)
            PASSWORD="$2"
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
        --port)
            PORT="$2"
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

[ -z "$SOURCE" ]   && { echo "ERROR: falta --source"; exit 1; }
[ -z "$HOST" ]     && { echo "ERROR: falta --host"; exit 1; }
[ -z "$USER" ]     && { echo "ERROR: falta --user"; exit 1; }
[ -z "$PASSWORD" ] && { echo "ERROR: falta --password"; exit 1; }
[ -z "$FORMAT" ]   && { echo "ERROR: falta --format"; exit 1; }
[ -z "$OUTPUT" ]   && { echo "ERROR: falta --output"; exit 1; }

python3 inventory-exporter.py \
    --source "$SOURCE" \
    --host "$HOST" \
    --user "$USER" \
    --password "$PASSWORD" \
    --format "$FORMAT" \
    --output "$OUTPUT" \
    ${PORT:+--port "$PORT"} \
    $IGNORE_SSL \
    $ONLY_POWERED_ON

echo "Exportación completada. Archivo generado: $OUTPUT"

