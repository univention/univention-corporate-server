import argparse
import subprocess
import xml.etree.ElementTree as ET


def parse_args():
	parser = argparse.ArgumentParser(description='Tool for extracting the /var/log/ folder from a virtual machine.')
	parser.add_argument('--dest', dest='dest', help='Destination to copy the log directory to.')
	parser.add_argument('--server', dest='server', required=True, help='The server the virtual machine is running on.')
	parser.add_argument('name', help='The IP address which is used by the virtual machine.')
	return parser.parse_args()


class LogExtractor(object):
	def __init__(self):
		self.args = parse_args()
		self.log_dir = self.args.name + '_log'
		self.xml_name = self.args.name + '.xml'

	def extract_logs(self):
		self.copy_logs_out_of_vm()
		self.copy_over_logs_from_server()
		self.clean_up_on_server()

	def copy_logs_out_of_vm(self):
		disk_image = self.get_primary_disk_image()
		self.execute_through_ssh('rm -rf %s' % (self.log_dir,))
		#self.execute_through_ssh(
		#	'virt-copy-out -a %s /var/log %s' % (disk_image, self.log_dir)
		#)
		# FIXME: This is just temporary, because virt-copy-out isn't installed yet.
		self.execute_through_ssh('mkdir %s; touch %s/test' % (self.log_dir, self.log_dir))

	def get_primary_disk_image(self):
		self.execute_through_ssh(
			'virsh dumpxml %s > %s' % (self.args.name, self.xml_name)
		)
		self.copy_through_ssh('%s:%s' % (self.args.server, self.xml_name), '.')
		disk_image_path = self.extract_primary_disk_from_xml(self.xml_name)
		return disk_image_path

	def copy_over_logs_from_server(self):
		self.copy_through_ssh('%s:%s' % (self.args.server, self.log_dir), '.')

	def clean_up_on_server(self):
		self.execute_through_ssh('rm -r %s' % (self.log_dir))
		self.execute_through_ssh('rm %s' % (self.xml_name,))

	def extract_primary_disk_from_xml(self, xml_file):
		tree = ET.parse(xml_file)
		root = tree.getroot()
		disks = root.find('devices').findall('disk')
		hdds = filter(lambda disk: disk.attrib['device'] == 'disk', disks)
		primary_hdd_image = hdds[0].find('source').attrib['file']
		return primary_hdd_image

	def execute_through_ssh(self, command):
		return_code = subprocess.call((
			'ssh',
			'%s' % (self.args.server,),
			command
		))
		if return_code > 0:
			raise RuntimeError('Command on %s exited with return code %s: %s' % (self.args.server, return_code, command))

	def copy_through_ssh(self, source_file, target_file):
		return_code = subprocess.call((
			'scp',
			'-r',
			source_file, target_file
		))
		if return_code > 0:
			raise RuntimeError("Trying to copy '%s' to '%s' failed with return code %s." % (source_file, target_file, return_code))

if __name__ == '__main__':
	extractor = LogExtractor()
	extractor.extract_logs()
