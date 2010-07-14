<?php

@%@BCWARNING=// @%@

/* Kolab Example (using Sieve) */
if ($GLOBALS['conf']['kolab']['enabled']) {
	$backends['kolab'] = array(
			'driver' => 'timsieved',
			'preferred' => '',
			'hordeauth' => 'full',
			'params' => array(
				'hostspec' => $GLOBALS['conf']['kolab']['imap']['server'],
				'logintype' => 'PLAIN',
				'port' => $GLOBALS['conf']['kolab']['imap']['sieveport'],
				'scriptname' => 'kmail-vacation.siv'
				),
			'script' => 'sieve',
			'scriptparams' => array()
	);
}
?>
