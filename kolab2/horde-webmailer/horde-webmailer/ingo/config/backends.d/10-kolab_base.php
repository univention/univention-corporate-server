<?php

$backends = array();

require_once 'Horde/Kolab.php';

if (!is_callable('Kolab', 'getServer')) {
    $server = $GLOBALS['conf']['kolab']['imap']['server'];
 } else {
    $server = Kolab::getServer('imap');
 }

$backends['kolab'] = array(
    'driver' => 'timsieved',
    'preferred' => '',
    'hordeauth' => 'full',
    'params' => array(
        'hostspec' => $server,
        'logintype' => 'PLAIN',
        'usetls' => false,
        'port' => $GLOBALS['conf']['kolab']['imap']['sieveport'],
        'scriptname' => 'kmail-vacation.siv'
    ),
    'script' => 'sieve',
    'scriptparams' => array(),
    'shares' => false
);
