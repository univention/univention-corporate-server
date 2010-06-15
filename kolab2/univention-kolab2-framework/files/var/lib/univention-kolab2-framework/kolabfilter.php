#!/usr/bin/php
<?php
/*
 *  Copyright (c) 2004 Klaraelvdalens Datakonsult AB
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

// Profiling code
/*
function mymtime(){
  $tmp=explode(' ',microtime());
  $rt=$tmp[0]+$tmp[1];
  return $rt;
}

class MyTimer {
  function MyTimer( $name ) {
    $this->name = $name;
  }
  function start() {
    $this->time = mymtime();
  }
  function stop() {
    $time = 100*(mymtime()-$this->time);
    myLog("Section ".$this->name." took $time msecs", RM_LOG_DEBUG);
  }

  var $name;
  var $time;
};

$totaltime =& new MyTimer("Total");
$totaltime->start();
*/

// Load our configuration file
$params = array();
require_once '/etc/kolab2/resmgr.conf';
init();

define( 'TMPDIR', '/var/lib/univention-kolab2-framework/filter' );
define( 'EX_TEMPFAIL', 75 );
define( 'EX_UNAVAILABLE', 69 );

//$inputtime =& new MyTimer("Input");
//$inputtime->start();

// Temp file for storing the message
$tmpfname = tempnam( TMPDIR, 'IN.' );
$tmpf = fopen($tmpfname, "w");

// Cleanup function
function cleanup() {
  global $tmpfname;
  file_exists($tmpfname) && unlink($tmpfname);
}
register_shutdown_function( 'cleanup' );

function is_my_domain( $addr ) {
  global $params;
  if( is_array($params['email_domain']) ) {
	$domains = $params['email_domain'];
  } else {
	$domains = array($params['email_domain']);
  }
  
  $adrs = imap_rfc822_parse_adrlist($addr, $params['email_domain']);
  foreach ($adrs as $adr) {
    $adrdom = $adr->host;
	foreach( $domains as $dom ) {
	  if( $dom == $adrdom ) return true;
	  if( $params['verify_subdomains'] && substr($adrdom, -strlen($dom)-1) == ".$dom" ) return true;
	}
  }
  return false;
}

// Check that mail from our domains have trustable
// From: header and that mail from the outside
// does not impersonate any user from our domain
function verify_sender( $sender, $from, $client_addr ) {
  global $params;

  $adrs = imap_rfc822_parse_adrlist($from, $params['email_domain']);
  foreach ($adrs as $adr) {
    $from = $adr->mailbox.'@'.$adr->host;
    $fromdom = $adr->host;

    if( is_array($params['email_domain']) ) {
      $domains = $params['email_domain'];
    } else {
      $domains = array($params['email_domain']);
    }
    $senderdom = substr(strrchr($sender, '@'), 1);
    foreach( $domains as $domain ) {
      if( $params['verify_subdomains'] ) {	
		//myLog( "Checking if ".substr($senderdom, -strlen($domain)-1)." == .$domain", RM_LOG_DEBUG );
		//myLog( "Checking if ".substr($fromdom, -strlen($domain)-1)." == .$domain", RM_LOG_DEBUG );
		if( $client_addr != '127.0.0.1' && 
			($senderdom == $domain ||
			 $fromdom   == $domain ||
			 substr($senderdom, -strlen($domain)-1) == ".$domain" ||
			 substr($fromdom, -strlen($domain)-1) == ".$domain" ) &&
			$sender != $from ) {
		  return false;
		}
      } else {
		if( ($senderdom == $domain ||
			 $fromdom   == $domain ) &&
			$sender != $from ) {
		  return false;
		}
      }
    }
  }
  return true;
}

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

myLog("Kolabfilter starting up, sender=$sender, recipients=".join(',', $recipients)
      .", client_address=$client_address", RM_LOG_DEBUG);

