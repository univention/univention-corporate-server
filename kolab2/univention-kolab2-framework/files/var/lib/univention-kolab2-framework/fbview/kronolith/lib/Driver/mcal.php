<?php
/**
 * The Kronolith_Driver_mcal:: class implements the Kronolith_Driver
 * API for an MCAL backend.
 *
 * $Horde: kronolith/lib/Driver/mcal.php,v 1.56 2004/04/26 19:33:48 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_Driver_mcal extends Kronolith_Driver {

    /**
     * The current MCAL connection.
     *
     * @var resource $_stream
     */
    var $_stream;

    /**
     * Get a globally unique ID for an event. We need to override this
     * since we really need the calendar in mstore GUIDs in order to
     * look at the right file.
     *
     * @param integer $eventId  The event id.
     *
     * @return string  A GUID referring to $eventId.
     */
    function getGUID($eventId)
    {
        return 'kronolith:' . $this->_calendar . ':' . $eventId;
    }

    function open($calendar)
    {
        $this->_calendar = $calendar;
        $this->_stream = @mcal_popen("{/mstore}<$calendar>",
                                     $this->_params['username'],
                                     $this->_params['password']);
    }

    function close()
    {
        @mcal_close($this->_stream);
    }

    function listEvents($startDate = null, $endDate = null)
    {
        $events = @mcal_list_events($this->_stream, $startDate->year, $startDate->month, $startDate->mday, $endDate->year, $endDate->month, $endDate->mday);
        return is_array($events) ?
            Horde_Array::combine(array_map(create_function('$e', 'return "kronolith:' . $this->_calendar . ':" . $e;'), $events), $events) :
            array();
    }

    function listAlarms($date)
    {
        $events = @mcal_list_alarms($this->_stream, $date->year, $date->month, $date->mday, $date->hour, $date->min, $date->sec);
        return is_array($events) ? $events : array();
    }

    function &getEvent($eventID = null)
    {
        if (!is_null($eventID)) {
            $event = @mcal_fetch_event($this->_stream, (int)$eventID);
            if ($event && $event->id > 0) {
                return $ret = &new Kronolith_Event_mcal($this, $event);
            } else {
                return false;
            }
        } else {
            return $ret = &new Kronolith_Event_mcal($this);
        }
    }

    function &getByGUID($guid)
    {
        /* Validate the GUID. */
        $pieces = explode(':', $guid);

        /* Make sure this is a Kronolith GUID. */
        if ($pieces[0] != 'kronolith') {
            return array(false, false);
        }

        /* Strip off the kronolith entry. */
        array_shift($pieces);

        /* The event id is the last entry in the array. */
        $eventId = array_pop($pieces);

        /* The calendar id is everything else. */
        $calendar = implode(':', $pieces);

        /* Open $calendar and fetch the event. */
        $this->open($calendar);
        return $this->getEvent($eventId);
    }

    function saveEvent($event)
    {
        if (!is_null($event->getID())) {
            if ($id = mcal_store_event($this->_stream)) {
                /* Log the modification of this item in the history
                 * log. */
                $history = &Horde_History::singleton();
                $history->log($this->getGUID($id), array('action' => 'modify'), true);

                return $event->getID();
            } else {
                return false;
            }
        } else {
            if ($id = mcal_append_event($this->_stream)) {
                /* Log the creation of this item in the history
                 * log. */
                $history = &Horde_History::singleton();
                $history->log($this->getGUID($id), array('action' => 'add'), true);

                return $id;
            } else {
                return false;
            }
        }
    }

    function nextRecurrence($eventID, $afterDate, $weekstart = KRONOLITH_SUNDAY)
    {
        $next = mcal_next_recurrence($this->_stream, $weekstart, $afterDate);
        if (empty($next->year)) {
            return false;
        }

        return Kronolith::dateObject($next);
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
        if (!$event) {
            return PEAR::raiseError('not found');
        }

        $event->setCalendar($newCalendar);
        return $event->save();
    }

    /**
     * Delete a calendar and all its events.
     *
     * @param string $calendar The name of the calendar to delete.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function delete($calendar)
    {
        /**
         * @TODO FIXME: this is horrid, but will work for mstore for
         * now.
         */
        $file = '/var/calendar/' . basename($calendar);

        $this->close();

        @unlink($file);
        if (!@file_exists($file)) {
            $result = true;
        } else {
            $result = PEAR::raiseError(sprintf(_("Unable to delete %s."), $calendar));
        }

        return $result;
    }

    function deleteEvent($eventID)
    {
        if (mcal_delete_event($this->_stream, $eventID)) {
            /* Log the deletion of this item in the history log. */
            $history = &Horde_History::singleton();
            $history->log($this->getGUID($eventID), array('action' => 'delete'), true);

            return true;
        }

        return false;
    }

    function parseMCALDate($dateObject)
    {
        if (count($dateObject) === 0) {
            return 0;
        }

        $year = isset($dateObject->year) ? $dateObject->year : 0;
        $month = isset($dateObject->month) ? $dateObject->month : 0;
        $day = isset($dateObject->mday) ? $dateObject->mday : 0;

        // Check for events with no recur_enddate
        if ($year == 9999 && $month == 12 && $day == 31) {
            return 0;
        }

        $hour = isset($dateObject->hour) ? $dateObject->hour : 0;
        $minute = isset($dateObject->min) ? $dateObject->min : 0;
        $second = isset($dateObject->sec) ? $dateObject->sec : 0;

        return mktime($hour, $minute, $second, $month, $day, $year);
    }

}

