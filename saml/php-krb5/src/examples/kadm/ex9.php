<?php

$config = array(
	'realm' => 'SPRINGFIELD',
	'admin_server' => 'homer.springfield'
);

// need to specify the realm in principal,
// otherwise krb5.conf default realm is used
$conn = new KADM5('testpw/admin@SPRINGFIELD', 'asdfgh', false, $config);

$princ = $conn->getPrincipal("testuser@SPRINGFIELD");
var_dump($princ->getAttributes());
var_dump($princ->getAuxAttributes());
var_dump($princ->getPropertyArray());
var_dump($princ->getTLData());
echo "Before\n";
$princ->setTLData(array(new KADM5TLData(KRB5_TL_DB_ARGS, "tktpolicy=\0")));
foreach ( $princ->getTLData() as $tldata) {
	echo $tldata->getType() . ":" . $tldata->getData() . "\n";
}
$princ->save();

echo "After\n";
var_dump($princ->getPropertyArray());

foreach ( $princ->getTLData() as $tldata) {
	echo $tldata->getType() . ":" . $tldata->getData() . "\n";
}
