<?php

require_once 'Horde/Kolab.php';
require_once 'Horde/Identity.php';

/**
 * Horde Kronolith driver for the Kolab IMAP Server.
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * $Horde: kronolith/lib/Driver/kolab.php,v 1.16.2.30 2009-01-06 15:24:45 jan Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @since   Kronolith 2.0
 * @package Kronolith
 */
class Kronolith_Driver_kolab extends Kronolith_Driver {

    /**
     * Our Kolab server connection.
     *
     * @var Kolab
     */
    var $_kolab = null;

    /**
     * The wrapper to decide between the Kolab implementation
     *
     * @var Kronolith_Driver_kolab_wrapper
     */
    var $_wrapper = null;

    /**
     * Attempts to open a Kolab Groupware folder.
     *
     * @return boolean  True on success, PEAR_Error on failure.
     */
    function initialize()
    {
        $this->_kolab = &new Kolab();
        if (empty($this->_kolab->version)) {
            $wrapper = "Kronolith_Driver_kolab_wrapper_old";
        } else {
            $wrapper = "Kronolith_Driver_kolab_wrapper_new";
        }

        $this->_wrapper = &new $wrapper($this);

        return true;
    }

    /**
     * Change current calendar
     */
    function open($calendar)
    {
        if ($this->_calendar != $calendar) {
            $this->_calendar = $calendar;
            $this->_wrapper->reset();
        }
        $this->_wrapper->open($calendar);

        return true;
    }

    function listAlarms($date, $fullevent = false)
    {
        return $this->_wrapper->listAlarms($date, $fullevent);
    }

    /**
     * Checks if the event's UID already exists and returns all event
     * ids with that UID.
     *
     * @param string $uid          The event's uid.
     * @param string $calendar_id  Calendar to search in.
     *
     * @return mixed  Returns a string with event_id or false if not found.
     */
    function exists($uid, $calendar_id = null)
    {
        return $this->_wrapper->exists($uid, $calendar_id);
    }

    /**
     * Lists all events in the time range, optionally restricting
     * results to only events with alarms.
     *
     * @param Horde_Date $startInterval  Start of range date object.
     * @param Horde_Date $endInterval    End of range date object.
     * @param boolean $hasAlarm          Only return events with alarms?
     *                                   Defaults to <code>false</code>.
     *
     * @return array  Events in the given time range.
     */
    function listEvents($startDate = null, $endDate = null, $hasAlarm = false)
    {
        return $this->_wrapper->listEvents($startDate, $endDate, $hasAlarm);
    }

    function &getEvent($eventID = null)
    {
        return $this->_wrapper->getEvent($eventID);
    }

    /**
     * Get an event or events with the given UID value.
     *
     * @param string $uid The UID to match
     * @param array $calendars A restricted array of calendar ids to search
     * @param boolean $getAll Return all matching events? If this is false,
     * an error will be returned if more than one event is found.
     *
     * @return Kronolith_Event
     */
    function &getByUID($uid, $calendars = null, $getAll = false)
    {
        return $this->_wrapper->getByUID($uid, $calendars, $getAll);
    }

    function saveEvent(&$event)
    {
        return $this->_wrapper->saveEvent($event);
    }

    /**
     * Move an event to a new calendar.
     *
     * @param string $eventId      The event to move.
     * @param string $newCalendar  The new calendar.
     */
    function move($eventID, $newCalendar)
    {
        return $this->_wrapper->move($eventID, $newCalendar);
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
        return $this->_wrapper->delete($calendar);
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
        return $this->_wrapper->rename($from, $to);
    }

    /**
     * Delete an event.
     *
     * @param string $eventId  The ID of the event to delete.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function deleteEvent($eventID, $silent = false)
    {
        return $this->_wrapper->deleteEvent($eventID, $silent);
    }
}

/**
 * Horde Kronolith wrapper to distinguish between both Kolab driver implementations.
 *
 * $Horde: kronolith/lib/Driver/kolab.php,v 1.16.2.30 2009-01-06 15:24:45 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kronolith
 */

class Kronolith_Driver_kolab_wrapper {
    /**
     * Our Kolab server connection.
     *
     * @var Kolab
     */
    var $_kolab = null;

    /**
     * Link to the parent driver object
     *
     * @var Kronolith_Driver
     */

    var $_driver = null;

    /**
      * Constructor
      *
      * @param Kronolith_driver $driver     Reference to the Kronolith_Driver
      */
    function Kronolith_Driver_kolab_wrapper(&$driver)
    {
        $this->_driver = &$driver;
        $this->_kolab = &$driver->_kolab;
    }

    function open($calendar)
    {
    }
}


/**
 * Horde Kronolith driver for the Kolab IMAP Server.
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @package Kronolith
 */
class Kronolith_Driver_kolab_wrapper_old extends Kronolith_Driver_kolab_wrapper {

    /**
     * Indicates if the wrapper has connected or not
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * Reset internal variable on share change
     */
    function reset()
    {
        $this->_connected = false;
    }

    /**
     * Connect to the Kolab backend
     *
     * @param int    $loader         The version of the XML
     *                               loader
     *
     * @return mixed True on success, a PEAR error otherwise
     */
    function connect()
    {
        if ($this->_connected) {
            return true;
        }

        $result = $this->_kolab->open($this->_driver->_calendar);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_connected = true;

        return true;
    }

