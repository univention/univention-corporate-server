<?php

@%@BCWARNING=// @%@

// sent mail folder
$_prefs['sent_mail_folder'] = array(
    'value' => Horde_String::convertCharset('@%@horde/folder/sent@%@', 'UTF-8', 'UTF7-IMAP')
);

// drafts folder
$_prefs['drafts_folder'] = array(
    'value' => Horde_String::convertCharset('@%@horde/folder/drafts@%@', 'UTF-8', 'UTF7-IMAP')
);

// trash folder
$_prefs['trash_folder'] = array(
    'value' => Horde_String::convertCharset('@%@horde/folder/trash@%@', 'UTF-8', 'UTF7-IMAP')
);

// spam folder
$_prefs['spam_folder'] = array(
    'value' => Horde_String::convertCharset('@%@horde/folder/spam@%@', 'UTF-8', 'UTF7-IMAP')
);

$_prefs['subscribe']['value'] = @%@horde/subscribe/value@%@;


?>
