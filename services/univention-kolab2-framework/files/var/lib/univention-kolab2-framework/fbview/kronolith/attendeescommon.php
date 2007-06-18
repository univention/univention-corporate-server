<?php
/**
 * $Horde: kronolith/attendeescommon.php,v 1.1 2004/05/25 08:34:21 stuart Exp $
 *
 * Copyright 2004 Code Fusion  <http://www.codefusion.co.za/>
 *                Stuart Binge <s.binge@codefusion.co.za>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

// Load our configuration file
$params = array();
require '/kolab/etc/resmgr/fbview.conf';
require_once 'Horde/Text.php';

function getKronolithHash($xml_text)
{
    $xmldoc = @domxml_open_mem($xml_text, DOMXML_LOAD_PARSING +
        DOMXML_LOAD_COMPLETE_ATTRS + DOMXML_LOAD_SUBSTITUTE_ENTITIES +
        DOMXML_LOAD_DONT_KEEP_BLANKS, $error);

    if (!empty($error)) {
        // There were errors parsing the XML data - abort
        return false;
    }

    $noderoot = $xmldoc->document_element();
    $childnodes = $noderoot->child_nodes();

    $event_hash = array();

    // Build the event hash
    foreach ($childnodes as $value) {
        $event_hash[$value->tagname] = $value->get_content();
    }

    // Perform some sanity checks on the event
    if (
        empty($event_hash['uid']) ||
        empty($event_hash['start-date']) ||
        empty($event_hash['end-date'])
    ) {
        return false;
    }

    // Make sure we're allowed to view this event
    if (!empty($event_hash['sensitivity']) && $event_hash['sensitivity'] != 'public') {
        return false;
    }

    // Convert the Kolab hash to a corresponding Kronolith hash
    $kronolith_hash = array();
    $kronolith_hash['uid'] = $event_hash['uid'];
    $kronolith_hash['title'] = empty($event_hash['summary']) ? '' : $event_hash['summary'];
    $kronolith_hash['description'] = empty($event_hash['body']) ? '' : $event_hash['body'];
    $kronolith_hash['category'] = empty($event_hash['categories']) ? '' : $event_hash['categories'];
    $kronolith_hash['location'] = empty($event_hash['location']) ? '' : $event_hash['location'];

    $kronolith_hash['start_date'] = empty($event_hash['start-date']) ? '' :
        substr($event_hash['start-date'], 0, 10);
    $kronolith_hash['start_time'] = empty($event_hash['start-date']) ? '' :
        substr($event_hash['start-date'], 11, 8);

    $kronolith_hash['end_date'] = empty($event_hash['start-date']) ? '' :
        substr($event_hash['start-date'], 0, 10);
    $kronolith_hash['end_time'] = empty($event_hash['start-date']) ? '' :
        substr($event_hash['start-date'], 11, 8);

    return $kronolith_hash;
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

function removePassword( $url ) {
  $parsed = parse_url($url);
  if( !empty($parsed['pass']) ) $parsed['pass'] = 'XXX';
  return assembleUri($parsed);
}

function getFreeBusy($user)
{
    global $params;

    $url = str_replace('${USER}', $user, $params['freebusy_url']);

    $text = @file_get_contents($url);
    if ($text == false || empty($text)) {
        return PEAR::raiseError(sprintf(_("Unable to read free/busy information from %s"), 
					removePassword($url)));
    }

    $iCalendar = &new Horde_iCalendar();
    $iCalendar->parsevCalendar($text);
    $vfb = &$iCalendar->findComponent('VFREEBUSY');

    if ($vfb === false) {
        return PEAR::raiseError(sprintf(_("No free/busy information found from %s"), 
					removePassword($url)));
    }

    return $vfb;
}

function imapClose()
{
    global $imap;

    if (defined($imap) && $imap !== false) {
        @imap_close($imap);
    }
}

function imapSuccess()
{
    $errors = imap_errors();
    if ($errors === false) {
        return true;
    }

    return false;
}

function imapConnect($user)
{
    global $params, $imap, $fullmbox;

    // Handle virtual domains
    $prefix = $user;
    $suffix = '';
    if ($params['virtual_domains']) {
        list($prefix, $suffix) = split('@', $user);
        if ($params['append_domains'] && !empty($suffix)) {
            $suffix = '@' . $suffix;
        } else {
            $suffix = '';
        }
    }

    // Get our mailbox strings for use in the imap_X functions
    $server = '{' . $params['server'] . '/imap/notls/novalidate-cert/norsh}';
    $mailbox = "user/$prefix/" . $params['calendar_store'] . "$suffix";
    $fullmbox = $server . $mailbox;

    $imap = @imap_open($fullmbox, $params['calendar_user'], $params['calendar_pass'], CL_EXPUNGE);
    return imapSuccess();
}

function accessDenied($viewEventUID) {
    echo '<table border="0" width="400" cellspacing="0" cellpadding="0" style="padding-left:10px;">
<tr><td class="header"><b>' . htmlentities($viewEventUID) . '</b></td></tr>
<tr><td class="item">' . _("You are not authorized to view this event") . '</td></tr>
</table>
';
}

$attendee_view = &Kronolith_FreeBusy_View::singleton($view);

// Add the Free/Busy information for each attendee.
foreach ($attendees as $email => $status) {
    if ($status['attendance'] == KRONOLITH_PART_REQUIRED) {
        $vfb = getFreeBusy($email);
        //$vfb = Kronolith::getFreeBusy($email);
        if (!is_a($vfb, 'PEAR_Error')) {
            $attendee_view->addRequiredMember($vfb);
        } else {
            $notification->push(sprintf(_("Error retrieving free/busy information for %s: %s"), $email, $vfb->getMessage()));
        }
    } else if ($status['attendance'] == KRONOLITH_PART_OPTIONAL) {
        $vfb = Kronolith::getFreeBusy($email);
        if (!is_a($vfb, 'PEAR_Error')) {
            $attendee_view->addOptionalMember($vfb);
        } else {
            $notification->push(sprintf(_("Error retrieving free/busy information for %s: %s"), $email, $vfb->getMessage()));
        }
    }
}

$timestamp = Util::getFormData('timestamp', time());
list($vfb_html, $legend_html) = $attendee_view->render($timestamp);

require KRONOLITH_TEMPLATES . '/attendees/attendees.inc';

if (!is_null($viewEventUID)) {
    echo '<br /><br /><div align="center">';

    $imap = NULL;
    $fullmbox = '';

    if (imapConnect($viewEventUser)) {
        $messages = @imap_sort($imap, SORTDATE, 0, SE_UID, 'SUBJECT "' . $viewEventUID . '"');
        if (!imapSuccess() || !is_array($messages) || count($messages) < 1) {
            $messages = @imap_sort($imap, SORTDATE, 0, SE_UID, 'BODY "<uid>" BODY "' . $viewEventUID . '" BODY "</uid>"');
        }

        if (imapSuccess() && is_array($messages) && count($messages) > 0) {
            $msg = $messages[0];
            // Fetch the message
            $textmsg = @imap_fetchheader($imap, $msg, FT_UID | FT_PREFETCHTEXT);
            $textmsg .= @imap_body($imap, $msg, FT_UID);
            if (imapSuccess()) {
                $mimemsg = &MIME_Structure::parseTextMIMEMessage($textmsg);

                // Read in a kolab event object, if one exists
                $parts = $mimemsg->contentTypeMap();
                $event = false;
                foreach ($parts as $mimeid => $conttype) {
                    if ($conttype == 'application/x-vnd.kolab.event') {
                        $part = $mimemsg->getPart($mimeid);

                        $event_hash = getKronolithHash($part->toString());
                        if ($event_hash !== false) {
                            $event = new Kronolith_Event($GLOBALS['kronolith']);
                            $event->setID($event_hash['uid']);
                            $event->fromHash($event_hash);

                            $event->meetingID = $viewEventUID;
                            $category = $event->getCategory();
                            $description = $event->getDescription();
                            $location = $event->getLocation();
                            $status = Kronolith::statusToString($event->getStatus());
                            $attendees = $event->getAttendees();

                            $mylinks = array();
                            require KRONOLITH_TEMPLATES . '/view/view.inc';
                        } else {
                            accessDenied($viewEventUID);
                        }
                    }
                }

                // TODO: check if an event was actually retrieved
            } else {
                accessDenied($viewEventUID);
            }
        } else {
            accessDenied($viewEventUID);
        }
    } else {
        accessDenied($viewEventUID);
    }

    imapClose();

    echo '</div>';
}

require $registry->getParam('templates', 'horde') . '/common-footer.inc';