    function listAlarms($date, $fullevent = false)
    {
        if (!$this->_kolab) {
            return array();
        }

        $allevents = $this->listEvents($date, $date, true);
        if (is_a($allevents, 'PEAR_Error')) {
            return $allevents;
        }

        $events = array();

        foreach ($allevents as $eventId) {
            $event = &$this->getEvent($eventId);
            if (is_a($event, 'PEAR_Error')) {
                return $event;
            }

            if (is_a($event, 'PEAR_Error')) {
                return $event;
            }

            if (!$event->recurs()) {
                $start = new Horde_Date($event->start);
                $start->min -= $event->getAlarm();
                $start->correct();
                if ($start->compareDateTime($date) <= 0 &&
                    $date->compareDateTime($event->end) <= -1) {
                    $events[] = $fullevent ? $event : $eventId;
                }
            } else {
                if ($next = $event->recurrence->nextRecurrence($date)) {
                    if ($event->recurrence->hasException($next->year, $next->month, $next->mday)) {
                        continue;
                    }
                    $start = new Horde_Date($next);
                    $start->min -= $event->getAlarm();
                    $start->correct();
                    $end = &new Horde_Date(array('year' => $next->year,
                                                 'month' => $next->month,
                                                 'mday' => $next->mday,
                                                 'hour' => $event->end->hour,
                                                 'min' => $event->end->min,
                                                 'sec' => $event->end->sec));
                    if ($start->compareDateTime($date) <= 0 &&
                        $date->compareDateTime($end) <= -1) {
                        if ($fullevent) {
                            $event->start = $start;
                            $event->end = $end;
                            $events[] = $event;
                        } else {
                            $events[] = $eventId;
                        }
                    }
                }
            }
        }

        return is_array($events) ? $events : array();
    }

    /**
     * Checks if the event's UID already exists and returns all event
     * ids with that UID.
     *
     * @param string $uid          The event's uid.
     * @param string $calendar_id  Calendar to search in.
     *
     * @return mixed  Returns a string with event_id or false if not found.
     */
    function exists($uid, $calendar_id = null)
    {
        $this->connect();

        // Don't use calendar id here.
        if (is_a($this->_kolab->loadObject($uid), 'PEAR_Error')) {
            return false;
        }

        return $uid;
    }

