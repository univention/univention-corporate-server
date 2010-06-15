<?php

require_once 'Horde/Kolab.php';
require_once 'Horde/iCalendar.php';
require_once 'Horde/Identity.php';

/**
 * Horde Kronolith driver for the Kolab IMAP Server.
 * Copyright (C) 2003, 2004 Code Fusion, cc.
 *
 * $Horde: kronolith/lib/Driver/kolab.php,v 1.8 2004/05/24 12:38:11 stuart Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stuart Bingë <s.binge@codefusion.co.za>
 * @version $Revision: 1.1.2.1 $
 * @package Kronolith
 */
class Kronolith_Driver_kolab extends Kronolith_Driver {

    /**
     * Our Kolab Cyrus server connection.
     *
     * @var object Kolab_Cyrus $_kc
     */
    var $_kc;

    /**
     * What IMAP folder we're using to store notes.
     *
     * @var string $_folder
     */
    var $_folder;

    /**
     * Should we create $_folder if it does not exist?
     *
     * @var boolean $_create
     */
    var $_create;

    /**
     * Constructor - we need to override this to set our default
     * 'folder' and 'server' parameters.
     *
     * @param optional array $params  Any parameters needed for this driver.
     */
    function Kronolith_Driver_kolab($params = array())
    {
        $this->_params = $params;

        $this->_params['folder'] = isset($params['folder']) ? $params['folder'] : 'Calendar';
        $this->_params['server'] = isset($params['server']) ? $params['server'] : $GLOBALS['conf']['kolab']['server'];

        $this->_kc = &new Kolab_Cyrus($this->_params['server']);
    }

    function open($calendar)
    {
        $result = Kolab_Cyrus::shareToFolder(
            'kronolith_shares',
            $calendar,
            $this->_params['folder'],
            $this->_folder,
            $this->_create
        );
        if (is_a('PEAR_Error', $result)) {
            return $result;
        }

        $this->_calendar = $result;

        $result = $this->_kc->openMailbox($this->_folder, $this->_create);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
    }

    function close()
    {
        $this->_kc->closeMailbox();
    }

    function listAlarms($date)
    {
        $events = $this->listEvents($date, $date);
        $alarms = array();

        $cal = &new Horde_iCalendar();
        foreach ($events as $event) {
            $matches = $this->_kc->getMessageList(SORTDATE, false, "SUBJECT \"$event\"");
            if (!is_array($matches) || count($matches) < 1) {
                continue;
            }

            $body = $this->_kc->getObject($matches[0], "text/calendar");
            if ($body === false) {
                continue;
            }

            $cal->parsevCalendar($body);
            $components = $cal->getComponents();

            foreach ($components as $component) {
                if (!is_a($component, 'Horde_iCalendar_vevent')) {
                    continue;
                }

                $subcomps = $component->getComponents();
                foreach ($subcomps as $subcomp) {
                    if (!is_a($subcomp, 'Horde_iCalendar_valarm')) {
                        continue;
                    }

                    $ts = Kronolith::objectToTimestamp($date);

                    $dateattr = $component->getAttribute('DTSTART');
                    if (is_array($dateattr) || is_a($dateattr, 'PEAR_Error')) {
                        continue;
                    }

                    $offset = $subcomp->getAttribute('TRIGGER');
                    $diff = $ts - $dateattr;
                    if ($diff >= $offset && $diff <= 0) {
                        array_push($alarms, $event);
                    }
                }
            }
        }

        return $alarms;
    }

    function listEvents($startDate = null, $endDate = null)
    {
        $events = array();

        $msgs = $this->_kc->getMessageList();
        $cal = &new Horde_iCalendar();
        foreach ($msgs as $msg) {
            $body = $this->_kc->getObject($msg, 'text/calendar');
            $cal->_components = array();
            $cal->parsevCalendar($body);

            $components = $cal->getComponents();
            $ispresent = false;

            foreach ($components as $component) {
                if (!is_a($component, 'Horde_iCalendar_vevent')) {
                    continue;
                }

                $startattr = $component->getAttribute('DTSTART');
                if (is_array($startattr) || is_a($startattr, 'PEAR_Error')) {
                    continue;
                }

                $start = getdate($startattr);
                //Leaving this check in screws up recurring events
                /*if (!$ispresent &&
                    $start['year'] >= $startDate->year && $start['year'] <= $endDate->year &&
                    $start['mon'] >= $startDate->month && $start['mon'] <= $endDate->month &&
                    $start['mday'] >= $startDate->mday && $start['mday'] <= $endDate->mday)
                {*/
                    array_push($events, $component->getAttribute('UID'));
                    $ispresent = true;
                //}
            }
        }

        return $events;
    }

