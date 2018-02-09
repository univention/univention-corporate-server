<?php
$conn = new KADM5('test2/admin', 'test.keytab', true);

$policy = null;
try {
	$policy = $conn->getPolicy('some');
} catch (Exception $e) {
	$newpol = new KADM5Policy('some');
	$conn->createPolicy($newpol);
	$policy = $conn->getPolicy('some');
}

var_dump($policy->getPropertyArray());

//$policy->setMinPasswordLife(1000);
//$policy->setMaxPasswordLife(6*31*24*60*60);
//$policy->setMinPasswordClasses(2);
//$policy->setHistoryNum(5);
//$policy->setMinPasswordLength(8);

$policy->save();

$princ = $conn->getPrincipal('testuser');
var_dump($princ->getPolicy());
$princ->clearPolicy();
$princ->save();

$policy->load();
var_dump($policy->getPropertyArray());


try {
	$policy = $conn->getPolicy('testing');
	$policy->delete();
} catch (Exception $e) {
}

$newpol = new KADM5Policy('testing');
$newpol->setMinPasswordLife(500023523);
$newpol->setHistoryNum(10);
echo $newpol->getName();
$conn->createPolicy($newpol);

var_dump($newpol->getPropertyArray());


echo "\nAvailable policies\n";
foreach($conn->getPolicies() as $policy) {
	$usage = $conn->getPolicy($policy)->getReferenceCount();
	echo " + $policy ($usage)\n";
}


$newpol->delete();


?>
