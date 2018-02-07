--TEST--
Testing for GSSAPI wrap/unwrap/Mic code
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

$cgssapi->acquireCredentials($client, $client_principal, GSS_C_INITIATE);
$sgssapi->acquireCredentials($server, $server_principal, GSS_C_ACCEPT);

$token = '';

var_dump($cgssapi->initSecContext($server_principal, null, null, null, $token));
var_dump($sgssapi->acceptSecContext($token));



$message = base64_decode('RKkOxMZ64GwEdZf+vZ6bp4mVQ4E=');
$mic = $sgssapi->getMic($message);
var_dump($cgssapi->verifyMic($message, $mic));
var_dump(@$cgssapi->verifyMic($message, $mic . '-'));
var_dump(@$cgssapi->verifyMic($message . '-', $mic));

$enc = '';
var_dump($sgssapi->wrap($message, $enc,true));
var_dump($enc !== $message);
var_dump($cgssapi->unwrap($enc, $decoded));
var_dump($decoded === $message);
var_dump($cgssapi->wrap($message, $enc));
var_dump($enc !== $message);
var_dump($sgssapi->unwrap($enc, $decoded));
var_dump($decoded === $message);

?>
--EXPECTF--
bool(true)
bool(true)
bool(true)
bool(false)
bool(false)
bool(true)
bool(true)
bool(true)
bool(true)
bool(true)
bool(true)
bool(true)
bool(true)