    function &getEvent($eventID = null)
    {
        if (is_null($eventID)) {
            return new Kronolith_Event_kolab($this);
        }

        $matches = $this->_kc->getMessageList(SORTDATE, false, "SUBJECT \"$eventID\"");

        $body = $this->_kc->getObject($matches, 'text/calendar');
        if ($body === false) {
            return $body;
        }

        $iCalendar = &new Horde_iCalendar();
        $iCalendar->parsevCalendar($body);
        $components = $iCalendar->getComponents();

        foreach ($components as $component) {
            if (!is_a($component, 'Horde_iCalendar_vevent')) {
                continue;
            }

            $event = &new Kronolith_Event_kolab($this, $component);
            return $event;
        }

        return false;
    }

    function &getByGUID($guid)
    {
        $pieces = explode(':', $guid);

        if ($pieces[0] != 'kronolith') {
            return PEAR::raiseError("GUID $guid is invalid");
        }

        array_shift($pieces);
        $calendar = array_pop($pieces);
        $eventId = implode(':', $pieces);

        $this->open($calendar);
        return $this->getEvent($eventId);
    }

    function saveEvent($event)
    {
        $eventID = $event->getID();
        $iCalendar = &new Horde_iCalendar();
        $vEvent = null;
        $vAlarm = null;
        $addEvent = false;
        $addAlarm = false;

        if (is_null($eventID)) {
            // We need the calendar UID in the event UID when moving messages
            // between calendars, as otherwise we have no way of knowing which
            // IMAP folder the event is stored in.
            $eventID = md5(uniqid(mt_rand(), true)) . ':' . $this->getCalendar();

            $vEvent = &$iCalendar->newComponent('VEVENT', $iCalendar);
            $vEvent->setAttribute('CREATED', time());
            $vEvent->setAttribute('UID', $eventID);

            $addEvent = true;
        } else {
            $matches = $this->_kc->getMessageList(SORTDATE, false, "SUBJECT \"$eventID\"");

            if (!is_array($matches) || count($matches) < 1) {
                $vEvent = &$iCalendar->newComponent('VEVENT', $iCalendar);
                $vEvent->setAttribute('CREATED', time());
                $vEvent->setAttribute('UID', $eventID);

                $addEvent = true;
            } else {
                $body = $this->_kc->getObject($matches[0], 'text/calendar');
                if ($body === false) {
                    return PEAR::raiseError('Corresponding message does not contain valid iCalendar data');
                }

                $this->_kc->deleteMessages($matches, true);
                $iCalendar->parsevCalendar($body);

                $vEvent = &$iCalendar->findComponent('VEVENT');
                if ($vEvent === false) {
                    return PEAR::raiseError('iCalendar data does not contain a valid vEvent object');
                }

                $vAlarm = &$vEvent->findComponent('VALARM');
                if ($vAlarm === false) {
                    $vAlarm = null;
                }
            }
        }

        $vEvent->setAttribute('SUMMARY', $event->getTitle(), array(), false);
        $vEvent->setAttribute('DESCRIPTION', $event->getDescription(), array(), false);
        $vEvent->setAttribute('LOCATION', $event->getLocation(), array(), false);
        $vEvent->setAttribute('X-HORDE-CATEGORY', $event->getCategory(), array(), false);
        $vEvent->setAttribute('STATUS', $this->statusToICal($event->getStatus()), array(), false);
        $vEvent->setAttribute('LAST-MODIFIED', time(), array(), false);
        $vEvent->setAttribute('ORGANIZER', "MAILTO:" . $event->getCreatorID(), array(), false);
        $vEvent->setAttribute('DTSTART', $event->getStartTimestamp(), array(), false);
        $vEvent->setAttribute('DTEND', $event->getEndTimestamp(), array(), false);
        $vEvent->setAttribute('TRANSP', 'OPAQUE', array(), false);

        $recend = ($event->recurEndTimestamp ? ';UNTIL=' . Horde_iCalendar::_exportDateTime($event->recurEndTimestamp) : '');
        switch ($event->recurType) {
        case KRONOLITH_RECUR_NONE:
            $vEvent->removeAttribute('RRULE');
            break;

        case KRONOLITH_RECUR_DAILY:
            $vEvent->setAttribute('RRULE', 'FREQ=DAILY;INTERVAL=' . $event->recurInterval . $recend, array(), false);
            break;

        case KRONOLITH_RECUR_WEEKLY:
            $rrule = 'FREQ=WEEKLY;INTERVAL=' . $event->recurInterval . ';BYDAY=';
            $vcaldays = array('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA');

            for ($i = $flag = 0; $i <= 7 ; $i++) {
                if ($event->recurOnDay(pow(2, $i))) {
                    if ($flag) {
                        $rrule .= ',';
                    }
                    $rrule .= $vcaldays[$i];
                    $flag = true;
                }
            }
            $rrule .= $recend;
            $vEvent->setAttribute('RRULE', $rrule, array(), false);
            break;

        case KRONOLITH_RECUR_DAY_OF_MONTH:
            $vEvent->setAttribute('RRULE', 'FREQ=MONTHLY;INTERVAL=' . $event->recurInterval . $recend, array(), false);
            break;

        case KRONOLITH_RECUR_WEEK_OF_MONTH:
            $vcaldays = array('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA');
            $vEvent->setAttribute('RRULE', 'FREQ=MONTHLY;INTERVAL=' . $event->recurInterval . ';BYDAY=' . ((
                date('W', $event->startTimestamp) - date('W', mktime(0, 0, 0, date('n', $event->startTimestamp),
                1, date('Y', $event->startTimestamp)))) + 1) . $vcaldays[date('w', $event->startTimestamp)] . $recend, array(), false);
            break;

        case KRONOLITH_RECUR_YEARLY:
            $vEvent->setAttribute('RRULE', 'FREQ=YEARLY;INTERVAL=' . $event->recurInterval . $recend, array(), false);
            break;
        }

        $vEvent->removeAttribute('ATTENDEE');
        foreach ($event->attendees as $email => $status) {
            $vEvent->setAttribute('ATTENDEE', "MAILTO:$email", array(
                    // 'RSVP' => 'FALSE',
                    'PARTSTAT' => $this->responseToICal($status['response']),
                    'ROLE' => $this->partToICal($status['attendance'])
                ), true
            );
        }

        $trigger = $event->getAlarm();
        if ($trigger != 0) {
            if (is_null($vAlarm)) {
                $addAlarm = true;
                $vAlarm = &$vEvent->newComponent('VALARM', $vEvent);
            }

            $vAlarm->setAttribute('TRIGGER', $trigger, array(), false);

            if ($addAlarm) {
                $vEvent->addComponent($vAlarm);
            }
        }

        if ($addEvent) {
            $iCalendar->addComponent($vEvent);
        }

        $result = $this->_kc->addObject(
            $eventID,
            $iCalendar->exportvCalendar(),
            'text/calendar',
            'kolab-calendar-entry.ics',
            'Kronolith'
        );
        if (is_a('PEAR_Error', $result)) {
            return $result;
        }

        // Generate 8 weeks worth of free/busy information.
        $vfbStart = time();
        $fb = Kronolith::generateFreeBusy($this->getCalendar(), $vfbStart, $vfbStart + 4838400);
        Kolab::storeFreeBusy('localhost', '/freebusy', $fb);

        return $eventID;
    }

