<?php

define('HORDE_BASE', dirname(__FILE__) . '/../../..');
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/Mobile.php';

$m = &new Horde_Mobile();
$m->add(new Horde_Mobile_text('This application (MIMP) is not properly configured. Please contact your system administrator.'));
$m->display();
