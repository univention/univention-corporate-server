#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable-msg=W0142,W0221,R0903
"""
Check if VMs are still valid
1. all referenced volumes exist
2. volumes contain snapshot data
3. snapshot XML exists for volume snapshots
4. unreferenced volumes
"""
from __future__ import print_function

import sys
import os
import re
import libvirt
import subprocess
import logging
from optparse import OptionParser
from lxml import etree as ET
# The expat parser fails on control characters
from xml.parsers.expat import ExpatError

try:
    import curses
    curses.setupterm()
    NORMAL = curses.tigetstr('sgr0').decode('ascii')
    SET_AF = curses.tigetstr('setaf')
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = [curses.tparm(SET_AF, i).decode('ascii') for i in range(8)]
except (ImportError, curses.error):
    NORMAL = BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ''


class Dotter(object):

    """Handle dot graph."""
    RE_KEY = re.compile('[^0-9A-Za-z]')

    def __init__(self, out=None):
        self.dot_out = out

    @staticmethod
    def key2dot(key):
        """Convert key to dot compatible format."""
        return '_' + Dotter.RE_KEY.sub('_', key)

    def __call__(self, fmt, data=None):
        """Print dot graph."""
        if self.dot_out:
            text = fmt % (data or {})
            print(text, file=self.dot_out)


class Resource(object):

    """A existing or required resource in the file system."""
    all = {}
    dotter = Dotter()

    def __init__(self, filename):
        """Create persistent resource."""
        self.filename = filename
        self.valid = None  # undecided
        self.exists = None  # unchecked
        self.used = False
        self.dependencies = []
        self.logger = logging.getLogger('%s.%s' % (self.__class__.__name__, self.__str__()))

    @classmethod
    def create(cls, name, *args):
        """Create or return unique resource."""
        res = cls(name, *args)
        res = cls.all.setdefault(res.filename, res)
        return res

    def mark_used(self):
        """Mark this and all downstream resources as being used."""
        if self.used:
            return
        self.logger.debug('now used')
        self.used = True
        for res in self.dependencies:
            res.mark_used()

    def depends_on(self, res):
        """This resource 'self' uses the other resource 'res'."""
        if res not in self.dependencies:
            self.logger.debug('Depends on "%s"', res)
            self.dependencies.append(res)

    def invalid(self, msg, *data):
        """Mark resource as invalid."""
        self.valid = False
        self.logger.warn('!VALID %s' % (msg,), *data)

    def check_valid(self):
        """This resource is valid if all referenced resources are valid."""
        if self.exists is None:
            self.logger.debug('Checking existence...')
            # FIXME: This only check the local system, but libvirt can remote
            self.exists = os.path.exists(self.filename)
        if not self.exists:
            self.invalid('Missing "%s"', self.filename)
        if self.valid is None:
            self.logger.debug('Checking validity...')
            for res in self.dependencies:
                if not res.check_valid():
                    self.invalid('Propagating "%s" to "%s"', res, self)
                    break
            else:
                self.valid = True
        assert not self.filename.endswith('stefan_Debian-Squeeze-0.qcow2')
        self.logger.info('valid=%r', self.valid)
        return self.valid

    def dot(self, label=None, shape=None, style=None, color=None):
        """Print dot graph."""
        fmt = ['label="%(label)s"', 'color=%(color)s']
        data = {
            'id': Dotter.key2dot(self.filename),
            'label': label or self.__str__(),
        }
        if shape:
            fmt.append('shape=%(shape)s')
            data['shape'] = shape
        if style:
            fmt.append('style=%(style)s')
            data['style'] = style
        if color:
            data['color'] = color
        else:
            if self.used and self.valid:
                data['color'] = 'green'
            elif self.used and not self.valid:
                data['color'] = 'red'
            elif not self.used and self.valid:
                data['color'] = 'blue'
            else:
                data['color'] = 'magenta'
        fmt = '%%(id)s [%s];' % (', '.join(fmt),)
        Resource.dotter(fmt, data)

    def console(self):
        """Print console output."""
        cls = ''.join([_ for _ in self.__class__.__name__ if _.isupper()])
        if self.used and self.valid:
            return '%s %sUSED%s    %s' % (cls, GREEN, NORMAL, self.filename)
        elif self.used and not self.valid:
            return '%s %sINVALID%s %s' % (cls, RED, NORMAL, self.filename)
        elif not self.used and self.valid:
            return '%s %sUNUSED%s  %s' % (cls, BLUE, NORMAL, self.filename)
        else:
            return '%s %sTRASH%s   %s' % (cls, MAGENTA, NORMAL, self.filename)

    def __str__(self):
        return self.filename

    def __repr__(self):
        return '%s(filename=%r valid=%r used=%r dependencies=%r exists=%r' % (
            self.__class__.__name__,
            self.filename,
            self.valid,
            self.used,
            self.dependencies,
            self.exists,
        )


