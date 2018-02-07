<?php


$princ = new KRB5CCache();
$princ->initPassword('test1', 'foo123');
var_dump($princ->getEntries());
?>
