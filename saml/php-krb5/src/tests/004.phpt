--TEST--
Testing for working mutual authentication
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

$client->initPassword($client_principal, $client_password, array('tkt_life' => 360));

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

var_dump($cgssapi->initSecContext($server_principal, null, GSS_C_MUTUAL_FLAG, null, $token));
var_dump($sgssapi->acceptSecContext($token, $token2));
var_dump($cgssapi->initSecContext($server_principal, $token2, GSS_C_MUTUAL_FLAG, null, $token));

?>
--EXPECTF--
bool(false)
bool(true)
bool(true)
