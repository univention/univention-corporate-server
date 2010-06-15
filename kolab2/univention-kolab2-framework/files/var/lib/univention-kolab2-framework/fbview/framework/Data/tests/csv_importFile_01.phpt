--TEST--
Simple CSV files
--FILE--
<?php

require 'Horde.php';
require 'Horde/Data.php';

$vcs = Horde_Data::singleton('csv');
var_dump($vcs->importFile(dirname(__FILE__) . '/simple_dos.csv', false, '', '', 4));
var_dump($vcs->importFile(dirname(__FILE__) . '/simple_unix.csv', false, '', '', 4));
var_dump($vcs->importFile(dirname(__FILE__) . '/simple_dos.csv', true, '', '', 4));
var_dump($vcs->importFile(dirname(__FILE__) . '/simple_unix.csv', true, '', '', 4));

?>
--EXPECT--
array(2) {
  [0]=>
  array(4) {
    [0]=>
    string(3) "one"
    [1]=>
    string(3) "two"
    [2]=>
    string(10) "three four"
    [3]=>
    string(6) "five
"
  }
  [1]=>
  array(4) {
    [0]=>
    string(3) "six"
    [1]=>
    string(5) "seven"
    [2]=>
    string(10) "eight nine"
    [3]=>
    string(6) " ten
"
  }
}
array(2) {
  [0]=>
  array(4) {
    [0]=>
    string(3) "one"
    [1]=>
    string(3) "two"
    [2]=>
    string(10) "three four"
    [3]=>
    string(5) "five
"
  }
  [1]=>
  array(4) {
    [0]=>
    string(3) "six"
    [1]=>
    string(5) "seven"
    [2]=>
    string(10) "eight nine"
    [3]=>
    string(5) " ten
"
  }
}
array(1) {
  [0]=>
  array(4) {
    ["one"]=>
    string(3) "six"
    ["two"]=>
    string(5) "seven"
    ["three four"]=>
    string(10) "eight nine"
    ["five
"]=>
    string(6) " ten
"
  }
}
array(1) {
  [0]=>
  array(4) {
    ["one"]=>
    string(3) "six"
    ["two"]=>
    string(5) "seven"
    ["three four"]=>
    string(10) "eight nine"
    ["five
"]=>
    string(5) " ten
"
  }
}