    /**
     * Lists all events in the time range, optionally restricting
     * results to only events with alarms.
     *
     * @param Horde_Date $startInterval  Start of range date object.
     * @param Horde_Date $endInterval    End of range date object.
     * @param boolean $hasAlarm          Only return events with alarms?
     *                                   Defaults to <code>false</code>.
     *
     * @return array  Events in the given time range.
     */
    function listEvents($startDate = null, $endDate = null, $hasAlarm = false)
    {
        $this->connect();

        // We don't perform any checking on $startDate and $endDate,
        // as that has the potential to leave out recurring event
        // instances.
        $events = array();

        $msg_list = null;
        if ($this->_kolab) {
            $msg_list = $this->_kolab->listObjects();
            if (is_a($msg_list, 'PEAR_Error')) {
                return $msg_list;
            }
        }
        if (!$msg_list) {
            return $events;
        }

        foreach ($msg_list as $msg) {
            $result = $this->_kolab->loadObject($msg, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $events[$this->_kolab->getUID()] = $this->_kolab->getUID();
        }

        return $events;
    }

    function &getEvent($eventID = null)
    {
        if (is_null($eventID)) {
            $event = &new Kronolith_Event_kolab_old($this->_driver);
            return $event;
        }

        $this->connect();

        $result = $this->_kolab->loadObject($eventID);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $event = &new Kronolith_Event_kolab_old($this->_driver);
        $event->fromDriver($this);

        return $event;
    }

    /**
     * Get an event or events with the given UID value.
     *
     * @param string $uid The UID to match
     * @param array $calendars A restricted array of calendar ids to search
     * @param boolean $getAll Return all matching events? If this is false,
     * an error will be returned if more than one event is found.
     *
     * @return Kronolith_Event
     */
    function &getByUID($uid, $calendars = null, $getAll = false)
    {
        if (!is_array($calendars)) {
            $calendars = array_keys(Kronolith::listCalendars(true, PERMS_READ));
        }

        foreach ($calendars as $calendar) {
            $this->_driver->open($calendar);
            $this->connect();

            $event = &$this->getEvent($uid);
            if (is_a($event, 'PEAR_Error')) {
                continue;
            }

            if ($getAll) {
                $events = array();
                $events[] = &$event;
                return $events;
            } else {
                return $event;
            }
        }

        return PEAR::raiseError(sprintf(_("Event not found: %s"), $uid));
    }

    function saveEvent(&$event)
    {
        $this->connect();

        $edit = false;
        if ($event->isStored() || $event->exists()) {
            $uid = $event->getUID();

            $result = $this->_kolab->loadObject($uid);
            //No error check here, already done in exists()

            $edit = true;
        } else {
            if ($event->getUID()) {
                $uid = $event->getUID();
            } else {
                $uid = md5(uniqid(mt_rand(), true));
                $event->setUID($uid);
                $event->setId($uid);
            }

            $this->_kolab->newObject($uid);
        }

        $xml_hash = &$this->_kolab->getCurrentObject();

        $this->_kolab->setStr('summary', $event->getTitle());
        $this->_kolab->setStr('body', $event->getDescription());
        $this->_kolab->setStr('categories', $event->getCategory());
        $this->_kolab->setStr('location', $event->getLocation());
        if ($event->isPrivate()) {
            $this->_kolab->setStr('sensitivity', 'private');
        }

        $organizer = &$this->_kolab->initRootElem('organizer');
        $this->_kolab->setElemStr($organizer, 'smtp-address', $event->getCreatorID());

        $this->_kolab->setVal('alarm', $event->getAlarm());
        if ($event->isAllDay()) {
            $this->_kolab->setVal('start-date', Kolab::encodeDate($event->start->timestamp()));
            $this->_kolab->setVal('end-date', Kolab::encodeDate($event->end->timestamp()-24*60*60));
        } else {
            $this->_kolab->setVal('start-date', Kolab::encodeDateTime($event->start->timestamp()));
            $this->_kolab->setVal('end-date', Kolab::encodeDateTime($event->end->timestamp()));
        }

        switch ($event->status) {
        case KRONOLITH_STATUS_FREE:
        case KRONOLITH_STATUS_CANCELLED:
            $this->_kolab->setVal('show-time-as', 'free');
            break;

        case KRONOLITH_STATUS_TENTATIVE:
            $this->_kolab->setVal('show-time-as', 'tentative');
            break;

        case KRONOLITH_STATUS_CONFIRMED:
        default:
            $this->_kolab->setVal('show-time-as', 'busy');
            break;
        }

        $this->_kolab->delAllRootElems('attendee');
        foreach ($event->attendees as $email => $status) {
            $attendee = &$this->_kolab->appendRootElem('attendee');
            $this->_kolab->setElemVal($attendee, 'smtp-address', $email);

            switch ($status['response']) {
            case KRONOLITH_RESPONSE_ACCEPTED:
                $this->_kolab->setElemVal($attendee, 'status', 'accepted');
                break;

            case KRONOLITH_RESPONSE_DECLINED:
                $this->_kolab->setElemVal($attendee, 'status', 'declined');
                break;

            case KRONOLITH_RESPONSE_TENTATIVE:
                $this->_kolab->setElemVal($attendee, 'status', 'tentative');
                break;

            case KRONOLITH_RESPONSE_NONE:
            default:
                $this->_kolab->setElemVal($attendee, 'status', 'none');
            }

            switch ($status['attendance']) {
            case KRONOLITH_PART_OPTIONAL:
                $this->_kolab->setElemVal($attendee, 'role', 'optional');
                break;

            case KRONOLITH_PART_NONE:
                $this->_kolab->setElemVal($attendee, 'role', 'resource');
                break;

            case KRONOLITH_PART_REQUIRED:
            default:
                $this->_kolab->setElemVal($attendee, 'role', 'required');
            }
        }

        $this->_kolab->delAllRootElems('recurrence');

        $range_type = 'none';
        $range = 0;

        if ($event->recurs()) {
            $recurrence = &$this->_kolab->initRootElem('recurrence');
            $this->_kolab->setElemVal($recurrence, 'interval', $event->recurrence->getRecurInterval());

            switch ($event->recurrence->getRecurType()) {
                case HORDE_DATE_RECUR_DAILY:
                    $recurrence->set_attribute('cycle', 'daily');
                    break;

                case HORDE_DATE_RECUR_WEEKLY:
                    $recurrence->set_attribute('cycle', 'weekly');

                    $days = array('sunday', 'monday', 'tuesday', 'wednesday',
                                  'thursday', 'friday', 'saturday');

                    for ($i = 0; $i <= 7 ; ++$i) {
                        if ($event->recurrence->recurOnDay(pow(2, $i))) {
                            $day = &$this->_kolab->appendElem('day', $recurrence);
                            $day->set_content($days[$i]);
                        }
                    }
                    break;

                case HORDE_DATE_RECUR_MONTHLY_DATE:
                    $recurrence->set_attribute('cycle', 'monthly');
                    $recurrence->set_attribute('type', 'daynumber');
                    $this->_kolab->setElemVal($recurrence, 'daynumber', $event->start->mday);
                    break;

                case HORDE_DATE_RECUR_MONTHLY_WEEKDAY:
                    $recurrence->set_attribute('cycle', 'monthly');
                    $recurrence->set_attribute('type', 'weekday');
                    $this->_kolab->setElemVal($recurrence, 'daynumber', (int)(($event->start->mday - 1) / 7));
                    $start = new Horde_Date($event->start);
                    $days = array('sunday', 'monday', 'tuesday', 'wednesday',
                                  'thursday', 'friday', 'saturday');
                    $this->_kolab->setElemVal($recurrence, 'day', $days[$start->dayOfWeek()]);
                    break;

                case HORDE_DATE_RECUR_YEARLY_DATE:
                    $recurrence->set_attribute('cycle', 'yearly');
                    $recurrence->set_attribute('type', 'monthday');

                    $months = array('january', 'february', 'march', 'april',
                                    'may', 'june', 'july', 'august', 'september',
                                    'october', 'november', 'december');

                    $this->_kolab->setElemVal($recurrence, 'month', $months[$event->start->month]);
                    $this->_kolab->setElemVal($recurrence, 'daynumber', $event->start->mday);
                    break;

                case HORDE_DATE_RECUR_YEARLY_DAY:
                    $recurrence->set_attribute('cycle', 'yearly');
                    $recurrence->set_attribute('type', 'yearday');
                    $this->_kolab->setElemVal($recurrence, 'daynumber', $event->start->dayOfYear());
                    break;

                case HORDE_DATE_RECUR_YEARLY_WEEKDAY:
                    $recurrence->set_attribute('cycle', 'yearly');
                    $recurrence->set_attribute('type', 'weekday');
                    $this->_kolab->setElemVal($recurrence, 'daynumber', (int)(($event->start->mday - 1) / 7));
                    $start = new Horde_Date($event->start);
                    $days = array('sunday', 'monday', 'tuesday', 'wednesday',
                                  'thursday', 'friday', 'saturday');
                    $this->_kolab->setElemVal($recurrence, 'day', $days[$start->dayOfWeek()]);
                    $months = array('january', 'february', 'march', 'april',
                                    'may', 'june', 'july', 'august', 'september',
                                    'october', 'november', 'december');
                    $this->_kolab->setElemVal($recurrence, 'month', $months[$event->start->month]);
                    break;
            }

            if ($event->recurrence->hasRecurEnd()) {
                $range_type = 'date';
                // fix off-by-one day
                $recur_end = $event->recurrence->getRecurEnd();
                $recur_end->mday -= 1;
                $recur_end->correct();
                $range = Kolab::encodeDate($recur_end->timestamp());
            } elseif ($event->recurrence->getRecurCount()) {
                $range_type = 'number';
                $range = $event->recurrence->getRecurCount();
            } else {
                $range_type = 'none';
                $range = '';
            }

            $range = &$this->_kolab->setElemVal($recurrence, 'range', $range);
            $range->set_attribute('type', $range_type);

            foreach ($event->recurrence->getExceptions() as $exception) {
                $extime = strtotime($exception);
                $exception = Kolab::encodeDate($extime);
                $exclusion = &$this->_kolab->appendElem('exclusion', $recurrence);
                $exclusion->set_content($exception);
            }
        }

        $result = $this->_kolab->saveObject();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (is_callable('Kolab', 'triggerFreeBusyUpdate')) {
            Kolab::triggerFreeBusyUpdate($this->_driver->_calendar);
        }

        /* Notify about the changed event. */
        $result = Kronolith::sendNotification($event, $edit ? 'edit' : 'add');
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        return $uid;
    }

    /**
     * Move an event to a new calendar.
     *
     * @param string $eventId      The event to move.
     * @param string $newCalendar  The new calendar.
     */
    function move($eventID, $newCalendar)
    {
        $this->connect();

        $result = $this->_kolab->moveObject($eventID, $newCalendar);

        if (is_callable('Kolab', 'triggerFreeBusyUpdate')) {
            Kolab::triggerFreeBusyUpdate($this->_driver->_calendar);
            Kolab::triggerFreeBusyUpdate($newCalendar);
        }

        return $result;
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
        // For the old code we don't care
        return true;
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
        // For the old code we don't care
        return true;
    }

    /**
     * Delete an event.
     *
     * @param string $eventId  The ID of the event to delete.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function deleteEvent($eventID, $silent = false)
    {
        $this->connect();

        /* Fetch the event for later use. */
        $event = &$this->getEvent($eventID);
        if (is_a($event, 'PEAR_Error')) {
            return $event;
        }

        /* Delete the event. */
        $deleted = $this->_kolab->removeObjects($eventID);
        if (!$deleted || is_a($deleted, 'PEAR_Error')) {
            return $deleted;
        }

        if (is_callable('Kolab', 'triggerFreeBusyUpdate')) {
            Kolab::triggerFreeBusyUpdate($this->_driver->_calendar);
        }

        /* Notify about the deleted event. */
        if (!$silent) {
            $result = Kronolith::sendNotification($event, 'delete');
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }
    }

}

class Kronolith_Event_kolab_old extends Kronolith_Event {

