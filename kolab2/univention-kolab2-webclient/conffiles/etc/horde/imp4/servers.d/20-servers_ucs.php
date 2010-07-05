<?php
@%@BCWARNING=// @%@

if ($GLOBALS['conf']['kolab']['enabled']) {
	if ($useDefaults) {
        $imapParams = array(
			'hostspec' => $GLOBALS['conf']['kolab']['imap']['server'],
			'port'     => $GLOBALS['conf']['kolab']['imap']['port'],
            'protocol' => 'imap/notls/novalidate-cert',
        );
	}
    $servers['kolab'] = array(
        'name' => 'Kolab Cyrus IMAP Server',
        'hordeauth' => 'full',
        'server'     => $imapParams['hostspec'],
        'port'       => $imapParams['port'],
        'protocol'   => $imapParams['protocol'],
        'maildomain' => $GLOBALS['conf']['kolab']['imap']['maildomain'],
        'realm' => '',
        'preferred' => '',
        'quota' => array(
            'driver' => 'imap',
            'params' => array(
                'userhierarchy' => 'user.'
            )
        ),
        'acl' => array(
            'driver' => 'rfc2086',
        ),
    );
}
?>
