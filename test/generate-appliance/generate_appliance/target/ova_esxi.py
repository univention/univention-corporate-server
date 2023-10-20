# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

from argparse import Namespace
from logging import getLogger
from typing import List, Tuple, Union, cast  # noqa: F401

import lxml.builder

from ..files import File  # noqa: F401
from ..files.raw import Raw
from ..files.tar import Tar
from ..files.vmdk import Vmdk
from . import ANNOTATION, LICENSE, TargetFile


log = getLogger(__name__)


def create_ovf_descriptor_esxi(image_name: str, vmdk: Vmdk, options: Namespace) -> bytes:
    machine_name = options.product
    if options.version is not None:
        machine_name += ' ' + options.version

    CIM_NAMESPACE = 'http://schemas.dmtf.org/wbem/wscim/1/common'
    OVF_NAMESPACE = 'http://schemas.dmtf.org/ovf/envelope/1'
    RASD_NAMESPACE = 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData'
    VMW_NAMESPACE = 'http://www.vmware.com/schema/ovf'
    VSSD_NAMESPACE = 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_VirtualSystemSettingData'
    XSI_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'

    E = lxml.builder.ElementMaker(nsmap={
        None: OVF_NAMESPACE,
        'ovf': OVF_NAMESPACE,
        'cim': CIM_NAMESPACE,
        'rasd': RASD_NAMESPACE,
        'vmw': VMW_NAMESPACE,
        'vssd': VSSD_NAMESPACE,
        'xsi': XSI_NAMESPACE,
    })

    OVF = f'{{{OVF_NAMESPACE}}}'
    VMW = f'{{{VMW_NAMESPACE}}}'
    Erasd = lxml.builder.ElementMaker(namespace=RASD_NAMESPACE)
    Evmw = lxml.builder.ElementMaker(namespace=VMW_NAMESPACE)
    Evssd = lxml.builder.ElementMaker(namespace=VSSD_NAMESPACE)

    envelope = E.Envelope(
        E.References(
            E.File(**{
                OVF + 'href': image_name,
                OVF + 'id': 'file1',
                OVF + 'size': '%d' % (vmdk.file_size(),),
            }),
        ),
        E.DiskSection(
            E.Info('Virtual disk information'),
            E.Disk(**{
                OVF + 'capacityAllocationUnits': 'byte * 2^30',
                OVF + 'capacity': '%d' % (vmdk.volume_size() / 2**30,),
                OVF + 'populatedSize': '0',
                OVF + 'diskId': 'vmdisk1',
                OVF + 'fileRef': 'file1',
                OVF + 'format': 'http://www.vmware.com/interfaces/specifications/vmdk.html#streamOptimized',
            }),
        ),
        E.NetworkSection(
            E.Info('The list of logical networks'),
            E.Network(
                E.Description('The VM Network network'),
                **{
                    OVF + 'name': 'VM Network',
                },
            ),
        ),
        E.VirtualSystem(
            E.Info('A virtual machine'),
            E.Name(machine_name),
            E.ProductSection(
                E.Info('Meta-information about the installed software'),
                E.Product(options.product),
                E.Vendor(options.vendor),
                E.Version(options.version) if options.version is not None else '',
                E.ProductUrl(options.product_url),
                E.VendorUrl(options.vendor_url),
            ),
            E.AnnotationSection(
                E.Info('A human-readable annotation'),
                E.Annotation(ANNOTATION),
            ),
            E.EulaSection(
                E.Info('License agreement for the virtual system'),
                E.License(LICENSE),
            ),
            E.OperatingSystemSection(
                E.Info('The kind of installed guest operating system'),
                **{
                    OVF + 'id': '100',
                    VMW + 'osType': 'other26xLinux64Guest',
                },
            ),
            E.VirtualHardwareSection(
                E.Info('Virtual hardware requirements'),
                E.System(
                    Evssd.ElementName('Virtual Hardware Family'),
                    Evssd.InstanceID('0'),
                    Evssd.VirtualSystemIdentifier(machine_name),
                    Evssd.VirtualSystemType('vmx-07'),
                ),
                E.Item(
                    Erasd.AllocationUnits('hertz * 10^6'),
                    Erasd.Description('Number of Virtual CPUs'),
                    Erasd.ElementName('%d virtual CPU(s)' % (options.cpu_count,)),
                    Erasd.InstanceID('1'),
                    Erasd.ResourceType('3'),
                    Erasd.VirtualQuantity('%d' % (options.cpu_count,)),
                ),
                E.Item(
                    Erasd.AllocationUnits('byte * 2^20'),
                    Erasd.Description('Memory Size'),
                    Erasd.ElementName('%dMB of memory' % (options.memory_size,)),
                    Erasd.InstanceID('2'),
                    Erasd.ResourceType('4'),
                    Erasd.VirtualQuantity('%d' % (options.memory_size,)),
                ),
                E.Item(
                    Erasd.Address('0'),
                    Erasd.Description('SCSI Controller'),
                    Erasd.ElementName('SCSI Controller 0'),
                    Erasd.InstanceID('3'),
                    Erasd.ResourceSubType('lsilogic'),
                    Erasd.ResourceType('6'),
                ),
                E.Item(
                    Erasd.Address('0'),
                    Erasd.Description('USB Controller (EHCI)'),
                    Erasd.ElementName('USB Controller'),
                    Erasd.InstanceID('4'),
                    Erasd.ResourceSubType('vmware.usb.ehci'),
                    Erasd.ResourceType('23'),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'autoConnectDevices',
                        VMW + 'value': 'false',
                    }),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'ehciEnabled',
                        VMW + 'value': 'true',
                    }),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'slotInfo.ehciPciSlotNumber',
                        VMW + 'value': '-1',
                    }),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'slotInfo.pciSlotNumber',
                        VMW + 'value': '-1',
                    }),
                    **{
                        OVF + 'required': 'false',
                    },
                ),
                E.Item(
                    Erasd.AutomaticAllocation('false'),
                    Erasd.ElementName('VirtualVideoCard'),
                    Erasd.InstanceID('7'),
                    Erasd.ResourceType('24'),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'enable3DSupport',
                        VMW + 'value': 'false',
                    }),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'enableMPTSupport',
                        VMW + 'value': 'false',
                    }),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'use3dRenderer',
                        VMW + 'value': 'automatic',
                    }),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'useAutoDetect',
                        VMW + 'value': 'false',
                    }),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'videoRamSizeInKB',
                        VMW + 'value': '16384',
                    }),
                    **{
                        OVF + 'required': 'false',
                    },
                ),
                E.Item(
                    Erasd.AutomaticAllocation('false'),
                    Erasd.ElementName('VirtualVMCIDevice'),
                    Erasd.InstanceID('8'),
                    Erasd.ResourceSubType('vmware.vmci'),
                    Erasd.ResourceType('1'),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'allowUnrestrictedCommunication',
                        VMW + 'value': 'false',
                    }),
                    **{
                        OVF + 'required': 'false',
                    },
                ),
                E.Item(
                    Erasd.AddressOnParent('0'),
                    Erasd.ElementName('Hard Disk 1'),
                    Erasd.HostResource('ovf:/disk/vmdisk1'),
                    Erasd.InstanceID('10'),
                    Erasd.Parent('3'),
                    Erasd.ResourceType('17'),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'backing.writeThrough',
                        VMW + 'value': 'false',
                    }),
                ),
                E.Item(
                    Erasd.AddressOnParent('7'),
                    Erasd.AutomaticAllocation('true'),
                    Erasd.Connection('VM Network'),
                    Erasd.Description('PCNet32 ethernet adapter on "VM Network"'),
                    Erasd.ElementName('Ethernet 1'),
                    Erasd.InstanceID('12'),
                    Erasd.ResourceSubType('PCNet32'),
                    Erasd.ResourceType('10'),
                    Evmw.Config(**{
                        OVF + 'required': 'false',
                        VMW + 'key': 'wakeOnLanEnabled',
                        VMW + 'value': 'true',
                    }),
                ),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'cpuHotAddEnabled',
                    VMW + 'value': 'true',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'cpuHotRemoveEnabled',
                    VMW + 'value': 'false',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'firmware',
                    VMW + 'value': 'bios',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'virtualICH7MPresent',
                    VMW + 'value': 'false',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'virtualSMCPresent',
                    VMW + 'value': 'false',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'memoryHotAddEnabled',
                    VMW + 'value': 'true',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'nestedHVEnabled',
                    VMW + 'value': 'false',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'powerOpInfo.powerOffType',
                    VMW + 'value': 'hard',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'powerOpInfo.resetType',
                    VMW + 'value': 'hard',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'powerOpInfo.standbyAction',
                    VMW + 'value': 'checkpoint',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'powerOpInfo.suspendType',
                    VMW + 'value': 'hard',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'tools.afterPowerOn',
                    VMW + 'value': 'false',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'tools.afterResume',
                    VMW + 'value': 'false',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'tools.beforeGuestShutdown',
                    VMW + 'value': 'false',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'tools.beforeGuestStandby',
                    VMW + 'value': 'false',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'tools.syncTimeWithHost',
                    VMW + 'value': 'false',
                }),
                Evmw.Config(**{
                    OVF + 'required': 'false',
                    VMW + 'key': 'tools.toolsUpgradePolicy',
                    VMW + 'value': 'manual',
                }),
            ),
            **{
                OVF + 'id': machine_name,
            },
        ),
        **{
            VMW + 'buildId': 'build-1331820',
        },
    )
    return cast(bytes, lxml.etree.tostring(envelope, encoding='UTF-8', xml_declaration=True, pretty_print=True))


class OVA_ESXi(TargetFile):
    """VMware ESXi OVA (VMDK based)"""

    SUFFIX = "ESX.ova"

    def create(self, image: Raw) -> None:
        options = self.options
        image_name = f'{options.product}-ESX-disk1.vmdk'
        descriptor_name = f'{options.product}-ESX.ovf'
        archive_name = self.archive_name()

        vmdk = Vmdk(image, adapter_type="lsilogic", hwversion="7", subformat="streamOptimized")
        descriptor = create_ovf_descriptor_esxi(image_name, vmdk, options)
        files = [
            (descriptor_name, descriptor),
            (image_name, vmdk),
        ]  # type: List[Tuple[str, Union[File, bytes]]]
        ova = Tar(files)
        ova.path().rename(archive_name)
        log.info('Generated "%s" appliance as\n  %s', self, archive_name)