class Kronolith_Event_mcal extends Kronolith_Event {

    function toDriver()
    {
        $driver = &$this->getDriver();

        // Basic fields.
        mcal_event_set_title($driver->_stream, $this->getTitle());
        mcal_event_set_description($driver->_stream, $this->getDescription());
        mcal_event_set_category($driver->_stream, $this->getCategory());
        mcal_event_add_attribute($driver->_stream, 'location', $this->getLocation());
        mcal_event_add_attribute($driver->_stream, 'keywords', implode(',', $this->getKeywords()));
        mcal_event_add_attribute($driver->_stream, 'exceptions', implode(',', $this->getExceptions()));
        mcal_event_add_attribute($driver->_stream, 'modified', time());
        mcal_event_add_attribute($driver->_stream, 'creatorid', $this->getCreatorID());

        // Event start.
        $start = explode(':', date('Y:n:j:G:i', $this->getStartTimestamp()));
        mcal_event_set_start($driver->_stream, $start[0], $start[1], $start[2], $start[3], $start[4]);

        // Event end.
        $end = explode(':', date('Y:n:j:G:i', $this->getEndTimestamp()));
        mcal_event_set_end($driver->_stream, $end[0], $end[1], $end[2], $end[3], $end[4]);

        // Alarm.
        mcal_event_set_alarm($driver->_stream, $this->getAlarm());

        // Recurrence.
        $recur_end = explode(':', date('Y:n:j', $this->getRecurEndTimestamp()));
        if ($recur_end[0] == 1969) {
            $recur_end[0] = 9999;
            $recur_end[1] = 12;
            $recur_end[2] = 31;
        }

        switch ($this->getRecurType()) {
        case KRONOLITH_RECUR_NONE:
            mcal_event_set_recur_none($driver->_stream);
            break;

        case KRONOLITH_RECUR_DAILY:
            mcal_event_set_recur_daily($driver->_stream,
                                       $recur_end[0],
                                       $recur_end[1],
                                       $recur_end[2],
                                       $this->getRecurInterval());
            break;

        case KRONOLITH_RECUR_WEEKLY:
            mcal_event_set_recur_weekly($driver->_stream,
                                        $recur_end[0],
                                        $recur_end[1],
                                        $recur_end[2],
                                        $this->getRecurInterval(),
                                        $this->getRecurOnDays());
            break;

        case KRONOLITH_RECUR_DAY_OF_MONTH:
            mcal_event_set_recur_monthly_mday($driver->_stream,
                                              $recur_end[0],
                                              $recur_end[1],
                                              $recur_end[2],
                                              $this->getRecurInterval());
            break;

        case KRONOLITH_RECUR_WEEK_OF_MONTH:
            mcal_event_set_recur_monthly_wday($driver->_stream,
                                              $recur_end[0],
                                              $recur_end[1],
                                              $recur_end[2],
                                              $this->getRecurInterval());
            break;

        case KRONOLITH_RECUR_YEARLY:
            mcal_event_set_recur_yearly($driver->_stream,
                                        $recur_end[0],
                                        $recur_end[1],
                                        $recur_end[2],
                                        $this->getRecurInterval());
            break;
        }
    }

    function fromDriver($mcalEvent)
    {
        $this->title = $mcalEvent->title;
        if (isset($mcalEvent->category)) {
            $this->category = $mcalEvent->category;
        }
        if (isset($mcalEvent->description)) {
            $this->description = $mcalEvent->description;
        }
        if (isset($mcalEvent->attrlist['creatorid'])) {
            $this->creatorID = $mcalEvent->attrlist['creatorid'];
        }
        if (isset($mcalEvent->attrlist['location'])) {
            $this->location = $mcalEvent->attrlist['location'];
        }
        if (isset($mcalEvent->attrlist['keywords'])) {
            $this->keywords = explode(',', $mcalEvent->attrlist['keywords']);
        }
        if (isset($mcalEvent->attrlist['exceptions'])) {
            $this->exceptions = explode(',', $mcalEvent->attrlist['exceptions']);
        }
        $this->eventID = $mcalEvent->id;

        $this->startTimestamp = Kronolith_Driver_mcal::parseMCALDate($mcalEvent->start);
        $this->start = Kronolith::timestampToObject($this->startTimestamp);

        $this->endTimestamp = Kronolith_Driver_mcal::parseMCALDate($mcalEvent->end);
        $this->end = Kronolith::timestampToObject($this->endTimestamp);

        $this->durMin = ($this->endTimestamp - $this->startTimestamp) / 60;

        if (isset($mcalEvent->recur_enddate)) {
            $this->recurEndTimestamp = Kronolith_Driver_mcal::parseMCALDate($mcalEvent->recur_enddate);
            $this->recurEnd = $mcalEvent->recur_enddate;
        }

        $this->alarm = $mcalEvent->alarm;

        $this->recurType = $mcalEvent->recur_type;
        $this->recurInterval = $mcalEvent->recur_interval;
        if (isset($mcalEvent->recur_data)) {
            $this->recurData = $mcalEvent->recur_data;
        }

        $this->initialized = true;
        $this->stored = true;
    }

}
