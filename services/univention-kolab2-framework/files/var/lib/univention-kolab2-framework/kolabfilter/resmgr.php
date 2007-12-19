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

require_once '/var/lib/univention-kolab2-framework/kolabfilter/misc.php';
require_once '/var/lib/univention-kolab2-framework/freebusy/domxml-php4-to-php5.php';

// What actions we can take when receiving an event request
define('RM_ACT_ALWAYS_ACCEPT',              1);
define('RM_ACT_REJECT_IF_CONFLICTS',        2);
define('RM_ACT_MANUAL_IF_CONFLICTS',        3);
define('RM_ACT_MANUAL',                     4);
define('RM_ACT_ALWAYS_REJECT',              5);

// What possible ITIP notification we can send
define('RM_ITIP_DECLINE',                   1);
define('RM_ITIP_ACCEPT',                    2);
define('RM_ITIP_TENTATIVE',                 3);

require_once 'Net/IMAP.php';
require_once '/var/lib/univention-kolab2-framework/fbview/lib/core.php';
require_once 'Horde/iCalendar.php';
require_once 'Horde/NLS.php';
require_once 'Horde/MIME.php';
require_once 'Horde/MIME/Message.php';
require_once 'Horde/MIME/Headers.php';
require_once 'Horde/MIME/Part.php';
require_once 'Horde/MIME/Structure.php';
//include_once 'Horde/Kolab.php';
require_once 'Horde/Text.php';
require_once '/var/lib/univention-kolab2-framework/freebusy/recurrence.class.php';

// Globals
$imap = NULL;
$server = '';
$mailbox = '';
$calmbox = '';
$prefix = '';
$suffix = '';
$connected = false;

/* Recurrence implementation for looking for
   conflicts between an event and a freebusy list
*/
class ResmgrRecurrence extends Recurrence {
  function ResmgrRecurrence() { 
    $this->conflict = false;
  }

  function setBusy( $start, $end, $duration ) {
    //myLog("ResmgrRecurrence::setBusy( $start, $end, $duration ), conflict=".$this->conflict, RM_LOG_DEBUG);
    if( $this->conflict ) return;
    if( is_null($end) ) $end = $start + $duration;
    foreach ($this->busyperiods as $busyfrom => $busyto) {
      if ( in_array(base64_decode($this->extraparams[$busyfrom]['X-UID']), $this->ignore) ||
	   in_array(base64_decode($this->extraparams[$busyfrom]['X-SID']), $this->ignore) ) {
	// Ignore
	continue;
      }
      if (($busyfrom >= $start && $busyfrom < $end) || ($start >= $busyfrom && $start < $busyto)) {
	myLog('Request overlaps', RM_LOG_DEBUG);
	$this->conflict = true;
	break;
      }
    }
  }

  function hasConflict() { return $this->conflict; }

  var $busyperiods;
  var $extraparams;
  var $ignore;
  var $conflict;
};

function imapClose()
{
    global $imap, $connected;

    if (defined($imap) && $imap !== false) {
      $imap->disconnect();      
    }

    $connected = false;
}

$is_shutting_down = false;

function shutdown($return = 1, $errormsg = "", $updatefb = true )
{
    global $is_shutting_down;

    //Guard against recursion(!)
    if( $is_shutting_down ) return;
    $is_shutting_down = true;
    myLog("Shutting down ($return)", RM_LOG_SUPER);

    imapClose();
    logClose();
    print $errormsg;
    exit($return);
}

function parseactionstring( $action ) {
  switch (trim($action)) {
  case 'ACT_ALWAYS_ACCEPT': return RM_ACT_ALWAYS_ACCEPT;
  case 'ACT_ALWAYS_REJECT': return RM_ACT_ALWAYS_REJECT;
  case 'ACT_REJECT_IF_CONFLICTS': return RM_ACT_REJECT_IF_CONFLICTS;
  case 'ACT_MANUAL_IF_CONFLICTS': return RM_ACT_MANUAL_IF_CONFLICTS;
  case 'ACT_MANUAL': return RM_ACT_MANUAL;
  default:  return false;
  }
}

function getDN( $ldap, $mail ) {
  global $params;
  $filter = "(&(objectClass=kolabInetOrgPerson)(|(mail=$mail)(alias=$mail)(mailPrimaryAddress=$mail)))";
  $result = ldap_search($ldap, $params['base_dn'],
			$filter,
			array('dn'));
  if (!$result) {
    myLog('Unable to perform LDAP search: ' . ldap_error($ldap));
    return false;
  }
  $dn = false;
  if( ldap_count_entries( $ldap, $result ) > 0 ) {
    $entries = ldap_get_entries($ldap, $result);
    $dn = $entries[0]['dn'];
  }
  ldap_free_result( $result );
  return $dn;
}

/**
 * Look up action and encrypted password from LDAP and decrypt it
 */
function getLDAPData($sender,$resource)
{
    global $params;
    myLog("getLDAPData($sender,$resource)");

    // Connect to the LDAP server and retrieve the users' password
    $ldap = ldap_connect($params['ldap_uri']);
    if (!ldap_bind($ldap)) {
        myLog('Unable to contact LDAP server: ' . ldap_error($ldap));
        return new PEAR_Error('Unable to contact LDAP server: ' . ldap_error($ldap));
    }

    $result = ldap_search($ldap, $params['base_dn'],
                          "(&(objectClass=kolabInetOrgPerson)(|(mail=$resource)(mailPrimaryAddress=$resource)))",
                          array("cn", "kolabHomeServer", "kolabEncryptedPassword", "kolabInvitationPolicy" ));
    if (!$result) {
        myLog('Unable to perform LDAP search: ' . ldap_error($ldap));
        return new PEAR_Error('Unable to perform LDAP search: ' . ldap_error($ldap));
    }

    $entries = ldap_get_entries($ldap, $result);
    if ($entries['count'] != 1) {
        myLog($entries['count']." objects returned for $resource");
        return false;
    }
    
    $cn = $entries[0]['cn'][0];
    $hs = $entries[0]['kolabhomeserver'][0];
    $actions = $entries[0]['kolabinvitationpolicy'];

	if (isset($params['priv_key_file'])) {
		$encpw = base64_decode($entries[0]['kolabencryptedpassword'][0]);

		// Now get private key and decrypt the password
		$pkd = file_get_contents($params['priv_key_file']);
		$pkey = openssl_pkey_get_private($pkd);
		if ($pkey === false) {
			while ($msg = openssl_error_string())
				myLog("Error reading private key: $msg");
		}

		if (!openssl_private_decrypt($encpw, $cleartext, $pkey)) {
			while ($msg = openssl_error_string())
				myLog("Error decrypting password: $msg");
		ldap_free_result( $result );
		$cleartext = false;
		}

    	openssl_free_key($pkey);
	} elseif(isset($params['calender_pass'])) {
		$cleartext = $params['calender_pass'];
	}
	
    
    $policies = array();
    $defaultpolicy = false;
    foreach( $actions as $action ) {
      if( ereg( '(.*):(.*)', $action, $regs ) ) {
	myLog('found policy '.$regs[1].':'.$regs[2], RM_LOG_DEBUG );
	$policies[strtolower($regs[1])] = parseactionstring($regs[2]);
      } else {
	$defaultpolicy = parseactionstring($action);
      }
    }
    // Find sender's policy
    if( array_key_exists( $sender, $policies ) ) {
      // We have an exact match, stop processing
      $action = $policies[$sender];
      myLog("Found exact policy match $action for $sender", RM_LOG_DEBUG);
    } else {
      $action = false;
      $dn = getDN( $ldap, $sender );
      if( $dn ) {
	// Sender is local, check for groups
	foreach( $policies as $gid => $policy ) {
	  list($cn, $domain) = split( '@', $gid );
	  if( $domain != $params['email_domain'] ) continue;
	  $result = ldap_search($ldap, $params['base_dn'],
				"(&(objectClass=kolabGroupOfNames)(cn=$cn)(member=$dn))",
				array('dn'));
	  if (!$result) {
	    myLog('Unable to perform LDAP search: ' . ldap_error($ldap));
	    return false;
	  }
	  if(ldap_count_entries($ldap, $result) > 0) {
	    // User is member of group
	    if( !$action ) $action = $policy;
	    else $action = min( $action, $policy );
	  }
	}
      }
      if( !$action && $defaultpolicy ) $action = $defaultpolicy;
    }


    ldap_close($ldap);
    return array( 'cn' => $cn, 'homeserver' => $hs, 'password' => $cleartext, 'action' => $action );
}

