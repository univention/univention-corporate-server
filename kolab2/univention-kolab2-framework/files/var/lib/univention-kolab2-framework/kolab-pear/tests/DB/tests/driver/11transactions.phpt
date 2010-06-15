--TEST--
DB_driver::transaction test
--SKIPIF--
<?php chdir(dirname(__FILE__)); require_once './skipif.inc'; ?>
--FILE--
<?php
require_once './mktable.inc';
require_once '../transactions.inc';
?>
--EXPECT--
after autocommit: bing one.  ops=ok
before commit: bing one two three.  ops=ok
after commit: bing one two three.  ops=ok
before rollback: bing one two three four five.  ops=ok
after rollback: bing one two three.  ops=ok
before autocommit+rollback: bing one two three six seven.  ops=ok
after autocommit+rollback: bing one two three six seven.  ops=ok
testing that select doesn't disturbe opcount: ok
