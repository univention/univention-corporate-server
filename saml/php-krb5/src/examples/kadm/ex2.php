<?php

$conn = new KADM5('test2/admin', 'test.keytab', true);
$princ = $conn->getPrincipal('test');
var_dump($princ->getPropertyArray());
$princ->setExpiryTime(time() + 60*60*24*100);
$princ->save();
echo "\n";
?>
