<?php

$config = array(
	'realm' => 'FOREIGN',
	'admin_server' => 'kdc.foreign',
	'kadmind_port' => 1234
);

// need to specify the realm in principal,
// otherwise krb5.conf default realm is used
$conn = new KADM5('testpw/admin@FOREIGN', 'asdfgh', false, $config);


