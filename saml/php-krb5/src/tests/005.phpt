--TEST--
Testing for working credential delegation
--SKIPIF--
<?php 
if(!file_exists(dirname(__FILE__) . '/config.php')) { echo "skip config missing"; return; }
if(!include(dirname(__FILE__) . '/config.php')) return; 
?>
--FILE--
<?php
include(dirname(__FILE__) . '/config.php');
$client = new KRB5CCache();
if($use_config) {
	$client->setConfig(dirname(__FILE__) . '/krb5.ini');	
}

$client->initPassword($client_principal, $client_password, array('forwardable' => true , 'proxiable' => true));

$server = new KRB5CCache();
if($use_config) {
        $server->setConfig(dirname(__FILE__) . '/krb5.ini');
}

$server->initKeytab($server_principal, $server_keytab);

$cgssapi = new GSSAPIContext();
$sgssapi = new GSSAPIContext();

$cgssapi->acquireCredentials($client);
$sgssapi->acquireCredentials($server);

$token = '';
$token2 = '';
$prinicipal = '';
$time_rec = 0;
$ret_flags = '';
$deleg = new KRB5CCache();

var_dump($cgssapi->initSecContext($server_principal, null, GSS_C_DELEG_FLAG, null, $token));
var_dump($sgssapi->acceptSecContext($token, $token2, $principal, $ret_flags, $time_rec, $deleg));
var_dump(count($deleg->getEntries()));

$dgssapi = new GSSAPIContext();
$dgssapi->acquireCredentials($deleg, $principal, GSS_C_INITIATE);


$s2gssapi = new GSSAPIContext();
$s2gssapi->acquireCredentials($server);

$token = '';
$token2 = '';
$principal2 = '';

var_dump($dgssapi->initSecContext($server_principal, null, null, null, $token));
var_dump($s2gssapi->acceptSecContext($token, $token2, $principal2, $ret_flags, $time_rec, $deleg));
var_dump($principal2 === $principal);

?>
--EXPECTF--
bool(true)
bool(true)
int(1)
bool(true)
bool(true)
bool(true)