    /**
     * Move an event to a new calendar.
     *
     * @param string $eventId      The event to move.
     * @param string $newCalendar  The new calendar.
     */
    function move($eventID, $newCalendar)
    {
        $event = &$this->getByGUID(Kronolith_Driver::getGUID($eventID));
        $this->deleteEvent($eventID);

        $eventID = "$eventID:$newCalendar";

        $event->setID($eventID);
        $event->setCalendar($newCalendar);

        $this->open($newCalendar);
        $this->saveEvent($event);

        return true;
    }

    /**
     * Delete a calendar and all its events.
     *
     * @param string $calendar  The name of the calendar to delete.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function delete($calendar)
    {
        $calendars = Kronolith::listCalendars(true, PERMS_EDIT);
        if (!isset($calendars[$calendar])) {
            return PEAR::raiseError("Unable to delete calendar $calendar");
        }

        $owner = $calendars[$calendar]->get('owner');
        $mailbox = $calendars[$calendar]->get('name');
        $mailbox = ($owner == $calendars[$calendar]->getName() ? $this->_params['folder'] : $mailbox);

        return $this->_kc->deleteMailbox($mailbox);
    }

    /**
     * Rename a calendar.
     *
     * @param string $from  The current name of the calendar.
     * @param string $to    The new name of the calendar.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function rename($from, $to)
    {
        return $this->_kc->renameMailbox($from, $to);
    }

    /**
     * Delete an event.
     *
     * @param string $eventId  The ID of the event to delete.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function deleteEvent($eventID)
    {
        $matches = $this->_kc->getMessageList(SORTDATE, false, "SUBJECT \"$eventID\"");
        $this->_kc->deleteMessages($matches, true);

        // Generate 8 weeks worth of free/busy information
        $vfbStart = time();
        Kolab::storeFreeBusy('localhost', '/freebusy/', Kronolith::generateFreeBusy($this->_calendar, $vfbStart, $vfbStart + 4838400));

        /* Log the deletion of this item in the history log. */
        $history = &Horde_History::singleton();
        $history->log($this->getGUID($eventID), array('action' => 'delete'), true);

