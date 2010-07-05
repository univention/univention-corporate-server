<?php
/**
 * The Kronolith_Driver_ical:: class implements the Kronolith_Driver
 * API for iCalendar data.
 *
 * $Horde: kronolith/lib/Driver/ical.php,v 1.3.2.6 2008-04-30 21:33:20 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.0
 * @package Kronolith
 */
class Kronolith_Driver_ical extends Kronolith_Driver {

    /**
     * Cache events as we fetch them to avoid fetching or parsing the same
     * event twice.
     *
     * @var array
     */
    var $_cache = array();

    function listAlarms($date, $fullevent = false)
    {
        return array();
    }

    function listEvents($startDate = null, $endDate = null, $hasAlarm = false)
    {
        $data = Kronolith::getRemoteCalendar($url);
        if (is_a($data, 'PEAR_Error')) {
            return $data;
        }

        require_once 'Horde/iCalendar.php';
        $iCal = &new Horde_iCalendar();
        if (!$iCal->parsevCalendar($data)) {
            return array();
        }

        $components = $iCal->getComponents();
        $events = array();
        $count = count($components);
        for ($i = 0; $i < $count; $i++) {
            $component = $components[$i];
            if ($component->getType() == 'vEvent') {
                $event = &new Kronolith_Event_ical($this);
                $event->fromiCalendar($component);
                $event->remoteCal = $url;
                $event->eventID = $i;
                $events[] = $event;
            }
        }

        return $events;
    }

    function &getEvent($eventId = null)
    {
        $data = Kronolith::getRemoteCalendar($url);
        if (is_a($data, 'PEAR_Error')) {
            return $data;
        }

        require_once 'Horde/iCalendar.php';
        $iCal = &new Horde_iCalendar();
        if (!$iCal->parsevCalendar($data)) {
            return array();
        }

        $components = $iCal->getComponents();
        if (isset($components[$eventId]) && $components[$eventId]->getType() == 'vEvent') {
            $event = &new Kronolith_Event_ical($this);
            $event->fromiCalendar($components[$eventId]);
            $event->remoteCal = $url;
            $event->eventID = $eventId;

            return $event;
        }

        return false;
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
        return PEAR::raiseError('Not supported');
    }

    function exists()
    {
        return PEAR::raiseError('Not supported');
    }

    function saveEvent($event)
    {
        return PEAR::raiseError('Not supported');
    }

    /**
     * Move an event to a new calendar.
     *
     * @param string $eventId      The event to move.
     * @param string $newCalendar  The new calendar.
     */
    function move($eventId, $newCalendar)
    {
        return PEAR::raiseError('Not supported');
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
        return PEAR::raiseError('Not supported');
    }

    /**
     * Delete an event.
     *
     * @param string $eventId  The ID of the event to delete.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function deleteEvent($eventId)
    {
        return PEAR::raiseError('Not supported');
    }

}

class Kronolith_Event_ical extends Kronolith_Event {

    function fromDriver($vEvent)
    {
        $this->fromiCalendar($vEvent);
        $this->initialized = true;
        $this->stored = true;
    }

    function toDriver()
    {
        return $this->toiCalendar();
    }

}
