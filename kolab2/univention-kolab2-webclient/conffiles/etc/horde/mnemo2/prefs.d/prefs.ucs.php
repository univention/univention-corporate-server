<?php

@%@BCWARNING=// @%@

// Make sure that constants are defined.
@define('MNEMO_BASE', '/usr/share/horde3/mnemo/');
require_once MNEMO_BASE . '/lib/Mnemo.php';

// default notepad
// Set locked to true if you don't want users to have multiple notepads.
$_prefs['default_notepad'] = array(
    'value' => Auth::getAuth() ? Auth::getAuth() : 0,
    'locked' => false,
    'shared' => true,
    'type' => 'implicit'
);
?>
