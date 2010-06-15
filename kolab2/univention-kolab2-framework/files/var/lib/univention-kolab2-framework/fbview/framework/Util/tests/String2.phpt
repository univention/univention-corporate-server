--TEST--
zh_TW String:: tests
--FILE--
<?php

require dirname(__FILE__) . '/../String.php';

echo String::length('Welcome', 'zh_TW'). "\n";
echo String::length('Åwªï', 'zh_TW') . "\n";

?>
--EXPECT--
7
4
