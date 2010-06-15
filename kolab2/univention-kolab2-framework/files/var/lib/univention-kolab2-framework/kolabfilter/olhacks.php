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

require_once 'kolabfilter/misc.php';
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/iCalendar.php';
require_once 'Horde/NLS.php';
require_once 'Horde/MIME.php';
require_once 'Horde/MIME/Message.php';
require_once 'Horde/MIME/Headers.php';
require_once 'Horde/MIME/Part.php';
require_once 'Horde/MIME/Structure.php';

$forwardtext = "This is an invitation forwarded by outlook and\n".
  "was rectified by the Kolab server.\n".
  "The invitation was originally sent by\n%s.\n\n".
  "Diese Einladung wurde von Outlook weitergeleitet\n".
  "und vom Kolab-Server in gute Form gebracht.\n".
  "Die Einladung wurde ursprünglich von\n%s geschickt.\n";

/*static*/ function olhacks_mime_parse( &$text ) {
  /* Taken from Horde's MIME/Structure.php */
  require_once 'Mail/mimeDecode.php';

  /* Set up the options for the mimeDecode class. */
  $decode_args = array();
  $decode_args['include_bodies'] = true;
  $decode_args['decode_bodies'] = false;
  $decode_args['decode_headers'] = false;
  
  $mimeDecode = &new Mail_mimeDecode($text, MIME_PART_EOL);
  if (!($structure = $mimeDecode->decode($decode_args))) {
    return false;
  }
  
  /* Put the object into imap_parsestructure() form. */
  MIME_Structure::_convertMimeDecodeData($structure);
  
  return array($structure->headers, $ret = &MIME_Structure::parse($structure));
}

/* static */ function copy_header( $name, &$msg_headers, &$headerarray ) {
  $lname = strtolower($name);
  if( array_key_exists($lname, $headerarray)) {
    if( is_array( $headerarray[$lname] ) ) {
      foreach( $headerarray[$lname] as $h ) {
	$msg_headers->addHeader($name, $h );	
      }
    } else {
      $msg_headers->addHeader($name, $headerarray[$lname] );
    }
  }
}

/*
 * Yet another problem: Outlook seems to remove the organizer
 * from the iCal when forwarding -- we put the original sender
 * back in as organizer.
 */
/* static */ function add_organizer( &$icaltxt, $from ) {
  global $params;
  $iCal = &new Horde_iCalendar();
  $iCal->parsevCalendar($icaltxt);
  $vevent =& $iCal->findComponent('VEVENT');
  if( $vevent ) {
    #myLog("Successfully parsed vevent", RM_LOG_DEBUG);
    if( !$vevent->organizerName() ) {
      #myLog("event has no organizer, adding $from", RM_LOG_DEBUG);
      $adrs = imap_rfc822_parse_adrlist($from, $params['email_domain']);
      if( count($adrs) > 0 ) {
	$org_email = $adrs[0]->mailbox.'@'.$adrs[0]->host;
	$org_name  = $adrs[0]->personal;
	if( $org_name ) $vevent->setAttribute( 'ORGANIZER', $org_email, 
					       array( 'CN' => $org_name), false );
	else $vevent->setAttribute( 'ORGANIZER', $org_email, 
				    array(), false );
	myLog("Adding missing organizer '$org_name <$org_email>' to iCal", RM_LOG_DEBUG);
	$icaltxt = $iCal->exportvCalendar();
      }
    }
  }
}

/* Yet another Outlook problem: Some versions of Outlook seems to be incapable
 * of handling non-ascii characters properly in text/calendar parts of
 * a multi-part/mixed mail which we use for forwarding.
 * As a solution, we encode common characters as humanreadable
 * two-letter ascii.
 */
