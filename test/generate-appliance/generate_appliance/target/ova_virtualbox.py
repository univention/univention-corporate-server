
# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

import uuid
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


def create_ovf_descriptor_virtualbox(machine_uuid: uuid.UUID, image_name: str, vmdk: Vmdk, image_uuid: uuid.UUID, options: Namespace,) -> bytes:
    machine_name = options.product
    if options.version is not None:
        machine_name += ' ' + options.version

    OVF_NAMESPACE = 'http://schemas.dmtf.org/ovf/envelope/1'
    RASD_NAMESPACE = 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData'
    VBOX_NAMESPACE = 'http://www.virtualbox.org/ovf/machine'
    VSSD_NAMESPACE = 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_VirtualSystemSettingData'
    XML_NAMESPACE = 'http://www.w3.org/XML/1998/namespace'
    XSI_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'

    E = lxml.builder.ElementMaker(nsmap={
        None: OVF_NAMESPACE,
        'ovf': OVF_NAMESPACE,
        'rasd': RASD_NAMESPACE,
        'vbox': VBOX_NAMESPACE,
        'vssd': VSSD_NAMESPACE,
        'xsi': XSI_NAMESPACE,
    })

    OVF = '{%s}' % (OVF_NAMESPACE,)
    VBOX = '{%s}' % (VBOX_NAMESPACE,)
    XML = '{%s}' % (XML_NAMESPACE,)
    Erasd = lxml.builder.ElementMaker(namespace=RASD_NAMESPACE)
    Evbox = lxml.builder.ElementMaker(namespace=VBOX_NAMESPACE)
    Evssd = lxml.builder.ElementMaker(namespace=VSSD_NAMESPACE)

    envelope = E.Envelope(
        E.References(
            E.File(**{
                OVF + 'href': image_name,
                OVF + 'id': 'file1',
            }),
        ),
        E.DiskSection(
            E.Info('List of the virtual disks used in the package'),
            E.Disk(**{
                OVF + 'capacity': '%d' % (vmdk.volume_size(),),
                OVF + 'diskId': 'vmdisk1',
                OVF + 'fileRef': 'file1',
                OVF + 'format': 'http://www.vmware.com/interfaces/specifications/vmdk.html#streamOptimized',
                VBOX + 'uuid': str(image_uuid),
            }),),
        E.NetworkSection(
            E.Info('Logical networks used in the package'),
            E.Network(
                E.Description('Logical network used by this appliance.'),
                **{
                    OVF + 'name': 'Bridged',
                },),),
        E.VirtualSystem(
            E.Info('A virtual machine'),
            E.ProductSection(
                E.Info('Meta-information about the installed software'),
                E.Product(options.product),
                E.Vendor(options.vendor),
                E.Version(options.version) if options.version is not None else '',
                E.ProductUrl(options.product_url),
                E.VendorUrl(options.vendor_url),),
            E.AnnotationSection(
                E.Info('A human-readable annotation'),
                E.Annotation(ANNOTATION),),
            E.EulaSection(
                E.Info('License agreement for the virtual system'),
                E.License(LICENSE),),
            E.OperatingSystemSection(
                E.Info('The kind of installed guest operating system'),
                E.Description('Debian_64'),
                Evbox.OSType(
                    'Debian_64',
                    **{
                        OVF + 'required': 'false',
                    },),
                **{
                    OVF + 'id': '96',
                },),
            E.VirtualHardwareSection(
                E.Info('Virtual hardware requirements for a virtual machine'),
                E.System(
                    Evssd.ElementName('Virtual Hardware Family'),
                    Evssd.InstanceID('0'),
                    Evssd.VirtualSystemIdentifier(machine_name),
                    Evssd.VirtualSystemType('virtualbox-2.2'),),
                E.Item(
                    Erasd.Caption('%d virtual CPU' % (options.cpu_count,)),
                    Erasd.Description('Number of virtual CPUs'),
                    Erasd.ElementName('%d virtual CPU' % (options.cpu_count,)),
                    Erasd.InstanceID('1'),
                    Erasd.ResourceType('3'),
                    Erasd.VirtualQuantity('%d' % (options.cpu_count,)),),
                E.Item(
                    Erasd.AllocationUnits('MegaBytes'),
                    Erasd.Caption('%d MB of memory' % (options.memory_size,)),
                    Erasd.Description('Memory Size'),
                    Erasd.ElementName('%d MB of memory' % (options.memory_size,)),
                    Erasd.InstanceID('2'),
                    Erasd.ResourceType('4'),
                    Erasd.VirtualQuantity('%d' % (options.memory_size,)),),
                E.Item(
                    Erasd.Address('0'),
                    Erasd.Caption('ideController0'),
                    Erasd.Description('IDE Controller'),
                    Erasd.ElementName('ideController0'),
                    Erasd.InstanceID('3'),
                    Erasd.ResourceSubType('PIIX4'),
                    Erasd.ResourceType('5'),),
                E.Item(
                    Erasd.AutomaticAllocation('true'),
                    Erasd.Caption("Ethernet adapter on 'Bridged'"),
                    Erasd.Connection('Bridged'),
                    Erasd.ElementName("Ethernet adapter on 'Bridged'"),
                    Erasd.InstanceID('5'),
                    Erasd.ResourceSubType('PCNet32'),
                    Erasd.ResourceType('10'),),
                E.Item(
                    Erasd.AddressOnParent('0'),
                    Erasd.Caption('disk1'),
                    Erasd.Description('Disk Image'),
                    Erasd.ElementName('disk1'),
                    Erasd.HostResource('/disk/vmdisk1'),
                    Erasd.InstanceID('7'),
                    Erasd.Parent('3'),
                    Erasd.ResourceType('17'),),),
            **{
                OVF + 'id': machine_name,
            },),
        **{
            XML + 'lang': 'en-US',
            OVF + 'version': '1.0',
        },)
    return cast(bytes, lxml.etree.tostring(envelope, encoding='UTF-8', xml_declaration=True, pretty_print=True,),)


class OVA_Virtualbox(TargetFile):
    """VirtualBox OVA (VMDK based)"""

    SUFFIX = "virtualbox.ova"

    def create(self, image: Raw,) -> None:
        options = self.options
        image_name = '%s-virtualbox-disk1.vmdk' % (options.product,)
        descriptor_name = '%s-virtualbox.ovf' % (options.product,)
        archive_name = self.archive_name()

        machine_uuid = uuid.uuid4()
        image_uuid = uuid.uuid4()
        vmdk = Vmdk(image, adapter_type="ide", hwversion="4", subformat="streamOptimized",)
        descriptor = create_ovf_descriptor_virtualbox(
            machine_uuid,
            image_name, vmdk, image_uuid,
            options,)
        files = [
            (descriptor_name, descriptor),
            (image_name, vmdk),
        ]  # type: List[Tuple[str, Union[File, bytes]]]
        ova = Tar(files)
        ova.path().rename(archive_name)
        log.info('Generated "%s" appliance as\n  %s', self, archive_name,)
