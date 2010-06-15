--TEST--
Simple String:: tests
--FILE--
<?php

require dirname(__FILE__) . '/../String.php';

echo String::length('Welcome', 'en_US'). "\n";
echo String::length('Welcome', 'zh_TW'). "\n";

echo String::upper('abCDefG', true, 'en_US') . "\n";
echo String::lower('abCDefG', true, 'en_US') . "\n";
echo String::upper('abCDefG', true, 'zh_TW') . "\n";
echo String::lower('abCDefG', true, 'zh_TW') . "\n";

?>
--EXPECT--
7
7
ABCDEFG
abcdefg
ABCDEFG
abcdefg