        return true;
    }

    /**
     * Maps a Kronolith meeting status to the corresponding iCalendar
     * string.
     *
     * @param integer $status   The meeting status; one of the
     *                          KRONOLITH_STATUS_XXX constants.
     *
     * @return string   The iCalendar status string.
     */
    function statusToICal($status)
    {
        switch ($status) {
        case KRONOLITH_STATUS_CONFIRMED:
            return 'CONFIRMED';

        case KRONOLITH_STATUS_CANCELLED:
            return 'CANCELLED';

        case KRONOLITH_STATUS_TENTATIVE:
        default:
            return 'TENTATIVE';
        }
    }

    /**
     * Maps a Kronolith attendee response string to the corresponding
     * iCalendar string.
     *
     * @param integer $response  The attendee response; one of the
     *                           KRONOLITH_RESPONSE_XXX constants.
     *
     * @return string   The iCalendar response string.
     */
    function responseToICal($response)
    {
        switch ($response) {
        case KRONOLITH_RESPONSE_ACCEPTED:
            return 'ACCEPTED';

        case KRONOLITH_RESPONSE_DECLINED:
            return 'DECLINED';

        case KRONOLITH_RESPONSE_TENTATIVE:
            return 'TENTATIVE';

        case KRONOLITH_RESPONSE_NONE:
        default:
            return 'NEEDS-ACTION';
        }
    }

    /**
     * Maps a Kronolith attendee participation string to the
     * corresponding iCalendar string.
     *
     * @param integer $part      The attendee participation; one of the
     *                           KRONOLITH_PART_XXX constants.
     *
     * @return string   The iCalendar participation string.
     */
    function partToICal($part)
    {
        switch ($part) {
        case KRONOLITH_PART_OPTIONAL:
            return 'OPT-PARTICIPANT';

        case KRONOLITH_PART_NONE:
            return 'NON-PARTICIPANT';

        case KRONOLITH_PART_REQUIRED:
        default:
            return 'REQ-PARTICIPANT';
        }
    }

    /**
     * Maps an iCalendar meeting status to the corresponding Kronolith
     * value.
     *
     * @param string $status    The meeting status.
     *
     * @return integer   The Kronolith status value.
     */
    function statusFromICal($status)
    {
        switch (String::upper($status)) {
        case 'CONFIRMED':
            return KRONOLITH_STATUS_CONFIRMED;

        case 'CANCELLED':
            return KRONOLITH_STATUS_CANCELLED;

        case 'TENTATIVE':
        default:
            return KRONOLITH_STATUS_TENTATIVE;
        }
    }

    /**
     * Maps an iCalendar attendee participation string to the
     * corresponding Kronolith value.
     *
     * @param string $part       The attendee participation.
     *
     * @return string   The Kronolith participation value.
     */
    function partFromICal($part)
    {
        switch (String::upper($part)) {
        case 'OPT-PARTICIPANT':
            return KRONOLITH_PART_OPTIONAL;

        case 'NON-PARTICIPANT':
            return KRONOLITH_PART_NONE;

        case 'REQ-PARTICIPANT':
        default:
            return KRONOLITH_PART_REQUIRED;
        }
    }

}

class Kronolith_Event_kolab extends Kronolith_Event {

    var $_properties = array();

    function toDriver()
    {
        // Nothing - all of this is done in saveEvent().
    }