    function fromDriver($dummy)
    {
        $driver = &$this->getDriver();
        $kolab = &$driver->_kolab;

        $this->eventID = $kolab->getUID();
        $this->setUID($kolab->getUID());
        $this->title = $kolab->getStr('summary');
        $this->description = $kolab->getStr('body');
        $this->location = $kolab->getStr('location');
        $this->category = $kolab->getStr('categories');

        $class = String::lower($kolab->getStr('sensitivity'));
        if ($class == 'private' || $class == 'confidential') {
            $this->private = true;
        }

        $organizer = &$kolab->getRootElem('organizer');
        $this->creatorID = $kolab->getElemStr($organizer, 'smtp-address');

        $this->alarm = $kolab->getVal('alarm');
        $this->start = new Horde_Date(Kolab::decodeDateOrDateTime($kolab->getVal('start-date')));
        $this->end = new Horde_Date(Kolab::decodeFullDayDate($kolab->getVal('end-date')));
        $this->durMin = ($this->end->timestamp() - $this->start->timestamp()) / 60;

        $status = $kolab->getVal('show-time-as');
        switch ($status) {
        case 'free':
            $this->status = KRONOLITH_STATUS_FREE;
            break;

        case 'tentative':
            $this->status = KRONOLITH_STATUS_TENTATIVE;
            break;

        case 'busy':
        case 'outofoffice':
        default:
            $this->status = KRONOLITH_STATUS_CONFIRMED;
        }

        $attendees = array_change_key_case($kolab->getAllRootElems('attendee'));
        for ($i = 0, $iMax = count($attendees); $i < $iMax; ++$i) {
            $attendee = $attendees[$i];

            $email = $kolab->getElemStr($attendee, 'smtp-address');
            if (empty($email)) {
                continue;
            }

            $role = $kolab->getElemVal($attendee, 'role');
            switch ($role) {
            case 'optional':
                $role = KRONOLITH_PART_OPTIONAL;
                break;

            case 'resource':
                $role = KRONOLITH_PART_NONE;
                break;

            case 'required':
            default:
                $role = KRONOLITH_PART_REQUIRED;
                break;
            }

            $status = $kolab->getElemVal($attendee, 'status');
            switch ($status) {
            case 'accepted':
                $status = KRONOLITH_RESPONSE_ACCEPTED;
                break;

            case 'declined':
                $status = KRONOLITH_RESPONSE_DECLINED;
                break;

            case 'tentative':
                $status = KRONOLITH_RESPONSE_TENTATIVE;
                break;

            case 'none':
            default:
                $status = KRONOLITH_RESPONSE_NONE;
                break;
            }

            $this->addAttendee($email, $role, $status, $kolab->getElemVal($attendee, 'display-name'));
        }

        $recurrence = &$kolab->getRootElem('recurrence');
        if ($recurrence !== false) {
            $this->recurrence = new Horde_Date_Recurrence($this->start);
            $cycle = $recurrence->get_attribute('cycle');
            $this->recurrence->setRecurInterval($kolab->getElemVal($recurrence, 'interval'));

            switch ($cycle) {
            case 'daily':
                $this->recurrence->setRecurType(HORDE_DATE_RECUR_DAILY);
                break;

            case 'weekly':
                $this->recurrence->setRecurType(HORDE_DATE_RECUR_WEEKLY);

                $mask = 0;
                $bits = array(
                    'monday' => HORDE_DATE_MASK_MONDAY,
                    'tuesday' => HORDE_DATE_MASK_TUESDAY,
                    'wednesday' => HORDE_DATE_MASK_WEDNESDAY,
                    'thursday' => HORDE_DATE_MASK_THURSDAY,
                    'friday' => HORDE_DATE_MASK_FRIDAY,
                    'saturday' => HORDE_DATE_MASK_SATURDAY,
                    'sunday' => HORDE_DATE_MASK_SUNDAY,
                );

                $days = $kolab->getAllElems('day', $recurrence);
                foreach ($days as $day) {
                    $day_str = $day->get_content();

                    if (empty($day_str) || !isset($bits[$day_str])) {
                        continue;
                    }

                    $mask |= $bits[$day_str];
                }

                $this->recurrence->setRecurOnDay($mask);
                break;

            case 'monthly':
                switch ($recurrence->get_attribute('type')) {
                case 'daynumber':
                    $this->recurrence->setRecurType(HORDE_DATE_RECUR_MONTHLY_DATE);
                    break;

                case 'weekday':
                    $this->recurrence->setRecurType(HORDE_DATE_RECUR_MONTHLY_DATE);
                    break;
                }
                break;

            case 'yearly':
                switch ($recurrence->get_attribute('type')) {
                case 'monthday':
                    $this->recurrence->setRecurType(HORDE_DATE_RECUR_YEARLY_DATE);
                    break;
                case 'daynumber':
                    $this->recurrence->setRecurType(HORDE_DATE_RECUR_YEARLY_DAY);
                    break;
                case 'weekday':
                    $this->recurrence->setRecurType(HORDE_DATE_RECUR_YEARLY_WEEKDAY);
                    break;
                }
            }

            $range = &$kolab->getElem('range', $recurrence);
            $range_type = $range->get_attribute('type');
            $range_val = $kolab->getElemVal($recurrence, 'range');

            switch ($range_type) {
            case 'number':
                $this->recurrence->setRecurCount($range_val);
                break;

            case 'date':
                // fix off-by-one day
                $timestamp = Kolab_Date::decodeDate($range_val);
                $this->recurrence->setRecurEnd(new Horde_Date($timestamp + 86400));
                break;
            }

            $exceptions = $kolab->getAllElems('exclusion', $recurrence);
            foreach ($exceptions as $exception) {
                $exception = new Horde_Date(Kolab::decodeDate($exception->get_content()));
                $this->recurrence->addException($exception->year, $exception->month, $exception->mday);
            }
        }

        $this->initialized = true;
        $this->stored = true;
    }

