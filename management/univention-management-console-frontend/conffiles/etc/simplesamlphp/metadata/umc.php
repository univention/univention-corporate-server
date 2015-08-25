<?php
#@%@UCRWARNING=# @%@
@!@
from subprocess import call, Popen, PIPE
from tempfile import NamedTemporaryFile
import sys
sys.path.insert(0, '/usr/share/univention-management-console/saml/')
from sp import CONFIG
from saml2.metadata import create_metadata_string

metadata = create_metadata_string('/usr/share/univention-management-console/saml/sp.py', None, valid='4', cert=None, keyfile=None, mid=None, name=None, sign=False)

php_code = '''<?php

set_error_handler(function($errno, $errstr, $errfile, $errline) {
    throw new ErrorException($errstr, 0, $errno, $errfile, $errline);
});

$entityid = $argv[1];
$_SERVER['REQUEST_URI'] = $entityid;
$_SERVER['REQUEST_METHOD'] = 'POST';
$_POST['xmldata'] = file_get_contents("php://stdin");
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
	process = Popen(['/usr/bin/php', temp.name, CONFIG['entityid']], stdout=PIPE, stderr=PIPE, stdin=PIPE)
	stdout, stderr = process.communicate(metadata)
	if process.returncode != 0:
		sys.stderr.write(stderr)
		sys.exit(1)
	sys.stdout.write(stdout)
@!@