function getResourceUid($resource)
{
    global $params;

    // Connect to the LDAP server and retrieve the users' password
    $ldap = ldap_connect($params['ldap_uri']);
    if (!ldap_bind($ldap)) {
        myLog('Unable to contact LDAP server: ' . ldap_error($ldap));
        return false;
    }

    $result = ldap_search($ldap, $params['base_dn'], "(&(objectClass=kolabInetOrgPerson)(|(mail=$resource)(mailPrimaryAddress=$resource)))", array("uid"));
    if (!$result) {
        myLog('Unable to perform LDAP search: ' . ldap_error($ldap));
        return false;
    }

    $entries = ldap_get_entries($ldap, $result);
    if ($entries['count'] != 1) {
        myLog($entries['count']." objects returned for $resource");
        return false;
    }

    $ldap_uid = $entries[0]['uid'][0];
    ldap_close($ldap);
    if( $ldap_uid ) return $ldap_uid;
    else return $resource;
}

function getRequest($filename)
{
    global $requestText;

    $requestText = '';
    $handle = fopen( $filename, "r" );
    while (!feof($handle)) {
        $requestText .= fread($handle, 8192);
    }
}

function checkSMTPResponse(&$smtp, $code)
{
    $resp = $smtp->getResponse();
    if ($resp[0] != $code) {
        myLog($resp[1], RM_LOG_ERROR);
        shutdown(1, $resp[1]);
    }

    return true;
}

function sendSMTP($sender, $recip, &$data)
{
    static $smtp;
    if (!isset($smtp)) {
        require_once 'Net/SMTP.php';

        $smtp = &new Net_SMTP('localhost',10026);
        if (!$smtp) {
            $msg = 'Could not create SMTP object';
            myLog($msg, RM_LOG_ERROR);
            shutdown(1, $msg);
        }

        if (PEAR::isError($error = $smtp->connect())) {
            $msg = 'Failed to connect to SMTP: ' . $error->getMessage();
            myLog($msg, RM_LOG_ERROR);
            shutdown(1, $msg);
        }
        checkSMTPResponse($smtp, 250);

        if (PEAR::isError($error = $smtp->mailFrom($sender))) {
            $msg = "Failed to set sender \"$sender\": " . $error->getMessage();
            myLog($msg, RM_LOG_ERROR);
            shutdown(1, $msg);
        }
        checkSMTPResponse($smtp, 250);

        if (PEAR::isError($error = $smtp->rcptTo($recip))) {
            $msg = "Failed to set recipient \"$recip\": " . $error->getMessage();
            myLog($msg, RM_LOG_ERROR);
            shutdown(1, $msg);
        }
        checkSMTPResponse($smtp, 250);

        if (PEAR::isError($error = $smtp->data($data))) {
            $msg = 'Failed to send data: ' . $error->getMessage();
            myLog($msg, RM_LOG_ERROR);
            shutdown(1, $msg);
        }
        checkSMTPResponse($smtp, 250);

        $smtp->disconnect();
    }
}

function &getICal($sender,$resource)
{
    global $requestText, $params;

    $mime = &MIME_Structure::parseTextMIMEMessage($requestText);

    $parts = $mime->contentTypeMap();
    foreach ($parts as $mimeid => $conttype) {
        if ($conttype == 'text/calendar') {
            $part = $mime->getPart($mimeid);

            $iCalendar = &new Horde_iCalendar();
            $iCalendar->parsevCalendar($part->transferDecode());

            return $iCalendar;
        }
    }
    
    // No iCal found
    return false;
}

/** Helper function */
function assembleUri($parsed)
{
    if (!is_array($parsed)) return false;

    $uri = empty($parsed['scheme']) ? '' :
        $parsed['scheme'] . ':' . ((strtolower($parsed['scheme']) == 'mailto') ? '' : '//');

    $uri .= empty($parsed['user']) ? '' :
        ($parsed['user']) .
        (empty($parsed['pass']) ? '' : ':'.($parsed['pass']))
        . '@';

    $uri .= empty($parsed['host']) ? '' :
        $parsed['host'];
    $uri .= empty($parsed['port']) ? '' :
        ':' . $parsed['port'];

    $uri .= empty($parsed['path']) ? '' :
        $parsed['path'];
    $uri .= empty($parsed['query']) ? '' :
        '?' . $parsed['query'];
    $uri .= empty($parsed['anchor']) ? '' :
        '#' . $parsed['anchor'];

    return $uri;
}

function &getFreeBusy($resource) {
  global $params;
  return internalGetFreeBusy( $resource, $params['freebusy_url']);
}

function &triggerFreeBusy($resource) {
  global $params;
  return internalGetFreeBusy( $resource, $params['pfb_trigger_url']);
}

function &internalGetFreeBusy($resource, $url)
{
    global $params, $calmbox;

    if( ereg( 'user/[^/].*/(.*)', $calmbox, $regs ) ) {
      // Folder in INBOX
      $folder = $regs[1];
    } else {
      // Best guess, probably wont work
      $folder = $calmbox;
    }
    $url = str_replace('${USER}', urlencode($resource), $url);
    $url = str_replace('${FOLDER}', urlencode($folder), $url);

    myLog("URL = $url", RM_LOG_DEBUG );

    $parsed = parse_url($url);
    $parsed['user'] = urlencode($params['calendar_user']);
    $parsed['pass'] = urlencode($params['calendar_pass']);
    $url = assembleUri($parsed);

    $text = @file_get_contents($url);
    if ($text == false || empty($text)) {
        $parsed = parse_url($url);
	$parsed['pass'] = 'XXX';
	$url = assembleUri($parsed);        
        myLog("Unable to retrieve free/busy information for $resource from $url", RM_LOG_ERROR);
        //shutdown(1, "Unable to retrieve free/busy information for $resource");
        return false;
    }

    // If this call is purely to cache the f/b list then we don't need to
    // bother parsing the VFB file
    if (!$cache) {
        $iCalendar = &new Horde_iCalendar();
        $iCalendar->parsevCalendar($text);
        $vfb = &$iCalendar->findComponent('VFREEBUSY');

        if ($vfb === false) {
            myLog("Invalid or no free/busy information available for $resource", RM_LOG_ERROR);
            //shutdown();
            return false;
        }

        $vfb->simplify();

        return $vfb;
    }
}

