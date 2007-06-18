<?php

require_once './setup.inc';
require_once 'DB.php';

if (!defined('DRIVER_DSN') || DRIVER_DSN == '') {
    die('skip DSN not defined');
}

$db =& DB::connect(DRIVER_DSN);
if (DB::isError($db)) {
    die("skip $db->message");
}

?>