    function toDriver()
    {
    }

}

/**
 * Horde Kronolith driver for the Kolab IMAP Server.
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @package Kronolith
 */
class Kronolith_Driver_kolab_wrapper_new extends Kronolith_Driver_kolab_wrapper {

    /**
     * Internal cache of Kronolith_Event_kolab_new. eventID/UID is key
     *
     * @var array
     */
    var $_events_cache;

    /**
     * Indicates if we have synchronized this folder
     *
     * @var boolean
     */
    var $_synchronized;

    /**
     * Shortcut to the imap connection
     *
     * @var Kolab_IMAP
     */
    var $_store;

    /**
      * Constructor
      */
    function Kronolith_Driver_kolab_wrapper_new(&$driver)
    {
        parent::Kronolith_Driver_kolab_wrapper($driver);
        $this->reset();
    }

    function open($calendar)
    {
        $this->synchronize();
    }

    /**
     * Reset internal variable on share change
     */
    function reset()
    {
        $this->_events_cache = array();
        $this->_synchronized = false;
    }

    // We delay initial synchronization to the first use
    // so multiple calendars don't add to the total latency.
    // This function must be called before all internal driver functions
    function synchronize($force = false)
    {
        if ($this->_synchronized && !$force) {
            return;
        }

        // Connect to the Kolab backend
        $result = $this->_kolab->open($this->_driver->_calendar, 1);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $this->_store = &$this->_kolab->_storage;

        // build internal event cache
        $this->_events_cache = array();
        $events = $this->_store->getObjects();
        foreach($events as $event) {
            $this->_events_cache[$event['uid']] = &new Kronolith_Event_kolab_new($this->_driver, $event);
        }

        $this->_synchronized = true;
    }