class VirtualMachine(Resource):

    """Persistent virtual machine resource."""

    def __init__(self, vm_name):
        filename = os.path.join('/etc/libvirt/qemu', '%s.xml' % (vm_name,))
        self.name = vm_name
        self.uuid = None
        super(VirtualMachine, self).__init__(filename)
        self.exists = True

    @classmethod
    def parse_domain(cls, domain):
        """Parse libvirt domain XML."""
        dom_name = domain.findtext('name')
        if not dom_name:  # old style
            raise TypeError('old snapshot without domain')
        self = VirtualMachine.create(dom_name)
        self.uuid = domain.findtext('uuid')
        devices = domain.find('devices')
        disks = devices.findall('disk')
        for disk in disks:
            disk_type = disk.attrib['type']
            source = disk.find('source')
            if disk.attrib['device'] in ('cdrom', 'floppy') and \
                    source is None:
                self.logger.warn("EMPTY type='%s'", disk_type)
                continue
            if disk_type == 'file':
                path = source.attrib['file']
            elif disk_type == 'block':
                path = source.attrib['dev']
            else:
                self.logger.warn("SKIP type='%s'", disk_type)
                continue
            res = StorageVolume.create(path)
            self.depends_on(res)
        return self

    @classmethod
    def libvirt(cls, dom):
        """Create instance from libvirt domain XML."""
        dom_xml = dom.XMLDesc(0)
        try:
            domain = ET.fromstring(dom_xml)
        except ExpatError:
            self = cls.create(dom.name())
            self.invalid('Failed to parse XML: %s', dom_xml)
            return self
        self = cls.parse_domain(domain)
        self.logger.info("created from libvirt")
        snapshots = dom.snapshotListNames(0)
        for snap_name in snapshots:
            self.logger.info("has snapshot '%s'", snap_name)
            snap = dom.snapshotLookupByName(snap_name, 0)
            res = SnapShot.libvirt(self, snap)
            if res:
                self.depends_on(res)
        return self

    def dot(self):
        """Print dot graph."""
        super(VirtualMachine, self).dot(shape='box')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '%s(name=%r, valid=%r, used=%r, dependencies=%r, uuid=%r' % (
            self.__class__.__name__,
            self.name,
            self.valid,
            self.used,
            self.dependencies,
            self.uuid,
        )


