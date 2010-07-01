<?php

require_once 'Horde/Kolab.php';

if (!is_callable('Kolab', 'getServer')) {
    $server = $GLOBALS['conf']['kolab']['imap']['server'];
} else {
    $server = Kolab::getServer('imap');
}

$servers['kolab'] = array(
    'name' => 'Kolab Cyrus IMAP Server',
    'server' => $server,
    'hordeauth' => 'full',
    'protocol' => 'imap/notls/novalidate-cert',
    'port' => $GLOBALS['conf']['kolab']['imap']['port'],
    'maildomain' => $GLOBALS['conf']['kolab']['imap']['maildomain'],
    'realm' => '',
    'preferred' => '',
    'quota' => array(
        'driver' => 'imap',
        'params' => array('hide_quota_when_unlimited' => true),
    ),
    'acl' => array(
        'driver' => 'rfc2086',
    ),
);