    function listAlarms($date, $fullevent = false)
    {
        $allevents = $this->listEvents($date, null, true);
        $events = array();

        foreach ($allevents as $eventId) {
            $event = &$this->getEvent($eventId);
            if (is_a($event, 'PEAR_Error')) {
                return $event;
            }

            if (!$event->recurs()) {
                $start = new Horde_Date($event->start);
                $start->min -= $event->getAlarm();
                $start->correct();
                if ($start->compareDateTime($date) <= 0 &&
                    $date->compareDateTime($event->end) <= -1) {
                    $events[] = $fullevent ? $event : $eventId;
                }
            } else {
                if ($next = $event->recurrence->nextRecurrence($date)) {
                    if ($event->recurrence->hasException($next->year, $next->month, $next->mday)) {
                        continue;
                    }
                    $start = new Horde_Date($next);
                    $start->min -= $event->getAlarm();
                    $start->correct();
                    $end = &new Horde_Date(array('year' => $next->year,
                                                 'month' => $next->month,
                                                 'mday' => $next->mday,
                                                 'hour' => $event->end->hour,
                                                 'min' => $event->end->min,
                                                 'sec' => $event->end->sec));
                    if ($start->compareDateTime($date) <= 0 &&
                        $date->compareDateTime($end) <= -1) {
                        if ($fullevent) {
                            $event->start = $start;
                            $event->end = $end;
                            $events[] = $event;
                        } else {
                            $events[] = $eventId;
                        }
                    }
                }
            }
        }

        return is_array($events) ? $events : array();
    }

    /**
     * Checks if the event's UID already exists and returns all event
     * ids with that UID.
     *
     * @param string $uid          The event's uid.
     * @param string $calendar_id  Calendar to search in.
     *
     * @return string|boolean  Returns a string with event_id or false if
     *                         not found.
     */
    function exists($uid, $calendar_id = null)
    {
        // Log error if someone uses this function in an unsupported way
        if ($calendar_id != $this->_driver->_calendar) {
            Horde::logMessage(sprintf("Kolab::exists called for calendar %s. Currently active is %s.", $calendar_id, $this->_driver->_calendar), __FILE__, __LINE__, PEAR_LOG_ERR);
            return PEAR::raiseError(sprintf("Kolab::exists called for calendar %s. Currently active is %s.", $calendar_id, $this->_driver->_calendar));
        }

        $result = $this->synchronize();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($this->_store->objectUidExists($uid)) {
            return $uid;
        }

        return false;
    }

    /**
     * Lists all events in the time range, optionally restricting
     * results to only events with alarms.
     *
     * @param Horde_Date $startInterval  Start of range date object.
     * @param Horde_Date $endInterval    End of range data object.
     * @param boolean $hasAlarm          Only return events with alarms?
     *                                   Defaults to all events.
     *
     * @return array  Events in the given time range.
     */
    function listEvents($startDate = null, $endDate = null, $hasAlarm = false)
    {
        $result = $this->synchronize();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (empty($startDate)) {
            $startDate = &new Horde_Date(array('mday' => 1, 'month' => 1, 'year' => 0000));
        }
        if (empty($endDate)) {
            $endDate = &new Horde_Date(array('mday' => 31, 'month' => 12, 'year' => 9999));
        }
        if (!is_a($startDate, 'Horde_Date')) {
            $startDate = &new Horde_Date($startDate);
        }
        if (!is_a($endDate, 'Horde_Date')) {
            $endDate = &new Horde_Date($endDate);
        }

        $ids = array();

        foreach($this->_events_cache as $event) {
            if ($hasAlarm && !$event->getAlarm()) {
                continue;
            }

            $keep_event = false;
            /* check if event period intersects with given period */
            if (!(($endDate->compareDateTime($event->start) < 0) ||
                  ($startDate->compareDateTime($event->end) > 0))) {
                $keep_event = true;
            }

            /* do recurrence expansion if not keeping anyway */
            if (!$keep_event && $event->recurs()) {
                $next = $event->recurrence->nextRecurrence($startDate);
                while ($next !== false &&
                       $event->recurrence->hasException($next->year, $next->month, $next->mday)) {
                    $next->mday++;
                    $next = $event->recurrence->nextRecurrence($next);
                }

                if ($next !== false) {
                    $duration = $next->timestamp() - $event->start->timestamp();
                    $next_end = &new Horde_Date($event->end->timestamp() + $duration);

                    if ((!(($endDate->compareDateTime($next) < 0) ||
                           ($startDate->compareDateTime($next_end) > 0)))) {
                        $keep_event = true;
                    }
                }
            }

            if ($keep_event) {
                $ids[$event->getUID()] = $event->getUID();
            }
        }

        return $ids;
    }

    function &getEvent($eventId = null)
    {
        if (is_null($eventId)) {
            $event = &new Kronolith_Event_kolab_new($this->_driver);
            return $event;
        }

        $result = $this->synchronize();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (array_key_exists($eventId, $this->_events_cache)) {
            return $this->_events_cache[$eventId];
        }

        return PEAR::raiseError(sprintf(_("Event not found: %s"), $eventId));
    }

