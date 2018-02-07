--TEST--
Testing for usable ticket acqusition
--SKIPIF--
<?php 
if(!file_exists(dirname(__FILE__) . '/config.php')) { echo "skip config missing"; return; }
if(!include(dirname(__FILE__) . '/config.php')) return; 
?>
--FILE--
<?php
include(dirname(__FILE__) . '/config.php');
$ccache = new KRB5CCache();
if($use_config) {
	$ccache->setConfig(dirname(__FILE__) . '/krb5.ini');	
}

var_dump(count($ccache->getEntries()));
$ccache->initPassword($client_principal, $client_password, array('tkt_life' => 360));
var_dump(count($ccache->getEntries())); // should contain a TGT
list($tgt) = $ccache->getEntries();
var_dump($ccache->isValid());
var_dump($ccache->isValid(720));
$ccache->save(dirname(__FILE__) . '/ccache.tmp');
$ccache->save('FILE:' . dirname(__FILE__) . '/ccache2.tmp');
var_dump(file_exists(dirname(__FILE__) . '/ccache.tmp'));
var_dump(file_exists(dirname(__FILE__) . '/ccache2.tmp'));
@unlink(dirname(__FILE__) . '/ccache2.tmp');
$ccache2 = new KRB5CCache();
$ccache2->open('FILE:' . dirname(__FILE__) . '/ccache.tmp');
var_dump(in_array($tgt,$ccache2->getEntries()));
@unlink(dirname(__FILE__) . '/ccache.tmp');

$ccache3 = new KRB5CCache();
$ccache3->initKeytab($server_principal, $server_keytab);
var_dump(count($ccache->getEntries()));
var_dump($ccache->isValid());

?>
--EXPECTF--
int(0)
int(1)
bool(true)
bool(false)
bool(true)
bool(true)
bool(true)
int(1)
bool(true)