function sendITipReply($cn,$resource, $itip, $type = RM_ITIP_ACCEPT)
{
    global $organiser, $uid, $sid, $is_update;

    // Build the reply.
    $vCal = &new Horde_iCalendar();
    $vCal->setAttribute('PRODID', '-//proko2//resmgr 1.0//EN');
    $vCal->setAttribute('METHOD', 'REPLY');

    $summary = _('No summary available');

    $itip_reply =& Horde_iCalendar::newComponent('VEVENT', $vCal);
    $itip_reply->setAttribute('UID', $sid);
    if (!is_a($itip->getAttribute('SUMMARY'), 'PEAR_error')) {
        $itip_reply->setAttribute('SUMMARY', $itip->getAttribute('SUMMARY'));
	$summary = $itip->getAttribute('SUMMARY');
    }
    if (!is_a($itip->getAttribute('DESCRIPTION'), 'PEAR_error')) {
        $itip_reply->setAttribute('DESCRIPTION', $itip->getAttribute('DESCRIPTION'));
    }
    if (!is_a($itip->getAttribute('LOCATION'), 'PEAR_error')) {
        $itip_reply->setAttribute('LOCATION', $itip->getAttribute('LOCATION'));
    }
    $itip_reply->setAttribute('DTSTART', $itip->getAttribute('DTSTART'), array_pop($itip->getAttribute('DTSTART', true)));
    if (!is_a($itip->getAttribute('DTEND'), 'PEAR_error')) {
        $itip_reply->setAttribute('DTEND', $itip->getAttribute('DTEND'), array_pop($itip->getAttribute('DTEND', true)));
    } else {
        $itip_reply->setAttribute('DURATION', $itip->getAttribute('DURATION'), array_pop($itip->getAttribute('DURATION', true)));
    }
    if (!is_a($itip->getAttribute('SEQUENCE'), 'PEAR_error')) {
        $itip_reply->setAttribute('SEQUENCE', $itip->getAttribute('SEQUENCE'));
    } else {
        $itip_reply->setAttribute('SEQUENCE', 0);
    }
    $itip_reply->setAttribute('ORGANIZER', $itip->getAttribute('ORGANIZER'), array_pop($itip->getAttribute('ORGANIZER', true)));

    // Let's try and remove this code and just create
    // the ATTENDEE stuff in the reply from scratch   
//     $attendees = $itip->getAttribute( 'ATTENDEE' );
//     if( !is_array( $attendees ) ) {
//       $attendees = array( $attendees );
//     }
//     $params = $itip->getAttribute( 'ATTENDEE', true );
//     for( $i = 0; $i < count($attendees); $i++ ) {
//       $attendee = preg_replace('/^mailto:\s*/i', '', $attendees[$i]);
//       if ($attendee != $resource) {
// 	continue;
//       }
//       $params = $params[$i];
//       break;
//     }

    $params = array();
    $params['CN'] = $cn;
    switch ($type) {
        case RM_ITIP_DECLINE:
            myLog("Sending DECLINE iTip reply to $organiser", RM_LOG_DEBUG);
            $message = $is_update ? sprintf(_("%s has declined the update to the following event:\r\n\r\n%s"), $resource, $summary) :
                sprintf(_("%s has declined the invitation to the following event:\r\n\r\n%s"), $resource, $summary);
            $subject = 'Declined: ' . $summary;
            $params['PARTSTAT'] = 'DECLINED';
            break;

        case RM_ITIP_ACCEPT:
            myLog("Sending ACCEPT iTip reply to $organiser", RM_LOG_DEBUG);
            $message = $is_update ? sprintf(_("%s has accepted the update to the following event:\r\n\r\n%s"), $resource, $summary) :
                sprintf(_("%s has accepted the invitation to the following event:\r\n\r\n%s"), $resource, $summary);
            $subject = 'Accepted: ' . $summary;
            $params['PARTSTAT'] = 'ACCEPTED';
            break;

        case RM_ITIP_TENTATIVE:
            myLog("Sending TENTATIVE iTip reply to $organiser", RM_LOG_DEBUG);
            $message = $is_update ? sprintf(_("%s has tentatively accepted the update to the following event:\r\n\r\n%s"), $resource, $summary) :
                sprintf(_("%s has tentatively accepted the invitation to the following event:\r\n\r\n%s"), $resource, $summary);
            $subject = 'Tentative: ' . $summary;
            $params['PARTSTAT'] = 'TENTATIVE';
            break;

        default:
            myLog("Unknown iTip method ($type) passed to sendITipReply()", RM_LOG_ERROR);
            shutdown(1, "Unknown iTip method ($type) passed to sendITipReply()");
    }

    $itip_reply->setAttribute('ATTENDEE', 'MAILTO:' . $resource, $params);
    $vCal->addComponent($itip_reply);

    //$mime = &new MIME_Part('multipart/alternative');
    //$body = &new MIME_Part('text/plain', Text::wrap($message, 76, "\n"));

    $ics = &new MIME_Part('text/calendar', $vCal->exportvCalendar(), 'UTF-8' );
    //$ics->setName('event-reply.ics');
    $ics->setContentTypeParameter('method', 'REPLY');

    //$mime->addPart($body);
    //$mime->addPart($ics);
    // The following was ::convertMimePart($mime). This was removed so that we
    // send out single-part MIME replies that have the iTip file as the body,
    // with the correct mime-type header set, etc. The reason we want to do this
    // is so that Outlook interprets the messages as it does Outlook-generated
    // responses, i.e. double-clicking a reply will automatically update your
    // meetings, showing different status icons in the UI, etc.
    $mime = &MIME_Message::convertMimePart($ics);
    $mime->setCharset('UTF-8');
    $mime->setTransferEncoding('quoted-printable');
    $mime->transferEncodeContents();

    // Build the reply headers.
    $msg_headers = &new MIME_Headers();
    $msg_headers->addReceivedHeader();
    $msg_headers->addMessageIdHeader();
    $msg_headers->addHeader('Date', date('r'));
    $msg_headers->addHeader('From', "$cn <$resource>");
    $msg_headers->addHeader('To', $organiser);
    $msg_headers->addHeader('Subject', $subject);
    $msg_headers->addMIMEHeaders($mime);

    // Send the reply.
    static $mailer;

    if (!isset($mailer)) {
        require_once 'Mail.php';
        $mailer = &Mail::factory('SMTP', array('auth' => false));
    }

    $msg = $mime->toString();
    if (is_object($msg_headers)) {
        $headerArray = $mime->encode($msg_headers->toArray(), $mime->getCharset());
    } else {
        $headerArray = $mime->encode($msg_headers, $mime->getCharset());
    }

    /* Make sure the message has a trailing newline. */
    if (substr($msg, -1) != "\n") {
        $msg .= "\n";
    }

    //myLog("Sending ".join("\n",$headerArray)."\n\n".$msg." to ".MIME::encodeAddress($organiser), RM_LOG_DEBUG);
    $status = $mailer->send(MIME::encodeAddress($organiser), $headerArray, $msg);

    //$status = $mime->send($organiser, $msg_headers);
    if (is_a($status, 'PEAR_Error')) {
        myLog("Unable to send iTip reply: " . $status->getMessage(), RM_LOG_ERROR);
        shutdown(1, "Unable to send iTip reply: " . $status->getMessage());
    } else {
        myLog("Successfully sent iTip reply");
    }
}