    /**
     * Get an event or events with the given UID value.
     *
     * @param string $uid The UID to match
     * @param array $calendars A restricted array of calendar ids to search
     * @param boolean $getAll Return all matching events? If this is false,
     * an error will be returned if more than one event is found.
     *
     * @return Kronolith_Event
     */
    function &getByUID($uid, $calendars = null, $getAll = false)
    {
        if (!is_array($calendars)) {
            $calendars = array_keys(Kronolith::listCalendars(true, PERMS_READ));
        }

        foreach ($calendars as $calendar) {
            $this->_driver->open($calendar);
            $this->synchronize();

            if (!array_key_exists($uid, $this->_events_cache)) {
                continue;
            }

            // Ok, found event
            $event = &$this->_events_cache[$uid];

            if ($getAll) {
                $events = array();
                $events[] = &$event;
                return $events;
            } else {
                return $event;
            }
        }

        return PEAR::raiseError(sprintf(_("Event not found: %s"), $uid));
    }

    /**
     * Saves an event in the backend.
     * If it is a new event, it is added, otherwise the event is updated.
     *
     * @param Kronolith_Event_new $event  The event to save.
     *
     * @return mixed  UID on success, a PEAR error otherwise
     */
    function saveEvent(&$event)
    {
        $result = $this->synchronize();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $uid = $event->getUID();
        if ($uid == null) {
            $event->setUID($this->_store->generateUID());
        }

        $attributes = $event->toDriver();

        $edit = false;
        $stored_uid = null;
        if ($event->isStored() || $event->exists()) {
            $stored_uid = $attributes['uid'];
            $action = array('action' => 'modify');
            $edit = true;
        } else {
            $action = array('action' => 'add');
        }

        $result = $this->_store->save($attributes, $stored_uid);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Notify about the changed event. */
        $result = Kronolith::sendNotification($event, $edit ? 'edit' : 'add');
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        /* Log the creation/modification of this item in the history log. */
        $history = &Horde_History::singleton();
        $history->log('kronolith:' . $event->getCalendar() . ':' . $event->getUID(), $action, true);

        // refresh IMAP cache
        $this->synchronize(true);

        if (is_callable('Kolab', 'triggerFreeBusyUpdate')) {
            Kolab::triggerFreeBusyUpdate($this->_store->parseFolder($event->getCalendar()));
        }

        return $event->getUID();
    }

    /**
     * Move an event to a new calendar.
     *
     * @param string $eventId      The event to move.
     * @param string $newCalendar  The new calendar.
     */
    function move($eventId, $newCalendar)
    {
        $event = &$this->getEvent($eventId);

        $result = $this->synchronize();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        global $kronolith_shares;
        $target = &$kronolith_shares->getShare($newCalendar);
        $folder = $target->get('folder');

        $result = $this->_store->move($eventId, $folder);
        if ($result) {
            unset($this->_events_cache[$eventId]);
        }

        if (is_callable('Kolab', 'triggerFreeBusyUpdate')) {
            Kolab::triggerFreeBusyUpdate($this->_store->parseFolder($this->_driver->_calendar));
            Kolab::triggerFreeBusyUpdate($this->_store->parseFolder($newCalendar));
        }

        /* Log the moving of this item in the history log. */
        $uid = $event->getUID();
        $history = &Horde_History::singleton();
        $history->log('kronolith:' . $event->getCalendar() . ':' . $uid, array('action' => 'delete'), true);
        $history->log('kronolith:' . $newCalendar . ':' . $uid, array('action' => 'add'), true);

        return $result;
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
        $this->_driver->open($calendar);
        $result = $this->synchronize();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->_store->deleteAll($calendar);
        if (is_callable('Kolab', 'triggerFreeBusyUpdate')) {
            Kolab::triggerFreeBusyUpdate($this->_store->parseFolder($calendar));
        }
        return true;
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
        // FIXME: We can't do much here. We'd need to be called after
        // renaming the share here. This needs to be checked again.
        // kolab/issue2249 ([horde/kronolith] Kronolith is unable to
        // trigger a free/busy update on a folder rename)
        return true;
    }

    /**
     * Delete an event.
     *
     * @param string $eventId  The ID of the event to delete.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function deleteEvent($eventId, $silent = false)
    {
        $result = $this->synchronize();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!$this->_store->objectUidExists($eventId)) {
            return PEAR::raiseError(sprintf(_("Event not found: %s"), $eventId));
        }

        $event = &$this->getEvent($eventId);

        if ($this->_store->delete($eventId)) {
            // Notify about the deleted event.
            if (!$silent) {
                $result = Kronolith::sendNotification($event, 'delete');
                if (is_a($result, 'PEAR_Error')) {
                    Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                }
            }

            /* Log the deletion of this item in the history log. */
            $history = &Horde_History::singleton();
            $history->log('kronolith:' . $event->getCalendar() . ':' . $event->getUID(), array('action' => 'delete'), true);

            if (is_callable('Kolab', 'triggerFreeBusyUpdate')) {
                Kolab::triggerFreeBusyUpdate($this->_store->parseFolder($event->getCalendar()));
            }

            unset($this->_events_cache[$eventId]);
        } else {
            return PEAR::raiseError(sprintf(_("Cannot delete event: %s"), $eventId));
        }

        return true;
    }

}

/**
 * @package Kronolith
 */
class Kronolith_Event_kolab_new extends Kronolith_Event {

