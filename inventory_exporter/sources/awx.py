"""
Clase para obtener inventario desde AWX.
"""

import requests
import urllib3
import yaml

from models.host import Host
from sources.base import InventorySource

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


class AwxSource(InventorySource):

    # Constructor de la clase AWXSource.
    def __init__(
        self,
        host,
        user,
        password,
        inventory_id=2,
        ignore_ssl=True
    ):

        self.awx_url = "https://" + host.rstrip("/")
        self.awx_user = user
        self.awx_token = password
        self.inventory_id = inventory_id
        self.ignore_ssl = ignore_ssl

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Authorization":
                    f"Bearer {self.awx_token}",
                "Content-Type":
                    "application/json"
            }
        )

    # Función para realizar una solicitud GET a la API de AWX.
    def _get(self, url):

        response = self.session.get(
            url,
            verify= not self.ignore_ssl,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    # Función para obtener todos los hosts de un inventario específico en AWX.
    def _get_all_hosts(self):

        url = (
            f"{self.awx_url}"
            f"/api/v2/inventories/"
            f"{self.inventory_id}/hosts/"
            f"?page_size=200"
        )

        hosts = []

        while url:

            data = self._get(url)

            hosts.extend(
                data.get(
                    "results",
                    []
                )
            )

            url = data.get("next")

            if (
                url
                and url.startswith("/")
            ):
                url = (
                    self.awx_url + url
                )

        return hosts

    # Función para obtener las variables de un host específico en AWX.
    def _get_host_variables(
        self,
        host_id
    ):

        url = (
            f"{self.awx_url}"
            f"/api/v2/hosts/"
            f"{host_id}/"
        )

        data = self._get(url)

        variables = data.get(
            "variables",
            ""
        )

        if not variables:
            return {}

        try:

            parsed = yaml.safe_load(
                variables
            )

            if isinstance(
                parsed,
                dict
            ):
                return parsed

        except Exception:
            pass

        return {}

    # Función para obtener la dirección IP de una máquina virtual desde Proxmox.
    def get_hosts(self):

        awx_hosts = (
            self._get_all_hosts()
        )

        hosts = []

        for awx_host in awx_hosts:

            try:

                host_vars = (
                    self._get_host_variables(
                        awx_host["id"]
                    )
                )

                hostname = (
                    host_vars.get(
                        "ansible_host"
                    )
                    or awx_host["name"]
                )

                username = (
                    host_vars.get(
                        "ansible_user"
                    )
                    or "root"
                )

                host_groups = (
                   self._get_host_groups(
                        awx_host["id"]
                    )
                )   

                hosts.append(

                    Host(
                        name=awx_host[
                            "name"
                        ],
                        hostname=hostname,
                        os_family="unknown",
                        username=username,
                        description=(
                            awx_host.get(
                                "description",
                                ""
                            )
                        ),
                        tags=[
                            "awx"
                        ],
                        groups=host_groups,
                        metadata={
                            "platform":
                                "awx",
                            "inventoryId":
                                self.inventory_id,
                            **host_vars
                        }
                    )

                )

            except Exception as exc:

                print(
                    f"ERROR procesando "
                    f"host "
                    f"{awx_host.get('name')}: "
                    f"{exc}"
                )

        return hosts

    # Función para obtener los grupos a los que pertenece un host específico en AWX.
    def _get_host_groups(self, host_id):

        url = (
            f"{self.awx_url}"
            f"/api/v2/hosts/"
            f"{host_id}/groups/"
            f"?page_size=200"
        )

        groups = []

        while url:

            data = self._get(url)

            groups.extend([
                group["name"]
                for group in data.get(
                    "results",
                    []
                )
            ])

            url = data.get("next")

            if (
                url
                and url.startswith("/")
            ):
                url = (
                    self.awx_url + url
                )

        return groups
