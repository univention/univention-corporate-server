<?php
/**
 * The Kronolith_Driver_holidays implements support for the PEAR package
 * Date_Holidays.
 *
 * @see     http://pear.php.net/packages/Date_Holidays
 * @author  Stephan Hohmann <webmaster@dasourcerer.net>
 * @package Kronolith
 * @since   Kronolith 2.2
 */

class Kronolith_Driver_holidays extends Kronolith_Driver {

    function listAlarms($date, $fullevent = false)
    {
        return array();
    }

    /**
     * Returns a list of all holidays occuring between <code>$startDate</code>
     * and <code>$endDate</code>.
     *
     * @param int|Horde_Date $startDate  The start of the datespan to be
     *                                   checked. Defaults to the current date.
     * @param int|Horde_Date $endDate    The end of the datespan. Defaults to
     *                                   the current date.
     * @param bool $hasAlarm             Left in for compatibility reasons and
     *                                   has no effect on this function.
     *                                   Defaults to <code>false</code>
     *
     * @return array  An array of all holidays within the given datespan.
     */
    function listEvents($startDate = null, $endDate = null, $hasAlarm = false)
    {
        global $language;

        $events = array();

        if (is_null($startDate)) {
            $startDate = new Horde_Date($_SERVER['REQUEST_TIME']);
        }

        if (is_null($endDate)) {
            $endDate = new Horde_Date($_SERVER['REQUEST_TIME']);
        }

        Date_Holidays::staticSetProperty('DIE_ON_MISSING_LOCALE', false);
        foreach (unserialize($GLOBALS['prefs']->getValue('holiday_drivers')) as $driver) {
            for ($year = $startDate->year; $year <= $endDate->year; $year++) {
                $dh = Date_Holidays::factory($driver, $year, $language);
                if (Date_Holidays::isError($dh)) {
                    Horde::logMessage(sprintf('Factory was unable to produce driver object for driver %s in year %s with locale %s',
                                              $driver, $year, $language),
                                      __FILE__, __LINE__, PEAR_LOG_ERR);
                    continue;
                }
                $dh->addTranslation($language);
                $events = array_merge($events, $this->_getEvents($dh, $startDate, $endDate));
            }
        }

        return $events;
    }

    function _getEvents($dh, $startDate, $endDate)
    {
        $events = array();
        for ($date = new Horde_Date($startDate);
             $date->compareDate($endDate) <= 0;
             $date->mday++, $date->correct()) {
            $holidays = $dh->getHolidayForDate((int)$date->timestamp(), null, true);
            if (Date_Holidays::isError($holidays)) {
                Horde::logMessage(sprintf('Unable to retrieve list of holidays from %s to %s',
                                          $startDate->cTime(), $endDate->cTime()), __FILE__, __LINE__);
                continue;
            }

            if (is_null($holidays)) {
                continue;
            }

            foreach ($holidays as $holiday) {
                $event = &new Kronolith_Event_holidays($this);
                $event->fromDriver($holiday);
                $events[] = $event;
            }
        }
        return $events;
    }

    function &getEvent($eventId = null)
    {
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
     * Moves an event to a new calendar.
     *
     * @param string $eventId      The event to move.
     * @param string $newCalendar  The new calendar.
     */
    function move($eventId, $newCalendar)
    {
        return PEAR::raiseError('Not supported');
    }

    /**
     * Deletes a calendar and all its events.
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
     * Deletes an event.
     *
     * @param string $eventId  The ID of the event to delete.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function deleteEvent($eventId)
    {
        return PEAR::raiseError('Not supported');
    }

    function _getTranslationFile($driver)
    {
        static $data_dir;
        if (!isset($data_dir)) {
            include_once 'PEAR/Config.php';
            $pear_config = new PEAR_Config();
            $data_dir = $pear_config->get('data_dir');
        }
        if (empty($data_dir)) {
            return;
        }

        foreach (array('', '_' . $driver) as $pkg_ext) {
            foreach (array('ser', 'xml') as $format) {
                $location = $data_dir . '/Date_Holidays' . $pkg_ext . '/lang/'
                    . $driver . '/' . $GLOBALS['language'] . '.' . $format;
                if (file_exists($location)) {
                    return array($format, $location);
                }
            }
        }

        return array(null, null);
    }

}

class Kronolith_Event_holidays extends Kronolith_Event {

    /**
     * The status of this event.
     *
     * @var integer
     */
    var $status = KRONOLITH_STATUS_FREE;

    /**
     * Parse in an event from the driver.
     *
     * @param Date_Holidays_Holiday $dhEvent  A holiday returned
     *                                        from the driver
     */
    function fromDriver($dhEvent)
    {
        $this->stored = true;
        $this->initialized = true;
        $this->setTitle(String::convertCharset($dhEvent->getTitle(), 'UTF-8'));
        $this->setId($dhEvent->getInternalName());

        $this->start = new Horde_Date($dhEvent->_date->getTime());
        $this->end = new Horde_Date($this->start);
        $this->end->mday++;
        $this->end->correct();
    }

    /**
     * Return this events title.
     *
     * @return string The title of this event
     */
    function getTitle()
    {
        return $this->title;
    }

    /**
     * Is this event an all-day event?
     *
     * Since there are no holidays lasting only a few hours, this is always
     * true.
     *
     * @return boolean <code>true</code>
     */
    function isAllDay()
    {
        return true;
    }

}
