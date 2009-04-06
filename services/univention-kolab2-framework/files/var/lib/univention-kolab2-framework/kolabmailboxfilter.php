#!/usr/bin/php
<?php
/*
 *  Copyright (c) 2004,2005 Klaraelvdalens Datakonsult AB
 *
 *    Writen by Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 *
 *  This  program is free  software; you can redistribute  it and/or
 *  modify it  under the terms of the GNU  General Public License as
 *  published by the  Free Software Foundation; either version 2, or
 *  (at your option) any later version.
 *
 *  This program is  distributed in the hope that it will be useful,
 *  but WITHOUT  ANY WARRANTY; without even the  implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 *  General Public License for more details.
 *
 *  You can view the  GNU General Public License, online, at the GNU
 *  Project's homepage; see <http://www.gnu.org/licenses/gpl.html>.
 */

/* Fix include_path to pick up our modified Horde classes */
$include_path = ini_get('include_path');
ini_set( 'include_path', 
	 '.:/usr/share/php/PEAR:'.$include_path);

require_once 'PEAR.php';
require_once '/var/lib/univention-kolab2-framework/kolabfilter/misc.php';
require_once '/var/lib/univention-kolab2-framework/kolabfilter/kolabmailtransport.php';

// Load our configuration file
$params = array();
require_once '/etc/kolab2/resmgr.conf';
init();

define( 'TMPDIR', '/var/lib/univention-kolab2-framework/filter' );
define( 'EX_TEMPFAIL', 75 );
define( 'EX_UNAVAILABLE', 69 );

// Temp file for storing the message
$tmpfname = tempnam( TMPDIR, 'IN.' );
$tmpf = fopen($tmpfname, "w");

// Cleanup function
function cleanup() {
  global $tmpfname;
  file_exists($tmpfname) && unlink($tmpfname);
}
register_shutdown_function( 'cleanup' );

$options = parse_args( array( 's', 'r', 'c', 'h' ), $_SERVER['argv']); //getopt("s:r:c:h:");

if (!array_key_exists('r', $options) || !array_key_exists('s', $options)) {
    fwrite(STDOUT, "Usage is $argv[0] -s sender@domain -r recip@domain\n");
    exit(EX_TEMPFAIL);
}

$sender = strtolower($options['s']);
$recipients = $options['r'];
$client_address = $options['c'];
$fqhostname = strtolower($options['h']);

// make sure recipients is an array
if( !is_array($recipients) ) {
  $recipients = array( $recipients );
}

// make recipients lowercase
for( $i = 0; $i < count($recipients); $i++ ) {
  $recipients[$i] = strtolower($recipients[$i]);
}

myLog("Kolabmailboxfilter starting up, sender=$sender, recipients=".join(',', $recipients)
      .", client_address=$client_address", RM_LOG_DEBUG);

$ical = false;
$add_headers = array();
$headers_done = false;
$from = false;
while (!feof(STDIN)) {
  $buffer = fgets(STDIN, 8192);
  $line = rtrim( $buffer, "\r\n");
  if( $line == '' ) {
    // Done with headers
    $headers_done = true;
  } else if( !$headers_done && $params['allow_sender_header'] && eregi( '^Sender: (.*)', $line, $regs ) ) {
    $from = strtolower($regs[1]);
  } else if( !$headers_done && !$from && eregi( '^From: (.*)', $line, $regs ) ) {
    $from = strtolower($regs[1]);
  } else if( eregi( '^Content-Type: text/calendar', $line ) ) {
    myLog("Found iCal data in message", RM_LOG_DEBUG);    
    $ical = true;
  }
  if( fwrite($tmpf, $buffer) === false ) {
    exit(EX_TEMPFAIL);
  }
}
fclose($tmpf);
if( $ical ) {
  require_once '/var/lib/univention-kolab2-framework/kolabfilter/resmgr.php';
  $newrecips = array();
  foreach( $recipients as $recip ) {
    myLog("Calling resmgr_filter( $sender, $recip, $tmpfname )", RM_LOG_DEBUG);
    $rc = resmgr_filter( $fqhostname, $sender, $recip, $tmpfname );
    if( PEAR::isError( $rc ) ) {
      fwrite(STDOUT,"Filter failed: ".$rc->getMessage()."\n");
      exit(EX_TEMPFAIL);
    } else if( $rc === true ) {
      $newrecips[] = $recip;
    }
  }
  $recipients = $newrecips;
  $add_headers[] = "X-Kolab-Scheduling-Message: TRUE";
} else {
  $add_headers[] = "X-Kolab-Scheduling-Message: FALSE";
}

// Check if we still have recipients
if( empty($recipients) ) exit(0);

$tmpf = fopen($tmpfname,"r");

// Cyrus Murder extension
$frontend_interface = chop(shell_exec('/usr/sbin/univention-config-registry get mail/cyrus/murder/frontend/interface'));
if ($frontend_interface != '') {
$bind_host = chop(shell_exec("/usr/sbin/univention-config-registry get interfaces/$frontend_interface/address"));
$pass = chop(shell_exec('cat /etc/cyrus.secret'));
} else {
  $bind_host = 'localhost';
}

if ($bind_host != 'localhost') {
	$lmtp = new KolabLMTP($bind_host, 2003, 'cyrus', $pass);
} else {
	$lmtp = new KolabLMTP();
}
if( PEAR::isError( $lmtp ) ) {
  fwrite(STDOUT, $lmtp->getMessage()."\n");
  if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
  else exit(EX_UNAVAILABLE);
}
if( PEAR::isError( $error = $lmtp->start($sender,$recipients) ) ) {
  fwrite(STDOUT, $error->getMessage().", code ".$error->getCode()."\n"); 
  if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
  else exit(EX_UNAVAILABLE);
}

$headers_done = false;
while (!feof($tmpf) && !$headers_done) {
  $buffer = fgets($tmpf, 8192);
  if( !$headers_done && rtrim( $buffer, "\r\n" ) == '' ) {
    $headers_done = true;
    foreach( $add_headers as $h ) {
      if( PEAR::isError($error = $lmtp->data( "$h\r\n" )) ) {
	fwrite(STDOUT, $error->getMessage().", code ".$error->getCode()."\n"); 
	if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
	else exit(EX_UNAVAILABLE);
      }
    }
  }
  //myLog("Calling smtp->data( ".rtrim($buffer)." )", RM_LOG_DEBUG);
  if( PEAR::isError($error = $lmtp->data( $buffer )) ) {
    fwrite(STDOUT, $error->getMessage().", code ".$error->getCode()."\n"); 
    if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
    else exit(EX_UNAVAILABLE);
  }
}
while (!feof($tmpf) ) {
    $buffer = fread($tmpf, 8192);
    if( PEAR::isError($error = $lmtp->data( $buffer )) ) {
	fwrite(STDOUT, $error->getMessage().", code ".$error->getCode()."\n"); 
	if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
	else exit(EX_UNAVAILABLE);
    }
};
//myLog("Calling smtp->end()", RM_LOG_DEBUG);
$lmtp->end();
myLog("Kolabmailboxfilter successfully completed", RM_LOG_DEBUG);
exit(0);
?>
