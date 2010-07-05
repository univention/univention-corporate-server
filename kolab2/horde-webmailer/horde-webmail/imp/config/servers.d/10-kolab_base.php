<?php

$servers = array();

if (isset($_SESSION['imp']['user']) && isset($_SESSION['imp']['pass'])) {
    require_once 'Horde/Kolab/Session.php';
    $session = Horde_Kolab_Session::singleton($_SESSION['imp']['user'],
                                              array('password' => Secret::read(Secret::getKey('imp'), $_SESSION['imp']['pass'])));
    $imapParams = $session->getImapParams();
    if (is_a($imapParams, 'PEAR_Error')) {
        $useDefaults = true;
    } else {
        $useDefaults = false;
    }
    $_SESSION['imp']['uniquser'] = $session->user_mail;
 } else {
    $useDefaults = true;
 }

if ($useDefaults) {
    require_once 'Horde/Kolab.php';
    
    if (is_callable('Kolab', 'getServer')) {
        $server = Kolab::getServer('imap');
        if (is_a($server, 'PEAR_Error')) {
            $useDefaults = true;
        } else {
            $useDefaults = false;
        }
    } else {
        $useDefaults = true;
    }
    
    if ($useDefaults) {
        $server = $GLOBALS['conf']['kolab']['imap']['server'];
    }
    
    $imapParams = array(
        'hostspec' => $server,
        'port'     => $GLOBALS['conf']['kolab']['imap']['port'],
        'protocol' => 'imap/novalidate-cert'
    );
 }

$servers['kolab'] = array(
    'name'       => 'Kolab Cyrus IMAP Server',
    'hordeauth'  => 'full',
    'server'     => $imapParams['hostspec'],
    'port'       => $imapParams['port'],
    'protocol'   => $imapParams['protocol'],
    'maildomain' => $GLOBALS['conf']['kolab']['imap']['maildomain'],
    'realm'      => '',
    'preferred'  => '',
    'quota'      => array(
        'driver' => 'imap',
        'params' => array('hide_quota_when_unlimited' => true),
    ),
    'acl'        => array(
        'driver' => 'rfc2086',
    ),
    'login_tries' => 1,
);
