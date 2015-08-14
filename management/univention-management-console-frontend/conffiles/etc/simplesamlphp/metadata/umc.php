<?php
#@%@UCRWARNING=# @%@
@!@
from subprocess import call, Popen, PIPE
from tempfile import NamedTemporaryFile
import sys
sys.path.insert(0, '/usr/share/univention-management-console/saml/')
from sp import CONFIG


php_code = '''<?php
$entityid = $argv[1];
$_SERVER['REQUEST_URI'] = $entityid;
$_SERVER['REQUEST_METHOD'] = 'POST';
$_POST['xmldata'] = file_get_contents(str_replace('https://', 'http://', $entityid));  # FIXME: can we use https?
chdir('/usr/share/simplesamlphp/www/admin');
ob_start();
require_once('./metadata-converter.php');
ob_end_clean();
print($output["saml20-sp-remote"]);
print("array_merge(\$metadata['$entityid'], array(
	'simplesaml.nameidattribute' => 'uid',
	'simplesaml.attributes' => TRUE,
	'attributes' => array('uid'),
	'description' => 'Univention Management Console SAML2.0 Service Provider',  # TODO:
	'OrganizationName' => 'Univention Management Console SAML2.0 Service Provider',
));");
'''

with NamedTemporaryFile() as temp:
	temp.write(php_code)
	temp.flush()
	process = Popen(['/usr/bin/php', temp.name, CONFIG['entityid']], stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	if process.returncode != 0:
		sys.stderr.write(stderr)
		sys.exit(1)
	sys.stdout.write(stdout)
@!@
