<?php

$ticket = new KRB5CCache();
$ticket->initPassword('test', 'foobar');
var_dump($ticket);

$ticket2 = new KRB5CCache();
$ticket2->initKeytab('test2', 'test.keytab');
var_dump($ticket2);


$conn = new KADM5('test2/admin', 'test.keytab', true);

$princ = new KADM5Principal("test");
var_dump($princ);

try {
	var_dump($princ->changePassword('footest'));
	die("A password change on a new entry succeeded");
} catch (Exception $e) {
}

echo "\nListing prinicpals:\n";

foreach($conn->getPrincipals() as $princ) {
	echo " +  $princ\n";
}


echo "\nGet principal testuser\n";
$princ2 = $conn->getPrincipal('testuser');
var_dump($princ2);
var_dump($princ2->load());
var_dump($princ2);



try {
var_dump($princ2->changePassword('fooobar'));
} catch(Exception $e) {

}

?>
