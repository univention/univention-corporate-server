# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

import uuid
from argparse import Namespace
from logging import getLogger
from typing import Dict, List, Tuple, Union, cast  # noqa: F401

import lxml.builder

from ..files import File  # noqa: F401
from ..files.pkzip import Pkzip
from ..files.raw import Raw
from ..files.vmdk import Vmdk
from . import TargetFile


log = getLogger(__name__)


def encode_vmware_uuid(u: uuid.UUID,) -> str:
    # <https://kb.vmware.com/s/article/1880>
    FMT = "-".join([" ".join(["{}{}"] * 8)] * 2)
    return FMT.format(*u.hex)


def create_vmxf(machine_uuid: uuid.UUID, image_name: str,) -> bytes:
    E = lxml.builder.ElementMaker()
    foundry = E.Foundry(
        E.VM(
            E.VMId(
                encode_vmware_uuid(machine_uuid),
                type='string',),
            E.ClientMetaData(
                E.clientMetaDataAttributes(),
                E.HistoryEventList(),),
            E.vmxPathName(
                '%s.vmx' % (image_name,),
                type='string',),),
    )
    return cast(bytes, lxml.etree.tostring(foundry, encoding='UTF-8', xml_declaration=True, pretty_print=True,),)


def encode_vmx_file(vmx: Dict[str, str],) -> bytes:
    output = '.encoding = "UTF-8"\n'
    for key, value, in sorted(vmx.items()):
        output += '%s = "%s"\n' % (key, value)
    return output.encode('UTF-8')


def create_vmx(image_name: str, image_uuid: uuid.UUID, options: Namespace,) -> bytes:
    machine_name = options.product
    if options.version is not None:
        machine_name += ' ' + options.version
    vmx = {
        'config.version': "8",
        'virtualHW.version': "9",
        'numvcpus': "%d" % (options.cpu_count,),
        'vcpu.hotadd': "TRUE",
        'scsi0.present': "TRUE",
        'scsi0.virtualDev': "lsilogic",
        'memsize': "%d" % (options.memory_size,),
        'mem.hotadd': "TRUE",
        'scsi0:0.present': "TRUE",
        'scsi0:0.fileName': "%s.vmdk" % (image_name,),
        'ide1:0.present': "FALSE",
        'floppy0.present': "FALSE",
        'ethernet0.present': "TRUE",
        'ethernet0.wakeOnPcktRcv': "FALSE",
        'ethernet0.addressType': "generated",
        'usb.present': "TRUE",
        'ehci.present': "TRUE",
        'ehci.pciSlotNumber': "34",
        'pciBridge0.present': "TRUE",
        'pciBridge4.present': "TRUE",
        'pciBridge4.virtualDev': "pcieRootPort",
        'pciBridge4.functions': "8",
        'pciBridge5.present': "TRUE",
        'pciBridge5.virtualDev': "pcieRootPort",
        'pciBridge5.functions': "8",
        'pciBridge6.present': "TRUE",
        'pciBridge6.virtualDev': "pcieRootPort",
        'pciBridge6.functions': "8",
        'pciBridge7.present': "TRUE",
        'pciBridge7.virtualDev': "pcieRootPort",
        'pciBridge7.functions': "8",
        'vmci0.present': "TRUE",
        'hpet0.present': "TRUE",
        'usb.vbluetooth.startConnected': "TRUE",
        'displayName': machine_name,
        'guestOS': "other26xlinux-64",
        'nvram': "%s.nvram" % (image_name,),
        'virtualHW.productCompatibility': "hosted",
        'gui.exitOnCLIHLT': "FALSE",
        'powerType.powerOff': "hard",
        'powerType.powerOn': "hard",
        'powerType.suspend': "hard",
        'powerType.reset': "hard",
        'extendedConfigFile': "%s.vmxf" % (image_name,),
        'scsi0.pciSlotNumber': "16",
        'ethernet0.generatedAddress': "00:0C:29:DD:56:97",
        'ethernet0.pciSlotNumber': "33",
        'usb.pciSlotNumber': "32",
        'vmci0.id': "417158807",
        'vmci0.pciSlotNumber': "35",
        'uuid.location': encode_vmware_uuid(image_uuid),
        'uuid.bios': encode_vmware_uuid(image_uuid),
        'uuid.action': "create",
        'cleanShutdown': "TRUE",
        'replay.supported': "FALSE",
        'replay.filename': "",
        'scsi0:0.redo': "",
        'pciBridge0.pciSlotNumber': "17",
        'pciBridge4.pciSlotNumber': "21",
        'pciBridge5.pciSlotNumber': "22",
        'pciBridge6.pciSlotNumber': "23",
        'pciBridge7.pciSlotNumber': "24",
        'usb:1.present': "TRUE",
        'ethernet0.generatedAddressOffset': "0",
        'softPowerOff': "TRUE",
        'usb:1.speed': "2",
        'usb:1.deviceType': "hub",
        'usb:1.port': "1",
        'usb:1.parent': "-1",
        'usb:0.present': "TRUE",
        'usb:0.deviceType': "hid",
        'usb:0.port': "0",
        'usb:0.parent': "-1",
    }
    return encode_vmx_file(vmx)


class VMware(TargetFile):
    """Zipped VMware®-compatible (VMDK based)"""

    SUFFIX = "vmware-zip"

    def create(self, image: Raw,) -> None:
        options = self.options
        archive_name = self.archive_name()

        machine_uuid = uuid.uuid4()
        image_uuid = uuid.uuid4()
        vmdk = Vmdk(image)
        files = [
            ('%s/' % (options.product,), b""),
            ('%s/%s.vmdk' % (options.product, options.product), vmdk),
            ('%s/%s.vmxf' % (options.product, options.product), create_vmxf(machine_uuid, options.product,)),
            ('%s/%s.vmx' % (options.product, options.product), create_vmx(options.product, image_uuid, options,)),
            ('%s/%s.vmsd' % (options.product, options.product), b""),
        ]  # type: List[Tuple[str, Union[File, bytes]]]
        pkzip = Pkzip(files)
        pkzip.path().rename(archive_name)
        log.info('Generated "%s" appliance as\n  %s', self, archive_name,)