class SnapShot(Resource):

    """Snapshot of a virtual machine resource.

    <domainsnapshot>
      <name>err72</name>
      <state>running</state>
      <parent>
        <name>pre ucs-test</name>
      </parent>
      <creationTime>1337597096</creationTime>
      <domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>
        ...
      </domain>
      <active>0</active>
    </domainsnapshot>
    """

    def __init__(self, virtual_machine, name):
        filename = os.path.join('/var/lib/libvirt/qemu/snapshot', virtual_machine.name, '%s.xml' % (name,))
        self.virtual_machine = virtual_machine
        self.name = name
        self.state = None
        super(SnapShot, self).__init__(filename)

    def parse_types(self, domainsnap):
        """Parse different snapshot types."""
        if self.state in ('shutoff', 'running'):
            for disk in self.virtual_machine.dependencies:
                if not isinstance(disk, StorageVolume):
                    continue
                self.depends_on(disk)
        elif self.state == 'disk-snapshot':
            disks = domainsnap.find('disks')
            for disk in disks.findall('disk'):
                snap_type = disk.attrib['snapshot']
                if snap_type == 'no':
                    continue
                elif snap_type == 'external':
                    source = disk.find('source')
                    path = source.attrib['file']
                    vol_res = StorageVolume.create(path)
                    self.depends_on(vol_res)
                else:
                    self.logger.debug('vm=%s state=%s disk=%s', self.virtual_machine.name, self.state, snap_type)
        else:
            self.logger.debug('vm=%s state=%s', self.virtual_machine.name, self.state)

    @classmethod
    def libvirt(cls, virtual_machine, snap):
        """Create snapshot from libvirt domain XML."""
        snap_xml = snap.getXMLDesc(0)
        try:
            domainsnap = ET.fromstring(snap_xml)
        except ExpatError:
            self = SnapShot.create(virtual_machine, '//DUMMY//')
            self.invalid('Failed to parse XML: %s', snap_xml)
            return self
        try:
            snap_name = snap.getName()
        except AttributeError:
            snap_name = domainsnap.findtext('name')
        self = SnapShot.create(virtual_machine, snap_name)
        self.logger.info("created from libvirt for '%s'", virtual_machine.name)
        self.exists = True
        state = domainsnap.findtext('state')
        if self.state and self.state != state:
            self.invalid('vm=%s snap=%s: Duplicate state: %s %s', virtual_machine.name, snap_name, self.state, state)
        else:
            self.state = state
        self.parse_types(domainsnap)
        domain = domainsnap.find('domain')
        try:
            vm2 = VirtualMachine.parse_domain(domain)
        except TypeError:
            pass
        else:
            if virtual_machine != vm2:
                self.invalid('vm=%s: Domain mismatches %s', virtual_machine, vm2)
        return self

    def check_valid(self):
        """This volume is valid if all snapshots are accounted."""
        if self.valid is None:
            if not super(SnapShot, self).check_valid():
                return False
        else:
            return self.valid

        if self.state in ('shutoff', 'running'):
            self.logger.info('Checking for snapshot data')
            for disk in [_ for _ in self.dependencies if isinstance(_, StorageVolume) and _.target_format_type == 'qcow2']:
                # FIXME: only 1st disk contains the VM state
                try:
                    snaps = disk.read_snapshots()
                except LookupError:
                    self.logger.warn('Could not read "%s"', disk)
                    break
                for _num, tag, vm_size, _date, _time, _clock in snaps:
                    if tag != self.name:
                        continue
                    if self.state == 'shutoff' and vm_size != '0':
                        self.invalid('vm=%s: Shutoff but vm_size=%d', self.virtual_machine.name, vm_size)
                    elif self.state == 'running' and vm_size == '0':
                        self.invalid('vm=%s: Running but vm_size=0', self.virtual_machine.name)
                    break
                else:
                    continue
                break
            else:
                self.invalid('vm=%s: Missing saved state', self.virtual_machine.name)

        return self.valid

    def dot(self):
        """Print dot graph."""
        super(SnapShot, self).dot(shape='trapezium')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '%s(vm=%r name=%r valid=%r used=%r dependencies=%r state=%r' % (
            self.__class__.__name__,
            self.virtual_machine.name,
            self.name,
            self.valid,
            self.used,
            self.dependencies,
            self.state,
        )


