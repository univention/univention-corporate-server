--TEST--
Testing for basic GSSAPI context establishment
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

$orig_ktname = getenv("KRB5_KTNAME");
$orig_ccname = getenv("KRB5CCNAME");

$cgssapi->acquireCredentials($client, $client_principal, GSS_C_INITIATE);
$sgssapi->acquireCredentials($server);

$client_info = $cgssapi->inquireCredentials();
$server_info = $sgssapi->inquireCredentials();

var_dump($orig_ktname === getenv("KRB5_KTNAME"));
var_dump($orig_ccname === getenv("KRB5CCNAME"));

var_dump($client->isValid($client_info['lifetime_remain'] - 300));
var_dump($server->isValid($server_info['lifetime_remain'] - 300));

$token = '';

var_dump($cgssapi->initSecContext($server_principal, null, null, null, $token));
var_dump($sgssapi->acceptSecContext($token));



?>
--EXPECTF--
bool(true)
bool(true)
bool(true)
bool(true)
bool(true)
bool(true)
