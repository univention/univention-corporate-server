<?php
// Warning: This file is auto-generated and might be overwritten by
//          univention-baseconfig.
//          Please edit the following file instead:
// Warnung: Diese Datei wurde automatisch generiert und kann durch
//          univention-baseconfig überschrieben werden.
//          Bitte bearbeiten Sie an Stelle dessen die folgende Datei:
//
// 	/etc/univention/templates/files/etc/horde/imp4/servers.php
//

/* Any entries whose key value ('foo' in $servers['foo']) begin with '_'
 * (an underscore character) will be treated as prompts, and you won't be
 * able to log in to them. The only property these entries need is 'name'.
 * This lets you put labels in the list, like this example: */
$servers['_prompt'] = array(
    'name' => _("Choose a mail server:")
);

if ($GLOBALS['conf']['kolab']['enabled']) {
    $servers['kolab'] = array(
        'name' => 'Kolab Cyrus IMAP Server',
        'server' => $GLOBALS['conf']['kolab']['imap']['server'],
        'hordeauth' => 'full',
        'protocol' => 'imap/notls/novalidate-cert',
        'port' => $GLOBALS['conf']['kolab']['imap']['port'],
        'maildomain' => $GLOBALS['conf']['kolab']['imap']['maildomain'],
        'realm' => '',
        'preferred' => '',
        'quota' => array(
            'driver' => 'cyrus',
            'params' => array(
                'userhierarchy' => 'user.'
            )
        ),
        'acl' => array(
            'driver' => 'rfc2086',
        ),
    );
}
