<?php
/**
 * The MIME_Viewer_icalendar class displays vCalendar/iCalendar data
 * and provides an option to import the data into a calendar source,
 * if one is available.
 *
 * $Horde: framework/MIME/MIME/Viewer/icalendar.php,v 1.41 2004/04/07 14:43:10 chuck Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_icalendar extends MIME_Viewer {

    /**
     * Messages.
     */
    var $_msgs = array();

    var $_method = 'PUBLISH';

    /**
     * Render out the currently set icalendar contents.
     *
     * @access public
     *
     * @param optional array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        global $registry;

        require_once 'Horde/iCalendar.php';

        // Extract the data.
        $data = $this->mime_part->getContents();

        // Parse the iCal file.
        $vCal = &new Horde_iCalendar();
        if (!$vCal->parsevCalendar($data)) {
            return sprintf('<b>%s</b><br /><pre>%s</pre>', _("The calendar data is invalid"), htmlspecialchars($data));
        }

        // Get the method type
        $this->_method = $vCal->getAttribute('METHOD');

        // Get the iCalendar file components.
        $components = $vCal->getComponents();

        // Handle the action requests
        $actions = Util::getFormData('action', array());
        foreach ($actions as $key => $action) {
            switch ($action) {
            case 'import':
                // vFreebusy reply
                // vFreebusy publish
                // vEvent request
                // vEvent publish
                // vTodo publish
                // vJournal publish
                switch ($components[$key]->getType()) {
                case 'vEvent':
                    // Import into Kronolith
                    if ($registry->hasMethod('calendar/import')) {
                        $guid = $registry->call('calendar/import', array($components[$key]));
                        if (is_a($guid, 'PEAR_Error')) {
                            $this->_msgs[$key] = array('error', sprintf(_("There was an error importing the event: %s."), $guid->getMessage()));
                        } else {
                            $url = Horde::url($registry->link('calendar/show', array('guid' => $guid)));
                            $this->_msgs[$key] = array('success', _("The event has been added to your calendar.") .
                                                       '&nbsp;' . Horde::link($url, _("View event"), null, '_blank') . Horde::img('mime/icalendar.gif', _("View event"), null, $registry->getParam('graphics', 'horde')) . '</a>');
                        }
                    } else {
                        $this->_msgs[$key] = array('warning', _("This action is not supported."));
                    }
                    break;

                case 'vFreebusy':
                    // Import into Moment.
                    if ($registry->hasMethod('calendar/import_vfreebusy')) {
                        $res = $registry->call('calendar/import_vfreebusy', array($components[$key]));
                        if (is_a($res, 'PEAR_Error')) {
                            $this->_msgs[$key] = array('error', sprintf(_("There was an error importing user's free/busy information: %s."), $res->getMessage()));
                        } else {
                            $this->_msgs[$key] = array('success', _("The user's free/busy information was sucessfully stored."));
                        }
                    } else {
                        $this->_msgs[$key] = array('warning', _("This action is not supported."));
                    }
                    break;

                case 'vTodo':
                    // Import into Nag.
                    if ($registry->hasMethod('tasks/import')) {
                        $guid = $registry->call('tasks/import', array($components[$key], 'text/x-vtodo'));
                        if (is_a($guid, 'PEAR_Error')) {
                            $this->_msgs[$key] = array('error', sprintf(_("There was an error importing the task: %s."), $test->getMessage()));
                        } else {
                            $url = Horde::url($registry->link('tasks/show', array('guid', $guid)));
                            $this->_msgs[$key] = array('success', _("The task has been added to your tasklist.") .
                                                       '&nbsp;' . Horde::link($url, _("View task"), null, '_blank') . Horde::img('mime/icalendar.gif', _("View task"), null, $registry->getParam('graphics', 'horde')) . '</a>');
                        }
                    } else {
                        $this->_msgs[$key] = array('warning', _("This action is not supported."));
                    }
                    break;

                case 'vJournal':
                default:
                    $this->_msgs[$key] = array('warning', _("This action is not yet implemented."));
                }

                break;

            case 'accept':
            case 'deny':
            case 'tentative':
                // vEvent request
                if (array_key_exists($key, $components) && $components[$key]->getType() == 'vEvent') {
                    $vEvent = $components[$key];

                    require_once 'Horde/Identity.php';
                    require_once 'Horde/MIME.php';
                    require_once 'Horde/MIME/Headers.php';
                    require_once 'Horde/MIME/Part.php';
                    require_once 'Horde/Text.php';

                    // Find out who we are and update status.
                    $identity = &Identity::singleton();
                    $email = $identity->getValue('from_addr');
                    $cn = $identity->getValue('fullname');
                    switch ($action) {
                    case 'accept':
                        $vEvent->updateAttendee($email, 'ACCEPTED', $cn);
                        break;

                    case 'deny':
                        $vEvent->updateAttendee($email, 'DECLINED', $cn);
                        break;

                    case 'tentative':
                        $vEvent->updateAttendee($email, 'TENTATIVE', $cn);
                        break;
                    }

                    // Get the organizer details
                    $organizer = parse_url($vEvent->getAttribute('ORGANIZER'));
                    $organizerEmail = $organizer['path'];
                    $organizer = $vEvent->getAttribute('ORGANIZER', true);
                    $organizerName = array_key_exists('cn', $organizer) ? $organizer['cn'] : '';

                    // Build the reply
                    $vCal = &new Horde_iCalendar();
                    $vCal->setAttribute('PRODID', '-//The Horde Project//' . HORDE_AGENT_HEADER . '//EN');
                    $vCal->setAttribute('METHOD', 'REPLY');
                    $vCal->addComponent($vEvent);

                    $mime = &new MIME_Message();
                    $message = _("Attached is an iCalendar file reply to a request you sent");
                    $body = &new MIME_Part('text/plain', Text::wrap($message, 76, "\n"));

                    $ics = &new MIME_Part('text/calendar', $vCal->exportvCalendar());
                    $ics->setName('icalendar.ics');
                    $ics->setContentTypeParameter('METHOD', 'REPLY');

                    $mime->addPart($body);
                    $mime->addPart($ics);

                    // Build the reply headers
                    $msg_headers = &new MIME_Headers();
                    $msg_headers->addReceivedHeader();
                    $msg_headers->addMessageIdHeader();
                    $msg_headers->addHeader('Date', date('r'));
                    $msg_headers->addHeader('From', $email);
                    $msg_headers->addHeader('To', $organizerEmail);

                    $identity->setDefault(Util::getFormData('identity'));
                    $replyto = $identity->getValue('replyto_addr');
                    if (!empty($replyto) && ($replyto != $barefrom)) {
                        $msg_headers->addHeader('Reply-to', $replyto);
                    }
                    $msg_headers->addHeader('Subject', sprintf(_("Reply: %s"), $vEvent->getAttribute('SUMMARY')));
                    $msg_headers->addMIMEHeaders($mime);

                    // Send the reply
                    $status = $mime->send($organizerEmail, $msg_headers);
                    if (is_a($status, 'PEAR_Error')) {
                        $this->_msgs[$key] = array('error', sprintf(_("Error sending reply: %s."), $status->getMessage()));
                    } else {
                        $this->_msgs[$key] = array('success', _("Reply Sent."));
                    }
                } else {
                    $this->_msgs[$key] = array('warning', _("This action is not supported."));
                }
                break;

            case 'send':
                // vEvent refresh
                // vTodo refresh
            case 'reply':
                // vfreebusy request
                if (array_key_exists($key, $components) && $components[$key]->getType() == 'vFreebusy') {
                    $vFb = $components[$key];
                    $startStamp = $vFb->getAttribute('DTSTART');
                    if (is_a($startStamp, 'PEAR_Error')) {
                        $startStamp = time();
                    }
                    $endStamp = $vFb->getAttribute('DTEND');
                    if (is_a($endStamp, 'PEAR_Error')) {
                        $duration = $vFb->getAttribute('DURATION');
                        if (is_a($duration, 'PEAR_Error')) {
                            $endStamp = $startStamp + (60 * 24 * 3600);
                        } else {
                            $endStamp = $startStamp + $duration;
                        }
                    }
                    $vfb_reply = $registry->call('calendar/getFreeBusy', array('startStamp' => $startStamp,
                                                                               'endStamp' => $endStamp));
                    require_once 'Horde/Identity.php';
                    require_once 'Horde/MIME.php';
                    require_once 'Horde/MIME/Headers.php';
                    require_once 'Horde/MIME/Part.php';
                    require_once 'Horde/Text.php';

                    // Find out who we are and update status.
                    $identity = &Identity::singleton();
                    $email = $identity->getValue('from_addr');
                    $cn = $identity->getValue('fullname');

                    // Get the organizer details
                    $organizer = parse_url($vFb->getAttribute('ORGANIZER'));
                    $organizerEmail = $organizer['path'];
                    $organizer = $vFb->getAttribute('ORGANIZER', true);
                    $organizerName = array_key_exists('cn', $organizer) ? $organizer['cn'] : '';

                    // Build the reply
                    $vCal = &new Horde_iCalendar();
                    $vCal->setAttribute('PRODID', '-//The Horde Project//' . HORDE_AGENT_HEADER . '//EN');
                    $vCal->setAttribute('METHOD', 'REPLY');
                    $vCal->addComponent($vfb_reply);

                    $mime = &new MIME_Message();
                    $message = _("Attached is an iCalendar file reply to a request you sent");
                    $body = &new MIME_Part('text/plain', Text::wrap($message, 76, "\n"));

                    $ics = &new MIME_Part('text/calendar', $vCal->exportvCalendar());
                    $ics->setName('icalendar.ics');
                    $ics->setContentTypeParameter('METHOD', 'REPLY');

                    $mime->addPart($body);
                    $mime->addPart($ics);

                    // Build the reply headers
                    $msg_headers = &new MIME_Headers();
                    $msg_headers->addReceivedHeader();
                    $msg_headers->addMessageIdHeader();
                    $msg_headers->addHeader('Date', date('r'));
                    $msg_headers->addHeader('From', $email);
                    $msg_headers->addHeader('To', $organizerEmail);

                    $identity->setDefault(Util::getFormData('identity'));
                    $replyto = $identity->getValue('replyto_addr');
                    if (!empty($replyto) && ($replyto != $barefrom)) {
                        $msg_headers->addHeader('Reply-to', $replyto);
                    }
                    $msg_headers->addHeader('Subject', _("Free/Busy Request Response"));
                    $msg_headers->addMIMEHeaders($mime);

                    // Send the reply
                    $status = $mime->send($organizerEmail, $msg_headers);
                    if (is_a($status, 'PEAR_Error')) {
                        $this->_msgs[$key] = array('error', sprintf(_("Error sending reply: %s."), $status->getMessage()));
                    } else {
                        $this->_msgs[$key] = array('success', _("Reply Sent."));
                    }
                } else {
                    $this->_msgs[$key] = array('warning', _("Invalid Action selected for this component."));
                }
                break;

            case 'reply2m':
                // vFreebusy request.
                if (array_key_exists($key, $components) && $components[$key]->getType() == 'vFreebusy') {
                    $vFb = $components[$key];
                    $startStamp = time();
                    $endStamp = $startStamp + (60 * 24 * 3600);
                    $vfb_reply = $registry->call('calendar/getFreeBusy', array('startStamp' => $startStamp,
                                                                               'endStamp' => $endStamp));
                    require_once 'Horde/Identity.php';
                    require_once 'Horde/MIME.php';
                    require_once 'Horde/MIME/Headers.php';
                    require_once 'Horde/MIME/Part.php';
                    require_once 'Horde/Text.php';

                    // Find out who we are and update status.
                    $identity = &Identity::singleton();
                    $email = $identity->getValue('from_addr');
                    $cn = $identity->getValue('fullname');

                    // Get the organizer details
                    $organizer = parse_url($vFb->getAttribute('ORGANIZER'));
                    $organizerEmail = $organizer['path'];
                    $organizer = $vFb->getAttribute('ORGANIZER', true);
                    $organizerName = array_key_exists('cn', $organizer) ? $organizer['cn'] : '';

                    // Build the reply
                    $vCal = &new Horde_iCalendar();
                    $vCal->setAttribute('PRODID', '-//The Horde Project//' . HORDE_AGENT_HEADER . '//EN');
                    $vCal->setAttribute('METHOD', 'REPLY');
                    $vCal->addComponent($vfb_reply);

                    $mime = &new MIME_Message();
                    $message = _("Attached is an iCalendar file reply to a request you sent");
                    $body = &new MIME_Part('text/plain', Text::wrap($message, 76, "\n"));

                    $ics = &new MIME_Part('text/calendar', $vCal->exportvCalendar());
                    $ics->setName('icalendar.ics');
                    $ics->setContentTypeParameter('METHOD', 'REPLY');

                    $mime->addPart($body);
                    $mime->addPart($ics);

                    // Build the reply headers.
                    $msg_headers = &new MIME_Headers();
                    $msg_headers->addReceivedHeader();
                    $msg_headers->addMessageIdHeader();
                    $msg_headers->addHeader('Date', date('r'));
                    $msg_headers->addHeader('From', $email);
                    $msg_headers->addHeader('To', $organizerEmail);

                    $identity->setDefault(Util::getFormData('identity'));
                    $replyto = $identity->getValue('replyto_addr');
                    if (!empty($replyto) && ($replyto != $barefrom)) {
                        $msg_headers->addHeader('Reply-to', $replyto);
                    }
                    $msg_headers->addHeader('Subject', _("Free/Busy Request Response"));
                    $msg_headers->addMIMEHeaders($mime);

                    // Send the reply
                    $status = $mime->send($organizerEmail, $msg_headers);
                    if (is_a($status, 'PEAR_Error')) {
                        $this->_msgs[$key] = array('error', sprintf(_("Error sending reply: %s."), $status->getMessage()));
                    } else {
                        $this->_msgs[$key] = array('success', _("Reply Sent."));
                    }
                } else {
                    $this->_msgs[$key] = array('warning', _("Invalid Action selected for this component."));
                }
                break;

            case 'nosup':
                // vFreebusy request.
            default:
                $this->_msgs[$key] = array('warning', _("This action is not yet implemented."));
                break;
            }
        }

        // Create the HTML to display the iCal file.
        // Need to work out if we are inline and acutally need this
        $html = Util::bufferOutput('require', $registry->getParam('templates', 'horde') . '/common-header.inc');
        $html .= '<form method="post" name="iCal" action="' . Horde::selfURL(true) . '">';

        foreach ($components as $key => $component) {
            switch ($component->getType()) {
            case 'vEvent':
                $html .= $this->_vEvent($component, $key);
                break;

            case 'vTimeZone':
                // Ignore these.
                break;

            case 'vFreebusy':
                $html .= $this->_vFreebusy($component, $key);
                break;

            default:
                $html .= sprintf(_("Unhandled component of type: %s"), $component->getType());
            }
        }

        // Need to work out if we are inline and acutally need this
        $html .= "</form>";
        $html .= Util::bufferOutput('require', $registry->getParam('templates', 'horde') . '/common-footer.inc');

        return $html;
    }

    function _row($label, $value)
    {
        if (substr($label, 0, 2) == 'DT') {
            $value = strftime("%x %X", $value);
        }
        return '<tr><td valign="top" class="item">' . $label . '</td><td valign="top" class="item">' . $value . "</td></tr>\n";
    }

    /**
     * Return the html for a vFreebusy.
     */
    function _vFreebusy($vfb, $id)
    {
        global $registry, $conf;

        $html = '<table cellspacing="1" cellpadding="1" border="0">';

        $desc = '';
        $title = '';
        switch ($this->_method) {
        case 'PUBLISH':
            $desc = _("%s has sent you free/busy information.");
            $title = _("Free/Busy Information");
            break;

        case 'REQUEST':
            $desc = _("%s requests your free/busy information.");
            $title = _("Free/Busy Request");
            break;

        case 'REPLY':
            $desc = _("%s has replied to a free/busy request.");
            $title = _("Free/Busy Reply");
            break;
        }

        $desc = sprintf($desc, $vfb->getName());

        $html .= '<tr><td colspan="2" class="header">' . $title . '</td></tr>';
        $html .= '<tr><td colspan="2" class="control">' . $desc . '<br/>';
        $html .= _("Please select an action from the menu below.") . '</td></tr>';

        if (array_key_exists($id, $this->_msgs)) {
            $html .= '<tr><td colspan="2" class="smallheader"><b>' . Horde::img('alerts/' . $this->_msgs[$id][0] . '.gif', '', 'hspace="5"', $registry->getParam('graphics', 'horde')) . $this->_msgs[$id][1] . '</b></td></tr>';
        }

        $start = $vfb->getAttribute('DTSTART');
        if (!is_a($start, 'PEAR_Error')) {
            $html .= sprintf('<tr><td colspan="2" class="item"><b>%s:</b>&nbsp;%s</td></tr>', _("Start"), strftime($conf['mailbox']['date_format'] . ' ' . $conf['mailbox']['time_format'], $start));
        }

        $end = $vfb->getAttribute('DTEND');
        if (!is_a($end, 'PEAR_Error')) {
            $html .= sprintf('<tr><td colspan="2" class="item"><b>%s:</b>&nbsp;%s</td></tr>', _("End"), strftime("%x %X", $end));
        }

        $html .= '<tr><td colspan="2" class="control"><b>' . _("Actions") . ":</b><br/>";
        $html .= _("Choose an action:") . "&nbsp;<select name='action[$id]'>";

        switch ($this->_method) {
        case 'PUBLISH':
            if ($registry->hasMethod('calendar/import_vfreebusy')) {
                $html .= '<option value="import">' .   _("Remember the free/busy information.") . "</option>";
            } else {
                $html .= '<option value="nosup">' . _("Reply with Not Supported Message") . "</option>";
            }
            break;

        case 'REQUEST':
            if ($registry->hasMethod('calendar/getFreeBusy')) {
                $html .= '<option value="reply">' .   _("Reply with requested free/busy information.") . "</option>";
                $html .= '<option value="reply2m">' . _("Reply with free/busy for next 2 months.") . "</option>";
            } else {
                $html .= '<option value="nosup">' . _("Reply with Not Supported Message") . "</option>";
            }

            $html .= '<option value="deny">' . _("Deny request for free/busy information") . "</option>";
            break;

        case 'REPLY':
            if ($registry->hasMethod('calendar/import_vfreebusy')) {
                $html .= '<option value="import">' .   _("Remember the free/busy information.") . "</option>";
            } else {
                $html .= '<option value="nosup">' . _("Reply with Not Supported Message") . "</option>";
            }
            break;
        }

        $html .= sprintf('</select>&nbsp<input type="submit" class="button" value="%s" /><br />', _("OK"));
        $html .= "</td></tr>";
        $html .= '</table>';
        return $html;
    }

    /**
     * Return the html for a vEvent
     */
    function _vEvent($vevent, $id)
    {
        global $registry, $conf;

        $html = '<table cellspacing="1" cellpadding="1" border="0">';

        $desc = '';
        $title = '';
        switch ($this->_method) {
        case 'PUBLISH':
            $desc = _("%s wishes to make you aware of %s.");
            $title = _("Meeting Information");
            break;

        case 'REQUEST':
            // Check that you are one of the attendess here
            $desc = _("%s requests your presence at %s.");
            $title = _("Meeting Proposal");
            break;

        case 'ADD':
            $desc = _("%s wishes to add to %s.");
            $title = _("Meeting Update");
            break;

        case 'REFRESH':
            $desc = _("%s wishes to receive the latest information about %s.");
            $title = _("Meeting Update Request");
            // Fetch the event info from the UID here
            break;

        case 'REPLY':
            $desc = _("%s has replied to the invitation to %s.");
            $title = _("Meeting Reply");
            // Fetch the event info from the UID here
            break;

        case 'CANCEL':
            $desc = _("%s has cancelled %s.");
            $title = _("Meeting Cancellation");
            // Fetch the event info from the UID here
            break;
        }

        $desc = sprintf($desc, $vevent->organizerName(), $vevent->getAttribute('SUMMARY'));

        $html .= '<tr><td colspan="2" class="header">' . $title . '</td></tr>';
        $html .= '<tr><td colspan="2" class="control">' . $desc . '<br/>';
        $html .= _("Please review the following information, and then select an action from the menu below.") . '</td></tr>';

        if (array_key_exists($id, $this->_msgs)) {
            $html .= '<tr><td colspan="2" class="smallheader"><b>' . Horde::img('alerts/' . $this->_msgs[$id][0] . '.gif', '', 'hspace="5"', $registry->getParam('graphics', 'horde')) . $this->_msgs[$id][1] . '</b></td></tr>';
        }

        $start = $vevent->getAttribute('DTSTART');
        if (!is_a($start, 'PEAR_Error')) {
            $html .= sprintf('<tr><td colspan="2" class="item"><b>%s:</b>&nbsp;%s</td></tr>', _("Start"), strftime($conf['mailbox']['date_format'] . ' ' . $conf['mailbox']['time_format'], $start));
        }

        $end = $vevent->getAttribute('DTEND');
        if (!is_a($end, 'PEAR_Error')) {
            $html .= sprintf('<tr><td colspan="2" class="item"><b>%s:</b>&nbsp;%s</td></tr>', _("End"), strftime("%x %X", $end));
        }

        $sum = $vevent->getAttribute('SUMMARY');
        if (!is_a($sum, 'PEAR_Error')) {
            $html .= sprintf('<tr><td colspan="2" class="item"><b>%s:</b>&nbsp;%s</td></tr>', _("Summary"), $sum);
        } else {
            $html .= sprintf('<tr><td colspan="2" class="item"><b>%s:</b>&nbsp;<i>%s</i></td></tr>', _("Summary"), _("None"));
        }

        $desc = $vevent->getAttribute('DESCRIPTION');
        if (!is_a($desc, 'PEAR_Error')) {
            $html .= sprintf('<tr><td colspan="2" class="item"><b>%s:</b>&nbsp;%s</td></tr>', _("Description"), $desc);
        }

        $loc = $vevent->getAttribute('LOCATION');
        if (!is_a($loc, 'PEAR_Error')) {
            $html .= sprintf('<tr><td colspan="2" class="item"><b>%s:</b>&nbsp;%s</td></tr>', _("Location"), $loc);
        }

        $attendees = $vevent->getAttribute('ATTENDEE');
        $params    = $vevent->getAttribute('ATTENDEE', true);

        if (!is_a($attendees, 'PEAR_Error')) {
            $html .= sprintf('<tr><td colspan="2" class="item"><b>%s:</b><br/>', _("Attendees"));
            if (!is_array($attendees)) {
                $attendees = array($attendees);
                $params    = array($params);
            }

            $html .= sprintf('<table width="100%%"><tr><th align="left">%s</th><th align="left">%s</th><th align="left">%s</th></tr>', _("Name"), _("Role"), _("Status"));
            foreach ($attendees as $key => $attendee) {
                $attendee = parse_url($attendee);
                $attendee = $attendee['path'];

                if (array_key_exists('CN', $params[$key])) {
                    $attendee = $params[$key]['CN'];
                }

                $role = _("Required Participant");
                if (array_key_exists('ROLE', $params[$key])) {
                    switch ($params[$key]['ROLE']) {
                    case 'CHAIR':
                        $role = _("Chair Person");
                        break;

                    case 'OPT-PARTICIPANT':
                        $role = _("Optional Participant");
                        break;

                    case 'NON-PARTICIPANT':
                        $role = _("Non Participant");
                        break;

                    case 'REQ-PARTICIPANT':
                    default:
                        // Already set above.
                        break;
                    }
                }

                $status = _("Awaiting Response");
                if (array_key_exists('PARTSTAT', $params[$key])) {
                    $status = $this->_partstatToString($params[$key]['PARTSTAT'], $status);
                }

                $html .= sprintf('<tr><td>%s</td><td>%s</td><td>%s</td></tr>', $attendee, $role, $status);
            }
            $html .= "</table>";
            $html .= '</td></tr>';
        }

        $html .= '<tr><td colspan="2" class="control"><b>' . _("Actions") . ":</b><br/>";
        $html .= _("Choose an action:") . "&nbsp;<select name='action[$id]'>";

        switch ($this->_method) {
        case 'PUBLISH':
            if ($registry->hasMethod('calendar/import')) {
                $html .= '<option value="import">' .   _("Add this to my calendar") . "</option>";
            }
            break;

        case 'REQUEST':
            if ($registry->hasMethod('calendar/import')) {
                $html .= '<option value="import">' .   _("Add this to my calendar") . "</option>";
            }

            $html .= '<option value="accept">' . _("Accept request") . "</option>";
            $html .= '<option value="tentative">' . _("Tentatively Accept request") . "</option>";
            $html .= '<option value="deny">' . _("Deny request") . "</option>";
            $html .= '<option value="delegate">' . _("Delegate position") . "</option>";
            break;

        case 'REPLY':
            if ($registry->hasMethod('calendar/update_meeting')) {
                $html .= '<option value="import">' . _("Update respondent status") . "</option>";
            }
            break;

        case 'REFRESH':
            $html .= '<option value="send">' . _("Send Latest Information") . "</option>";
            break;

        case 'CANCEL':
            if ($registry->hasMethod('calendar/delete_event')) {
                $html .= '<option value="import">' . _("Remove from my calendar") . "</option>";
            }
            break;
        }

        $html .= sprintf('</select>&nbsp<input type="submit" class="button" value="%s" /><br />', _("OK"));
        $html .= '</td></tr>';
        $html .= '</table>';
        return $html;
    }

    /**
     * Translate the Participation status to string
     *
     * @param string    $value  The value of PARTSTAT
     * @param string    $default The value to return as default.
     *
     * @return string   The translated string.
     */
    function _partstatToString($value, $default = null)
    {
        switch ($value) {
        case 'ACCEPTED':
            return _("Accepted");
            break;

        case 'DECLINED':
            return _("Declined");
            break;

        case 'TENTATICE':
            return _("Tentatively Accepted");
            break;

        case 'DELEGATED':
            return _("Delegated");
            break;

        case 'COMPLETED':
            return _("Completed");
            break;

        case 'IN-PROCESS':
            return _("In Process");
            break;

        case 'NEEDS-ACTION':
        default:
            return is_null($default) ? _("Needs Action") : $default;
        }
    }

    /**
     * Return text/html as the content-type.
     *
     * @return string "text/html" constant
     */
    function getType()
    {
        return 'text/html';
    }

}
