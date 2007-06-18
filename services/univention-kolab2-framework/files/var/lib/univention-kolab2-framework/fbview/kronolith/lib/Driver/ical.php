<?php
/**
 * The Kronolith_Driver_ical:: class implements the Kronolith_Driver
 * API for iCalendar data.
 *
 * $Horde: kronolith/lib/Driver/ical.php,v 1.1 2004/05/02 21:50:23 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Kronolith 2.0
 * @package Kronolith
 */
class Kronolith_Driver_ical extends Kronolith_Driver {

    /**
     * Cache events as we fetch them to avoid fetching or parsing the
     * same event twice.
     *
     * @var array $_cache
     */
    var $_cache = array();

    function open($calendar)
    {
        $this->_calendar = $calendar;
    }

    function listAlarms($date)
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
                $event->eventIndex = $i;
                $events[] = $event;
            }
        }

        return $events;
        if (!isset($endDate)) {
            $endDate = Kronolith::dateObject(array('mday' => 31, 'month' => 12, 'year' => 9999));
        } else {
            list($endDate->mday, $endDate->month, $endDate->year) = explode('/', Date_Calc::nextDay($endDate->mday, $endDate->month, $endDate->year, '%d/%m/%Y'));
        }
        $endDate = &new Kronolith_Date($endDate);

        return array();
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
            $event->eventIndex = $eventId;

            return $event;
        }

        return false;
    }

    function &getByGUID($guid)
    {
    }

    function saveEvent($event)
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Move an event to a new calendar.
     *
     * @param string $eventId      The event to move.
     * @param string $newCalendar  The new calendar.
     */
    function move($eventId, $newCalendar)
    {
        return PEAR::raiseError('not supported');
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
        return PEAR::raiseError('not supported');
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
        return PEAR::raiseError('not supported');
    }

    function close()
    {
        return true;
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