$ical = false;
$add_headers = array();
$headers_done = false;
$from = false;
$subject = false;
$senderok = true;
$rewrittenfrom = false;
while (!feof(STDIN) && !$headers_done) {
  $buffer = fgets(STDIN, 8192);
  $line = rtrim( $buffer, "\r\n");
  if( $line == '' ) {
    // Done with headers
    $headers_done = true;
    if( $from && $params['verify_from_header'] ) {
      if( !verify_sender( strtolower($sender), strtolower($from), $client_address) ) {
		myLog("$sender and $from differ!", RM_LOG_DEBUG);
		if( $params['reject_forged_from_header'] ) {
		  // Always reject mismatches
		  $senderok = false;
		} else {
		  // Only rewrite if from is ours and envelope not
		  if( is_my_domain( $from ) && !is_my_domain( $sender )) {
			myLog("Rewriting From header", RM_LOG_DEBUG);
			$rewrittenfrom = "From: $from (UNTRUSTED, sender is \"$sender\")\r\n";
		  } else {
			// Not our domain in From, reject
			$senderok = false;			
		  }
		}
      }
    }
  } else if( !$headers_done && $params['allow_sender_header'] && eregi( '^Sender: (.*)', $line, $regs ) ) {
    $from = $regs[1];
  } else if( !$headers_done && !$from && eregi( '^From: (.*)', $line, $regs ) ) {
    $from = $regs[1];
  } else if( !$headers_done && eregi( '^Subject: (.*)', $line, $regs ) ) {
    $subject = $regs[1];
  } else if( !$headers_done && eregi( '^Content-Type: text/calendar', $line ) ) {
    myLog("Found iCal data in message", RM_LOG_DEBUG);
    $ical = true;
  }
  if( fwrite($tmpf, $buffer) === false ) {
    exit(EX_TEMPFAIL);
  }
}
while (!feof(STDIN)) {
  $buffer = fread( STDIN, 8192 );
  if( fwrite($tmpf, $buffer) === false ) {
    exit(EX_TEMPFAIL);
  }
}
fclose($tmpf);

//$inputtime->stop();

if( !$senderok ) {
  if( $ical && $params['allow_outlook_ical_forward'] ) {
    require_once('kolabfilter/olhacks.php');
    $rc = olhacks_embedical( $fqhostname, $sender, $recipients, $from, $subject, $tmpfname );
    if( PEAR::isError( $rc ) ) {
      fwrite(STDOUT,"Filter failed: ".$rc->getMessage()."\n");
      exit(EX_TEMPFAIL);
    } else if( $rc === true ) {
      exit(0);
    }
  } else {
    myLog("Invalid From: header. $from does not match envelope $sender\n", RM_LOG_DEBUG);
    fwrite(STDOUT,"Invalid From: header. $from does not match envelope $sender\n");
    exit(EX_UNAVAILABLE);
  }
}

//$outputtime =& new MyTimer("Output");
//$outputtime->start();

$tmpf = fopen($tmpfname,"r");
$smtp = new KolabSMTP( 'localhost', 10026 );
if( PEAR::isError( $smtp ) ) {
  fwrite(STDOUT, $error->getMessage().", code ".$error->getCode()."\n"); 
  if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
  else exit(EX_UNAVAILABLE);
}
if( PEAR::isError( $error = $smtp->start($sender,$recipients) ) ) {
  fwrite(STDOUT, $error->getMessage().", code ".$error->getCode()."\n"); 
  if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
  else exit(EX_UNAVAILABLE);
}

$headers_done = false;
while (!feof($tmpf) && !$headers_done) {
  $buffer = fgets($tmpf, 8192);
  if( !$headers_done && $rewrittenfrom && eregi( '^From: (.*)', $buffer ) ) {
	if( PEAR::isError($error = $smtp->data( $rewrittenfrom )) ) {
	  fwrite(STDOUT, $error->getMessage().", code ".$error->getCode()."\n"); 
	  if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
	  else exit(EX_UNAVAILABLE);
	}
	continue;
  } 
  if( !$headers_done && rtrim( $buffer, "\r\n" ) == '' ) {
    $headers_done = true;
    foreach( $add_headers as $h ) {
      if( PEAR::isError($error = $smtp->data( "$h\r\n" )) ) {
	fwrite(STDOUT, $error->getMessage().", code ".$error->getCode()."\n"); 
	if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
	else exit(EX_UNAVAILABLE);
      }
    }
  }
  //myLog("Calling smtp->data( ".rtrim($buffer)." )", RM_LOG_DEBUG);
  if( PEAR::isError($error = $smtp->data( $buffer )) ) {
    fwrite(STDOUT, $error->getMessage().", code ".$error->getCode()."\n"); 
    if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
    else exit(EX_UNAVAILABLE);
  }
}
while (!feof($tmpf) ) {
    $buffer = fread($tmpf, 8192);
    if( PEAR::isError($error = $smtp->data( $buffer )) ) {
        fwrite(STDOUT, $error->getMessage().", code ".$error->getCode()."\n"); 
	if( $error->getCode() < 500 ) exit(EX_TEMPFAIL);
	else exit(EX_UNAVAILABLE);
    }
};

//myLog("Calling smtp->end()", RM_LOG_DEBUG);
$smtp->end();
//$outputtime->stop();
myLog("Kolabfilter successfully completed", RM_LOG_DEBUG);
//$totaltime->stop();
exit(0);
?>
