<?php

require_once 'Horde/History.php';

/**
 * Kronolith_Driver:: defines an API for implementing storage backends
 * for Kronolith.
 *
 * $Horde: kronolith/lib/Driver.php,v 1.74 2004/05/26 20:58:12 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_Driver {

    /**
     * A hash containing any parameters for the current driver.
     * @var array $_params
     */
    var $_params = array();

    /**
     * The current calendar.
     * @var string $_calendar
     */
    var $_calendar;

    /**
     * Constructor - just store the $params in our newly-created
     * object. All other work is done by open().
     *
     * @param optional array $params  Any parameters needed for this driver.
     */
    function Kronolith_Driver($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Get the currently open calendar.
     *
     * @return string  The current calendar name.
     */
    function getCalendar()
    {
        return $this->_calendar;
    }

    /**
     * Get a globally unique ID for an event.
     *
     * @param integer $eventId  The event id.
     *
     * @return string  A GUID referring to $eventId.
     */
    function getGUID($eventId)
    {
        if (substr($eventId, 0, 10) != 'kronolith:') {
            $eventId = 'kronolith:' . $eventId;
        }
        return $eventId;
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
        return true;
    }

    function nextRecurrence($eventId, $afterDate)
    {
        $after = &new Kronolith_Date($afterDate);
        $after->correct();

        $event = &$this->getEvent($eventId);
        if (is_a($event, 'PEAR_Error')) {
            return $event;
        }

        if (Kronolith::compareDates($event->start, $after) >= 0) {
            return $event->start;
        }

        $event->recurEnd->hour = 23;
        $event->recurEnd->min = 59;
        $event->recurEnd->sec = 59;

        switch ($event->getRecurType()) {
        case KRONOLITH_RECUR_DAILY:
            $diff = Date_Calc::dateDiff($event->start->mday, $event->start->month, $event->start->year, $after->mday, $after->month, $after->year);
            $recur = ceil($diff / $event->recurInterval) * $event->recurInterval;
            $next = $event->start;
            list($next->mday, $next->month, $next->year) = explode('/', Date_Calc::daysToDate(Date_Calc::dateToDays($next->mday, $next->month, $next->year) + $recur, '%e/%m/%Y'));
            if (Kronolith::compareDates($next, $event->recurEnd) <= 0 &&
                Kronolith::compareDates($next, $after) >= 0) {
                return $next;
            }
            break;

        case KRONOLITH_RECUR_WEEKLY:
            list($start_week->mday, $start_week->month, $start_week->year) = explode('/', Date_Calc::beginOfWeek($event->start->mday, $event->start->month, $event->start->year, '%e/%m/%Y'));
            $start_week->hour = $event->start->hour;
            $start_week->min = $event->start->min;
            $start_week->sec = $event->start->sec;
            list($after_week->mday, $after_week->month, $after_week->year) = explode('/', Date_Calc::beginOfWeek($after->mday, $after->month, $after->year, '%e/%m/%Y'));
            $after_week_end = &new Kronolith_Date($after_week);
            $after_week_end->mday += 7;
            $after_week_end->correct();

            $diff = Date_Calc::dateDiff($start_week->mday, $start_week->month, $start_week->year, $after_week->mday, $after_week->month, $after_week->year);
            $recur = $diff + $diff % ($event->recurInterval * 7);
            $next = $start_week;
            list($next->mday, $next->month, $next->year) = explode('/', Date_Calc::daysToDate(Date_Calc::dateToDays($next->mday, $next->month, $next->year) + $recur, '%e/%m/%Y'));
            $next = &new Kronolith_date($next);
            while (Kronolith::compareDates($next, $after) < 0 && Kronolith::compareDates($next, $after_week_end) < 0) {
                $next->mday++;
                $next->correct();
            }
            if (Kronolith::compareDates($next, $event->recurEnd) <= 0) {
                if (Kronolith::compareDates($next, $after_week_end) >= 0) {
                    return $this->nextRecurrence($eventId, $after_week_end);
                }
                while (!$event->recurOnDay((int)pow(2, (int)Date_Calc::dayOfWeek($next->mday, $next->month, $next->year))) && Kronolith::compareDates($next, $after_week_end) < 0) {
                    $next->mday++;
                    $next->correct();
                }
                if (Kronolith::compareDates($next, $event->recurEnd) <= 0) {
                    if (Kronolith::compareDates($next, $after_week_end) >= 0) {
                        return $this->nextRecurrence($eventId, $after_week_end);
                    } else {
                        return Kronolith::dateObject($next);
                    }
                }
            }
            break;

        case KRONOLITH_RECUR_DAY_OF_MONTH:
            $start = &Kronolith::dateObject($event->start);
            if (Kronolith::compareDates($after, $start) < 0) {
                $after = $start;
            }

            // If we're starting past this month's recurrence of the
            // event, look in the next month on the day the event
            // recurs.
            if ($after->mday > $start->mday) {
                $after->month++;
                $after->correct();
                $after->mday = $start->mday;
            }

            // Adjust $start to be the first match.
            $offset = ($after->month - $start->month) + ($after->year - $start->year) * 12;
            $offset = (($offset + $event->recurInterval - 1) / $event->recurInterval) * $event->recurInterval;

            $start->month += $offset;
            $start->correct();

            // Bail if we've gone past the end of recurrence.
            if (Kronolith::compareDates($event->recurEnd, $start) < 0) {
                return false;
            }

            return $start;
            break;

        case KRONOLITH_RECUR_WEEK_OF_MONTH:
            // Start with the start date of the event.
            $estart = Kronolith::dateObject($event->start);

            // What day of the week, and week of the month, do we
            // recur on?
            $nth = ceil($event->start->mday / 7);
            $weekday = $estart->dayOfWeek();

            // Adjust $estart to be the first candidate.
            $offset = ($after->month - $estart->month) + ($after->year - $estart->year) * 12;
            $offset = floor(($offset + $event->recurInterval - 1) / $event->recurInterval) * $event->recurInterval;

            // Adjust our working date until it's after $after.
            $estart->month += $offset - $event->recurInterval;
            do {
                $estart->month += $event->recurInterval;
                $estart->correct();

                $next = $estart->copy();
                $next->setNthWeekday($weekday, $nth);

                if (Kronolith::compareDates($next, $after) < 0) {
                    // We haven't made it past $after yet, try
                    // again.
                    continue;
                }
                if (Kronolith::compareDates($next, $event->recurEnd) > 0) {
                    // We've gone past the end of recurrence; we can
                    // give up now.
                    return false;
                }

                // We have a candidate to return.
                break;
            } while (true);

            return $next;

        case KRONOLITH_RECUR_YEARLY:
            // Start with the start date of the event.
            $estart = Kronolith::dateObject($event->start);

            // We probably need a seperate case here for February 29th
            // and leap years, but until we're absolutely sure it's a
            // bug, we'll leave it out.
            if ($after->month > $estart->month ||
                ($after->month == $estart->month && $after->mday > $estart->mday)) {
                $after->year++;
                $after->month = $estart->month;
                $after->mday = $estart->mday;
            }

            // Adjust $estart to be the first candidate.
            $offset = $after->year - $estart->year;
            if ($offset > 0) {
                $offset = (($offset + $event->recurInterval - 1) / $event->recurInterval) * $event->recurInterval;
                $estart->year += $offset;
            }

            // We've gone past the end of recurrence; give up.
            if (Kronolith::compareDates($event->recurEnd, $estart) < 0) {
                return false;
            }

            return $estart;
        }

        // We didn't find anything, the recurType was bad, or
        // something else went wrong - return false.
        return false;
    }

    /**
     * Attempts to return a concrete Kronolith_Driver instance based
     * on $driver.
     *
     * @param $driver   The type of concrete Kronolith_Driver subclass to return.
     *                  This is based on the calendar driver ($driver). The
     *                  code is dynamically included.
     *
     * @param $params   (optional) A hash containing any additional
     *                  configuration or connection parameters a subclass
     *                  might need.
     *
     * @return          The newly created concrete Kronolith_Driver instance, or
     *                  a PEAR_Error on error.
     */
    function &factory($driver = null, $params = null)
    {
        if (is_null($driver)) {
            $driver = $GLOBALS['conf']['calendar']['driver'];
        }

        $driver = basename($driver);

        if (is_null($params)) {
            $params = Horde::getDriverConfig('calendar', $driver);
        }

        include_once dirname(__FILE__) . '/Driver/' . $driver . '.php';
        $class = 'Kronolith_Driver_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            Horde::fatal(PEAR::raiseError(sprintf(_("Unable to load the definition of %s."), $class)), __FILE__, __LINE__);
        }
    }

}

