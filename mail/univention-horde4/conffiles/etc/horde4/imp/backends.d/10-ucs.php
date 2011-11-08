<?php

@%@BCWARNING=// @%@

$servers['cyrus'] = array(
    'name' => 'Cyrus IMAP Server',
    'hostspec'  => '@%@horde/imap/hostspec@%@',
    'hordeauth' => '@%@horde/imap/hordeauth@%@',
    'protocol'  => 'imap',
    'preferred' => true,
    'port'      => @%@horde/imap/port@%@,
    'secure'    => '@%@horde/imap/secure@%@',
    'quota'     => array(
        'driver' => '@%@horde/imap/quota/driver@%@',
        'params' => array(
            'userhierarchy' => '@%@horde/imap/quota/params/userhierarchy@%@',
        )
    ),
    'acl' => array(
        'driver' => '@%@horde/imap/acl/driver@%@',
    ),
);