class StorageVolume(Resource):

    """Disk volume of a virtual machine resource.

    <volume>
      <name>b.qcow2</name>
      <key>/var/lib/libvirt/images/b.qcow2</key>
      <source>
      </source>
      <capacity>1073741824</capacity>
      <allocation>139264</allocation>
      <target>
        <path>/var/lib/libvirt/images/b.qcow2</path>
        <format type='qcow2'/>
        <permissions>
          <mode>0644</mode>
          <owner>2260</owner>
          <group>110</group>
        </permissions>
      </target>
      <backingStore>
        <path>/var/lib/libvirt/images/a.qcow2</path>
        <format type='qcow2'/>
        <permissions>
          <mode>0644</mode>
          <owner>2260</owner>
          <group>110</group>
        </permissions>
      </backingStore>
    </volume>
    """

    pools = set()

    def __init__(self, filename):
        self.target_format_type = None
        super(StorageVolume, self).__init__(filename)

    @classmethod
    def libvirt(cls, disk):
        """Create instance from libvirt volume XML."""
        disk_name = disk.path()
        self = StorageVolume.create(disk_name)
        self.logger.info("created from libvirt")
        self.exists = True
        try:
            vol_xml = disk.XMLDesc(0)
        except libvirt.libvirtError as ex:
            if ex.get_error_code() != libvirt.VIR_ERR_SYSTEM_ERROR:
                self.logger.exception('Failed to get XML for %s', disk_name)
            self.invalid('Failed to get XML')
            return self
        try:
            volume = ET.fromstring(vol_xml)
        except ExpatError:
            self.invalid('Failed to parse XML: %s', vol_xml)
            return self
        try:
            target = volume.find('target')
            target_format = target.find('format')
            self.target_format_type = target_format.attrib['type']
        except (AttributeError, LookupError):
            self.target_format_type = None

        try:
            backing_store = volume.find('backingStore')
            path2 = backing_store.findtext('path')
        except (AttributeError, LookupError):
            pass
        else:
            self.logger.info("backed by '%s'", path2)
            vol2 = cls.create(path2)
            self.depends_on(vol2)
        return self

    def read_snapshots(self):  # pylint: disable-msg=R0914
        """Get snapshots stored in qcow2 file."""
        with open(os.path.devnull, 'w') as null:
            cmd = ('qemu-img', 'snapshot', '-l', self.filename)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=null)
        stdout, _stderr = proc.communicate()
        if proc.wait() != 0:
            self.logger.info("failed to read snapshots")
            raise LookupError(self.filename)

        snapshots = []
        lines = stdout.splitlines()  # pylint: disable-msg=E1103
        del lines[:2]  # strip header
        for line in lines:  # %-10s%-20s%7s%20s%15s
            num = line[0:10].rstrip()
            tag = line[10:-42]
            if len(tag) == 20:
                tag = tag.rstrip()
            vm_size = line[-42:-35].lstrip()
            date, time = line[-35:-15].split(None, 1)
            clock = line[-15:].lstrip()
            record = (num, tag, vm_size, date, time, clock)
            snapshots.append(record)
        return snapshots

    def check_valid(self):
        """This volume is valid if all snapshots are accounted."""
        if self.valid is None:
            if not super(StorageVolume, self).check_valid():
                return False
        else:
            return self.valid

        if self.target_format_type == 'qcow2':
            self.logger.info('Checking for snapshot data')
            try:
                snaps = self.read_snapshots()
            except LookupError:
                snaps = ()
            for _num, tag, _vm_size, _date, _time, _clock in snaps:
                self.logger.debug("Looking for snapshot '%s'", tag)
                snaps = [_ for _ in Resource.all.values() if isinstance(_, SnapShot) and _.name == tag]
                vms = [_.virtual_machine for _ in snaps]
                for virtual_machine in vms:
                    disks = [_ for _ in virtual_machine.dependencies if isinstance(_, StorageVolume)]
                    if self in disks:
                        self.logger.debug("Found snapshot %s in %s", tag, virtual_machine.filename)
                        break
                else:
                    self.invalid('disk=%s: Unknown vm for %s', self.filename, tag)
                    virtual_machine = VirtualMachine.create('//DUMMY//')
                    snap = SnapShot.create(virtual_machine, tag)
                    snap.depends_on(self)
                    snap.valid = False
                    virtual_machine.depends_on(snap)

        return self.valid

    def dot(self):
        """Print dot graph."""
        super(StorageVolume, self).dot(shape='ellipse')

    def __str__(self):
        return os.path.basename(self.filename)

    def __repr__(self):
        return '%s(filename=%r valid=%r used=%r dependencies=%r format=%r' % (
            self.__class__.__name__,
            self.filename,
            self.valid,
            self.used,
            self.dependencies,
            self.target_format_type,
        )


TEMP_POOL = """
virsh # pool-create-as --type dir --name temp --target /etc/libvirt/qemu
virsh # vol-list temp
"""


def check_storage_pools(conn):
    """Check active and defined storage pools."""
    logger = logging.getLogger('root')
    for pool in conn.listAllStoragePools():
        logger.debug('POOL %s', pool)
        try:
            pool.refresh(0)
        except libvirt.libvirtError as ex:
            if ex.get_error_code() != libvirt.VIR_ERR_OPERATION_DENIED:
                raise

        # Remember paths for which pools are defined
        pool_xml = pool.XMLDesc(0)
        try:
            pool2 = ET.fromstring(pool_xml)
        except ExpatError:
            logger.exception('Failed to parse XML: %s', pool_xml)
            return
        target = pool2.find('target')
        target_path = target.findtext('path')
        StorageVolume.pools.add(target_path)

        for volume in pool.listAllVolumes():
            StorageVolume.libvirt(volume)
    # TODO: conn.listDefinedStoragePools() are inactive


