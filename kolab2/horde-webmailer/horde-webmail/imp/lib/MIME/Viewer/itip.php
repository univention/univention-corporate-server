<?php
/**
 * The IMP_MIME_Viewer_itip class displays vCalendar/iCalendar data
 * and provides an option to import the data into a calendar source,
 * if one is available.
 *
 * $Horde: imp/lib/MIME/Viewer/itip.php,v 1.37.2.47 2009-05-14 10:12:26 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_itip extends MIME_Viewer {

    /**
     * Force viewing of a part inline, regardless of the Content-Disposition
     * of the MIME Part.
     *
     * @var boolean
     */
    var $_forceinline = true;

    /**
     * The messages to output to the user.
     *
     * @var array
     */
    var $_msgs = array();

    /**
     * The method as marked in either the iCal structure or message header.
     *
     * @var string
     */
    var $_method = 'PUBLISH';

    /**
     * The headers of the message.
     *
     * @var string
     */
    var $_headers;

    /**
     * Render out the currently set iCalendar contents.
     *
     * @param array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        global $registry;
        require_once 'Horde/iCalendar.php';

        // Extract the data.
        $data = $this->mime_part->getContents();
        if (empty($this->_headers) && is_a($params[0], 'IMP_Contents')) {
            $this->_headers = $params[0]->getHeaderOb();
        }

        // Parse the iCal file.
        $vCal = new Horde_iCalendar();
        if (!$vCal->parsevCalendar($data, 'VCALENDAR', $this->mime_part->getCharset())) {
            return '<h1>' . _("The calendar data is invalid") . '</h1>' .
                '<pre>' . htmlspecialchars($data) . '</pre>';
        }

        // Check if we got vcard data with the wrong vcalendar mime type.
        $c = $vCal->getComponentClasses();
        if (count($c) == 1 && !empty($c['horde_icalendar_vcard'])) {
            $vcard_renderer = &MIME_Viewer::factory($this->mime_part, 'text/x-vcard');
            return $vcard_renderer->render($params);
        }

        // Get the method type.
        $this->_method = $vCal->getAttribute('METHOD');
        if (is_a($this->_method, 'PEAR_Error')) {
            $this->_method = '';
        }

        // Get the iCalendar file components.
        $components = $vCal->getComponents();

        // Handle the action requests.
        $actions = Util::getFormData('action', array());
        foreach ($actions as $key => $action) {
            $this->_msgs[$key] = array();
            switch ($action) {
            case 'delete':
                // vEvent cancellation.
                if ($registry->hasMethod('calendar/delete')) {
                    $guid = $components[$key]->getAttribute('UID');
                    $event = $registry->call('calendar/delete', array('guid' => $guid));
                    if (is_a($event, 'PEAR_Error')) {
                        $this->_msgs[$key][] = array('error', _("There was an error deleting the event:") . ' ' . $event->getMessage());
                    } else {
                        $this->_msgs[$key][] = array('success', _("Event successfully deleted."));
                    }
                } else {
                    $this->_msgs[$key][] = array('warning', _("This action is not supported."));
                }
                break;

            case 'update':
                // vEvent reply.
                if ($registry->hasMethod('calendar/updateAttendee')) {
                    $event = $registry->call('calendar/updateAttendee', array('response' => $components[$key], 'sender' => $params[0]->getFromAddress()));
                    if (is_a($event, 'PEAR_Error')) {
                        $this->_msgs[$key][] = array('error', _("There was an error updating the event:") . ' ' . $event->getMessage());
                    } else {
                        $this->_msgs[$key][] = array('success', _("Respondent Status Updated."));
                    }
                } else {
                    $this->_msgs[$key][] = array('warning', _("This action is not supported."));
                }
                break;

            case 'import':
            case 'acceptimport':
                // vFreebusy reply.
                // vFreebusy publish.
                // vEvent request.
                // vEvent publish.
                // vTodo publish.
                // vJournal publish.
                switch ($components[$key]->getType()) {
                case 'vEvent':
                    $handled = false;
                    $guid = $components[$key]->getAttribute('UID');
                    // Check if this is an update.
                    if ($registry->hasMethod('calendar/export') &&
                        !is_a($registry->call('calendar/export', array('uid' => $guid, 'contentType' => 'text/calendar')), 'PEAR_Error')) {
                        // Try to update in calendar.
                        if ($registry->hasMethod('calendar/replace')) {
                            $result = $registry->call('calendar/replace', array('uid' => $guid, 'content' => $components[$key], 'contentType' => $this->mime_part->getType()));
                            if (is_a($result, 'PEAR_Error')) {
                                // Could be a missing permission.
                                $this->_msgs[$key][] = array('warning', _("There was an error updating the event:") . ' ' . $result->getMessage() . '. ' . _("Trying to import the event instead."));
                            } else {
                                $handled = true;
                                $url = Horde::url($registry->link('calendar/show', array('uid' => $guid)));
                                $this->_msgs[$key][] = array('success', _("The event was updated in your calendar.") .
                                                             '&nbsp;' . Horde::link($url, _("View event"), null, '_blank') . Horde::img('mime/icalendar.png', _("View event"), null, $registry->getImageDir('horde')) . '</a>');
                            }
                        }
                    }
                    if (!$handled && $registry->hasMethod('calendar/import')) {
                        // Import into calendar.
                        $handled = true;
                        $guid = $registry->call('calendar/import', array('content' => $components[$key], 'contentType' => $this->mime_part->getType()));
                        if (is_a($guid, 'PEAR_Error')) {
                            $this->_msgs[$key][] = array('error', _("There was an error importing the event:") . ' ' . $guid->getMessage());
                        } else {
                            $url = Horde::url($registry->link('calendar/show', array('uid' => $guid)));
                            $this->_msgs[$key][] = array('success', _("The event was added to your calendar.") .
                                                         '&nbsp;' . Horde::link($url, _("View event"), null, '_blank') . Horde::img('mime/icalendar.png', _("View event"), null, $registry->getImageDir('horde')) . '</a>');
                        }
                    }
                    if (!$handled) {
                        $this->_msgs[$key][] = array('warning', _("This action is not supported."));
                    }
                    break;

                case 'vFreebusy':
                    // Import into Kronolith.
                    if ($registry->hasMethod('calendar/import_vfreebusy')) {
                        $res = $registry->call('calendar/import_vfreebusy', array($components[$key]));
                        if (is_a($res, 'PEAR_Error')) {
                            $this->_msgs[$key][] = array('error', _("There was an error importing user's free/busy information:") . ' ' . $res->getMessage());
                        } else {
                            $this->_msgs[$key][] = array('success', _("The user's free/busy information was sucessfully stored."));
                        }
                    } else {
                        $this->_msgs[$key][] = array('warning', _("This action is not supported."));
                    }
                    break;

                case 'vTodo':
                    // Import into Nag.
                    if ($registry->hasMethod('tasks/import')) {
                        $guid = $registry->call('tasks/import', array($components[$key], $this->mime_part->getType()));
                        if (is_a($guid, 'PEAR_Error')) {
                            $this->_msgs[$key][] = array('error', _("There was an error importing the task:") . ' ' . $guid->getMessage());
                        } else {
                            $url = Horde::url($registry->link('tasks/show', array('uid' => $guid)));
                            $this->_msgs[$key][] = array('success', _("The task has been added to your tasklist.") .
                                                         '&nbsp;' . Horde::link($url, _("View task"), null, '_blank') . Horde::img('mime/icalendar.png', _("View task"), null, $registry->getImageDir('horde')) . '</a>');
                        }
                    } else {
                        $this->_msgs[$key][] = array('warning', _("This action is not supported."));
                    }
                    break;

                case 'vJournal':
                default:
                    $this->_msgs[$key][] = array('warning', _("This action is not yet implemented."));
                }

                if ($action != 'acceptimport') {
                    break;
                }

            case 'accept':
            case 'acceptimport':
            case 'deny':
            case 'tentative':
                // vEvent request.
                if (isset($components[$key]) &&
                    $components[$key]->getType() == 'vEvent') {
                    $vEvent = $components[$key];

                    // Get the organizer details.
                    $organizer = $vEvent->getAttribute('ORGANIZER');
                    if (is_a($organizer, 'PEAR_Error')) {
                        break;
                    }
                    $organizer = parse_url($organizer);
                    $organizerEmail = $organizer['path'];
                    $organizer = $vEvent->getAttribute('ORGANIZER', true);
                    $organizerName = isset($organizer['cn']) ? $organizer['cn'] : '';

                    require_once 'Horde/Identity.php';
                    require_once 'Horde/MIME.php';
                    require_once 'Horde/MIME/Headers.php';
                    require_once 'Horde/MIME/Part.php';

                    // Build the reply.
                    $vCal = new Horde_iCalendar();
                    $vCal->setAttribute('PRODID', '-//The Horde Project//' . HORDE_AGENT_HEADER . '//EN');
                    $vCal->setAttribute('METHOD', 'REPLY');

                    $vEvent_reply = &Horde_iCalendar::newComponent('vevent', $vCal);
                    $vEvent_reply->setAttribute('UID', $vEvent->getAttribute('UID'));
                    if (!is_a($vEvent->getAttribute('SUMMARY'), 'PEAR_error')) {
                        $vEvent_reply->setAttribute('SUMMARY', $vEvent->getAttribute('SUMMARY'));
                    }
                    if (!is_a($vEvent->getAttribute('DESCRIPTION'), 'PEAR_error')) {
                        $vEvent_reply->setAttribute('DESCRIPTION', $vEvent->getAttribute('DESCRIPTION'));
                    }
                    $dtstart = $vEvent->getAttribute('DTSTART', true);
                    $vEvent_reply->setAttribute('DTSTART', $vEvent->getAttribute('DTSTART'), array_pop($dtstart));
                    if (!is_a($vEvent->getAttribute('DTEND'), 'PEAR_error')) {
                        $dtend = $vEvent->getAttribute('DTEND', true);
                        $vEvent_reply->setAttribute('DTEND', $vEvent->getAttribute('DTEND'), array_pop($dtend));
                    } else {
                        $duration = $vEvent->getAttribute('DURATION', true);
                        $vEvent_reply->setAttribute('DURATION', $vEvent->getAttribute('DURATION'), array_pop($duration));
                    }
                    if (!is_a($vEvent->getAttribute('SEQUENCE'), 'PEAR_error')) {
                        $vEvent_reply->setAttribute('SEQUENCE', $vEvent->getAttribute('SEQUENCE'));
                    }
                    $vEvent_reply->setAttribute('ORGANIZER', $vEvent->getAttribute('ORGANIZER'), array_pop($organizer));

                    // Find out who we are and update status.
                    $identity = &Identity::singleton(array('imp', 'imp'));
                    $attendees = $vEvent->getAttribute('ATTENDEE');
                    if (!is_array($attendees)) {
                        $attendees = array($attendees);
                    }
                    foreach ($attendees as $attendee) {
                        $attendee = preg_replace('/mailto:/i', '', $attendee);
                        if (!is_null($id = $identity->getMatchingIdentity($attendee))) {
                            $identity->setDefault($id);
                            break;
                        }
                    }
                    $name = $email = $identity->getFromAddress();
                    $params = array();
                    $cn = $identity->getValue('fullname');
                    if (!empty($cn)) {
                        $name = $params['CN'] = $cn;
                    }

                    switch ($action) {
                    case 'accept':
                    case 'acceptimport':
                        $message = sprintf(_("%s has accepted."), $name);
                        $subject = _("Accepted: ") . $vEvent->getAttribute('SUMMARY');
                        $params['PARTSTAT'] = 'ACCEPTED';
                        break;

                    case 'deny':
                        $message = sprintf(_("%s has declined."), $name);
                        $subject = _("Declined: ") . $vEvent->getAttribute('SUMMARY');
                        $params['PARTSTAT'] = 'DECLINED';
                        break;

                    case 'tentative':
                        $message = sprintf(_("%s has tentatively accepted."), $name);
                        $subject = _("Tentative: ") . $vEvent->getAttribute('SUMMARY');
                        $params['PARTSTAT'] = 'TENTATIVE';
                        break;
                    }

                    $vEvent_reply->setAttribute('ATTENDEE', 'mailto:' . $email, $params);
                    $vCal->addComponent($vEvent_reply);

                    $mime = new MIME_Part('multipart/alternative');
                    $body = new MIME_Part('text/plain',
                                          String::wrap($message, 76, "\n"),
                                          NLS::getCharset());

                    $ics = new MIME_Part('text/calendar', $vCal->exportvCalendar());
                    $ics->setName('event-reply.ics');
                    $ics->setContentTypeParameter('METHOD', 'REPLY');
                    $ics->setCharset(NLS::getCharset());

                    $mime->addPart($body);
                    $mime->addPart($ics);
                    $mime = &MIME_Message::convertMimePart($mime);

                    // Build the reply headers.
                    $msg_headers = new MIME_Headers();
                    $msg_headers->addReceivedHeader();
                    $msg_headers->addMessageIdHeader();
                    $msg_headers->addHeader('Date', date('r'));
                    $msg_headers->addHeader('From', $email);
                    $msg_headers->addHeader('To', $organizerEmail);

                    $identity->setDefault(Util::getFormData('identity'));
                    $replyto = $identity->getValue('replyto_addr');
                    if (!empty($replyto) && ($replyto != $email)) {
                        $msg_headers->addHeader('Reply-to', $replyto);
                    }
                    $msg_headers->addHeader('Subject', MIME::encode($subject, NLS::getCharset()));
                    $msg_headers->addMIMEHeaders($mime);

                    // Send the reply.
                    $mail_driver = $this->_getMailDriver();
                    $status = $mime->send($organizerEmail, $msg_headers,
                                          $mail_driver['driver'],
                                          $mail_driver['params']);
                    if (is_a($status, 'PEAR_Error')) {
                        $this->_msgs[$key][] = array('error', sprintf(_("Error sending reply: %s."), $status->getMessage()));
                    } else {
                        $this->_msgs[$key][] = array('success', _("Reply Sent."));
                    }
                } else {
                    $this->_msgs[$key][] = array('warning', _("This action is not supported."));
                }
                break;

            case 'send':
                // vEvent refresh.
                if (isset($components[$key]) &&
                    $components[$key]->getType() == 'vEvent') {
                    $vEvent = $components[$key];
                }

                // vTodo refresh.
            case 'reply':
            case 'reply2m':
                // vfreebusy request.
                if (isset($components[$key]) &&
                    $components[$key]->getType() == 'vFreebusy') {
                    $vFb = $components[$key];

                    // Get the organizer details.
                    $organizer = $vFb->getAttribute('ORGANIZER');
                    if (is_a($organizer, 'PEAR_Error')) {
                        break;
                    }
                    $organizer = parse_url($organizer);
                    $organizerEmail = $organizer['path'];
                    $organizer = $vFb->getAttribute('ORGANIZER', true);
                    $organizerName = isset($organizer['cn']) ? $organizer['cn'] : '';

                    if ($action == 'reply2m') {
                        $startStamp = time();
                        $endStamp = $startStamp + (60 * 24 * 3600);
                    } else {
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
                    }
                    $vfb_reply = $registry->call('calendar/getFreeBusy',
                                                 array('startStamp' => $startStamp,
                                                       'endStamp' => $endStamp));
                    require_once 'Horde/Identity.php';
                    require_once 'Horde/MIME.php';
                    require_once 'Horde/MIME/Headers.php';
                    require_once 'Horde/MIME/Part.php';

                    // Find out who we are and update status.
                    $identity = &Identity::singleton();
                    $email = $identity->getFromAddress();

                    // Build the reply.
                    $vCal = new Horde_iCalendar();
                    $vCal->setAttribute('PRODID', '-//The Horde Project//' . HORDE_AGENT_HEADER . '//EN');
                    $vCal->setAttribute('METHOD', 'REPLY');
                    $vCal->addComponent($vfb_reply);

                    $mime = new MIME_Message();
                    $message = _("Attached is a reply to a calendar request you sent.");
                    $body = new MIME_Part('text/plain',
                                          String::wrap($message, 76, "\n"),
                                          NLS::getCharset());

                    $ics = new MIME_Part('text/calendar', $vCal->exportvCalendar());
                    $ics->setName('icalendar.ics');
                    $ics->setContentTypeParameter('METHOD', 'REPLY');
                    $ics->setCharset(NLS::getCharset());

                    $mime->addPart($body);
                    $mime->addPart($ics);

                    // Build the reply headers.
                    $msg_headers = new MIME_Headers();
                    $msg_headers->addReceivedHeader();
                    $msg_headers->addMessageIdHeader();
                    $msg_headers->addHeader('Date', date('r'));
                    $msg_headers->addHeader('From', $email);
                    $msg_headers->addHeader('To', $organizerEmail);

                    $identity->setDefault(Util::getFormData('identity'));
                    $replyto = $identity->getValue('replyto_addr');
                    if (!empty($replyto) && ($replyto != $email)) {
                        $msg_headers->addHeader('Reply-to', $replyto);
                    }
                    $msg_headers->addHeader('Subject', MIME::encode(_("Free/Busy Request Response"), NLS::getCharset()));
                    $msg_headers->addMIMEHeaders($mime);

                    // Send the reply.
                    $mail_driver = $this->_getMailDriver();
                    $status = $mime->send($organizerEmail, $msg_headers,
                                          $mail_driver['driver'],
                                          $mail_driver['params']);
                    if (is_a($status, 'PEAR_Error')) {
                        $this->_msgs[$key][] = array('error', sprintf(_("Error sending reply: %s."), $status->getMessage()));
                    } else {
                        $this->_msgs[$key][] = array('success', _("Reply Sent."));
                    }
                } else {
                    $this->_msgs[$key][] = array('warning', _("Invalid Action selected for this component."));
                }
                break;

            case 'nosup':
                // vFreebusy request.
            default:
                $this->_msgs[$key][] = array('warning', _("This action is not yet implemented."));
                break;
            }
        }

        // Create the HTML to display the iCal file.
        $html = '';
        if (MIME_Contents::viewAsAttachment()) {
            $html .= Util::bufferOutput('require', $registry->get('templates', 'horde') . '/common-header.inc');
        }
        if ($_SESSION['imp']['viewmode'] == 'imp') {
            $html .= '<form method="post" name="iCal" action="' . Horde::selfUrl(true) . '">';
        }

        foreach ($components as $key => $component) {
            switch ($component->getType()) {
            case 'vEvent':
                $html .= $this->_vEvent($component, $key);
                break;

            case 'vTodo':
                $html .= $this->_vTodo($component, $key);
                break;

            case 'vTimeZone':
                // Ignore them.
                break;

            case 'vFreebusy':
                $html .= $this->_vFreebusy($component, $key);
                break;

            // @todo: handle stray vcards here as well.
            default:
                $html .= sprintf(_("Unhandled component of type: %s"), $component->getType());
            }
        }

        // Need to work out if we are inline and actually need this.
        if ($_SESSION['imp']['viewmode'] == 'imp') {
            $html .= '</form>';
        }
        if (MIME_Contents::viewAsAttachment()) {
            $html .= Util::bufferOutput('require', $registry->get('templates', 'horde') . '/common-footer.inc');
        }

        return $html;
    }

    /**
     * Return text/html as the content-type.
     *
     * @return string "text/html" constant
     */
    function getType()
    {
        return 'text/html; charset=' . NLS::getCharset();
    }

    /**
     * Return mail driver/params necessary to send a message.
     *
     * @return array  'driver' => mail driver; 'params' => list of params.
     */
    function _getMailDriver()
    {
        global $conf;

        /* We don't actually want to alter the contents of the $conf['mailer']
         * array, so we make a copy of the current settings. We will apply our
         * modifications (if any) to the copy, instead. */
        $params = $conf['mailer']['params'];
        $driver = $conf['mailer']['type'];

        /* If user specifies an SMTP server on login, force SMTP mailer. */
        if (!empty($conf['server']['change_smtphost'])) {
            $driver = 'smtp';
            if (empty($params['mailer']['auth'])) {
                $params['mailer']['auth'] = '1';
            }
        }

        /* Force the SMTP host and port value to the current SMTP server if
         * one has been selected for this connection. */
        if (!empty($_SESSION['imp']['smtphost'])) {
            $params['host'] = $_SESSION['imp']['smtphost'];
        }
        if (!empty($_SESSION['imp']['smtpport'])) {
            $params['port'] = $_SESSION['imp']['smtpport'];
        }

        /* If SMTP authentication has been requested, use either the username
         * and password provided in the configuration or populate the username
         * and password fields based on the current values for the user. Note
         * that we assume that the username and password values from the
         * current IMAP / POP3 connection are valid for SMTP authentication as
         * well. */
        if (!empty($params['auth']) && empty($params['username'])) {
            $params['username'] = $_SESSION['imp']['user'];
            $params['password'] = Secret::read(Secret::getKey('imp'), $_SESSION['imp']['pass']);
        }

        return array('driver' => $driver, 'params' => $params);
    }

    /**
     * Return the html for a vFreebusy.
     */
    function _vFreebusy($vfb, $id)
    {
        global $registry, $prefs;

        $html = '';
        $desc = '';
        $sender = $vfb->getName();
        switch ($this->_method) {
        case 'PUBLISH':
            $desc = _("%s has sent you free/busy information.");
            break;

        case 'REQUEST':
            $sender = $this->_headers->getValue('From');
            $desc = _("%s requests your free/busy information.");
            break;

        case 'REPLY':
            $desc = _("%s has replied to a free/busy request.");
            break;
        }

        $html .= '<h1 class="header">' . sprintf($desc, $sender) . '</h1>';

        if ($this->_msgs) {
            foreach ($this->_msgs[$id] as $msg) {
                $html .= '<p class="notice">' . Horde::img('alerts/' . $msg[0] . '.png', '', null, $registry->getImageDir('horde')) . $msg[1] . '</p>';
            }
        }

        $start = $vfb->getAttribute('DTSTART');
        if (!is_a($start, 'PEAR_Error')) {
            if (is_array($start)) {
                $html .= '<p><strong>' . _("Start:") . '</strong> ' . strftime($prefs->getValue('date_format'), mktime(0, 0, 0, $start['month'], $start['mday'], $start['year'])) . '</p>';
            } else {
                $html .= '<p><strong>' . _("Start:") . '</strong> ' . strftime($prefs->getValue('date_format'), $start) . ' ' . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $start) . '</p>';
            }
        }

        $end = $vfb->getAttribute('DTEND');
        if (!is_a($end, 'PEAR_Error')) {
            if (is_array($end)) {
                $html .= '<p><strong>' . _("End:") . '</strong> ' . strftime($prefs->getValue('date_format'), mktime(0, 0, 0, $end['month'], $end['mday'], $end['year'])) . '</p>';
            } else {
                $html .= '<p><strong>' . _("End:") . '</strong> ' . strftime($prefs->getValue('date_format'), $end) . ' ' . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $end) . '</p>';
            }
        }

        if ($_SESSION['imp']['viewmode'] != 'imp') {
            return $html;
        }

        $html .= '<h2 class="smallheader">' . _("Actions") . '</h2>' .
            '<select name="action[' . $id . ']">';

        switch ($this->_method) {
        case 'PUBLISH':
            if ($registry->hasMethod('calendar/import_vfreebusy')) {
                $html .= '<option value="import">' .   _("Remember the free/busy information.") . '</option>';
            } else {
                $html .= '<option value="nosup">' . _("Reply with Not Supported Message") . '</option>';
            }
            break;

        case 'REQUEST':
            if ($registry->hasMethod('calendar/getFreeBusy')) {
                $html .= '<option value="reply">' .   _("Reply with requested free/busy information.") . '</option>' .
                    '<option value="reply2m">' . _("Reply with free/busy for next 2 months.") . '</option>';
            } else {
                $html .= '<option value="nosup">' . _("Reply with Not Supported Message") . '</option>';
            }

            $html .= '<option value="deny">' . _("Deny request for free/busy information") . '</option>';
            break;

        case 'REPLY':
            if ($registry->hasMethod('calendar/import_vfreebusy')) {
                $html .= '<option value="import">' .   _("Remember the free/busy information.") . '</option>';
            } else {
                $html .= '<option value="nosup">' . _("Reply with Not Supported Message") . '</option>';
            }
            break;
        }

        return $html . '</select> <input type="submit" class="button" value="' . _("Go") . '/>';
    }

    /**
     * Return the html for a vEvent.
     */
    function _vEvent($vevent, $id)
    {
        global $registry, $prefs;

        $html = '';
        $desc = '';
        $sender = $vevent->organizerName();
        $options = array();

        $attendees = $vevent->getAttribute('ATTENDEE');
        if (!is_a($attendees, 'PEAR_Error') &&
            !empty($attendees) &&
            !is_array($attendees)) {
            $attendees = array($attendees);
        }
        $attendee_params = $vevent->getAttribute('ATTENDEE', true);

        switch ($this->_method) {
        case 'PUBLISH':
            $desc = _("%s wishes to make you aware of \"%s\".");
            if ($registry->hasMethod('calendar/import')) {
                $options['import'] = _("Add this to my calendar");
            }
            break;

        case 'REQUEST':
            // Check if this is an update.
            if ($registry->hasMethod('calendar/export') &&
                !is_a($registry->call('calendar/export', array($vevent->getAttribute('UID'), 'text/calendar')), 'PEAR_Error')) {
                $is_update = true;
                $desc = _("%s wants to notify you about changes of \"%s\".");
            } else {
                $is_update = false;

                // Check that you are one of the attendees here.
                $is_attendee = false;
                if (!is_a($attendees, 'PEAR_Error') && !empty($attendees)) {
                    require_once 'Horde/Identity.php';
                    $identity = &Identity::singleton(array('imp', 'imp'));
                    for ($i = 0, $c = count($attendees); $i < $c; ++$i) {
                        $attendee = parse_url($attendees[$i]);
                        if (!empty($attendee['path']) &&
                            $identity->hasAddress($attendee['path'])) {
                            $is_attendee = true;
                            break;
                        }
                    }
                }

                $desc = $is_attendee
                    ? _("%s requests your presence at \"%s\".")
                    : _("%s wishes to make you aware of \"%s\".");
            }
            if ($is_update && $registry->hasMethod('calendar/replace')) {
                $options['acceptimport'] = _("Accept and update in my calendar");
                $options['import'] = _("Update in my calendar");
            } elseif ($registry->hasMethod('calendar/import')) {
                $options['acceptimport'] = _("Accept and add to my calendar");
                $options['import'] = _("Add to my calendar");
            }
            $options['accept'] = _("Accept request");
            $options['tentative'] = _("Tentatively Accept request");
            $options['deny'] = _("Deny request");
            // $options['delegate'] = _("Delegate position");
            break;

        case 'ADD':
            $desc = _("%s wishes to ammend \"%s\".");
            if ($registry->hasMethod('calendar/import')) {
                $options['import'] = _("Update this event on my calendar");
            }
            break;

        case 'REFRESH':
            $desc = _("%s wishes to receive the latest information about \"%s\".");
            $options['send'] = _("Send Latest Information");
            break;

        case 'REPLY':
            $desc = _("%s has replied to the invitation to \"%s\".");
            $sender = $this->_headers->getValue('From');
            if ($registry->hasMethod('calendar/updateAttendee')) {
                $options['update'] = _("Update respondent status");
            }
            break;

        case 'CANCEL':
            if (is_a($instance = $vevent->getAttribute('RECURRENCE-ID'), 'PEAR_Error')) {
                $desc = _("%s has cancelled \"%s\".");
                if ($registry->hasMethod('calendar/delete')) {
                    $options['delete'] = _("Delete from my calendar");
                }
            } else {
                $desc = _("%s has cancelled an instance of the recurring \"%s\".");
                if ($registry->hasMethod('calendar/replace')) {
                    $options['import'] = _("Update in my calendar");
                }
            }
            break;
        }

        $summary = $vevent->getAttribute('SUMMARY');
        if (is_a($summary, 'PEAR_Error')) {
            $desc = sprintf($desc, htmlspecialchars($sender), _("Unknown Meeting"));
        } else {
            $desc = sprintf($desc, htmlspecialchars($sender), htmlspecialchars($summary));
        }

        if ($_SESSION['imp']['viewmode'] == 'dimp') {
            require_once DIMP_BASE . '/lib/DIMP.php';

            function _createMEntry($text, $image, $id, $class = '', $show_text = true, $app = null)
            {
                $params = array('icon' => $image, 'id' => $id, 'class' => $class);
                if ($show_text) {
                    $params['title'] = $text;
                } else {
                    $params['tooltip'] = $text;
                }
                if (isset($app)) {
                    $params['app'] = $app;
                }
                return DIMP::actionButton($params);
            }

            $script = 'if (DIMP.baseWindow) {var B = DIMP.baseWindow.DimpBase;} else {B = DimpBase;};DimpCore.addMouseEvents({ id: \'button_invitation_cont\', type: \'itippopdown\', offset: \'button_invitation_cont\', left: true});';
            $html .= '<div><span id="button_invitation_cont">' . _createMEntry(_("Invitation"), 'kronolith.png', 'button_invitation', 'hasmenu', true, 'kronolith') . Horde::img('popdown.png', '', array(), $GLOBALS['registry']->getImageDir('dimp')) . '</span></div><p/><script type="text/javascript">' . $script . '</script>';

            if ($this->_msgs) {
                global $notification;
                foreach ($this->_msgs[$id] as $msg) {
                    $notification->push($msg[1], 'horde.' . $msg[0]);
                }
            }
        }

        $html .= '<h2 class="header">' . $desc . '</h2>';

        if ($this->_msgs) {
            foreach ($this->_msgs[$id] as $msg) {
                $html .= '<p class="notice">' . Horde::img('alerts/' . $msg[0] . '.png', '', null, $registry->getImageDir('horde')) . $msg[1] . '</p>';
            }
        }

        $start = $vevent->getAttribute('DTSTART');
        if (!is_a($start, 'PEAR_Error')) {
            if (is_array($start)) {
                $html .= '<p><strong>' . _("Start:") . '</strong> ' . strftime($prefs->getValue('date_format'), mktime(0, 0, 0, $start['month'], $start['mday'], $start['year'])) . '</p>';
            } else {
                $html .= '<p><strong>' . _("Start:") . '</strong> ' . strftime($prefs->getValue('date_format'), $start) . ' ' . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $start) . '</p>';
            }
        }

        $end = $vevent->getAttribute('DTEND');
        if (!is_a($end, 'PEAR_Error')) {
            if (is_array($end)) {
                $html .= '<p><strong>' . _("End:") . '</strong> ' . strftime($prefs->getValue('date_format'), mktime(0, 0, 0, $end['month'], $end['mday'], $end['year'])) . '</p>';
            } else {
                $html .= '<p><strong>' . _("End:") . '</strong> ' . strftime($prefs->getValue('date_format'), $end) . ' ' . date($prefs->getValue('twentyFour') ? ' G:i' : ' g:i a', $end) . '</p>';
            }
        }

        $sum = $vevent->getAttribute('SUMMARY');
        if (!is_a($sum, 'PEAR_Error')) {
            $html .= '<p><strong>' . _("Summary") . ':</strong> ' . htmlspecialchars($sum) . '</p>';
        } else {
            $html .= '<p><strong>' . _("Summary") . ':</strong> <em>' . _("None") . '</em></p>';
        }

        $desc = $vevent->getAttribute('DESCRIPTION');
        if (!is_a($desc, 'PEAR_Error')) {
            $html .= '<p><strong>' . _("Description") . ':</strong> ' . nl2br(htmlspecialchars($desc)) . '</p>';
        }

        $loc = $vevent->getAttribute('LOCATION');
        if (!is_a($loc, 'PEAR_Error')) {
            $html .= '<p><strong>' . _("Location") . ':</strong> ' . htmlspecialchars($loc) . '</p>';
        }

        if (!is_a($attendees, 'PEAR_Error') && !empty($attendees)) {
            $html .= '<h2 class="smallheader">' . _("Attendees") . '</h2>';

            $html .= '<table><thead class="leftAlign"><tr><th>' . _("Name") . '</th><th>' . _("Role") . '</th><th>' . _("Status") . '</th></tr></thead><tbody>';
            foreach ($attendees as $key => $attendee) {
                $attendee = parse_url($attendee);
                $attendee = empty($attendee['path']) ? _("Unknown") : $attendee['path'];

                if (!empty($attendee_params[$key]['CN'])) {
                    $attendee = $attendee_params[$key]['CN'];
                }

                $role = _("Required Participant");
                if (isset($attendee_params[$key]['ROLE'])) {
                    switch ($attendee_params[$key]['ROLE']) {
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
                if (isset($attendee_params[$key]['PARTSTAT'])) {
                    $status = $this->_partstatToString($attendee_params[$key]['PARTSTAT'], $status);
                }

                $html .= '<tr><td>' . htmlspecialchars($attendee) . '</td><td>' . htmlspecialchars($role) . '</td><td>' . htmlspecialchars($status) . '</td></tr>';
            }
            $html .= '</tbody></table>';
        }

        if ($options) {

            if ($_SESSION['imp']['viewmode'] == 'imp') {

                $html .= '<h2 class="smallheader">' . _("Actions") . '</h2>' .
                    '<label for="action_' . $id . '" class="hidden">' . _("Actions") . '</label>' .
                    '<select id="action_' . $id . '" name="action[' . $id . ']">';

                foreach ($options as $key => $description) {
                    $html .= '<option value="' . $key .'">' . $description . "</option>\n";
                }

                $html .= '</select> <input type="submit" class="button" value="' . _("Go") . '" />';

            } else if ($_SESSION['imp']['viewmode'] == 'dimp') {
                // the div of the context menu
                $script = "var itipContextMenu = document.createElement('div');\n";
                $script .= "itipContextMenu.setAttribute('class', 'context');\n";
                $script .= "itipContextMenu.setAttribute('id', 'ctx_itippopdown');\n";
                $script .= "itipContextMenu.setAttribute('style', 'display:none');\n";

                // all the context menu items
                foreach ($options as $key => $description) {
                    $script .= "var itipContextMenuItem = document.createElement('a');\n";
                    $script .= "itipContextMenuItem.setAttribute('id', 'ctx_itippopdown" . $key . "');\n";
                    $script .= "var linkText = document.createTextNode('" . $description . "');\n";
                    $script .= "itipContextMenuItem.appendChild(linkText);\n";
                    $script .= "itipContextMenu.appendChild(itipContextMenuItem);\n";
                    $script .= "var d = $(itipContextMenuItem);\n";
                    $script .= "DimpCore.clickObserveHandler({ d: d,\n";
                    $script .= "                               f: function(a) {\n";
                    $script .= "                                      B.itip(a, DIMP.conf.msg_index, DIMP.conf.msg_folder, '" . $id . "');\n";
                    $script .= "                                      window.close();\n";
                    $script .= "                                  }.curry('" . $key . "'),\n";
                    $script .= "                               ns: true,\n";
                    $script .= "                             });\n";
                }
                $script .= "document.getElementById('dimpPage').appendChild(itipContextMenu);\n";
                $html .= '<script type="text/javascript">' . $script . '</script>';
            }
        }

        return $html;
    }

    /**
     * Returns the html for a vEvent.
     *
     * @todo IMP 5: move organizerName() from Horde_iCalendar_vevent to
     *       Horde_iCalendar
     */
    function _vTodo($vtodo, $id)
    {
        global $registry, $prefs;

        $html = '';
        $desc = '';
        $options = array();

        $organizer = $vtodo->getAttribute('ORGANIZER', true);
        if (is_a($organizer, 'PEAR_Error')) {
            $sender = _("An unknown person");
        } else {
            if (isset($organizer[0]['CN'])) {
                $sender = $organizer[0]['CN'];
            } else {
                $organizer = parse_url($vtodo->getAttribute('ORGANIZER'));
                $sender = $organizer['path'];
            }
        }

        switch ($this->_method) {
        case 'PUBLISH':
            $desc = _("%s wishes to make you aware of \"%s\".");
            if ($registry->hasMethod('tasks/import')) {
                $options[] = '<option value="import">' . _("Add this to my tasklist") . '</option>';
            }
            break;
        }

        $summary = $vtodo->getAttribute('SUMMARY');
        if (is_a($summary, 'PEAR_Error')) {
            $desc = sprintf($desc, htmlspecialchars($sender), _("Unknown Task"));
        } else {
            $desc = sprintf($desc, htmlspecialchars($sender), htmlspecialchars($summary));
        }

        $html .= '<h2 class="header">' . $desc . '</h2>';

        if ($this->_msgs) {
            foreach ($this->_msgs[$id] as $msg) {
                $html .= '<p class="notice">' . Horde::img('alerts/' . $msg[0] . '.png', '', null, $registry->getImageDir('horde')) . $msg[1] . '</p>';
            }
        }

        $priority = $vtodo->getAttribute('PRIORITY');
        if (!is_a($priority, 'PEAR_Error')) {
            $html .= '<p><strong>' . _("Priority") . ':</strong> ' . (int)$priority . '</p>';
        }

        $sum = $vtodo->getAttribute('SUMMARY');
        if (!is_a($sum, 'PEAR_Error')) {
            $html .= '<p><strong>' . _("Summary") . ':</strong> ' . htmlspecialchars($sum) . '</p>';
        } else {
            $html .= '<p><strong>' . _("Summary") . ':</strong> <em>' . _("None") . '</em></p>';
        }

        $desc = $vtodo->getAttribute('DESCRIPTION');
        if (!is_a($desc, 'PEAR_Error')) {
            $html .= '<p><strong>' . _("Description") . ':</strong> ' . nl2br(htmlspecialchars($desc)) . '</p>';
        }

        $attendees = $vtodo->getAttribute('ATTENDEE');
        $params = $vtodo->getAttribute('ATTENDEE', true);

        if (!is_a($attendees, 'PEAR_Error') && !empty($attendees)) {
            $html .= '<h2 class="smallheader">' . _("Attendees") . '</h2>';
            if (!is_array($attendees)) {
                $attendees = array($attendees);
            }

            $html .= '<table><thead class="leftAlign"><tr><th>' . _("Name") . '</th><th>' . _("Role") . '</th><th>' . _("Status") . '</th></tr></thead><tbody>';
            foreach ($attendees as $key => $attendee) {
                $attendee = parse_url($attendee);
                $attendee = $attendee['path'];

                if (isset($params[$key]['CN'])) {
                    $attendee = $params[$key]['CN'];
                }

                $role = _("Required Participant");
                if (isset($params[$key]['ROLE'])) {
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
                if (isset($params[$key]['PARTSTAT'])) {
                    $status = $this->_partstatToString($params[$key]['PARTSTAT'], $status);
                }

                $html .= '<tr><td>' . htmlspecialchars($attendee) . '</td><td>' . htmlspecialchars($role) . '</td><td>' . htmlspecialchars($status) . '</td></tr>';
            }
            $html .= '</tbody></table>';
        }

        if ($_SESSION['imp']['viewmode'] != 'imp') {
            return $html;
        }

        if ($options) {
            $html .= '<h2 class="smallheader">' . _("Actions") . '</h2>' .
                '<select name="action[' . $id . ']">' .
                implode("\n", $options) .
                '</select> <input type="submit" class="button" value="' . _("Go") . '" />';
        }

        return $html;
    }

    /**
     * Translate the Participation status to string.
     *
     * @param string $value    The value of PARTSTAT.
     * @param string $default  The value to return as default.
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

        case 'TENTATIVE':
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

}
