--TEST--
Text::Flowed tests
--FILE--
<?php

require dirname(__FILE__) . '/../Text/Flowed.php';
require dirname(__FILE__) . '/../../Util/String.php';
require dirname(__FILE__) . '/../../Util/Util.php';

$flowed = &new Text_Flowed("Hello, world!");
echo $flowed->toFixed();

echo "\n";

$flowed = &new Text_Flowed("Hello, \nworld!");
echo $flowed->toFixed();
$flowed = &new Text_Flowed("Hello,\n  world!");
echo $flowed->toFixed();

echo "\n";

$flowed = &new Text_Flowed("> Hello, world!");
echo $flowed->toFlowed();

echo "\n";

$flowed = &new Text_Flowed("From");
echo $flowed->toFlowed();

?>
--EXPECT--
Hello, world!

Hello, world!
Hello,
world!

>> Hello, world!

> From