/* static */ function olhacks_recode_to_ascii( $text ) {
  #myLog("recoding \"$text\"", RM_LOG_DEBUG);
  $text = str_replace( ('æ'), 'ae', $text );
  $text = str_replace( ('ø'), 'oe', $text );
  $text = str_replace( ('å'), 'aa', $text );
  $text = str_replace( ('ä'), 'ae', $text );
  $text = str_replace( ('ö'), 'oe', $text );
  $text = str_replace( ('ü'), 'ue', $text );
  $text = str_replace( ('ß'), 'ss', $text );

  $text = str_replace( ('Æ'), 'Ae', $text );
  $text = str_replace( ('Ø'), 'Oe', $text );
  $text = str_replace( ('Å'), 'Aa', $text );
  $text = str_replace( ('Ä'), 'Ae', $text );
  $text = str_replace( ('Ö'), 'Oe', $text );
  $text = str_replace( ('Ü'), 'Ue', $text );
  #myLog("recoded to \"$text\"", RM_LOG_DEBUG);

  return $text;
}

/* main entry point */
function olhacks_embedical( $fqhostname, $sender, $recipients, $origfrom, $subject, $tmpfname ) {
  myLog("Encapsulating iCal message forwarded by $sender", RM_LOG_DEBUG);
  global $forwardtext;
  // Read in message text
  $requestText = '';
  $handle = @fopen( $tmpfname, "r" );
  if( $handle === false ) {
    myLog("Error opening $tmpfname", RM_LOG_ERROR);
    return false;
  }
  while (!feof($handle)) {
    $requestText .= fread($handle, 8192);
  }
  fclose($handle);

  // Parse existing message
  list( $headers, $mime) = olhacks_mime_parse($requestText);
  $parts = $mime->contentTypeMap();
  if( count($parts) != 1 || $parts[1] != 'text/calendar' ) {
    myLog("Message does not contain exactly one toplevel text/calendar part, passing through", 
	  RM_LOG_DEBUG);
    return false;
  }
  $basepart = $mime->getBasePart();

  // Construct new MIME message with original message attached
  $toppart = &new MIME_Message();
  $dorigfrom = Mail_mimeDecode::_decodeHeader($origfrom);
  $textpart = &new MIME_Part('text/plain', sprintf($forwardtext,$dorigfrom,$dorigfrom), 'UTF-8' );
  $ical_txt = $basepart->transferDecode();
  add_organizer($ical_txt, $dorigfrom);
  $msgpart = &new MIME_Part($basepart->getType(), olhacks_recode_to_ascii($ical_txt), 
			    $basepart->getCharset() );
  
  $toppart->addPart($textpart);
  $toppart->addPart($msgpart);
  
  // Build the reply headers.
  $msg_headers = &new MIME_Headers();
  copy_header( 'Received', $msg_headers, $headers );
  //$msg_headers->addReceivedHeader();
  $msg_headers->addMessageIdHeader();
  //myLog("Headers=".print_r($headers,true), RM_LOG_DEBUG);
  copy_header( 'Date', $msg_headers, $headers );
  copy_header( 'Resent-Date', $msg_headers, $headers );
  copy_header( 'Subject', $msg_headers, $headers );
  $msg_headers->addHeader('From', $sender);
  foreach( $recipients as $recip ) {
    $msg_headers->addHeader('To', $recip);
  }
  $msg_headers->addHeader('X-Kolab-Forwarded', 'TRUE');
  $msg_headers->addMIMEHeaders($toppart);
  copy_header( 'Content-Transfer-Encoding', $msg_headers, $headers );

  if (is_object($msg_headers)) {
    $headerArray = $toppart->encode($msg_headers->toArray(), $toppart->getCharset());
  } else {
    $headerArray = $toppart->encode($msg_headers, $toppart->getCharset());
  }

  // Inject message back into postfix
  require_once 'Mail.php';
  $mailer = &Mail::factory('SMTP', array('auth' => false, 'port' => 10026 ));

  $msg = $toppart->toString();
  /* Make sure the message has a trailing newline. */
  if (substr($msg, -1) != "\n") {
    $msg .= "\n";
  }

  $error = $mailer->send($recipients, $headerArray, $msg);
  if( PEAR::isError($error) ) {
    fwrite(STDOUT, $error->getMessage()."\n"); exit(EX_TEMPFAIL);
  }

  return true;
}

?>
