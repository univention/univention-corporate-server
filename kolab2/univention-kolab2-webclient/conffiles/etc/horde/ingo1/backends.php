<?php

@%@BCWARNING=// @%@

/**
 * $Horde: ingo/config/backends.php.dist,v 1.41 2006/12/16 00:24:40 chuck Exp $
 *
 * Ingo works purely on a preferred mechanism for server selection. There are
 * a number of properties that you can set for each backend:
 *
 * driver:       The Ingo_Driver driver to use to get the script to the
 *               backend server. Valid options:
 *                   'null'       --  No backend server
 *                   'timsieved'  --  Cyrus timsieved server
 *                   'vfs'        --  Use Horde VFS
 *                   'ldap'       --  LDAP server
 *
 * preferred:    This is the field that is used to choose which server is
 *               used. The value for this field may be a single string or an
 *               array of strings containing the hostnames to use with this
 *               server.
 *
 * hordeauth:    Ingo uses the current logged in username and password. If
 *               you want the full username@realm to be used to connect then
 *               set this to 'full' otherwise set this to true and just the
 *               username will be used to connect to the driver.
 *
 * params:       An array containing any additional information that the
 *               Ingo_Driver class needs.
 *
 * script:       The type of Ingo_Script driver this server uses.
 *               Valid options:
 *                   'imap'      --  IMAP client side filtering
 *                   'maildrop'  --  Maildrop scripts
 *                   'procmail'  --  Procmail scripts
 *                   'sieve'     --  Sieve scripts
 *
 * scriptparams: An array containing any additional information that the
 *               Ingo_Script driver needs.
 *
 * shares:       Some drivers support sharing filter rules with other users.
 *               Users can then configure filters for each other if they
 *               give them permissions to do so. If you want to enable this
 *               feature, you need to set this parameter to true.
 */

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