function imapConnect($resource, $inbox = false)
{
    global $params, $imap, $server, $mailbox, $calmbox, $prefix, $suffix;

    // Handle virtual domains
    $prefix = $resource;
    $suffix = '';
    if ($params['virtual_domains']) {
        list($prefix, $suffix) = split('@', $resource);
        if ($params['append_domains'] && !empty($suffix)) {
            $suffix = '@' . $suffix;
        } else {
            $suffix = '';
        }
    }

    // Get our mailbox strings for use in the imap_X functions
    $server = '{' . $params['server'] . '/imap/notls/novalidate-cert/norsh}';
    if ($inbox) {
        $mymailbox = "user/$prefix$suffix";
    } else {
        $mymailbox = "user/$prefix/" . $params['calendar_store'] . "$suffix";
    }
    //$mailbox = "INBOX/Calendar";
    $fullmbox = $server . $mymailbox;

    $imap = &new Net_IMAP( $params['server'] );
    if( PEAR::isError($imap) ) {
      myLog('Unable to create Net_IMAP object: ' . $imap->getMessage(), RM_LOG_ERROR);
      return false;
    }
    //$imap->setDebug(true);
    $rc = $imap->login($params['calendar_user'], $params['calendar_pass'], true, false);
    if( PEAR::isError($rc) ) {
      myLog('Unable to authenticate: ' . $rc->getMessage(), RM_LOG_ERROR);
      return false;      
    }
    $mailboxes = $imap->getMailBoxes( "user/$prefix$suffix" );
    if( PEAR::isError( $mailboxes ) ) {
      myLog('Unable to get mailbox list: ' . $mailboxes->getMessage(), RM_LOG_ERROR);      
    }
    $calmbox = false;
    foreach( $mailboxes as $mailbox ) {
      $a = $imap->getAnnotation('/vendor/kolab/folder-type',
				/*array('value.shared' => 'event.default')*/'value.shared',
				$mailbox);
      myLog("/vendor/kolab/folder-type annotation for folder $mailbox is ".print_r($a,true), RM_LOG_DEBUG);
      if( $a == 'event.default' ) {
	// Found default calendar!
	$calmbox = $mailbox;
	break;
      }
    }

    if( !$calmbox ) {
      // No default calendar, try to create one
      $calmbox = "user/$prefix/" . $params['calendar_store'] . "$suffix";
      if( !in_array( $calmbox, $mailboxes ) ) {
	// Create mailbox
	$rc = $imap->createMailBox( $calmbox );
	if( PEAR::isError($rc) ) {
	  myLog('IMAP Errors from createMailBox: ' . $rc->getMessage(), RM_LOG_ERROR );
	  return false;
	}
      }
      $rc = $imap->setAnnotation('/vendor/kolab/folder-type',
				 array('value.shared' => 'event.default'),
				 $calmbox);
      if( PEAR::isError($rc)) {
	// Non fatal error
	myLog("Unable to set the folder-type annotation on mailbox $mymailbox: "
	      . $rc->getMessage(), RM_LOG_ERROR);
      }
    }

    myLog("Set ACL $calmbox for ".$params['calendar_user'], RM_LOG_DEBUG);
    $rc = $imap->setACL( $calmbox, $params['calendar_user'], "lrswipcda" );
    if( PEAR::isError($rc)) {
        myLog("Error setACL $calmbox: ".$rc->getMessage(), RM_LOG_ERROR);
        return false;
    }

    myLog("Selecting $calmbox for ".$params['calendar_user'], RM_LOG_DEBUG);
    // Open an IMAP connection to the requested users' calendar
    $rc = $imap->selectMailBox( $calmbox );
    if( PEAR::isError($rc)) {
      myLog("Error selecting $calmbox: ".$rc->getMessage(), RM_LOG_ERROR);
      return false;
    }

    myLog("Connected to $calmbox, imap object is " . print_r($imap, true), RM_LOG_DEBUG);
    return $imap;
}

function expire_events( $imap, $when )
{
  // PENDING(steffen): Think about how to add event expiry
  // without serious overhead and without deleting events from 
  // normal user accounts
}

function iCalDate2Kolab($ical_date)
{
    // $ical_date should be a timestamp
    return gmstrftime('%Y-%m-%dT%H:%M:%SZ', $ical_date);
}

