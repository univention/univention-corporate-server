<?php
$conn = new KADM5('test2/admin', 'test.keytab', true);


try {
	$policy = $conn->getPolicy('testing');
	$policy->delete();
} catch (Exception $e) {
}

$newpol = new KADM5Policy('testing');
$newpol->setMinPasswordLength(10);
$newpol->setMinPasswordClasses(3);
$conn->createPolicy($newpol);


try {
	$princ = $conn->getPrincipal('testuser');
	$princ->delete();
} catch (Exception $e) {
	echo $e;
}

$princ = new KADM5Principal('testuser');
$conn->createPrincipal($princ , 'testpass');

// either of this should work
//$princ->setPolicy($conn->getPolicy('testing'));
$princ->setPolicy($newpol);
//$princ->setPolicy('testing');

$princ->save();

var_dump($princ);