    function fromDriver($event)
    {
        $this->eventID = $event['uid'];
        $this->setUID($this->eventID);

        if (isset($event['summary'])) {
            $this->title = $event['summary'];
        }
        if (isset($event['body'])) {
            $this->description = $event['body'];
        }
        if (isset($event['location'])) {
            $this->location = $event['location'];
        }
        if (isset($event['categories'])) {
            $this->category = $event['categories'];
        }

        if (isset($event['sensitivity']) &&
            ($event['sensitivity'] == 'private' || $event['sensitivity'] == 'confidential')) {
            $this->setPrivate(true);
        }

        if (isset($event['organizer']['smtp-address'])) {
            if (Kronolith::isUserEmail(Auth::getAuth(), $event['organizer']['smtp-address'])) {
                $this->creatorID = Auth::getAuth();
            } else {
                $this->creatorID = $event['organizer']['smtp-address'];
            }
        }

        if (isset($event['alarm'])) {
            $this->alarm = $event['alarm'];
        }

        $this->start = new Horde_Date($event['start-date']);
        $this->end = new Horde_Date($event['end-date']);
        $this->durMin = ($this->end->timestamp() - $this->start->timestamp()) / 60;

        if (isset($event['show-time-as'])) {
            switch ($event['show-time-as']) {
                case 'free':
                    $this->status = KRONOLITH_STATUS_FREE;
                    break;

                case 'tentative':
                    $this->status = KRONOLITH_STATUS_TENTATIVE;
                    break;

                case 'busy':
                case 'outofoffice':
                default:
                    $this->status = KRONOLITH_STATUS_CONFIRMED;
            }
        } else {
            $this->status = KRONOLITH_STATUS_CONFIRMED;
        }

        // Recurrence
        if (isset($event['recurrence'])) {
            $this->recurrence = new Horde_Date_Recurrence($this->start);
            $this->recurrence->fromHash($event['recurrence']);
        }

        // Attendees
        $attendee_count = 0;
        foreach($event['attendee'] as $attendee) {
            $name = $attendee['display-name'];
            $email = $attendee['smtp-address'];

            $role = $attendee['role'];
            switch ($role) {
            case 'optional':
                $role = KRONOLITH_PART_OPTIONAL;
                break;

            case 'resource':
                $role = KRONOLITH_PART_NONE;
                break;

            case 'required':
            default:
                $role = KRONOLITH_PART_REQUIRED;
                break;
            }

            $status = $attendee['status'];
            switch ($status) {
            case 'accepted':
                $status = KRONOLITH_RESPONSE_ACCEPTED;
                break;

            case 'declined':
                $status = KRONOLITH_RESPONSE_DECLINED;
                break;

            case 'tentative':
                $status = KRONOLITH_RESPONSE_TENTATIVE;
                break;

            case 'none':
            default:
                $status = KRONOLITH_RESPONSE_NONE;
                break;
            }

            // Attendees without an email address get added as incremented number
            if (empty($email)) {
                $email = $attendee_count;
                $attendee_count++;
            }

            $this->addAttendee($email, $role, $status, $name);
        }

        $this->initialized = true;
        $this->stored = true;
    }

    function toDriver()
    {
        $event = array();
        $event['uid'] = $this->getUID();
        $event['summary'] = $this->title;
        $event['body']  = $this->description;
        $event['location'] = $this->location;
        $event['categories'] = $this->category;

        if ($this->isPrivate()) {
            $event['sensitivity'] = 'private';
        } else {
            $event['sensitivity'] = 'public';
        }

        // Only set organizer if this is a new event
        if ($this->getID() == null) {
            $organizer = array(
                            'display-name' => Kronolith::getUserName($this->getCreatorId()),
                            'smtp-address' => Kronolith::getUserEmail($this->getCreatorId())
                         );
            $event['organizer'] = $organizer;
        }

        if ($this->alarm != 0) {
            $event['alarm'] = $this->alarm;
        }

        $event['start-date'] = $this->start->timestamp();
        $event['end-date'] = $this->end->timestamp();
        $event['_is_all_day'] = $this->isAllDay();

        switch ($this->status) {
        case KRONOLITH_STATUS_FREE:
        case KRONOLITH_STATUS_CANCELLED:
            $event['show-time-as'] = 'free';
            break;

        case KRONOLITH_STATUS_TENTATIVE:
            $event['show-time-as'] = 'tentative';
            break;

        // No mapping for outofoffice
        case KRONOLITH_STATUS_CONFIRMED:
        default:
            $event['show-time-as'] = 'busy';
        }

        // Recurrence
        if ($this->recurs()) {
            $event['recurrence'] = $this->recurrence->toHash();
        } else {
            $event['recurrence'] = array();
        }


        // Attendees
        $event['attendee'] = array();
        $attendees = $this->getAttendees();

        foreach($attendees as $email => $attendee) {
            $new_attendee = array();
            $new_attendee['display-name'] = $attendee['name'];

            // Attendee without an email address
            if (is_int($email)) {
                $new_attendee['smtp-address'] = '';
            } else {
                $new_attendee['smtp-address'] = $email;
            }

            switch ($attendee['attendance']) {
            case KRONOLITH_PART_OPTIONAL:
                $new_attendee['role'] = 'optional';
                break;

            case KRONOLITH_PART_NONE:
                $new_attendee['role'] = 'resource';
                break;

            case KRONOLITH_PART_REQUIRED:
            default:
                $new_attendee['role'] = 'required';
                break;
            }

            $new_attendee['request-response'] = '0';

            switch ($attendee['response']) {
            case KRONOLITH_RESPONSE_ACCEPTED:
                $new_attendee['status'] = 'accepted';
                break;

            case KRONOLITH_RESPONSE_DECLINED:
                $new_attendee['status'] = 'declined';
                break;

            case KRONOLITH_RESPONSE_TENTATIVE:
                $new_attendee['status'] = 'tentative';
                break;

            case KRONOLITH_RESPONSE_NONE:
            default:
                $new_attendee['status'] = 'none';
                break;
            }

            $event['attendee'][] = $new_attendee;
        }

        return $event;
    }
}