function &buildKolabEvent(&$itip)
{
    global $organiser, $resource, $uid, $sid;

    $recurrence = false;
    $kolab_xml = domxml_new_doc('1.0');
    $kolab_event = $kolab_xml->append_child($kolab_xml->create_element('event'));
    $kolab_event->set_attribute('version', '1.0');

    // We're not interested in too much information about the event; the only
    // critical things are the UID and the time spans. We include the
    // summary, body and organizer for display purposes (e.g. in the free/busy viewer).
    //
    // Actually, we need everything! /steffen
    $kolab_node = $kolab_event->append_child($kolab_xml->create_element('uid'));
    $kolab_node->append_child($kolab_xml->create_text_node($uid));

    // No SID anymore
    //$kolab_node = $kolab_event->append_child($kolab_xml->create_element('scheduling-id'));
    //$kolab_node->append_child($kolab_xml->create_text_node($sid));

    $kolab_node = $kolab_event->append_child($kolab_xml->create_element('organizer'));
    $org_params = $itip->getAttribute('ORGANIZER', true);
    if( !is_a( $org_params, 'PEAR_Error' ) ) {
      $orgcn = $org_params[0]['CN'];
      $orgnzr_node = $kolab_node->append_child($kolab_xml->create_element('display-name'));
      $orgnzr_node->append_child($kolab_xml->create_text_node($orgcn));
    }
    $orgnzr_node = $kolab_node->append_child($kolab_xml->create_element('smtp-address'));
    $orgemail = $itip->getAttributeDefault('ORGANIZER', '');
    if( eregi('mailto:(.*)', $orgemail, $regs ) ) $orgemail = $regs[1];
    $orgnzr_node->append_child($kolab_xml->create_text_node( $orgemail ));

    $kolab_node = $kolab_event->append_child($kolab_xml->create_element('summary'));
    $kolab_node->append_child($kolab_xml->create_text_node(
        $itip->getAttributeDefault('SUMMARY', '')
    ));

    $kolab_node = $kolab_event->append_child($kolab_xml->create_element('location'));
    $kolab_node->append_child($kolab_xml->create_text_node(
        $itip->getAttributeDefault('LOCATION', '')
    ));

    $kolab_node = $kolab_event->append_child($kolab_xml->create_element('body'));
    $kolab_node->append_child($kolab_xml->create_text_node(
        $itip->getAttributeDefault('DESCRIPTION', '')
    ));

    $kolab_node = $kolab_event->append_child($kolab_xml->create_element('start-date'));
    $kolab_node->append_child($kolab_xml->create_text_node(
        iCalDate2Kolab($itip->getAttributeDefault('DTSTART', 0))
    ));

    $kolab_node = $kolab_event->append_child($kolab_xml->create_element('end-date'));
    $kolab_node->append_child($kolab_xml->create_text_node(
        iCalDate2Kolab($itip->getAttributeDefault('DTEND', 0))
    ));
    
    // Attendees
    $attendees = $itip->getAttribute('ATTENDEE');
    if( !is_a( $attendees, 'PEAR_Error' ) ) {
      $attendees_params = $itip->getAttribute('ATTENDEE', true);
      if( !is_array( $attendees ) ) $attendees = array( $attendees );
      if( !is_array( $attendees_params ) ) $attendees_params = array( $attendees_params );
      for( $i = 0; $i < count($attendees); $i++ ) {
	$attendee_node = $kolab_event->append_child($kolab_xml->create_element('attendee'));	
	$dispname_node = $attendee_node->append_child($kolab_xml->create_element('display-name'));	
	$dispname_node->append_child($kolab_xml->create_text_node($attendees_params[$i]['CN']));
	$kolab_node = $attendee_node->append_child($kolab_xml->create_element('smtp-address'));
	$attendeeemail = $attendees[$i];
	if( eregi('mailto:(.*)',$attendeeemail,$regs) ) {
	  $attendeeemail = $regs[1];
	}
	$kolab_node->append_child($kolab_xml->create_text_node($attendeeemail));
	$kolab_node = $attendee_node->append_child($kolab_xml->create_element('status'));
	$kolab_node->append_child($kolab_xml->create_text_node(strtolower($attendees_params[$i]['PARTSTAT'])));
	$kolab_node = $attendee_node->append_child($kolab_xml->create_element('request-response'));
	if( $attendees_params[$i]['RSVP'] == 'FALSE' ) {
	  $kolab_node->append_child($kolab_xml->create_text_node('false'));
	} else {
	  $kolab_node->append_child($kolab_xml->create_text_node('true'));	  
	}
	$kolab_node = $attendee_node->append_child($kolab_xml->create_element('role'));
	$kolab_node->append_child($kolab_xml->create_text_node(strtolower($attendees_params[$i]['ROLE'])));
      }
    }

    // Alarm
    $valarm = $itip->findComponent('VALARM');
    if( $valarm ) {
      $trigger = $valarm->getAttribute('TRIGGER');
      if( !PEAR::isError($trigger) ) {
	$p = $valarm->getAttribute('TRIGGER',true);
	if( $trigger < 0 ) {
	    // All OK, enter the alarm into the XML
	    // NOTE: The Kolab XML format seems underspecified
	    // wrt. alarms currently...
	    $kolab_node = $kolab_event->append_child($kolab_xml->create_element('alarm'));
	    $kolab_node->append_child($kolab_xml->create_text_node((int)(-$trigger/60)));
	}
      } else {
	myLog('No TRIGGER in VALARM', RM_LOG_DEBUG);	
      }
    }

    // Recurrence
    $rrule_str = $itip->getAttribute('RRULE');
    if( !is_a( $rrule_str, 'PEAR_Error' ) ) {
      $kolab_days = array( 'MO' => 'monday',
			   'TU' => 'tuesday',
			   'WE' => 'wednesday',
			   'TH' => 'thursday',
			   'FR' => 'friday',
			   'SA' => 'saturday',
			   'SU' => 'sunday');
      $kolab_months = array( 1  => 'january',
			     2  => 'february',
			     3  => 'march',
			     4  => 'april',
			     5  => 'may',
			     6  => 'june',
			     7  => 'july',
			     8  => 'august',
			     9  => 'september',
			     10 => 'october',
			     11 => 'november',
			     12 => 'december' );
      $rrule_list = split(';', $rrule_str);
      $rrule = array();
      foreach( $rrule_list as $r ) {
	list( $k, $v ) = split( '=', $r );
	$rrule[$k]=$v;
	myLog('RRULE['.$k.']='.$v, RM_LOG_DEBUG);
      }
      $recur_node = $kolab_event->append_child($kolab_xml->create_element('recurrence'));
      $recurrence =& new ResmgrRecurrence();
      $freq = strtolower($rrule['FREQ']);
      $recur_node->append_child( $kolab_xml->create_attribute( 'cycle', $freq ));
      $recurrence->setCycletype( $freq );
      $recurrence->setStartdate( $itip->getAttributeDefault('DTSTART', 0) );
      $recurrence->setEnddate( $itip->getAttributeDefault('DTEND', 0) );
      switch( $freq ) {
      case 'daily':
	break;
      case 'weekly':
	$days = split(',', $rrule['BYDAY']);
	$kdays = array();
	foreach( $days as $day ) {
	  $day_node = $recur_node->append_child( $kolab_xml->create_element( 'day'));	  
	  $day_node->append_child($kolab_xml->create_text_node($kolab_days[$day]));
	  $kdays[] = $kolab_days[$day];
	}
	$recurrence->setDay( $kdays );
	break;
      case 'monthly':
	if( $rrule['BYDAY'] ) {
	  $recur_node->append_child( $kolab_xml->create_attribute( 'type', 'weekday' ));
	  $recurrence->setType( 'weekday' );
	  $wdays = split(',', $rrule['BYDAY']);
	  $kdays = array();
	  $kdaynumbers = array();
	  foreach( $wdays as $wday ) {
	    if( ereg('([+-]?[0-9])(.*)', $wday, $regs ) ) {
	      $daynumber_node = $recur_node->append_child( $kolab_xml->create_element( 'daynumber'));
	      $daynumber_node->append_child($kolab_xml->create_text_node( $regs[1] ));	      
	      $day_node = $recur_node->append_child( $kolab_xml->create_element( 'day'));
	      $day_node->append_child($kolab_xml->create_text_node( $kolab_days[$regs[2]] ));	      
	      $kdaynumbers[] = $regs[1];
	      $kdays[] = $kolab_days[$regs[2]];
	    } else {
	      $day_node = $recur_node->append_child( $kolab_xml->create_element( 'day'));
	      $day_node->append_child($kolab_xml->create_text_node( $wday ));	      
	      $kdays[] = $wday;
	    }
	  }
	  if( !empty($kdaynumbers) ) $recurrence->setDaynumber($kdaynumbers);
	  $recurrence->setDay( $kday );
	} else if( $rrule['BYMONTHDAY'] ) {
	  $recur_node->append_child( $kolab_xml->create_attribute( 'type', 'daynumber' ));
	  $recurrence->setType( 'daynumber' );
	  $daynumbers = split(',', $rrule['BYMONTHDAY']);
	  $kdaynumbers = array();
	  foreach( $daynumbers as $daynumber ) {
	    $daynumber_node = $recur_node->append_child( $kolab_xml->create_element( 'daynumber'));
	    $daynumber_node->append_child($kolab_xml->create_text_node( $daynumber ));
	    $kdaynumbers[] = $daynumber;
	  }
	  $recurrence->setDaynumber($kdaynumbers);
	}
	break;
      case 'yearly':
	if( $rrule['BYDAY'] ) {
	  $recur_node->append_child( $kolab_xml->create_attribute( 'type', 'weekday' ));
	  $recurrence->setType( 'weekday' );
	  $wdays = split(',', $rrule['BYDAY']);
	  $kdays = array();
	  $kdaynumbers = array();
	  foreach( $wdays as $wday ) {
	    if( ereg('([+-]?[0-9])(.*)', $wday, $regs ) ) {
	      $daynumber_node = $recur_node->append_child( $kolab_xml->create_element( 'daynumber'));
	      $daynumber_node->append_child($kolab_xml->create_text_node( $regs[1] ));	      
	      $day_node = $recur_node->append_child( $kolab_xml->create_element( 'day'));
	      $day_node->append_child($kolab_xml->create_text_node( $kolab_days[$regs[2]] ));	      
	      $kdaynumbers[] = $regs[1];
	      $kdays[] = $kolab_days[$regs[2]];
	    } else {
	      $day_node = $recur_node->append_child( $kolab_xml->create_element( 'day'));
	      $day_node->append_child($kolab_xml->create_text_node( $wday ));	      
	      $kdays[] = $wday;
	    }
	  }
	  if( !empty($kdaynumbers) ) $recurrence->setDaynumber($kdaynumbers);
	  $recurrence->setDay( $kday );
	  $monthnumbers = split(',', $rrule['BYMONTH']);
	  $kmonth = array();
	  foreach( $monthnumbers as $monthnumber ) {
	    $month = $kolab_months[$monthnumber];
	    $month_node = $recur_node->append_child( $kolab_xml->create_element( 'month'));
	    $month_node->append_child($kolab_xml->create_text_node( $month ));
	    $kmonth[] = $month;
	  }
	  $recurrence->setMonth($kmonth);
	} else if( $rrule['BYMONTHDAY'] ) {
	  $recur_node->append_child( $kolab_xml->create_attribute( 'type', 'monthday' ));
	  $recurrence->setType( 'monthday' );
	  $daynumbers = split(',', $rrule['BYMONTHDAY']);
	  $kdaynumbers = array();
	  foreach( $daynumbers as $daynumber ) {
	    $daynumber_node = $recur_node->append_child( $kolab_xml->create_element( 'daynumber'));
	    $daynumber_node->append_child($kolab_xml->create_text_node( $daynumber ));
	    $kdaynumbers[] = $daynumber;
	  }
	  $recurrence->setDaynumber($kdaynumbers);
	  $monthnumbers = split(',', $rrule['BYMONTH']);
	  $kmonth = array();
	  foreach( $monthnumbers as $monthnumber ) {
	    $month = $kolab_months[$monthnumber];
	    $month_node = $recur_node->append_child( $kolab_xml->create_element( 'month'));
	    $month_node->append_child($kolab_xml->create_text_node( $month ));
	    $kmonth[] = $month;
	  }
	  $recurrence->setMonth($kmonth);
	} else if( $rrule['BYYEARDAY'] ) {
	  $recur_node->append_child( $kolab_xml->create_attribute( 'type', 'yearday' ));
	  $recurrence->setType( 'yearday' );
	  $daynumbers = split(',', $rrule['BYMONTHDAY']);
	  $kdaynumbers = array();
	  foreach( $daynumbers as $daynumber ) {
	    $daynumber_node = $recur_node->append_child( $kolab_xml->create_element( 'daynumber'));
	    $daynumber_node->append_child($kolab_xml->create_text_node( $daynumber ));
	    $kdaynumbers[] = $daynumber;
	  }
	  $recurrence->setDaynumber($kdaynumbers);	  
	}
	break;
      default:
	// Not supported
      }
      $interval_node = $recur_node->append_child( $kolab_xml->create_element( 'interval' ));
      $interval_node->append_child($kolab_xml->create_text_node($rrule['INTERVAL']));
      $recurrence->setInterval( $rrule['INTERVAL']);

      $range_node = $recur_node->append_child( $kolab_xml->create_element( 'range' ));
      if( $rrule['COUNT'] ) {
	$range_node->append_child( $kolab_xml->create_attribute( 'type', 'number' ));      
	$range_node->append_child($kolab_xml->create_text_node($rrule['COUNT']));
	$recurrence->setRangetype('number');
	$recurrence->setRange( $rrule['COUNT']);
      } else if( $rrule['UNTIL'] ) {
	$range_node->append_child( $kolab_xml->create_attribute( 'type', 'date' ));      
	$range_node->append_child($kolab_xml->create_text_node($rrule['UNTIL']));
	$recurrence->setRangetype('date');
	$recurrence->setRange( $rrule['UNTIL']);
      } else {
	$range_node->append_child( $kolab_xml->create_attribute( 'type', 'none' ));      
	$recurrence->setRangetype('none');
      }
      $exclusions = $itip->getAttribute('EXDATE');
      myLog("exslusions=".print_r($exclusions,true), RM_LOG_DEBUG);
      if( !is_a( $exclusions, 'PEAR_Error' ) ) {
	if( !is_array( $exclusions ) ) $exclusions = array( $exclusions );
	foreach( $exclusions as $ex ) {
	  myLog("ex=".print_r($ex[0],true).", ical=".iCalDate2Kolab($ex[0]), RM_LOG_DEBUG);
	  $ex_node = $recur_node->append_child( $kolab_xml->create_element( 'exclusion' ) );
	  $kolab_date = $ex[0]['year'].'-'.$ex[0]['month'].'-'.$ex[0]['mday'];
	  $ex_node->append_child($kolab_xml->create_text_node( $kolab_date ) );
	}
      }
    }

    return array($kolab_xml,$recurrence);
}




