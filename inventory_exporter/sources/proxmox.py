# Clase para obtener inventario desde Proxmox.
from urllib import response

import requests
import urllib3
from models.host import Host
from sources.base import InventorySource

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

class ProxmoxSource(InventorySource):

    # Constructor de la clase ProxmoxSource.
    def __init__(
        self,
        host,
        user,
        password
    ):
        self.host = host
        self.user = self.normalize_user(user)
        self.password = password


    # Normaliza el usuario de Proxmox para asegurarse de que tenga el sufijo correcto.
    def normalize_user(self, user):

        user = user.replace("CED\\", "")

        if ( 
            not user.endswith("@AD") and 
            not user.endswith("@PAM") and
            not user.endswith("@PVE")
        ):
            user += "@AD"

        return user

    # Función para obtener una sesión autenticada con Proxmox.
    def get_session(self):

        url = (
            f"https://{self.host}:8006/"
            "api2/json/access/ticket"
        )

        response = requests.post(
            url,
            data={
                "username": self.user,
                "password": self.password
            },
            verify=False,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()["data"]

        session = requests.Session()
        session.verify = False

        session.cookies.set(
            "PVEAuthCookie",
            data["ticket"]
        )

        return session

    # Función para obtener los recursos del clúster desde Proxmox.
    def get_cluster_resources(self, session):

        url = (
            f"https://{self.host}:8006/"
            "api2/json/cluster/resources?type=vm"
        )

        response = session.get(
            url,
            timeout=60
        )

        response.raise_for_status()

        return response.json()["data"]

    # Función para obtener la dirección IP de una máquina virtual QEMU desde Proxmox.
    def get_qemu_ip(
        self,
        session,
        node,
        vmid
    ):

        try:

            url = (
                f"https://{self.host}:8006/api2/json/"
                f"nodes/{node}/qemu/{vmid}/"
                "agent/network-get-interfaces"
            )

            response = session.get(
                url,
                timeout=15
            )

            if response.status_code != 200:
                return None

            interfaces = (
                response.json()["data"]["result"]
            )

            for iface in interfaces:

                for addr in iface.get(
                    "ip-addresses",
                    []
                ):

                    ip = addr.get("ip-address")

                    if (
                        ip
                        and ":" not in ip
                        and not ip.startswith("127.")
                    ):
                        return ip

        except Exception:
            pass

        return None

    # Función para obtener la dirección IP de un contenedor LXC desde Proxmox.
    def get_lxc_ip(
        self,
        session,
        node,
        vmid
    ):

        try:

            url = (
                f"https://{self.host}:8006/api2/json/"
                f"nodes/{node}/lxc/{vmid}/interfaces"
            )

            response = session.get(
                url,
                timeout=15
            )

            if response.status_code != 200:
                return None

            interfaces = response.json()["data"]

            for iface in interfaces:

                for inet in iface.get(
                    "inet",
                    []
                ):

                    ip = inet.get("address")

                    if (
                        ip
                        and not ip.startswith("127.")
                    ):
                        return ip

        except Exception:
            pass

        return None

    # Función para detectar el sistema operativo basado en el nombre de la máquina virtual.
    def detect_os(self, name):

        if not name:
            return "unix"

        return (
            "windows"
            if "win" in name.lower()
            else "unix"
        )

    # Función para obtener el sistema operativo de una máquina virtual QEMU desde Proxmox.
    def get_qemu_os(
        self,
        session,
        node,
        vmid
    ):

        try:

            url = (
                f"https://{self.host}:8006/api2/json/"
                f"nodes/{node}/qemu/{vmid}/"
                "agent/get-osinfo"
            )

            response = session.get(
                url,
                timeout=15
            )

            if response.status_code != 200:
                return "unknown"

            data = response.json()["data"]

            return (
                data.get("pretty-name")
                or data.get("name")
                or "unknown"
            )

        except Exception:

            return "unknown"

    # Función para obtener el sistema operativo de un contenedor LXC desde Proxmox.
    def get_lxc_os(
        self,
        session,
        node,
        vmid
    ):

        try:

            url = (
                f"https://{self.host}:8006/api2/json/"
                f"nodes/{node}/lxc/{vmid}/config"
            )

            response = session.get(
                url,
                timeout=15
            )

            if response.status_code != 200:
                return "unknown"

            data = response.json()["data"]

            return data.get(
                "ostype",
                "unknown"
            )

        except Exception:

            return "unknown"

    # Función para obtener la lista de hosts desde Proxmox.
    def get_hosts(self):

        session = self.get_session()

        resources = self.get_cluster_resources(
            session
        )

        hosts = []

        for vm in resources:

            vm_type = vm.get("type")

            if vm_type not in [
                "qemu",
                "lxc"
            ]:
                continue

            vmid = vm.get("vmid")
            name = vm.get("name")
            node = vm.get("node")
            status = vm.get("status")
            numcpu = vm.get("maxcpu")
            memoryMB = int(vm.get("maxmem", 0) / 1024 / 1024)
            vm_type = vm.get("type")
            platform = "Proxmox"

            ip = None

            if vm_type == "qemu":
                ip = self.get_qemu_ip(
                    session,
                    node,
                    vmid
                )

                os_version = self.get_qemu_os(
                    session,
                    node,
                    vmid
                )

            else:
                ip = self.get_lxc_ip(
                    session,
                    node,
                    vmid
                )

                os_version = self.get_lxc_os(
                    session,
                    node,
                    vmid
                )   
            
            os_family = self.detect_os(
                name
            )

            hosts.append(

                Host(
                    name=name,
                    hostname=ip or name,
                    os_family=os_family,
                    username=(
                        "Administrator"
                        if os_family == "windows"
                        else "root"
                    ),
                    description=(
                        f"Proxmox {vm_type}"
                    ),
                    tags=[
                        platform,
                        vm_type,
                        status
                    ],
                    metadata={
                        "platform": platform,
                        "node": node,
                        "id": vmid,
                        "type": vm_type,
                        "powerState": status,
                        "numCPU": numcpu,
                        "memoryMB": memoryMB,
                        "guestOS": os_version
                    }
                )

            )

        return hosts