    /**
     * @param object Horde_iCalendar_vevent $icalEvent
     */
    function fromDriver($icalEvent)
    {
        $this->eventID = $icalEvent->getAttributeDefault('UID', '');
        $this->title = $icalEvent->getAttributeDefault('SUMMARY', '');
        $this->description = trim($icalEvent->getAttributeDefault('DESCRIPTION', ''));
        $this->location = $icalEvent->getAttributeDefault('LOCATION', '');
        $this->category = $icalEvent->getAttributeDefault('X-HORDE-CATEGORY', '');
        $this->status = Kronolith_Driver_kolab::statusFromICal($icalEvent->getAttributeDefault('STATUS', ''));
        $this->creatorID = preg_replace("/^mailto:\s*/i", '', $icalEvent->getAttributeDefault('ORGANIZER', ''));

        $this->startTimestamp = $icalEvent->getAttributeDefault('DTSTART', 0);
        if ($this->startTimestamp) {
            $this->start = Kronolith::timestampToObject($this->startTimestamp);
        }

        $this->endTimestamp = $icalEvent->getAttributeDefault('DTEND', 0);
        if ($this->endTimestamp) {
            $this->end = Kronolith::timestampToObject($this->endTimestamp);
        }

        if ($this->startTimestamp && $this->endTimestamp) {
            $this->durMin = ($this->endTimestamp - $this->startTimestamp) / 60;
        }

        $this->recurEnd = null;
        $this->recurType = KRONOLITH_RECUR_NONE;

        $tmp = $icalEvent->getAttributeDefault('RRULE', '');
        preg_match_all('/([^;=]*)=?([^;]*);?/', $tmp, $rmatches);

        for ($i = 0; $i < count($rmatches[2]); $i++) {
            switch ($rmatches[1][$i]) {
            case 'FREQ':
                $freq = $rmatches[2][$i];

                switch ($freq) {
                case 'DAILY':
                    $this->recurType = KRONOLITH_RECUR_DAILY;
                    break;

                case 'WEEKLY':
                    $this->recurType = KRONOLITH_RECUR_WEEKLY;
                    break;

                case 'MONTHLY':
                    $this->recurType = KRONOLITH_RECUR_DAY_OF_MONTH;
                    break;

                case 'YEARLY':
                    $this->recurType = KRONOLITH_RECUR_YEARLY;
                    break;

                default:
                    $this->recurType = KRONOLITH_RECUR_NONE;
                }
                break;

            case 'UNTIL':
                $until = $rmatches[2][$i];
                $this->recurEndTimestamp = $icalEvent->_parseDateTime($until);
                $this->recurEnd = Kronolith::timestampToObject($this->recurEndTimestamp);
                break;

            case 'INTERVAL':
                $interval = $rmatches[2][$i];
                $this->recurInterval = $interval;
                break;

            case 'COUNT':
                $this->recurEndTimestamp = Kolab::countToUntil($this->startTimestamp, $rmatches[2][$i], $this->recurType);
                $this->recurEnd = Kronolith::timestampToObject($this->recurEndTimestamp);
                break;

            case 'BYDAY':
                preg_match_all('/([^,]*)/', $rmatches[2][$i], $days);
                $bits = array('SU' => KRONOLITH_MASK_SUNDAY,
                              'MO' => KRONOLITH_MASK_MONDAY,
                              'TU' => KRONOLITH_MASK_TUESDAY,
                              'WE' => KRONOLITH_MASK_WEDNESDAY,
                              'TH' => KRONOLITH_MASK_THURSDAY,
                              'FR' => KRONOLITH_MASK_FRIDAY,
                              'SA' => KRONOLITH_MASK_SATURDAY,
                              );
                $mask = 0;
                foreach ($days[1] as $day) {
                    if (empty($day) || !isset($bits[$day])) {
                        continue;
                    }

                    $mask |= $bits[$day];
                }

                $this->setRecurOnDay($mask);
                break;
            }
        }

        $subcomps = $icalEvent->getComponents();
        foreach ($subcomps as $subcomp) {
            if (!is_a($subcomp, 'Horde_iCalendar_valarm')) {
                continue;
            }

            $this->alarm = Kolab::_getAttr($subcomp, 'TRIGGER', 0);
        }

        $atnames = $icalEvent->getAttribute('ATTENDEE');
        $atparms = $icalEvent->getAttribute('ATTENDEE', true);

        if (!is_a($atnames, 'PEAR_Error')) {
            if (!is_array($atnames)) {
                $atnames = array(strval($atnames));
            }
            foreach ($atnames as $index => $attendee) {
                $this->addAttendee(preg_replace("/^mailto:\s*/i", '', $attendee),
                                   Kronolith_Driver_kolab::partFromICal($atparms[$index]['ROLE']),
                                   Kronolith::responseFromICal($atparms[$index]['PARTSTAT'])
                                   );
            }
        }

        $this->initialized = true;
        $this->stored = true;
    }

    function getProperties()
    {
        return $this->_properties;
    }

}