/**
 * Kronolith_Event:: defines a generic API for events.
 *
 * $Horde: kronolith/lib/Driver.php,v 1.74 2004/05/26 20:58:12 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_Event {

    /**
     * Flag that is set to true if this event has data from either a
     * storage backend or a form or other import method.
     * @var boolean $initialized
     */
    var $initialized = false;

    /**
     * Flag that is set to true if this event exists in a storage driver.
     * @var boolean $stored
     */
    var $stored = false;

    /**
     * The driver unique identifier for this event.
     * @var string $eventID
     */
    var $eventID = null;

    /**
     * The user id of the creator of the event
     * @var string $creatorID
     */
    var $creatorID = null;

    /**
     * The title of this event,
     * @var string $title
     */
    var $title = '';

    /**
     * The identifier of the category this event belongs to.
     * @var integer $category
     */
    var $category = 0;

    /**
     * The location this event occurs at.
     * @var string $location
     */
    var $location = '';

    /**
     * The status of this event.
     * @var integer $status
     */
    var $status = KRONOLITH_STATUS_TENTATIVE;

    /**
     * The description for this event
     * @var string $description
     */
    var $description = '';

    /**
     * All the attendees of this event.
     *
     * This is an associative array where the keys are the email addresses
     * of the attendees, and the values are also associative arrays with
     * keys 'attendance' and 'response' pointing to the attendees' attendance
     * and response values, respectively.
     *
     * @var array $attendees
     */
    var $attendees = array();

    /**
     * All the key words associtated with this event.
     * @var array $keywords
     */
    var $keywords = array();

    /**
     * All the exceptions from recurrence for this event.
     * @var array $exceptions
     */
    var $exceptions = array();

    /**
     * The timestamp for the start of this event.
     * @var integer $startTimestamp
     */
    var $startTimestamp = 0;

    /**
     * The timestamp for the end of this event.
     * @var integer $endTimestamp
     */
    var $endTimestamp = 0;

    /**
     * The duration of this event in minutes
     * @var integer $durMin
     */
    var $durMin = 0;

    /**
     * Number of minutes before the event starts to trigger an alarm.
     * @var integer $alarm
     */
    var $alarm = 0;

    /**
     * The timestamp for the end of the recurrence interval.
     * @var integer $recurEndTimestamp
     */
    var $recurEndTimestamp = null;

    /**
     * The type of recurrence this event follows. KRONOLITH_RECUR_* constant.
     * @var integer $recurType
     */
    var $recurType = KRONOLITH_RECUR_NONE;

    /**
     * TODO The length of time between recurrences in seconds?
     * @var integer $recurInterval
     */
    var $recurInterval = null;

    /**
     * Any additional recurrence data.
     * @var integer $recurData
     */
    var $recurData = null;

    /**
     * The identifier of the calender this event exists on.
     * @var string $_calendar
     */
    var $_calendar;

    /**
     * The VarRenderer class to use for printing select elements.
     * @var object Horde_UI_VarRenderer $_varRenderer
     */
    var $_varRenderer;

    /**
     * Constructor
     *
     * @param Kronolith_Driver $driver        The backend driver that this
     *                                        event is stored in.
     * @param Kronolith_Event  $eventObject   Backend specific event object
     *                                        that this will represent.
     */
    function Kronolith_Event(&$driver, $eventObject = null)
    {
        $this->_calendar = $driver->getCalendar();

        if (isset($eventObject)) {
            $this->fromDriver($eventObject);
        }
    }

    /**
     * Return a reference to a driver that's valid for this event.
     *
     * @return Kronolith_Driver  A driver that this event can use to save itself, etc.
     */
    function &getDriver()
    {
        global $kronolith;
        if ($kronolith->getCalendar() != $this->_calendar) {
            $kronolith->close();
            $kronolith->open($this->_calendar);
        }

        return $kronolith;
    }

    /**
     * Export this event in iCalendar format.
     *
     * @param object Horde_Data_icalendar $vcs       The data object to use to
     *                                               format the dates.
     * @param object Identity             $identity  The Identity object of the organizer.
     *
     * @return @array   Array of all the iCal attributes and their values.
     */
    function toiCalendar($vcs, $identity)
    {
        global $prefs;

        // Get a reference to the calendar object.
        $kronolith = &$this->getDriver();

        if (is_null($vcs)) {
            $vcs = &Horde_Data::singleton('icalendar');
        }

        if ($this->isAllDay()) {
            $start = date('Ymd', $this->startTimestamp);
            $end = date('Ymd', $this->endTimestamp);
        } else {
            $start = $vcs->makeDate($this->start);
            $end = $vcs->makeDate($this->end);
        }

        $vcal['DTSTAMP'] = date("Ymd\TGis");
        $vcal['UID'] = $kronolith->getGUID($this->eventID);
        $vcal['SUMMARY'] = $this->title;
        $vcal['DESCRIPTION'] = $this->description;
        $vcal['DTSTART'] = $start;
        $vcal['DTEND'] = $end;
        $vcal['CATEGORIES'] = $this->getCategory();
        $vcal['LOCATION'] = $this->location;
        $vcal['TRANSP'] = 'OPAQUE';
        $ORGANIZER = 'ORGANIZER;' . 'CN=' . $identity->getValue('fullname');
        $vcal[$ORGANIZER] = 'MAILTO:' . $identity->getValue('from_addr');

        // Recurrence.
        if ($this->recurType) {
            switch ($this->recurType) {
            case KRONOLITH_RECUR_NONE:
                break;

            case KRONOLITH_RECUR_DAILY:
                $vcal['RRULE'] = 'FREQ=DAILY;INTERVAL='  . $this->recurInterval;
                break;

            case KRONOLITH_RECUR_WEEKLY:
                $vcal['RRULE'] = 'FREQ=WEEKLY;INTERVAL=' . $this->recurInterval . ';BYDAY=';
                $vcaldays = array('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA');

                for ($i = $flag = 0; $i <= 7 ; $i++) {
                    if ($this->recurOnDay(pow(2, $i))) {
                        if ($flag) {
                            $vcal['RRULE'] .= ',';
                        }
                        $vcal['RRULE'] .= $vcaldays[$i];
                        $flag = true;
                    }
                }
                break;

            case KRONOLITH_RECUR_DAY_OF_MONTH:
                $vcal['RRULE'] = 'FREQ=MONTHLY;INTERVAL=' . $this->recurInterval;
                break;

            case KRONOLITH_RECUR_WEEK_OF_MONTH:
                $vcaldays = array('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA');
                $vcal['RRULE'] = 'FREQ=MONTHLY;INTERVAL=' . $this->recurInterval . ';BYDAY=' .
                    ((date('W', $this->startTimestamp) - date('W', mktime(0, 0, 0, date('n', $this->startTimestamp), 1,
                                                                          date('Y', $this->startTimestamp)))) + 1) .
                    $vcaldays[date('w', $this->startTimestamp)];
                break;

            case KRONOLITH_RECUR_YEARLY:
                $vcal['RRULE'] = 'FREQ=YEARLY;INTERVAL=' . $this->recurInterval;
                break;
            }

            if (isset($vcal['RRULE']) && !empty($this->recurEndTimestamp)) {
                $vcal['RRULE'] .= ';UNTIL=' . $vcs->makeDate($this->recurEnd);
            }
        }

        return $vcal;
    }

    /**
     * Update the properties of this event from a
     * Horde_iCalendar_vevent object.
     *
     * @param Horde_iCalendar_vevent $vEvent  The iCalendar data to update from.
     */
    function fromiCalendar($vEvent)
    {
        // Title, category and description.
        $title = $vEvent->getAttribute('SUMMARY');
        if (!is_array($title) && !is_a($title, 'PEAR_Error')) {
            $this->setTitle($title);
        }
        $categories = $vEvent->getAttribute('CATEGORIES');
        if (!is_array($categories) && !is_a($categories, 'PEAR_Error')) {
            // The CATEGORY attribute is delimited by commas, so split
            // it up.
            $categories = explode(',', $categories);

            // We only support one category per event right now, so
            // arbitrarily take the last one.
            foreach ($categories as $category) {
                $this->setCategory($category);
            }
        }
        $desc = $vEvent->getAttribute('DESCRIPTION');
        if (!is_array($desc) && !is_a($desc, 'PEAR_Error')) {
            $this->setDescription($desc);
        }

        // Location.
        $location = $vEvent->getAttribute('LOCATION');
        if (!is_array($location) && !is_a($location, 'PEAR_Error')) {
            $this->setLocation($location);
        }

        // Start and end date.
        $start = $vEvent->getAttribute('DTSTART');
        if (!is_array($start) && !is_a($start, 'PEAR_Error')) {
            $this->setStartTimestamp($start);
        }
        $end = $vEvent->getAttribute('DTEND');
        if (!is_array($end) && !is_a($end, 'PEAR_Error')) {
            $this->setEndTimestamp($end);
        } else {
            $duration = $vEvent->getAttribute('DURATION');
            if (!is_array($duration) && !is_a($duration, 'PEAR_Error')) {
                $this->setEndTimestamp($this->getStartTimestamp() + $duration);
            }
        }

        // Recurrence.
        $rrule = $vEvent->getAttribute('RRULE');
        if (!is_array($rrule) && !is_a($rrule, 'PEAR_Error')) {
            // Parse the recurrence rule into keys and values.
            $parts = explode(';', $rrule);
            foreach ($parts as $part) {
                list($key, $value) = explode('=', $part, 2);
                $rdata[$key] = $value;
            }

            if (isset($rdata['FREQ'])) {
                // Always default the recurInterval to 1.
                $this->setRecurInterval(isset($rdata['INTERVAL']) ? $rdata['INTERVAL'] : 1);

                $frequency = String::upper($rdata['FREQ']);
                switch ($frequency) {
                case 'DAILY':
                    $this->setRecurType(KRONOLITH_RECUR_DAILY);
                    break;

                case 'WEEKLY':
                    $this->setRecurType(KRONOLITH_RECUR_WEEKLY);
                    if (isset($rdata['BYDAY'])) {
                        $vcaldays = array('SU' => KRONOLITH_MASK_SUNDAY,
                                          'MO' => KRONOLITH_MASK_MONDAY,
                                          'TU' => KRONOLITH_MASK_TUESDAY,
                                          'WE' => KRONOLITH_MASK_WEDNESDAY,
                                          'TH' => KRONOLITH_MASK_THURSDAY,
                                          'FR' => KRONOLITH_MASK_FRIDAY,
                                          'SA' => KRONOLITH_MASK_SATURDAY);
                        $days = explode(',', $rdata['BYDAY']);
                        $mask = 0;
                        foreach ($days as $day) {
                            $mask |= $vcaldays[$day];
                        }
                        $this->setRecurOnDay($mask);
                    }
                    break;

                case 'MONTHLY':
                    if (isset($rdata['BYDAY'])) {
                        $this->setRecurType(KRONOLITH_RECUR_WEEK_OF_MONTH);
                    } else {
                        $this->setRecurType(KRONOLITH_RECUR_DAY_OF_MONTH);
                    }
                    break;

                case 'YEARLY':
                    $this->setRecurType(KRONOLITH_RECUR_YEARLY);
                    break;
                }
            } else {
                // No recurrence data - event does not recur.
                $this->setRecurType(KRONOLITH_RECUR_NONE);
            }
        }

        $this->initialized = true;
    }

    /**
     * Import the values for this event from an array of values.
     *
     * @param array $hash  Array containing all the values.
     */
    function fromHash($hash)
    {
        // See if it's a new event.
        if (is_null($this->getID())) {
            $this->setCreatorID(Auth::getAuth());
        }
        if (!empty($hash['title'])) {
            $this->setTitle($hash['title']);
        }
        if (!empty($hash['description'])) {
            $this->setDescription($hash['description']);
        }
        if (!empty($hash['category'])) {
            $this->setCategory($hash['category']);
        }
        if (!empty($hash['location'])) {
            $this->setLocation($hash['location']);
        }
        if (!empty($hash['keywords'])) {
            $this->setKeywords(explode(',', $hash['keywords']));
        }
        if (!empty($hash['start_date'])) {
            $date = explode('-', $hash['start_date']);
            if (empty($hash['start_time'])) {
                $time = array(0, 0, 0);
            } else {
                $time = explode(':', $hash['start_time']);
                if (count($time) == 2) {
                    $time[2] = 0;
                }
            }
            if (count($time) == 3 && count($date) == 3) {
                $this->setStartTimestamp(mktime($time[0], $time[1], $time[2], $date[1], $date[2], $date[0]));
            }
        }
        if (!empty($hash['duration'])) {
            $weeks = str_replace('W', '', $hash['duration'][1]);
            $days = str_replace('D', '', $hash['duration'][2]);
            $hours = str_replace('H', '', $hash['duration'][4]);
            $minutes = isset($hash['duration'][5]) ? str_replace('M', '', $hash['duration'][5]) : 0;
            $seconds = isset($hash['duration'][6]) ? str_replace('S', '', $hash['duration'][6]) : 0;
            $hash['duration'] = ($weeks * 60 * 60 * 24 * 7) + ($days * 60 * 60 * 24) + ($hours * 60 * 60) + ($minutes * 60) + $seconds;
            $this->setEndTimestamp($this->getStartTimestamp() + $hash['duration']);
        }
        if (!empty($hash['end_date'])) {
            $date = explode('-', $hash['end_date']);
            if (empty($hash['end_time'])) {
                $time = array(0, 0, 0);
            } else {
                $time = explode(':', $hash['end_time']);
                if (count($time) == 2) {
                    $time[2] = 0;
                }
            }
            if (count($time) == 3 && count($date) == 3) {
                $this->setEndTimestamp(mktime($time[0], $time[1], $time[2], $date[1], $date[2], $date[0]));
            }
        }
        if (!empty($hash['alarm'])) {
            $this->setAlarm($hash['alarm']);
        } elseif (!empty($hash['alarm_date']) &&
                  !empty($hash['alarm_time'])) {
            $date = explode('-', $hash['alarm_date']);
            $time = explode(':', $hash['alarm_time']);
            if (count($time) == 2) {
                $time[2] = 0;
            }
            if (count($time) == 3 && count($date) == 3) {
                $this->setAlarm(($this->getStartTimestamp() - mktime($time[0], $time[1], $time[2], $date[1], $date[2], $date[0])) / 60);
            }
        }
        if (!empty($hash['recur_type'])) {
            $this->setRecurType($hash['recur_type']);
            if (!empty($hash['recur_end_date'])) {
                $date = explode('-', $hash['recur_end_date']);
                $this->setRecurEndTimestamp(mktime(0, 0, 0, $date[1], $date[2], $date[0]));
            }
            if (!empty($hash['recur_interval'])) {
                $this->setRecurInterval($hash['recur_interval']);
            }
            if (!empty($hash['recur_data'])) {
                $this->setRecurOnDay($hash['recur_data']);
            }
        }

        $this->initialized = true;
    }

    /**
     * Save changes to this event.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function save()
    {
        if (!$this->isInitialized()) {
            return PEAR::raiseError('no data');
        }

        $this->toDriver();
        $driver = &$this->getDriver();
        return $driver->saveEvent($this);
    }

    /**
     * Add an exception to a recurring event.
     *
     * @param integer $year     The year of the execption.
     * @param integer $month    The month of the execption.
     * @param integer $mday     The day of the month of the exception.
     */
    function addException($year, $month, $mday)
    {
        $this->exceptions[] = sprintf('%04d%02d%02d', $year, $month, $mday);
    }

    /**
     * Check if an exception exists for a given reccurence of an event.
     *
     * @param integer $year     The year of the reucrance.
     * @param integer $month    The month of the reucrance.
     * @param integer $mday     The day of the month of the reucrance.
     *
     * @return boolean  True if an exception exists for the given date.
     */
    function hasException($year, $month, $mday)
    {
        return in_array(sprintf('%04d%02d%02d', $year, $month, $mday), $this->getExceptions());
    }

    /**
     * Retrieve all the exceptions for this event
     *
     * @return array    Array containing the dates of all the exceptions in
     *                  YYYYMMDD form.
     */
    function getExceptions()
    {
        return $this->exceptions;
    }

    /**
     * TODO
     */
    function isInitialized()
    {
        return $this->initialized;
    }

    /**
     * TODO
     */
    function isStored()
    {
        return $this->stored;
    }

    /**
     * Check if this event recurs on a given day of the week.
     *
     * @param integer $dayMask  A mask specifying the day(s) to check.
     *
     * @return boolean  True if this event recurs on the given day(s).
     */
    function recurOnDay($dayMask)
    {
        return ($this->recurData & $dayMask);
    }

    /**
     * Specify the days this event recurs on.
     *
     * @param integer $dayMask  A mask specifying the day(s) to recur on.
     */
    function setRecurOnDay($dayMask)
    {
        $this->recurData = $dayMask;
    }

    /**
     * Return the days this event recurs on.
     *
     * @return intenger A mask specifying the day(s) this event recurs on.
     */
    function getRecurOnDays()
    {
        return $this->recurData;
    }

    function getRecurType()
    {
        return $this->recurType;
    }

    function hasRecurType($recurrence)
    {
        return ($recurrence === $this->recurType);
    }

    function setRecurType($recurrence)
    {
        $this->recurType = $recurrence;
    }

    /**
     * Set the length of time between recurrences of this event.
     *
     * @param integer $interval     The number of seconds between recurrences.
     */
    function setRecurInterval($interval)
    {
        if ($interval > 0) {
            $this->recurInterval = $interval;
        }
    }

    /**
     * Retrieve the length of time between recurrences fo this event.
     *
     * @return integer  The number of seconds between recurrences.
     */
    function getRecurInterval()
    {
        return $this->recurInterval;
    }

    /**
     * Retrieve the locally unique identifier for this event.
     *
     * @return integer  The local identifier for this event.
     */
    function getID()
    {
        return $this->eventID;
    }

    /**
     * Set the locally unique identifier for this event.
     *
     * @param string $eventId  The local identifier for this event.
     */
    function setID($eventId)
    {
        if (substr($eventId, 0, 10) == 'kronolith:') {
            $eventId = substr($eventId, 10);
        }
        $this->eventID = $eventId;
    }

    /**
     * Retrieve the id of the user who created the event
     *
     * @return string The creator id
     */
    function getCreatorID()
    {
        return !empty($this->creatorID) ? $this->creatorID : Auth::getAuth();
    }

    /**
     * Set the id of the creator of the event
     *
     * @param string $creatorID The user id for who created the event
     */
    function setCreatorID($creatorID)
    {
        $this->creatorID = $creatorID;
    }

    /**
     * Retrieve the title of this event.
     *
     * @return string  The title of this event.
     */
    function getTitle()
    {
        if (isset($this->taskID) || isset($this->remoteCal) || isset($this->meetingID)) {
            return !empty($this->title) ? $this->title : _("[none]");
        }

        if (!$this->isInitialized()) {
            return '';
        }

        $share = $GLOBALS['all_calendars'][$this->getCalendar()];
        if (!is_a($share, 'PEAR_Error') && $share->hasPermission(Auth::getAuth(), PERMS_READ, $this->getCreatorID())) {
            return !empty($this->title) ? $this->title : _("[none]");
        } else {
            global $prefs;
            return sprintf(_("Event from %s to %s"),
                           $this->getStartDate($prefs->getValue('twentyFour') ? 'G:i' : 'g:ia'),
                           $this->getEndDate($prefs->getValue('twentyFour') ? 'G:i' : 'g:ia'));
        }
    }

    /**
     * Set the title of this event.
     *
     * @param string  The new title for this event.
     */
    function setTitle($title)
    {
        $this->title = $title;
    }

    /**
     * Retieve the description of this event.
     *
     * @return string The description of this event.
     */
    function getDescription()
    {
        return $this->description;
    }

    /**
     * Set the description of this event.
     *
     * @param string $description The new description for this event.
     */
    function setDescription($description)
    {
        $this->description = $description;
    }

    /**
     * Set the category this event belongs to.
     *
     * @param integer $category     The identifier of the category this
     *                                  event belongs to.
     */
    function setCategory($category)
    {
        $this->category = $category;
    }

    /**
     * Retrieve the category this event belongs to.
     *
     * @return integer The identifier of the category this event belongs to.
     */
    function getCategory()
    {
        return $this->category;
    }

    /**
     * Set the location this event occurs at.
     *
     * @param string $location  The new location for this event.
     */
    function setLocation($location)
    {
        $this->location = $location;
    }

    /**
     * Retrieve the location this event occurs at.
     *
     * @return string   The location of this event.
     */
    function getLocation()
    {
        return $this->location;
    }

    /**
     * Retrieve the event status.
     *
     * @return integer   The status of this event.
     */
    function getStatus()
    {
        return $this->status;
    }

    /**
     * Checks whether the events status is the same as the specified value.
     *
     * @param integer $status  The status value to check against.
     *
     * @return boolean   True if the events status is the same as $status.
     */
    function hasStatus($status)
    {
        return ($status === $this->status);
    }

    /**
     * Set the status of this event.
     *
     * @param integer $status  The new event status.
     */
    function setStatus($status)
    {
        $this->status = $status;
    }

    /**
     * Retrieve the time this event starts.
     *
     * @param integer $dayTimestamp   (optional) The timestamp of a day a
     *                                recurrence occurs. First recurrence
     *                                is used if not specified.
     *
     * @return integer The timestamp for the start of this event.
     */
    function getStartTimestamp($dayTimestamp = null)
    {
        if (empty($dayTimestamp)) {
            return $this->startTimestamp;
        }

        list($year, $month, $day) = explode(':', date('Y:n:j', $dayTimestamp));
        list($hour, $min, $sec) = explode(':', date('G:i:s', $this->startTimestamp));

        return mktime($hour, $min, $sec, $month, $day, $year);
    }

    /**
     * Set the time this event starts.
     *
     * @param integer $startTimestamp   The timestamp for the start
     *                                      of this event.
     */
    function setStartTimestamp($startTimestamp)
    {
        $this->startTimestamp = $startTimestamp;
        $this->start = new stdClass();
        list($this->start->mday, $this->start->month, $this->start->year,
             $this->start->hour, $this->start->min, $this->start->sec) =
             explode(':', date('d:m:Y:H:i:s', $startTimestamp));
    }

    /**
     * Sets the entire attendee array.
     *
     * @param array $attendees   The new attendees array. This should be of
     *                           the correct format to avoid driver problems.
     */
    function setAttendees($attendees)
    {
        $this->attendees = $attendees;
    }

    /**
     * Adds a new attendee to the current event. This will overwrite an
     * existing attendee if one exists with the same email address.
     *
     * @param string $email        The email address of the attendee.
     * @param integer $attendance  The attendance code of the attendee.
     * @param integer $response    The response code of the attendee.
     */
    function addAttendee($email, $attendance, $response)
    {
        if ($attendance == KRONOLITH_PART_IGNORE) {
            if (array_key_exists($email, $this->attendees)) {
                $attendance = $this->attendees[$email]['attendance'];
            } else {
                $attendance = KRONOLITH_PART_REQUIRED;
            }
        }

        $this->attendees[$email] = array(
            'attendance' => $attendance,
            'response' => $response
        );
    }

    /**
     * Removes the specified attendee from the current event.
     *
     * @param string $email        The email address of the attendee.
     */
    function removeAttendee($email)
    {
        if (array_key_exists($email, $this->attendees))
            unset($this->attendees[$email]);
    }

    /**
     * Returns the entire attendees array.
     *
     * @return array  A copy of the attendees array.
     */
    function getAttendees()
    {
        return $this->attendees;
    }

    /**
     * Checks to see whether the specified attendee is associated with the
     * current event.
     *
     * @param string $email        The email address of the attendee.
     *
     * @return boolen  True if the specified attendee is present for this event.
     */
    function hasAttendee($email)
    {
        return array_key_exists($email, $this->attendees);
    }

    function setKeywords($keywords)
    {
        $this->keywords = $keywords;
    }

    function getKeywords()
    {
        return $this->keywords;
    }

    function hasKeyword($keyword)
    {
        return in_array($keyword, $this->keywords);
    }

    function getStartDate($formatString, $dayTimestamp = null)
    {
        return date($formatString, $this->getStartTimestamp($dayTimestamp));
    }

    function getStartDatestamp()
    {
        return mktime(0, 0, 0,
                      $this->getStartDate('n'),
                      $this->getStartDate('j'),
                      $this->getStartDate('Y'));
    }

    function setEndTimestamp($endTimestamp)
    {
        $this->endTimestamp = $endTimestamp;
        $this->end = new stdClass();
        list($this->end->mday, $this->end->month, $this->end->year,
             $this->end->hour, $this->end->min, $this->end->sec) =
             explode(':', date('d:m:Y:H:i:s', $endTimestamp));
    }

    function getEndTimestamp($dayTimestamp = null)
    {
        if (empty($dayTimestamp)) {
            return $this->endTimestamp;
        }

        list($year, $month, $day) = explode(':', date('Y:n:j', $dayTimestamp));
        list($hour, $min, $sec) = explode(':', date('G:i:s', $this->endTimestamp));

        return mktime($hour, $min, $sec, $month, $day, $year);
    }

    function getEndDate($formatString, $dayTimestamp = null)
    {
        return date($formatString, $this->getEndTimestamp($dayTimestamp));
    }

    function setRecurEndTimestamp($recurTimestamp)
    {
        $this->recurEndTimestamp = $recurTimestamp;
    }

    function getRecurEndTimestamp()
    {
        return $this->recurEndTimestamp;
    }

    function hasRecurEnd()
    {
        return (isset($this->recurEnd) && isset($this->recurEnd->year) && $this->recurEnd->year != 9999);
    }

    function getRecurEndDate($formatString)
    {
        return date($formatString, $this->recurEndTimestamp);
    }

    function isAllDay()
    {
        return ($this->start->hour == 0 && $this->start->min == 0 && $this->start->sec == 0 &&
                $this->end->hour == 0 && $this->end->min == 0 && $this->start->sec == 0 &&
                ($this->end->mday > $this->start->mday ||
                 $this->end->month > $this->start->month ||
                 $this->end->year > $this->start->year));
    }

    function setAlarm($alarm)
    {
        $this->alarm = $alarm;
    }

    function getAlarm()
    {
        return $this->alarm;
    }

    function readForm()
    {
        global $prefs, $cManager;

        // See if it's a new event.
        if (!$this->isInitialized()) {
            $this->setCreatorID(Auth::getAuth());
        }

        // Basic fields.
        $this->setTitle(Util::getFormData('title', $this->title));
        $this->setDescription(Util::getFormData('description', $this->description));
        $this->setLocation(Util::getFormData('location', $this->location));
        $this->setKeywords(Util::getFormData('keywords', $this->keywords));

        // Category.
        if ($new_category = Util::getFormData('new_category')) {
            $new_category = $cManager->add($new_category);
            if ($new_category) {
                $category = $new_category;
            }
        } else {
            $category = Util::getFormData('category', $this->category);
        }
        $this->setCategory($category);

        // Status.
        $this->setStatus(Util::getFormData('status', $this->status));

        // Attendees.
        if (array_key_exists('attendees', $_SESSION) && is_array($_SESSION['attendees']))
            $this->setAttendees($_SESSION['attendees']);

        // Event start.
        $start = Util::getFormData('start');
        $start_year = $start['year'];
        $start_month = $start['month'];
        $start_day = $start['day'];
        $start_hour = Util::getFormData('start_hour');
        $start_min = Util::getFormData('start_min');
        $am_pm = Util::getFormData('am_pm');

        if (!$prefs->getValue('twentyFour')) {
            if ($am_pm == 'PM') {
                if ($start_hour != 12) {
                    $start_hour += 12;
                }
            } elseif ($start_hour == 12) {
                $start_hour = 0;
            }
        }

        if (Util::getFormData('end_or_dur') == 1) {
            if (Util::getFormData('whole_day') == 1) {
                $start_hour = 0;
                $start_min = 0;
                $dur_day = 0;
                $dur_hour = 24;
                $dur_min = 0;
            } else {
                $dur_day = Util::getFormData('dur_day');
                $dur_hour = Util::getFormData('dur_hour');
                $dur_min = Util::getFormData('dur_min');
            }
        }

        $this->setStartTimestamp(mktime($start_hour, $start_min, 0,
                                        $start_month, $start_day,
                                        $start_year));

        if (Util::getFormData('end_or_dur') == 1) {
            // Event duration.
            $this->setEndTimestamp(mktime($start_hour + $dur_hour,
                                          $start_min + $dur_min,
                                          0,
                                          $start_month,
                                          $start_day + $dur_day,
                                          $start_year));
        } else {
            // Event end.
            $end = Util::getFormData('end');
            $end_year = $end['year'];
            $end_month = $end['month'];
            $end_day = $end['day'];
            $end_hour = Util::getFormData('end_hour');
            $end_min = Util::getFormData('end_min');
            $end_am_pm = Util::getFormData('end_am_pm');

            if (!$prefs->getValue('twentyFour')) {
                if ($end_am_pm == 'PM') {
                    if ($end_hour != 12) {
                        $end_hour += 12;
                    }
                } elseif ($end_hour == 12) {
                    $end_hour = 0;
                }
            }

            $endstamp = mktime($end_hour, $end_min, 0,
                               $end_month, $end_day, $end_year);
            if ($endstamp < $this->getStartTimestamp()) {
                $endstamp = $this->getStartTimestamp();
            }
            $this->setEndTimestamp($endstamp);
        }

        // Alarm.
        if (Util::getFormData('alarm') == 1) {
            $this->setAlarm(Util::getFormData('alarm_value') * Util::getFormData('alarm_unit'));
        } else {
            $this->setAlarm(0);
        }

        // Recurrence.
        $recur = Util::getFormData('recur');
        if (!is_null($recur) && $recur !== '') {
            if (Util::getFormData('recur_enddate_type') == 'none') {
                $recur_enddate_year = 9999;
                $recur_enddate_month = 12;
                $recur_enddate_day = 31;
            } else {
                $recur_enddate = Util::getFormData('recur_enddate');
                $recur_enddate_year = $recur_enddate['year'];
                $recur_enddate_month = $recur_enddate['month'];
                $recur_enddate_day = $recur_enddate['day'];
            }

            $this->setRecurEndTimestamp(@mktime(1, 1, 1,
                                                $recur_enddate_month,
                                                $recur_enddate_day,
                                                $recur_enddate_year));

            $this->setRecurType($recur);
            switch ($recur) {
            case KRONOLITH_RECUR_DAILY:
                $this->setRecurInterval(Util::getFormData('recur_daily_interval', 1));
                break;

            case KRONOLITH_RECUR_WEEKLY:
                $weekly = Util::getFormData('weekly');
                $weekdays = 0;
                if (is_array($weekly)) {
                    foreach ($weekly as $day) {
                        $weekdays |= $day;
                    }
                }

                if ($weekdays == 0) {
                    // date('w') starts Sunday at 0.
                    switch ($this->getStartDate('w')) {
                    case 0: $weekdays |= KRONOLITH_MASK_SUNDAY; break;
                    case 1: $weekdays |= KRONOLITH_MASK_MONDAY; break;
                    case 2: $weekdays |= KRONOLITH_MASK_TUESDAY; break;
                    case 3: $weekdays |= KRONOLITH_MASK_WEDNESDAY; break;
                    case 4: $weekdays |= KRONOLITH_MASK_THURSDAY; break;
                    case 5: $weekdays |= KRONOLITH_MASK_FRIDAY; break;
                    case 6: $weekdays |= KRONOLITH_MASK_SATURDAY; break;
                    }
                }

                $this->setRecurInterval(Util::getFormData('recur_weekly_interval', 1));
                $this->setRecurOnDay($weekdays);
                break;

            case KRONOLITH_RECUR_DAY_OF_MONTH:
                $this->setRecurInterval(Util::getFormData('recur_day_of_month_interval', 1));
                break;

            case KRONOLITH_RECUR_WEEK_OF_MONTH:
                $this->setRecurInterval(Util::getFormData('recur_week_of_month_interval', 1));
                break;

            case KRONOLITH_RECUR_YEARLY:
                $this->setRecurInterval(Util::getFormData('recur_yearly_interval', 1));
                break;
            }
        }

        $this->initialized = true;
    }

    function getDuration()
    {
        static $duration;
        if (isset($duration)) {
            return $duration;
        }

        if ($this->isInitialized()) {
            $dur_day_match = $this->getEndDate('j') - $this->getStartDate('j');
            $dur_hour_match = $this->getEndDate('G') - $this->getStartDate('G');
            $dur_min_match = $this->getEndDate('i') - $this->getStartDate('i');
            while ($dur_min_match < 0) {
                $dur_min_match += 60;
                $dur_hour_match--;
            }
            while ($dur_hour_match < 0) {
                $dur_hour_match += 24;
                $dur_day_match--;
            }
            if ($dur_hour_match == 0 && $dur_min_match == 0
                && ($this->getEndDate('d') - $this->getStartDate('d')) == 1) {
                $dur_day_match = 0;
                $dur_hour_match = 23;
                $dur_min_match = 60;
                $whole_day_match = true;
            } else {
                $whole_day_match = false;
            }
        } else {
            $dur_day_match = 0;
            $dur_hour_match = 1;
            $dur_min_match = 0;
            $whole_day_match = false;
        }

        $duration = &new stdClass();
        $duration->day = $dur_day_match;
        $duration->hour = $dur_hour_match;
        $duration->min = $dur_min_match;
        $duration->wholeDay = $whole_day_match;

        return $duration;
    }

    function html($property)
    {
        global $prefs;

        $options = array();
        $attributes = '';
        $sel = false;

        switch ($property) {
        case 'start[year]':
            $sel = $this->getStartDate('Y');
            for ($i = -1; $i < 6; $i++) {
                $yr = date('Y') + $i;
                $options[$yr] = $yr;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            break;

        case 'start[month]':
            $sel = $this->getStartDate('n');
            for ($i = 1; $i < 13; $i++) {
                $options[$i] = strftime('%b', mktime(1, 1, 1, $i, 1));
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            break;

        case 'start[day]':
            $sel = $this->getStartDate('j');
            for ($i = 1; $i < 32; $i++) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            break;

        case 'start_hour':
            $sel = $this->getStartDate(($prefs->getValue('twentyFour')) ? 'G' : 'g');
            $hour_min = ($prefs->getValue('twentyFour')) ? 0 : 1;
            $hour_max = ($prefs->getValue('twentyFour')) ? 24 : 13;
            for ($i = $hour_min; $i < $hour_max; $i++) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="document.event.whole_day.checked = false; updateEndDate();"';
            break;

        case 'start_min':
            $sel = $this->getStartDate('i');
            for ($i = 0; $i < 12; $i++) {
                $min = sprintf('%02d', $i * 5);
                $options[$min] = $min;
            }
            $attributes = ' onchange="document.event.whole_day.checked = false; updateEndDate();"';
            break;

        case 'end[year]':
            $sel = $this->isInitialized() ? $this->getEndDate('Y') : $this->getStartDate('Y');
            for ($i = -1; $i < 6; $i++) {
                $yr = date('Y') + $i;
                $options[$yr] = $yr;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            break;

        case 'end[month]':
            $sel = $this->isInitialized() ? $this->getEndDate('n') : $this->getStartDate('n');
            for ($i = 1; $i < 13; $i++) {
                $options[$i] = strftime('%b', mktime(1, 1, 1, $i, 1));
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            break;

        case 'end[day]':
            $sel = $this->isInitialized() ? $this->getEndDate('j') : $this->getStartDate('j');
            for ($i = 1; $i < 32; $i++) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            break;

        case 'end_hour':
            $sel = $this->isInitialized() ?
                $this->getEndDate(($prefs->getValue('twentyFour')) ? 'G' : 'g') :
                $this->getStartDate(($prefs->getValue('twentyFour')) ? 'G' : 'g') + 1;
            $hour_min = $prefs->getValue('twentyFour') ? 0 : 1;
            $hour_max = $prefs->getValue('twentyFour') ? 24 : 13;
            for ($i = $hour_min; $i < $hour_max; $i++) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="updateDuration(); document.event.end_or_dur[0].checked = true"';
            break;

        case 'end_min':
            $sel = $this->isInitialized() ? $this->getEndDate('i') : $this->getStartDate('i');
            for ($i = 0; $i < 12; $i++) {
                $min = sprintf('%02d', $i * 5);
                $options[$min] = $min;
            }
            $attributes = ' onchange="updateDuration(); document.event.end_or_dur[0].checked = true"';
            break;

        case 'dur_day':
            $dur = $this->getDuration();
            $sel = $dur->day;
            for ($i = 0; $i < 366; $i++) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="document.event.whole_day.checked = false; updateEndDate(); document.event.end_or_dur[1].checked = true;"';
            break;

        case 'dur_hour':
            $dur = $this->getDuration();
            $sel = $dur->hour;
            for ($i = 0; $i < 24; $i++) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="document.event.whole_day.checked = false; updateEndDate(); document.event.end_or_dur[1].checked = true;"';
            break;

        case 'dur_min':
            $dur = $this->getDuration();
            $sel = $dur->min;
            for ($i = 0; $i < 13; $i++) {
                $min = sprintf('%02d', $i * 5);
                $options[$min] = $min;
            }
            $attributes = ' onchange="document.event.whole_day.checked = false;updateEndDate();document.event.end_or_dur[1].checked=true"';
            break;

        case 'recur_enddate[year]':
            if ($this->isInitialized()) {
                $sel = $this->hasRecurEnd() ? $this->recurEnd->year : $this->end->year;
            } else {
                $sel = $this->getStartDate('Y');
            }
            for ($i = -1; $i < 6; $i++) {
                $yr = date('Y') + $i;
                $options[$yr] = $yr;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            break;

        case 'recur_enddate[month]':
            if ($this->isInitialized()) {
                $sel = $this->hasRecurEnd() ? $this->recurEnd->month : $this->end->month;
            } else {
                $sel = $this->getStartDate('m');
            }
            for ($i = 1; $i < 13; $i++) {
                $options[$i] = strftime('%b', mktime(1, 1, 1, $i, 1));
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            break;

        case 'recur_enddate[day]':
            if ($this->isInitialized()) {
                $sel = $this->hasRecurEnd() ? $this->recurEnd->mday : $this->end->mday;
            } else {
                $sel = $this->getStartDate('d');
            }
            for ($i = 1; $i < 32; $i++) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            break;
        }

        if (!$this->_varRenderer) {
            require_once 'Horde/UI/VarRenderer.php';
            $this->_varRenderer = &Horde_UI_VarRenderer::factory('html');
        }

        $html = '<select name="' . $property . '"' . $attributes . ' id="' . $property . '">';
        $html .= $this->_varRenderer->_selectOptions($options, $sel);
        $html .= '</select>';

        return $html;
    }

    function js($property)
    {
        switch ($property) {
        case 'start[month]':
        case 'start[year]':
        case 'start[day]':
        case 'start':
            return 'updateWday(\'start_wday\'); document.event.whole_day.checked = false; updateEndDate();';

        case 'end[month]':
        case 'end[year]':
        case 'end[day]':
        case 'end':
            return 'updateWday(\'end_wday\'); updateDuration(); document.event.end_or_dur[0].checked = true;';

        case 'recur_enddate[month]':
        case 'recur_enddate[year]':
        case 'recur_enddate[day]':
        case 'recur_enddate':
            return 'updateWday(\'recur_end_wday\'); document.event.recur_enddate_type[1].checked = true;';
        }
    }

    function getLink($timestamp = 0, $icons = true)
    {
        global $print_view, $prefs, $registry;

        $share = $GLOBALS['all_calendars'][$this->getCalendar()];
        $link = '';
        if (!is_a($share, 'PEAR_Error') && $share->hasPermission(Auth::getAuth(), PERMS_READ, $this->getCreatorID())) {
            if (isset($this->remoteCal)) {
                $url = Util::addParameter('viewevent.php', 'eventID', $this->eventIndex);
                $url = Util::addParameter($url, 'calendar', '**remote');
                $url = Util::addParameter($url, 'remoteCal', $this->remoteCal);
                $url = Util::addParameter($url, 'timestamp', $timestamp);
                $url = Horde::applicationUrl($url);
                if ($this->isAllDay()) {
                    $event_time = _("All day");
                } else {
                    $event_time = date($prefs->getValue('twentyFour') ? 'G:i' : 'g:ia',
                                       $this->getStartTimestamp()) . '-' .
                                  date($prefs->getValue('twentyFour') ? 'G:i' : 'g:ia',
                                       $this->getEndTimestamp());
                }
                $link .= Horde::linkTooltip($url, $this->getTitle(), 'event', '', '', $event_time . ($this->location ? '; ' . $this->location : '') . ($this->description ? ': ' : '') . $this->description);
            } elseif (isset($this->eventID)) {
                $url = Util::addParameter('viewevent.php', 'eventID', $this->eventID);
                $url = Util::addParameter($url, 'calendar', $this->getCalendar());
                $url = Util::addParameter($url, 'timestamp', $timestamp);
                $url = Horde::applicationUrl($url);
                if ($this->isAllDay()) {
                    $event_time = _("All day");
                } else {
                    $event_time = date($prefs->getValue('twentyFour') ? 'G:i' : 'g:ia',
                                       $this->getStartTimestamp()) . '-' .
                                  date($prefs->getValue('twentyFour') ? 'G:i' : 'g:ia',
                                       $this->getEndTimestamp());
                }
                $link .= Horde::linkTooltip($url, $this->title, 'event', '', '', $event_time . ($this->location ? '; ' . $this->location : '') . ($this->description ? ': ' : '') . $this->description);
            } elseif (isset($this->taskID)) {
                $link .= Horde::link(Horde::url($GLOBALS['registry']->link('tasks/show', array('task' => $this->taskID, 'tasklist' => $this->tasklistID))), $this->title, 'event');
            } elseif (isset($this->meetingID)) {
                $link .= Horde::link(Horde::url($GLOBALS['registry']->link('meeting/show', array('meeting' => $this->meetingID))), $this->title, 'event');
            }
        }

        $link .= @htmlspecialchars($this->getTitle(), ENT_QUOTES, NLS::getCharset());

        if (!is_a($share, 'PEAR_Error') && $share->hasPermission(Auth::getAuth(), PERMS_READ, $this->getCreatorID()) &&
            (isset($this->eventID) || isset($this->taskID) || isset($this->remoteCal))) {
            $link .= '</a>';
        }

        if ($icons && $prefs->getValue('show_icons')) {
            $status = '';
            if ($this->alarm) {
                if ($this->alarm % 10080 == 0) {
                    $alarm_value = $this->alarm / 10080;
                    $alarm_unit = 'week';
                } elseif ($this->alarm % 1440 == 0) {
                    $alarm_value = $this->alarm / 1440;
                    $alarm_unit = 'day';
                } elseif ($this->alarm % 60 == 0) {
                    $alarm_value = $this->alarm / 60;
                    $alarm_unit = 'hour';
                } else {
                    $alarm_value = $this->alarm;
                    $alarm_unit = 'minute';
                }
                $plural = ($alarm_value == 1 ? '' : 's');
                $alarm_unit = "$alarm_unit$plural";
                $status .= Horde::img('alarm_small.gif', sprintf(_("Alarm %s $alarm_unit before"), $alarm_value));
            }

            if (!$this->hasRecurType(KRONOLITH_RECUR_NONE)) {
                $status .= Horde::img('recur.gif', Kronolith::recurToString($this->recurType));
            }

            if (!empty($this->attendees)) {
                $plural = (count($this->attendees) == 1 ? '' : 's');
                $status .= Horde::img('attendees.gif', sprintf(_("%s attendee$plural"), count($this->attendees)));
            }

            $link .= " $status";

            if (!$print_view) {
                if (!is_a($share, 'PEAR_Error') && $share->hasPermission(Auth::getAuth(), PERMS_DELETE, $this->getCreatorID())) {
                    if (isset($this->eventID)) {
                        $url = Util::addParameter('editevent.php', 'eventID', $this->eventID);
                        $url = Util::addParameter($url, 'calendar', $this->getCalendar());
                        $url = Util::addParameter($url, 'timestamp', $timestamp);
                        $url = Util::addParameter($url, 'url', str_replace('&amp;', '&', Horde::selfUrl(true, false)));
                        $link .= ' ' . Horde::link(Horde::applicationUrl($url), sprintf(_("Edit %s"), $this->title)) . Horde::img('edit.gif', sprintf(_("Edit %s"), $this->getTitle()), null, $registry->getParam('graphics', 'horde')) . '</a>';

                        $url = Util::addParameter('delevent.php', 'eventID', $this->eventID);
                        $url = Util::addParameter($url, 'calendar', $this->getCalendar());
                        $url = Util::addParameter($url, 'timestamp', $timestamp);
                        $url = Util::addParameter($url, 'url', str_replace('&amp;', '&', Horde::selfUrl(true, false)));
                        $link .= ' ' . Horde::link(Horde::applicationUrl($url), sprintf(_("Delete %s"), $this->title)) . Horde::img('delete-small.gif', sprintf(_("Delete %s"), $this->getTitle()), null, $registry->getParam('graphics', 'horde')) . '</a>';
                    }
                }
            }
        }
        return $link;
    }

    function nextRecurrence($afterDate, $weekstart = KRONOLITH_SUNDAY)
    {
        $driver = &$this->getDriver();
        return $driver->nextRecurrence($this->eventID, $afterDate, $weekstart);
    }

    function getCalendar()
    {
        return $this->_calendar;
    }

    function setCalendar($calendar)
    {
        $this->_calendar = $calendar;
    }

}
