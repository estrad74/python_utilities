# Clase para obtener inventario desde vSphere.
import ssl
from pyVim.connect import (
    SmartConnect,
    Disconnect
)

from pyVmomi import vim
from models.host import Host
from sources.base import InventorySource

class VsphereSource(InventorySource):

    def __init__(
        self,
        host,
        user,
        password,
        port=443,
        ignore_ssl=True,
        only_powered_on=False
    ):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.ignore_ssl = ignore_ssl
        self.only_powered_on = (
            only_powered_on
        )

    def get_datacenter_name(self, vm):

        obj = vm.parent

        while obj is not None:

            if isinstance(obj, vim.Datacenter):
                return obj.name

            obj = obj.parent

        return "unknown"


    def get_hosts(self):

        context = None

        if self.ignore_ssl:

            context = (
                ssl.create_default_context()
            )

            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        si = SmartConnect(
            host=self.host,
            user=self.user,
            pwd=self.password,
            port=self.port,
            sslContext=context
        )

        content = si.RetrieveContent()

        container = (
            content.viewManager
            .CreateContainerView(
                content.rootFolder,
                [vim.VirtualMachine],
                True
            )
        )

        hosts = []

        for vm in container.view:

            try:

                summary = vm.summary

                if summary.config.template:
                    continue

                power_state = str(
                    summary.runtime.powerState
                )

                if (
                    self.only_powered_on
                    and power_state !=
                    "poweredOn"
                ):
                    continue

                guest = summary.guest
                config = summary.config

                platform = "vSphere"
                power_state = str(summary.runtime.powerState)
                host_node = self.get_datacenter_name(vm)
                vm_type = "vm"
                id = config.uuid
                num_cpu = config.numCpu
                memory_mb = config.memorySizeMB

                guest_os = (
                    config.guestFullName
                    or ""
                )

                os_family = (
                    "windows"
                    if "windows"
                    in guest_os.lower()
                    else "unix"
                )

                hosts.append(

                    Host(
                        name=config.name,
                        hostname=(
                            guest.ipAddress
                            or config.name
                        ),
                        os_family=os_family,
                        username=(
                            "Administrator"
                            if os_family ==
                            "windows"
                            else "root"
                        ),
                        description=(
                            f"vSphere {vm_type}"
                        ),
                        tags=[
                            platform,
                            vm_type,
                            power_state
                        ],
                        metadata={
                            "platform": platform,
                            "node": host_node,
                            "id": id,
                            "type": vm_type,
                            "powerState": power_state,
                            "numcpu": num_cpu,
                            "memoryMB": memory_mb,
                            "guestOS": guest_os
                        }
                    )
                )

            except Exception:
                continue

        Disconnect(si)

        return hosts