////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

function resmgr_filter( $fqhostname, $sender, $resource, $tmpfname ) {
  global $params, $conf, $ldapdata,$calmbox,$organiser,$uid,$sid,$requestText;

  // Make Horde happy
  $conf['server']['name'] = $params['email_domain'];

  // Set some parameters
  $ldapdata = &getLDAPData($sender,$resource);
  if( PEAR::isError($ldapdata) ) return $ldapdata;
  else if( $ldapdata === false ) {
    // No data, probably not a local user
    return true;
  } else if( (boolean)strtolower($ldapdata['homeserver']) && strtolower($ldapdata['homeserver']) != $fqhostname ) {
    // Not the users homeserver, ignore
    return true;
  }
  //if( $ldapdata['password'] === false ) {
  //  // No decryptable password, use calendar user
  //  $params['calendar_uid'] = getResourceUid($resource);  
  //} else {
  //  $params['calendar_user'] = $resource;
  //  $params['calendar_uid'] = getResourceUid($resource);
  //  $params['calendar_pass'] = $ldapdata['password'];
  //}

  $cn = $ldapdata['cn'];
  $params['action'] = $ldapdata['action'];
  myLog("Action for $sender is ".$params['action'], RM_LOG_DEBUG);
  if( !$params['action'] ) {
    // Manual is the only safe default!
    $params['action'] = RM_ACT_MANUAL;
  }

  // Get out as early as possible if manual
  if( $params['action'] == RM_ACT_MANUAL ) {
    myLog("Passing through message to $resource");
    return true;
  }

  $requestText = '';

  // Get our request from tmp file
  getRequest($tmpfname);

  // Get the iCalendar data (i.e. the iTip request)
  $iCalendar = &getICal($sender,$resource);
  if( $iCalendar === false ) {
    // No iCal in mail
    return true;
  }
  // Get the event details out of the iTip request
  $itip = &$iCalendar->findComponent('VEVENT');
  if ($itip === false) {
    myLog("No VEVENT found in iCalendar data, Passing through to $resource");
    return true;
  }

  // What is the request's method? i.e. should we create a new event/cancel an
  // existing event, etc.
  $method = strtoupper($iCalendar->getAttributeDefault('METHOD',
						       $itip->getAttributeDefault('METHOD', 'REQUEST')));

  // What resource are we managing?
  myLog("Processing $method method for $resource", RM_LOG_DEBUG);

  // This is assumed to be constant across event creation/modification/deletipn
  $uid = $itip->getAttributeDefault('UID', '');
  myLog("Event has UID $sid", RM_LOG_DEBUG);
  $sid = $uid;

  // Who is the organiser?
  $organiser = preg_replace('/^mailto:\s*/i', '', $itip->getAttributeDefault('ORGANIZER', ''));
  myLog("Request made by $organiser", RM_LOG_DEBUG);

  // What is the events summary?
  $summary = $itip->getAttributeDefault('SUMMARY', '');

  $dtstart = $itip->getAttributeDefault('DTSTART', 0);
  $dtend = $itip->getAttributeDefault('DTEND', 0);

  myLog('Event starts on ' . strftime('%a, %d %b %Y %H:%M:%S %z', $dtstart) .
	' and ends on ' . strftime('%a, %d %b %Y %H:%M:%S %z', $dtend), RM_LOG_DEBUG);

  if ($params['action'] == RM_ACT_ALWAYS_REJECT) {
    myLog("Rejecting $method method");
    sendITipReply($cn,$resource,$itip,RM_ITIP_DECLINE);
    return false;//shutdown(0);
  }

  $is_update = false;
  $ignore = array();
  $imap = imapConnect($resource);
  $connected = ($imap !== false);
  if( !$connected ) {
    myLog("Error, could not open calendar folder!", RM_LOG_ERROR);
    return new PEAR_Error('Error, could not open calendar folder!');
  }
  switch ($method) {
  case 'REQUEST':
    if ($params['action'] == RM_ACT_MANUAL) {
      myLog("Passing through $method method");
      break;
    }

    // Check if the request is actually an update of an existing event
    $updated_messages = $imap->search('SUBJECT "' . $sid . '"');
    if( PEAR::isError( $updated_messages ) ) {
      myLog("Error searching mailbox: ".$updated_messages->getMessage(), RM_LOG_ERROR);
      $updated_messages = array();
    }
    if (!empty($updated_messages)) {
      myLog("Updating message $sid");
      $ignore[] = $sid;
      $is_update = true;

      if (!is_array($updated_messages)) {
	$updated_messages = array($updated_messages);
      }
    }
    list($kolab_xml,$recurrence) = buildKolabEvent($itip);

    // Don't even bother checking free/busy info if RM_ACT_ALWAYS_ACCEPT
    // is specified
    if ($params['action'] != RM_ACT_ALWAYS_ACCEPT) {
      // Get the resource's free/busy list
      triggerFreeBusy($resource);
      $vfb = &getFreeBusy($resource);

      if (!$vfb) {
	return new PEAR_Error("Error building free/busy list");
      }

      $vfbstart = $vfb->getAttributeDefault('DTSTART', 0);
      $vfbend = $vfb->getAttributeDefault('DTEND', 0);
      myLog('Free/busy info starts on ' . strftime('%a, %d %b %Y %H:%M:%S %z', $vfbstart) .
	    ' and ends on ' . strftime('%a, %d %b %Y %H:%M:%S %z', $vfbend), RM_LOG_DEBUG);

      // Check whether we are busy or not
      $busyperiods = $vfb->getBusyPeriods();
      $extraparams = $vfb->getExtraParams();
      $conflict = false;	    
      if( $recurrence !== false ) {
	$recurrence->busyperiods =& $busyperiods;
	$recurrence->extraparams =& $extraparams;
	$recurrence->ignore = $ignore;
	//myLog("Recurrence is ".print_r($recurrence,true), RM_LOG_DEBUG);
	$recurrence->expand( $vfbstart, $vfbend );
	$conflict = $recurrence->hasConflict();
      } else {	    
	foreach ($busyperiods as $busyfrom => $busyto) {
	  myLog('Busy period from ' . strftime('%a, %d %b %Y %H:%M:%S %z', $busyfrom) . ' to ' . strftime('%a, %d %b %Y %H:%M:%S %z', $busyto), RM_LOG_DEBUG);
	  if ( in_array(base64_decode($extraparams[$busyfrom]['X-UID']), $ignore) ||
	       in_array(base64_decode($extraparams[$busyfrom]['X-SID']), $ignore) ) {
	    // Ignore
	    continue;
	  }
	  if (($busyfrom >= $dtstart && $busyfrom < $dtend) || ($dtstart >= $busyfrom && $dtstart < $busyto)) {
	    myLog('Request overlaps', RM_LOG_DEBUG);
	    $conflict = true;
	    break;
	  }
	}
      }

      if ($conflict) {
	if ($params['action'] == RM_ACT_MANUAL_IF_CONFLICTS) {
	  //myLog("Conflict detected; tentatively accepting");
	  //sendITipReply(RM_ITIP_TENTATIVE);
	  myLog("Conflict detected; Passing mail through");
	  return true;
	} else if ($params['action'] == RM_ACT_REJECT_IF_CONFLICTS) {
	  myLog("Conflict detected; rejecting");
	  sendITipReply($cn,$resource,$itip,RM_ITIP_DECLINE);
	  return false;//shutdown(0);
	}
      }
    }

    // At this point there was either no conflict or RM_ACT_ALWAYS_ACCEPT
    // was specified; either way we add the new event & send an 'ACCEPT'
    // iTip reply

    myLog("Adding event $sid");

    $message = &new MIME_Message();

    $kolabinfo = 'This is a Kolab Groupware object. To view this object you will need a client that understands the Kolab Groupware format. For a list of such clients please visit http://www.kolab.org/kolab2-clients.html';

    $body = &new MIME_Part('text/plain', Text::wrap($kolabinfo, 76, "\n"));

    $part = &new MIME_Part('application/x-vnd.kolab.event', $kolab_xml->dump_mem(true));
    $part->setName('kolab.event');
    $part->setDisposition('attachment');

    $message->addPart($body);
    $message->addPart($part);

    $headers = &new MIME_Headers();
    $headers->addHeader("From", $resource);
    $headers->addHeader("To", $resource);
    $headers->addHeader("Subject", $sid);
    $headers->addHeader("User-Agent", "proko2/resmgr");
    $headers->addHeader("Reply-To", "");
    $headers->addHeader("Date", date("r"));
    $headers->addHeader("X-Kolab-Type", "application/x-vnd.kolab.event");
    $headers->addMIMEHeaders($message);

    $message = preg_replace("/\r\n|\n|\r/s", "\r\n",
			    $headers->toString() .
			    $message->toString(false)
			    );

    myLog("Appending message to $calmbox", RM_LOG_DEBUG);
    $rc = $imap->appendMessage($message);
    if( PEAR::isError($rc) ) {
      myLog("Error appending message: ".$rc->getMessage(), RM_LOG_ERROR);
    }

    // Update our status within the iTip request and send the reply
    $itip->setAttribute('STATUS', 'CONFIRMED', array(), false);
    $attendees = $itip->getAttribute('ATTENDEE');
    if (!is_array($attendees)) {
      $attendees = array($attendees);
    }
    $attparams = $itip->getAttribute('ATTENDEE', true);
    foreach ($attendees as $i => $attendee) {
      $attendee = preg_replace('/^mailto:\s*/i', '', $attendee);
      if ($attendee != $resource) {
	continue;
      }

      $attparams[$i]['PARTSTAT'] = 'ACCEPTED';
      if (array_key_exists('RSVP', $attparams[$i])) {
	unset($attparams[$i]['RSVP']);
      }
    }

    // Re-add all the attendees to the event, using our updates status info
    $firstatt = array_pop($attendees);
    $firstattparams = array_pop($attparams);
    $itip->setAttribute('ATTENDEE', $firstatt, $firstattparams, false);
    foreach ($attendees as $i => $attendee) {
      $itip->setAttribute('ATTENDEE', $attendee, $attparams[$i]);
    }

    sendITipReply($cn,$resource,$itip,RM_ITIP_ACCEPT);

    // Delete any old events that we updated
    if( !empty( $updated_messages ) ) {
      myLog("Deleting ".join(', ',$deleted_messages)." because of update", RM_LOG_DEBUG);
      $imap->deleteMessages( $updated_messages );
      $status = $imap->expunge();
      if (is_a($status, 'PEAR_Error')) {
        myLog("Unable to delete message. Status message:" . $status->getMessage(), RM_LOG_ERROR);
      }
    }
    // Get the resource's free/busy list
    // once more so it is up to date
    $imap->disconnect();
    unset($imap);
    if( !triggerFreeBusy($resource,false) ) {
      myLog("Error updating fblist", RM_LOG_SUPER );
    }
    return false;//shutdown(0);

  case 'CANCEL':
    myLog("Removing event $sid");
	
    // Try to delete the event
    $deleted_messages = $imap->search('SUBJECT "' . $sid . '"');
    if( PEAR::isError($deleted_messages) ) {
      myLog("Error searching mailbox: ".$deleted_messages->getMessage(), RM_LOG_ERROR);
      $deleted_messages = array();
    }
    if (empty($deleted_messages)) {
      myLog("Canceled event $sid is not present in $resource's calendar", RM_LOG_WARN);
      $body = sprintf(_("The following event that was canceled is not present in %s's calendar:\r\n\r\n%s"), $resource, $summary);
      $subject = sprintf(_("Error processing '%s'"), $summary);
    } else {
      $body = sprintf(_("The following event has been successfully removed:\r\n\r\n%s"), $summary);
      $subject = sprintf(_("%s has been cancelled"), $summary);
    }

    if (!is_array($deleted_messages)) {
      $deleted_messages = array($deleted_messages);
    }

    myLog("Sending confirmation of cancelation to $organiser");
    $body = &new MIME_Part('text/plain', Text::wrap($body, 76, "\n"));
    $mime = &MIME_Message::convertMimePart($body);
    $mime->setTransferEncoding('quoted-printable');
    $mime->transferEncodeContents();

    // Build the reply headers.
    $msg_headers = &new MIME_Headers();
    $msg_headers->addReceivedHeader();
    $msg_headers->addMessageIdHeader();
    $msg_headers->addHeader('Date', date('r'));
    $msg_headers->addHeader('From', $resource);
    $msg_headers->addHeader('To', $organiser);
    $msg_headers->addHeader('Subject', $subject);
    $msg_headers->addMIMEHeaders($mime);

    // Send the reply.
    static $mailer;

    if (!isset($mailer)) {
      require_once 'Mail.php';
      $mailer = &Mail::factory('SMTP', array('auth' => false));
    }

    $msg = $mime->toString();
    if (is_object($msg_headers)) {
      $headerArray = $mime->encode($msg_headers->toArray(), $mime->getCharset());
    } else {
      $headerArray = $mime->encode($msg_headers, $mime->getCharset());
    }

    /* Make sure the message has a trailing newline. */
    if (substr($msg, -1) != "\n") {
      $msg .= "\n";
    }

    $status = $mailer->send(MIME::encodeAddress($organiser), $headerArray, $msg);

    //$status = $mime->send($organiser, $msg_headers);
    if (is_a($status, 'PEAR_Error')) {
      myLog("Unable to send cancellation reply: " . $status->getMessage(), RM_LOG_ERROR);
      return new PEAR_Error("Unable to send cancellation reply: " . $status->getMessage());
    } else {
      myLog("Successfully sent cancellation reply");
    }

    // Delete the messages from IMAP
    // Delete any old events that we updated
    if( !empty( $deleted_messages ) ) {
      myLog("Deleting ".join(', ',$deleted_messages)." because of cancel", RM_LOG_DEBUG);
      $imap->deleteMessages( $deleted_messages );
      $status = $imap->expunge();
      if (is_a($status, 'PEAR_Error')) {
        myLog("Unable to delete message. Status message:" . $status->getMessage(), RM_LOG_ERROR);
      }
    }
    $imap->disconnect();
    unset($imap);
    // Get the resource's free/busy list
    // once more so it is up to date
    if( !triggerFreeBusy($resource,false) ) {
      myLog("Error updating fblist", RM_LOG_SUPER );
    }
    return false;;

  default:
    // We either don't currently handle these iTip methods, or they do not
    // apply to what we're trying to accomplish here
    if (!$params['group']) {
      myLog("Ignoring $method method");
      return false;
    }
  }

  // Pass the message through to the group's mailbox
  myLog("Passing through $method method to $resource");
  return true;
}
?>
