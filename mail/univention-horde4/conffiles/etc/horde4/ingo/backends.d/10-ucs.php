<?php

@%@BCWARNING=// @%@

$backends['imap']['disabled'] = @%@horde/ingo/imap/disabled@%@;

$backends['sieve'] = array(
    'disabled' => false,
    'transport' => 'timsieved',
    'hordeauth' => 'full',
    'params' => array(
        // Hostname of the timsieved server
        'hostspec' => '@%@horde/imap/hostspec@%@',
        // Login type of the server
        'logintype' => 'PLAIN',
        // Enable/disable TLS encryption
        'usetls' => true,
        // Port number of the timsieved server
        'port' => @%@horde/imap/sieve/port@%@,
        // Name of the sieve script
        'scriptname' => 'default',
    ),
    'script' => 'sieve',
    'scriptparams' => array(),
    'shares' => false
);

?>
