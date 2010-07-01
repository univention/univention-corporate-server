<?php
/**
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Outlook.php,v 1.3.2.4 2009-03-06 08:43:13 wrobel Exp $
 *
 * @package Kolab_Filter
 */

/* Load the iCal handling */
require_once 'Horde/iCalendar.php';

/* Load MIME handlers */
require_once 'Horde/MIME.php';
require_once 'Horde/MIME/Message.php';
require_once 'Horde/MIME/Headers.php';
require_once 'Horde/MIME/Part.php';
require_once 'Horde/MIME/Structure.php';

/**
 * Provides Mail rewriting for malformed Outlook messages
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Outlook.php,v 1.3.2.4 2009-03-06 08:43:13 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Filter
 */
class Kolab_Filter_Outlook
{

    /**
     * Returns a parsed MIME message
     *
     * @param string $text   The text of the message
     *
     * @return array An array with the MIME parsed headers and body.
     */
    function _mimeParse(&$text)
    {
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

    /**
     * Add a header entry.
     *
     * @param string        $name        The name of the header entry.
     * @param MIME_Headers  $msg_header  A link to the MIME header handler.
     * @param array         $headerarray The list of current headers.
     */
    function _copyHeader($name, &$msg_headers, &$headerarray)
    {
        $lname = strtolower($name);
        if (array_key_exists($lname, $headerarray)) {
            if (is_array($headerarray[$lname])) {
                foreach ($headerarray[$lname] as $h) {
                    $msg_headers->addHeader($name, $h);	
                }
            } else {
                $msg_headers->addHeader($name, $headerarray[$lname]);
            }
        }
    }

    /**
     * Yet another problem: Outlook seems to remove the organizer from
     * the iCal when forwarding -- we put the original sender back in
     * as organizer.
     *
     * @param string        $icaltext  The ical message.
     * @param MIME_Headers  $from      The message sender.
     */
    function _addOrganizer(&$icaltxt, $from)
    {
        global $conf;

        if (isset($conf['kolab']['filter']['email_domain'])) {
            $email_domain = $conf['kolab']['filter']['email_domain'];
        } else {
            $email_domain = 'localhost';
        }

        $iCal = &new Horde_iCalendar();
        $iCal->parsevCalendar($icaltxt);
        $vevent =& $iCal->findComponent('VEVENT');
        if ($vevent) {
            $organizer = $vevent->getAttribute('ORGANIZER', true);
            if (is_a($organizer, 'PEAR_Error')) {
                $adrs = imap_rfc822_parse_adrlist($from, $email_domain);
                if (count($adrs) > 0) {
                    $org_email = 'mailto:'.$adrs[0]->mailbox.'@'.$adrs[0]->host;
                    $org_name  = $adrs[0]->personal;
                    if ($org_name) {
                        $vevent->setAttribute('ORGANIZER', $org_email, 
                                              array( 'CN' => $org_name), false);
                    } else {
                        $vevent->setAttribute('ORGANIZER', $org_email, 
					    array(), false);
                    }
                    Horde::logMessage(sprintf("Adding missing organizer '%s <%s>' to iCal.",
                                              $org_name, $org_email), 
                                      __FILE__, __LINE__, PEAR_LOG_DEBUG);
                    $icaltxt = $iCal->exportvCalendar();
                }
            }
        }
    }

    /**
     * Yet another Outlook problem: Some versions of Outlook seems to be incapable
     * of handling non-ascii characters properly in text/calendar parts of
     * a multi-part/mixed mail which we use for forwarding.
     * As a solution, we encode common characters as humanreadable
     * two-letter ascii.
     *
     * @param string  $text  The message text.
     *
     * @return string The text with umlauts replaced.
     */
    function _recodeToAscii( $text ) {
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

        return $text;
    }

    /**
     * Clean up iCal messages from Outlook.
     *
     * @param string  $fqhostname  The name of this host.
     * @param string  $sender      The mail address of the sender.
     * @param array   $recipients  The recipients of the message.
     * @param string  $origfrom    The mail address of the original sender.
     * @param string  $subject     The mail subject.
     * @param string  $tmpfname    Path to the temporary message store.
     *
     * @return boolena|PEAR_Error True if the message was successfully rewritten.
     */
    function embedICal($fqhostname, $sender, $recipients, $origfrom, $subject,
		       $tmpfname, $transport)
    {
        Horde::logMessage(sprintf("Encapsulating iCal message forwarded by %s", $sender), 
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $forwardtext = "This is an invitation forwarded by outlook and\n".
            "was rectified by the Kolab server.\n".
            "The invitation was originally sent by\n%s.\n\n".
            "Diese Einladung wurde von Outlook weitergeleitet\n".
            "und vom Kolab-Server in gute Form gebracht.\n".
            "Die Einladung wurde ursprünglich von\n%s geschickt.\n";

        // Read in message text
        $requestText = '';
        $handle = @fopen($tmpfname, "r");
        if ($handle === false) {
            $msg = $php_errormsg;
            return PEAR::raiseError(sprintf("Error: Could not open %s for writing: %s",
                                            $tmpfname, $msg),
                                    OUT_LOG | EX_IOERR);
        }
        while (!feof($handle)) {
            $requestText .= fread($handle, 8192);
        }
        fclose($handle);

        // Parse existing message
        list( $headers, $mime) = Kolab_Filter_Outlook::_mimeParse($requestText);
        $parts = $mime->contentTypeMap();
        if (count($parts) != 1 || $parts[1] != 'text/calendar') {
            Horde::logMessage("Message does not contain exactly one toplevel text/calendar part, passing through.", 
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            return false;
        }
        $basepart = $mime->getBasePart();

        // Construct new MIME message with original message attached
        $toppart = &new MIME_Message();
        $dorigfrom = Mail_mimeDecode::_decodeHeader($origfrom);
        $textpart = &new MIME_Part('text/plain', sprintf($forwardtext,$dorigfrom,$dorigfrom), 'UTF-8' );
        $ical_txt = $basepart->transferDecode();
        Kolab_Filter_Outlook::_addOrganizer($ical_txt, $dorigfrom);
        $msgpart = &new MIME_Part($basepart->getType(), Kolab_Filter_Outlook::_recodeToAscii($ical_txt), 
                                  $basepart->getCharset() );

        $toppart->addPart($textpart);
        $toppart->addPart($msgpart);

        // Build the reply headers.
        $msg_headers = &new MIME_Headers();
        Kolab_Filter_Outlook::_copyHeader( 'Received', $msg_headers, $headers );
        //$msg_headers->addReceivedHeader();
        $msg_headers->addMessageIdHeader();
        Kolab_Filter_Outlook::_copyHeader( 'Date', $msg_headers, $headers );
        Kolab_Filter_Outlook::_copyHeader( 'Resent-Date', $msg_headers, $headers );
        Kolab_Filter_Outlook::_copyHeader( 'Subject', $msg_headers, $headers );
        $msg_headers->addHeader('From', $sender);
        $msg_headers->addHeader('To', join(', ', $recipients));
        $msg_headers->addHeader('X-Kolab-Forwarded', 'TRUE');
        $msg_headers->addMIMEHeaders($toppart);
        Kolab_Filter_Outlook::_copyHeader( 'Content-Transfer-Encoding', $msg_headers, $headers );

        if (is_object($msg_headers)) {
            $headerArray = $toppart->encode($msg_headers->toArray(), $toppart->getCharset());
        } else {
            $headerArray = $toppart->encode($msg_headers, $toppart->getCharset());
        }

        return Kolab_Filter_Outlook::_inject($toppart, $recipients, $msg_headers, $sender, $transport);
    }

    function _inject(&$toppart, $recipients, $msg_headers, $sender, $transport)
    {
        global $conf;

        if (isset($conf['kolab']['filter']['smtp_host'])) {
            $host = $conf['kolab']['filter']['smtp_host'];
        } else {
            $host = 'localhost';
        }
        if (isset($conf['kolab']['filter']['smtp_port'])) {
            $port = $conf['kolab']['filter']['smtp_port'];
        } else {
            $port = 10025;
        }

        $transport = &Horde_Kolab_Filter_Transport::factory($transport, 
                                               array('host' => $host, 
                                                     'port' => $port));

        $result = $transport->start($sender, $recipients);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $transport->data($msg_headers->toString() . $toppart->toString());
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $transport->end();
    }
}