def check_virtual_machines(conn):
    """Check running domains."""
    logger = logging.getLogger('root')
    for dom in conn.listAllDomains():
        logger.debug('domain %s', dom)
        virtual_machine = VirtualMachine.libvirt(dom)
        virtual_machine.mark_used()


def check_storage_volumes(conn):
    """Check crawled volumes exists."""
    disks = [_ for _ in Resource.all.values() if isinstance(_, StorageVolume)]
    while disks:
        vol = disks.pop(0)
        if vol.exists is not None:
            continue
        dirname = os.path.dirname(vol.filename)
        vol.logger.debug('Checking existence...')
        if dirname in StorageVolume.pools:
            try:
                disk2 = conn.storageVolLookupByPath(vol.filename)
            except libvirt.libvirtError as ex:
                if ex.get_error_code() != libvirt.VIR_ERR_NO_STORAGE_VOL:
                    raise
                vol.exists = False
                vol.invalid('vol=%s: Not found in pool', vol.filename)
            else:
                vol.logger.info('Found in pool %s', vol.storagePoolLookupByVolume().name())
                vol.exists = True
                vol2 = StorageVolume.libvirt(disk2)
                assert vol2 == vol
                disks.extend(vol.dependencies)
        else:
            vol.logger.info('Outside any pool. Assuming exists.')
            vol.exists = True  # FIXME: Assume volume outside pool exists


def print_dot(resources, out=sys.stdout):
    """Print dot graph for resources."""
    dot = Resource.dotter
    dot.dot_out = out
    dot('digraph G')
    dot('{')
    dot('rankdir=LR;')
    dot('splines=false;')
    dot('nodesep=.05;')
    clusters = {}
    for res in resources:
        container = os.path.dirname(res.filename)
        cluster = clusters.setdefault(container, set())
        cluster.add(res)
    for container, cluster in clusters.items():
        dot('subgraph cluster%s {', Dotter.key2dot(container))
        for res in cluster:
            res.dot()
        dot('label="%s";', container)
        dot('color=gray;')
        dot('splines=false;')
        dot('}')

    for res in resources:
        for ref in res.dependencies:
            Resource.dotter('%s -> %s;', (Dotter.key2dot(res.filename), Dotter.key2dot(ref.filename)))
    dot('node [shape=box, fontsize=5, height=.05];')
    dot('}')


def resource_closure(resources):
    """Add references resources."""
    closure = set()
    while resources:
        res = resources.pop()
        closure.add(res)
        resources |= set(res.dependencies)
        resources -= closure
    return closure


def main():
    """Check if VMs are still valid."""
    parser = OptionParser(usage='Usage: %%prog [options] [uri]')
    parser.add_option(
        '-v', '--verbose',
        action='count', dest='verbose', default=0,
        help='Increase verbosity')
    parser.add_option(
        '-g', '--dot',
        action='store_true', dest='dot', default=False,
        help='Generate dot graph')
    parser.add_option(
        '-a', '--all',
        action='store_true', dest='show_all', default=False,
        help='Show all resources')
    parser.add_option(
        '-u', '--unused',
        action='store_true', dest='show_unused', default=False,
        help='Show unused resources')

    options, arguments = parser.parse_args()

    logging.basicConfig(level={
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG,
        5: logging.NOTSET,
    }.get(options.verbose, logging.NOTSET))
    try:
        url = arguments[0]
    except IndexError:
        if os.path.exists('/dev/kvm'):
            url = 'qemu:///system'
        else:
            parser.print_usage(sys.stderr)
            sys.exit(2)

    libvirt.registerErrorHandler(lambda f, ctx: None, None)
    conn = libvirt.open(url)
    try:
        # volumes first because this is more detailed
        check_storage_pools(conn)
        check_virtual_machines(conn)
        check_storage_volumes(conn)
    finally:
        conn.close()

    # Validate all resources
    for res in list(Resource.all.values()):
        res.check_valid()

    # Print all resources
    filtered = set()
    for res in Resource.all.values():
        if options.show_all or \
                options.show_unused and not res.used or \
                not res.valid:
            filtered.add(res)
            text = '// %s' % (res.console(),)
            print(text)

    if options.dot:
        if not options.show_all:
            filtered = resource_closure(filtered)
        print_dot(filtered)


if __name__ == '__main__':
    main()
# vim:set ts=4 sw=4 et:
