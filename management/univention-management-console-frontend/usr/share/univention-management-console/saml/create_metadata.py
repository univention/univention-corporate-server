#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Management Console Web Server
# SAML metadata creation
#
# Copyright 2015 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

from subprocess import call, Popen, PIPE
from tempfile import NamedTemporaryFile
import sys
sys.path.insert(0, '/usr/share/univention-management-console/saml/')
from sp import CONFIG


def exit(*args):
	raise ValueError(*args)


php_code = '''<?php
$entityid = '%s';
$_SERVER['REQUEST_URI'] = $entityid;
$_SERVER['REQUEST_METHOD'] = 'POST';
$_POST['xmldata'] = file_get_contents(str_replace('https://', 'http://', $entityid));
chdir('/usr/share/simplesamlphp/www/admin');
ob_start();
require_once('./metadata-converter.php');
ob_end_clean();
print("<?php\n");
print($output["saml20-sp-remote"]);
print("array_merge(\$metadata['$entityid'], array(
	'simplesaml.nameidattribute' => 'uid',
	'simplesaml.attributes' => TRUE,
	'attributes' => array('uid'),
	'description' => 'Univention Management Console SAML2.0 Service Provider',
	'OrganizationName' => 'Univention Management Console SAML2.0 Service Provider',
));");
''' % (CONFIG['entityid'],)


with NamedTemporaryFile() as temp:
	temp.write(php_code)
	temp.flush()
	process = Popen(['/usr/bin/php', temp.name], stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	if process.returncode != 0:
		sys.stderr.write(stderr)
		sys.exit(1)
	with open('/usr/share/simplesamlphp/config/metadata.d/UMC.php', 'w') as fd:
		fd.write(stdout)


call('wget --no-check-certificate https://$(hostname -f)/simplesamlphp/saml2/idp/metadata.php -O /usr/share/univention-management-console/saml/idp/simplesamlphp.xml', shell=True) and exit('Could not download IDP metadata')
call('ucr commit /etc/pam.d/univention-management-console', shell=True) and exit('Could not write UMC PAM configuration')
#call('invoke-rc.d univention-management-console-web-server restart', shell=True) and exit('Could not restart UMC-Web-Server')
#call('invoke-rc.d univention-management-console-server restart', shell=True) and exit('Could not restart UMC-server')
