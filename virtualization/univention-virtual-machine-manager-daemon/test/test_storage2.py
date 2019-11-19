#!/usr/bin/python2.7
# vim: set fileencoding=utf-8 backupcopy=auto sw=4 ts=4:
try:
	import pytest
except ImportError:
	exit(0)
from os.path import dirname, join

import univention
import univention.management.console.modules
univention.__path__.append(join(dirname(__file__), '../src/univention'))  # type: ignore
from univention.uvmm.protocol import Disk  # noqa E402
from univention.uvmm.storage import assign_disks, DISK_PREFIXES  # noqa E402


class D(Disk):
	def __init__(self, bus, dev, device='disk'):
		super(D, self).__init__()
		self.target_bus = bus
		self.target_dev = dev
		self.device = device


def test_none():
	disks = ()
	assign_disks(disks, {})
	assert disks == ()


@pytest.mark.parametrize('bus,dev', DISK_PREFIXES.iteritems())
def test_ide_old(bus, dev):
	disks = disk, = (D(bus, dev),)
	assign_disks(disks, {})
	assert disk.target_bus == bus
	assert disk.target_dev == dev


@pytest.mark.parametrize('device,bus,dev', [
	('floppy', 'fdc', 'fda'),
	('disk', 'ide', 'hda'),
	('cdrom', 'ide', 'hda'),
	('unknown', None, None),
])
def test_default_floppy(device, bus, dev):
	disks = disk, = (D(None, None, device),)
	assign_disks(disks, {})
	assert disk.target_bus == bus
	assert disk.target_dev == dev


def test_two():
	"""
	If the bus type is changed but the target name is kept, adding a new disk
	to the old bus assigned the taken name again.
	"""
	disks = disk1, disk2 = (
		D('virtio', 'hda'),
		D(None, None, 'disk'),
	)
	assign_disks(disks, {})
	assert disk1.target_bus == 'virtio'
	assert disk1.target_dev == 'hda'
	assert disk2.target_bus == 'ide'
	assert disk2.target_dev == 'hdb'


def test_many():
	"""a .. z, aa .. az, ba .. zz, aaa ..."""
	disks = [D('ide', None) for i in range(27)]
	assign_disks(disks, {})
	assert disks[0].target_dev == 'hda'
	assert disks[-2].target_dev == 'hdz'
	assert disks[-1].target_dev == 'hdaa'


def test_addr():
	disks = disk1, disk2 = (
		D('ide', 'hdb'),
		D('ide', None),
	)
	assign_disks(disks, {'ide': set((0,))})
	assert disk1.target_dev == 'hdb'
	assert disk2.target_dev == 'hdc'


if __name__ == '__main__':
	pass
