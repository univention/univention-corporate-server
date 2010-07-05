<?php
/**
 * Kronolith_Driver defines an API for implementing storage backends for
 * Kronolith.
 *
 * $Horde: kronolith/lib/Driver.php,v 1.116.2.84 2009-11-07 14:34:57 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_Driver {

    /**
     * A hash containing any parameters for the current driver.
     *
     * @var array
     */
    var $_params = array();

    /**
     * The current calendar.
     *
     * @var string
     */
    var $_calendar;

    /**
     * An error message to throw when something is wrong.
     *
     * @var string
     */
    var $_errormsg;

    /**
     * Constructor.
     *
     * Just stores the $params in our newly-created object. All other work is
     * done by {@link initialize()}.
     *
     * @param array $params  Any parameters needed for this driver.
     */
    function Kronolith_Driver($params = array(), $errormsg = null)
    {
        $this->_params = $params;
        if ($errormsg === null) {
            $this->_errormsg = _("The Calendar backend is not currently available.");
        } else {
            $this->_errormsg = $errormsg;
        }
    }

    function open($calendar)
    {
        $this->_calendar = $calendar;
    }

    /**
     * Returns the currently open calendar.
     *
     * @return string  The current calendar name.
     */
    function getCalendar()
    {
        return $this->_calendar;
    }

    /**
     * Generates a universal / unique identifier for a task.
     *
     * This is NOT something that we expect to be able to parse into a
     * calendar and an event id.
     *
     * @return string  A nice unique string (should be 255 chars or less).
     */
    function generateUID()
    {
        return date('YmdHis') . '.'
            . substr(str_pad(base_convert(microtime(), 10, 36), 16, uniqid(mt_rand()), STR_PAD_LEFT), -16)
            . '@' . $GLOBALS['conf']['server']['name'];
    }

    /**
     * Renames a calendar.
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

    /**
     * Searches a calendar.
     *
     * @param object Kronolith_Event $query  A Kronolith_Event object with the
     *                                       criteria to search for.
     *
     * @return mixed  An array of Kronolith_Events or a PEAR_Error.
     */
    function search($query)
    {
        /* Our default implementation first gets <em>all</em> events in a
         * specific period, and then filters based on the actual values that
         * are filled in. Drivers can optimize this behavior if they have the
         * ability. */
        $results = array();

        $events = &$this->listEvents($query->start, $query->end);
        if (is_a($events, 'PEAR_Error')) {
            return $events;
        }

        if (isset($query->start)) {
            $startTime = $query->start->timestamp();
        } else {
            $startTime = null;
        }

        if (isset($query->end)) {
            $endTime = $query->end->timestamp();
        } else {
            $endTime = null;
        }

        foreach ($events as $eventid) {
            $event = &$this->getEvent($eventid);
            if (is_a($event, 'PEAR_Error')) {
                return $event;
            }

            $evStartTime = $event->start->timestamp();
            $evEndTime = $event->end->timestamp();

            if (((($evEndTime > $startTime || !isset($startTime)) &&
                  ($evStartTime < $endTime || !isset($endTime))) ||
                 ($event->recurs() && $evEndTime >= $startTime && $evStartTime <= $endTime)) &&
                (empty($query->title) || stristr($event->getTitle(), $query->title)) &&
                (empty($query->location) || stristr($event->getLocation(), $query->location)) &&
                (empty($query->description) || stristr($event->getDescription(), $query->description)) &&
                (empty($query->creatorID) || stristr($event->getCreatorID(), $query->creatorID)) &&
                (!isset($query->category) || $event->getCategory() == $query->category) &&
                (!isset($query->status) || $event->getStatus() == $query->status)) {
                $results[] = $event;
            }
        }

        return $results;
    }

    /**
     * Finds the next recurrence of $eventId that's after $afterDate.
     *
     * @param string $eventId        The ID of the event to fetch.
     * @param Horde_Date $afterDate  Return events after this date.
     *
     * @return Horde_Date|boolean  The date of the next recurrence or false if
     *                             the event does not recur after $afterDate.
     */
    function nextRecurrence($eventId, $afterDate)
    {
        $event = &$this->getEvent($eventId);
        if (is_a($event, 'PEAR_Error')) {
            return $event;
        }

        return $event->recurs() ? $event->recurrence->nextRecurrence($afterDate) : false;
    }

    /**
     * Attempts to return a concrete Kronolith_Driver instance based on
     * $driver.
     *
     * @param string $driver  The type of concrete Kronolith_Driver subclass
     *                        to return.
     *
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return Kronolith_Driver  The newly created concrete Kronolith_Driver
     *                           instance, or a PEAR_Error on error.
     */
    function &factory($driver = null, $params = null)
    {
        if ($driver === null) {
            $driver = $GLOBALS['conf']['calendar']['driver'];
        }
        $driver = basename($driver);

        if ($params === null) {
            $params = Horde::getDriverConfig('calendar', $driver);
        }

        include_once dirname(__FILE__) . '/Driver/' . $driver . '.php';
        $class = 'Kronolith_Driver_' . $driver;
        if (class_exists($class)) {
            $driver = &new $class($params);
            $result = $driver->initialize();
            if (is_a($result, 'PEAR_Error')) {
                $driver = new Kronolith_Driver($params, sprintf(_("The Calendar backend is not currently available: %s"), $result->getMessage()));
            }
        } else {
            $driver = new Kronolith_Driver($params, sprintf(_("Unable to load the definition of %s."), $class));
        }

        return $driver;
    }

    /**
     * Stub to initiate a driver.
     */
    function initialize()
    {
        return true;
    }

    /**
     * Stub to be overridden in the child class.
     */
    function &getEvent()
    {
        $error = PEAR::raiseError($this->_errormsg);
        return $error;
    }

    /**
     * Stub to be overridden in the child class.
     */
    function listAlarms($date, $fullevent = false)
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * Stub to be overridden in the child class.
     */
    function listEvents()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * Stub o be overridden in the child class.
     */
    function saveEvent()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * Stub for child class to override if it can implement.
     */
    function removeUserData($user)
    {
        return PEAR::raiseError(_("Removing user data is not supported with the current calendar storage backend."));
    }

}

/**
 * Kronolith_Event defines a generic API for events.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_Event {

    /**
     * Flag that is set to true if this event has data from either a storage
     * backend or a form or other import method.
     *
     * @var boolean
     */
    var $initialized = false;

    /**
     * Flag that is set to true if this event exists in a storage driver.
     *
     * @var boolean
     */
    var $stored = false;

    /**
     * The driver unique identifier for this event.
     *
     * @var string
     */
    var $eventID = null;

    /**
     * The UID for this event.
     *
     * @var string
     */
    var $_uid = null;

    /**
     * The iCalendar SEQUENCE for this event.
     *
     * @var integer
     */
    var $_sequence = null;

    /**
     * The user id of the creator of the event.
     *
     * @var string
     */
    var $creatorID = null;

    /**
     * The title of this event.
     *
     * @var string
     */
    var $title = '';

    /**
     * The category of this event.
     *
     * @var string
     */
    var $category = '';

    /**
     * The location this event occurs at.
     *
     * @var string
     */
    var $location = '';

    /**
     * The status of this event.
     *
     * @var integer
     */
    var $status = KRONOLITH_STATUS_CONFIRMED;

    /**
     * The description for this event
     *
     * @var string
     */
    var $description = '';

    /**
     * Remote description of this event (URL).
     *
     * @var string
     */
    var $remoteUrl = '';

    /**
     * Remote calendar name.
     *
     * @var string
     */
    var $remoteCal = '';

    /**
     * Whether the event is private.
     *
     * @var boolean
     */
    var $private = false;

    /**
     * All the attendees of this event.
     *
     * This is an associative array where the keys are the email addresses
     * of the attendees, and the values are also associative arrays with
     * keys 'attendance' and 'response' pointing to the attendees' attendance
     * and response values, respectively.
     *
     * @var array
     */
    var $attendees = array();

    /**
     * All the key words associtated with this event.
     *
     * @var array
     */
    var $keywords = array();

    /**
     * The start time of the event.
     *
     * @var Horde_Date
     */
    var $start;

    /**
     * The end time of the event.
     *
     * @var Horde_Date
     */
    var $end;

    /**
     * The duration of this event in minutes
     *
     * @var integer
     */
    var $durMin = 0;

    /**
     * Number of minutes before the event starts to trigger an alarm.
     *
     * @var integer
     */
    var $alarm = 0;

    /**
     * The identifier of the calender this event exists on.
     *
     * @var string
     */
    var $_calendar;

    /**
     * The VarRenderer class to use for printing select elements.
     *
     * @var Horde_UI_VarRenderer
     */
    var $_varRenderer;

    /**
     * Constructor.
     *
     * @param Kronolith_Driver $driver        The backend driver that this
     *                                        event is stored in.
     * @param Kronolith_Event  $eventObject   Backend specific event object
     *                                        that this will represent.
     */
    function Kronolith_Event(&$driver, $eventObject = null)
    {
        /* Set default alarm value. */
        if (isset($GLOBALS['prefs'])) {
            $this->alarm = $GLOBALS['prefs']->getValue('default_alarm');
        }

        $this->_calendar = $driver->getCalendar();
        if ($eventObject !== null) {
            $this->fromDriver($eventObject);
        }
    }

    /**
     * Returns a reference to a driver that's valid for this event.
     *
     * @return Kronolith_Driver  A driver that this event can use to save
     *                           itself, etc.
     */
    function &getDriver()
    {
        global $kronolith_driver;
        if ($kronolith_driver->getCalendar() != $this->_calendar) {
            $kronolith_driver->open($this->_calendar);
        }

        return $kronolith_driver;
    }

    /**
     * Returns the share this event belongs to.
     *
     * @return Horde_Share  This event's share.
     */
    function &getShare()
    {
        if (isset($GLOBALS['all_calendars'][$this->getCalendar()])) {
            $share = $GLOBALS['all_calendars'][$this->getCalendar()];
        } else {
            $share = PEAR::raiseError('Share not found');
        }
        return $share;
    }

    /**
     * Encapsulates permissions checking.
     *
     * @param integer $permission  The permission to check for.
     * @param string $user         The user to check permissions for.
     *
     * @return boolean
     */
    function hasPermission($permission, $user = null)
    {
        if ($user === null) {
            $user = Auth::getAuth();
        }

        if ($this->remoteCal) {
            switch ($permission) {
            case PERMS_SHOW:
            case PERMS_READ:
            case PERMS_EDIT:
                return true;

            default:
                return false;
            }
        }

        return (!is_a($share = &$this->getShare(), 'PEAR_Error') &&
                $share->hasPermission($user, $permission, $this->getCreatorId()));
    }

    /**
     * Saves changes to this event.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function save()
    {
        if (!$this->isInitialized()) {
            return PEAR::raiseError('Event not yet initialized');
        }

        $this->toDriver();
        $driver = &$this->getDriver();
        $result = $driver->saveEvent($this);
        if (!is_a($result, 'PEAR_Error') &&
            !empty($GLOBALS['conf']['alarms']['driver'])) {
            $alarm = $this->toAlarm(new Horde_Date($_SERVER['REQUEST_TIME']));
            if ($alarm) {
                $alarm['start'] = new Horde_Date($alarm['start']);
                $alarm['end'] = new Horde_Date($alarm['end']);
                require_once 'Horde/Alarm.php';
                $horde_alarm = Horde_Alarm::factory();
                $horde_alarm->set($alarm);
            }
        }

        return $result;
    }

    /**
     * Exports this event in iCalendar format.
     *
     * @param Horde_iCalendar &$calendar  A Horde_iCalendar object that acts as
     *                                    a container.
     *
     * @return Horde_iCalendar_vevent  The vEvent object for this event.
     */
    function &toiCalendar(&$calendar)
    {
        $vEvent = &Horde_iCalendar::newComponent('vevent', $calendar);
        $v1 = $calendar->getAttribute('VERSION') == '1.0';

        if ($this->isAllDay()) {
            $vEvent->setAttribute('DTSTART', $this->start, array('VALUE' => 'DATE'));
            $vEvent->setAttribute('DTEND', new Horde_Date($this->end->timestamp()), array('VALUE' => 'DATE'));
        } else {
            $vEvent->setAttribute('DTSTART', $this->start);
            $vEvent->setAttribute('DTEND', $this->end);
        }

        $vEvent->setAttribute('DTSTAMP', $_SERVER['REQUEST_TIME']);
        $vEvent->setAttribute('UID', $this->_uid);

        /* Get the event's history. */
        $history = &Horde_History::singleton();
        $created = $modified = null;
        $log = $history->getHistory('kronolith:' . $this->_calendar . ':' . $this->_uid);
        if ($log && !is_a($log, 'PEAR_Error')) {
            foreach ($log->getData() as $entry) {
                switch ($entry['action']) {
                case 'add':
                    $created = $entry['ts'];
                    break;

                case 'modify':
                    $modified = $entry['ts'];
                    break;
                }
            }
        }
        if (!empty($created)) {
            $vEvent->setAttribute($v1 ? 'DCREATED' : 'CREATED', $created);
            if (empty($modified)) {
                $modified = $created;
            }
        }
        if (!empty($modified)) {
            $vEvent->setAttribute('LAST-MODIFIED', $modified);
        }

        $vEvent->setAttribute('SUMMARY', $v1 ? $this->getTitle() : String::convertCharset($this->getTitle(), NLS::getCharset(), 'utf-8'));
        $name = Kronolith::getUserName($this->getCreatorId());
        if (!$v1) {
            $name = String::convertCharset($name, NLS::getCharset(), 'utf-8');
        }
        $vEvent->setAttribute('ORGANIZER',
                              'mailto:' . Kronolith::getUserEmail($this->getCreatorId()),
                              array('CN' => $name));
        if (!$this->isPrivate() || $this->getCreatorId() == Auth::getAuth()) {
            if (!empty($this->description)) {
                $vEvent->setAttribute('DESCRIPTION', $v1 ? $this->description : String::convertCharset($this->description, NLS::getCharset(), 'utf-8'));
            }
            $categories = $this->getCategory();
            if (!empty($categories)) {
                $vEvent->setAttribute('CATEGORIES', $v1 ? $categories : String::convertCharset($categories, NLS::getCharset(), 'utf-8'));
            }
            if (!empty($this->location)) {
                $vEvent->setAttribute('LOCATION', $v1 ? $this->location : String::convertCharset($this->location, NLS::getCharset(), 'utf-8'));
            }
        }
        $vEvent->setAttribute('CLASS', $this->isPrivate() ? 'PRIVATE' : 'PUBLIC');

        // Status.
        switch ($this->getStatus()) {
        case KRONOLITH_STATUS_FREE:
            // This is not an official iCalendar value, but we need it for
            // synchronization.
            $vEvent->setAttribute('STATUS', 'FREE');
            $vEvent->setAttribute('TRANSP', $v1 ? 1 : 'TRANSPARENT');
            break;
        case KRONOLITH_STATUS_TENTATIVE:
            $vEvent->setAttribute('STATUS', 'TENTATIVE');
            $vEvent->setAttribute('TRANSP', $v1 ? 0 : 'OPAQUE');
            break;
        case KRONOLITH_STATUS_CONFIRMED:
            $vEvent->setAttribute('STATUS', 'CONFIRMED');
            $vEvent->setAttribute('TRANSP', $v1 ? 0 : 'OPAQUE');
            break;
        case KRONOLITH_STATUS_CANCELLED:
            if ($v1) {
                $vEvent->setAttribute('STATUS', 'DECLINED');
                $vEvent->setAttribute('TRANSP', 1);
            } else {
                $vEvent->setAttribute('STATUS', 'CANCELLED');
                $vEvent->setAttribute('TRANSP', 'TRANSPARENT');
            }
            break;
        }

        // Attendees.
        foreach ($this->getAttendees() as $email => $status) {
            $params = array();
            switch ($status['attendance']) {
            case KRONOLITH_PART_REQUIRED:
                if ($v1) {
                    $params['EXPECT'] = 'REQUIRE';
                } else {
                    $params['ROLE'] = 'REQ-PARTICIPANT';
                }
                break;

            case KRONOLITH_PART_OPTIONAL:
                if ($v1) {
                    $params['EXPECT'] = 'REQUEST';
                } else {
                    $params['ROLE'] = 'OPT-PARTICIPANT';
                }
                break;

            case KRONOLITH_PART_NONE:
                if ($v1) {
                    $params['EXPECT'] = 'FYI';
                } else {
                    $params['ROLE'] = 'NON-PARTICIPANT';
                }
                break;
            }

            switch ($status['response']) {
            case KRONOLITH_RESPONSE_NONE:
                if ($v1) {
                    $params['STATUS'] = 'NEEDS ACTION';
                    $params['RSVP'] = 'YES';
                } else {
                    $params['PARTSTAT'] = 'NEEDS-ACTION';
                    $params['RSVP'] = 'TRUE';
                }
                break;

            case KRONOLITH_RESPONSE_ACCEPTED:
                if ($v1) {
                    $params['STATUS'] = 'ACCEPTED';
                } else {
                    $params['PARTSTAT'] = 'ACCEPTED';
                }
                break;

            case KRONOLITH_RESPONSE_DECLINED:
                if ($v1) {
                    $params['STATUS'] = 'DECLINED';
                } else {
                    $params['PARTSTAT'] = 'DECLINED';
                }
                break;

            case KRONOLITH_RESPONSE_TENTATIVE:
                if ($v1) {
                    $params['STATUS'] = 'TENTATIVE';
                } else {
                    $params['PARTSTAT'] = 'TENTATIVE';
                }
                break;
            }

            if (strpos($email, '@') === false) {
                $email = '';
            }
            if ($v1) {
                if (!empty($status['name'])) {
                    require_once 'Horde/MIME.php';
                    if (!empty($email)) {
                        $email = ' <' . $email . '>';
                    }
                    $email = $status['name'] . $email;
                    $email = MIME::trimEmailAddress($email);
                }
            } else {
                if (!empty($status['name'])) {
                    $params['CN'] = String::convertCharset($status['name'], NLS::getCharset(), 'utf-8');
                }
                if (!empty($email)) {
                    $email = 'mailto:' . $email;
                }
            }

            $vEvent->setAttribute('ATTENDEE', $email, $params);
        }

        // Alarms.
        if (!empty($this->alarm)) {
            if ($v1) {
                $vEvent->setAttribute('AALARM', $this->start->timestamp() - $this->alarm * 60);
            } else {
                $vAlarm = &Horde_iCalendar::newComponent('valarm', $vEvent);
                $vAlarm->setAttribute('ACTION', 'DISPLAY');
                $vAlarm->setAttribute('TRIGGER;VALUE=DURATION', '-PT' . $this->alarm . 'M');
                $vEvent->addComponent($vAlarm);
            }
        }

        // Recurrence.
        if ($this->recurs()) {
            if ($v1) {
                $rrule = $this->recurrence->toRRule10($calendar);
            } else {
                $rrule = $this->recurrence->toRRule20($calendar);
            }
            if (!empty($rrule)) {
                $vEvent->setAttribute('RRULE', $rrule);
            }

            // Exceptions.
            $exceptions = $this->recurrence->getExceptions();
            foreach ($exceptions as $exception) {
                if (!empty($exception)) {
                    list($year, $month, $mday) = sscanf($exception, '%04d%02d%02d');
                    $exdate = new Horde_Date(array(
                        'year' => $year,
                        'month' => $month,
                        'mday' => $mday,
                        'hour' => $this->start->hour,
                        'min' => $this->start->min,
                        'sec' => $this->start->sec,
                    ));
                    $vEvent->setAttribute('EXDATE', array($exdate));
                }
            }
        }

        return $vEvent;
    }

    /**
     * Updates the properties of this event from a Horde_iCalendar_vevent
     * object.
     *
     * @param Horde_iCalendar_vevent $vEvent  The iCalendar data to update
     *                                        from.
     */
    function fromiCalendar($vEvent)
    {
        // Unique ID.
        $uid = $vEvent->getAttribute('UID');
        if (!empty($uid) && !is_a($uid, 'PEAR_Error')) {
            $this->setUID($uid);
        }

        // Sequence.
        $seq = $vEvent->getAttribute('SEQUENCE');
        if (is_int($seq)) {
            $this->_sequence = $seq;
        }

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

        // Remote Url
        $url = $vEvent->getAttribute('URL');
        if (!is_array($url) && !is_a($url, 'PEAR_Error')) {
            $this->remoteUrl = $url;
        }

        // Location
        $location = $vEvent->getAttribute('LOCATION');
        if (!is_array($location) && !is_a($location, 'PEAR_Error')) {
            $this->setLocation($location);
        }

        // Class
        $class = $vEvent->getAttribute('CLASS');
        if (!is_array($class) && !is_a($class, 'PEAR_Error')) {
            $class = String::upper($class);
            if ($class == 'PRIVATE' || $class == 'CONFIDENTIAL') {
                $this->setPrivate(true);
            } else {
                $this->setPrivate(false);
            }
        }

        // Status.
        $status = $vEvent->getAttribute('STATUS');
        if (!is_array($status) && !is_a($status, 'PEAR_Error')) {
            $status = String::upper($status);
            if ($status == 'DECLINED') {
                $status = 'CANCELLED';
            }
            if (defined('KRONOLITH_STATUS_' . $status)) {
                $this->setStatus(constant('KRONOLITH_STATUS_' . $status));
            }
        }

        // Start and end date.
        $start = $vEvent->getAttribute('DTSTART');
        if (!is_a($start, 'PEAR_Error')) {
            if (!is_array($start)) {
                // Date-Time field
                $this->start = new Horde_Date($start);
            } else {
                // Date field
                $this->start = new Horde_Date(
                    array('year'  => (int)$start['year'],
                          'month' => (int)$start['month'],
                          'mday'  => (int)$start['mday']));
            }
        }
        $end = $vEvent->getAttribute('DTEND');
        if (!is_a($end, 'PEAR_Error')) {
            if (!is_array($end)) {
                // Date-Time field
                $this->end = new Horde_Date($end);
                // All day events are transferred by many device as
                // DSTART: YYYYMMDDT000000 DTEND: YYYYMMDDT2359(59|00)
                // Convert accordingly
                if (is_object($this->start) && $this->start->hour == 0 &&
                    $this->start->min == 0 && $this->start->sec == 0 &&
                    $this->end->hour == 23 && $this->end->min == 59) {
                    $this->end = new Horde_Date(
                        array('year'  => (int)$this->end->year,
                              'month' => (int)$this->end->month,
                              'mday'  => (int)$this->end->mday + 1));
                    $this->end->correct();
                }
            } elseif (is_array($end) && !is_a($end, 'PEAR_Error')) {
                // Date field
                $this->end = new Horde_Date(
                    array('year'  => (int)$end['year'],
                          'month' => (int)$end['month'],
                          'mday'  => (int)$end['mday']));
                $this->end->correct();
            }
        } else {
            $duration = $vEvent->getAttribute('DURATION');
            if (!is_array($duration) && !is_a($duration, 'PEAR_Error')) {
                $this->end = new Horde_Date($this->start->timestamp() + $duration);
            } else {
                // End date equal to start date as per RFC 2445.
                $this->end = Util::cloneObject($this->start);
                if (is_array($start)) {
                    // Date field
                    $this->end->mday++;
                    $this->end->correct();
                }
            }
        }

        // vCalendar 1.0 alarms
        $alarm = $vEvent->getAttribute('AALARM');
        if (!is_array($alarm) &&
            !is_a($alarm, 'PEAR_Error') &&
            intval($alarm)) {
            $this->alarm = intval(($this->start->timestamp() - $alarm) / 60);
        }

        // @TODO: vCalendar 2.0 alarms

        // Attendance.
        // Importing attendance may result in confusion: editing an imported
        // copy of an event can cause invitation updates to be sent from
        // people other than the original organizer. So we don't import by
        // default. However to allow updates by SyncML replication, the custom
        // X-ATTENDEE attribute is used which has the same syntax as
        // ATTENDEE.
        $attendee = $vEvent->getAttribute('X-ATTENDEE');
        if (!is_a($attendee, 'PEAR_Error')) {
            require_once 'Horde/MIME.php';

            if (!is_array($attendee)) {
                $attendee = array($attendee);
            }
            $params = $vEvent->getAttribute('X-ATTENDEE', true);
            if (!is_array($params)) {
                $params = array($params);
            }
            for ($i = 0; $i < count($attendee); ++$i) {
                $attendee[$i] = str_replace(array('MAILTO:', 'mailto:'), '',
                                            $attendee[$i]);
                $email = MIME::bareAddress($attendee[$i]);
                // Default according to rfc2445:
                $attendance = KRONOLITH_PART_REQUIRED;
                // vCalendar 2.0 style:
                if (!empty($params[$i]['ROLE'])) {
                    switch($params[$i]['ROLE']) {
                    case 'OPT-PARTICIPANT':
                        $attendance = KRONOLITH_PART_OPTIONAL;
                        break;

                    case 'NON-PARTICIPANT':
                        $attendance = KRONOLITH_PART_NONE;
                        break;
                    }
                }
                // vCalendar 1.0 style;
                if (!empty($params[$i]['EXPECT'])) {
                    switch($params[$i]['EXPECT']) {
                    case 'REQUEST':
                        $attendance = KRONOLITH_PART_OPTIONAL;
                        break;

                    case 'FYI':
                        $attendance = KRONOLITH_PART_NONE;
                        break;
                    }
                }
                $response = KRONOLITH_RESPONSE_NONE;
                if (empty($params[$i]['PARTSTAT']) &&
                    !empty($params[$i]['STATUS'])) {
                    $params[$i]['PARTSTAT']  = $params[$i]['STATUS'];
                }

                if (!empty($params[$i]['PARTSTAT'])) {
                    switch($params[$i]['PARTSTAT']) {
                    case 'ACCEPTED':
                        $response = KRONOLITH_RESPONSE_ACCEPTED;
                        break;

                    case 'DECLINED':
                        $response = KRONOLITH_RESPONSE_DECLINED;
                        break;

                    case 'TENTATIVE':
                        $response = KRONOLITH_RESPONSE_TENTATIVE;
                        break;
                    }
                }
                $name = isset($params[$i]['CN']) ? $params[$i]['CN'] : null;

                $this->addAttendee($email, $attendance, $response, $name);
            }
        }

        // Recurrence.
        $rrule = $vEvent->getAttribute('RRULE');
        if (!is_array($rrule) && !is_a($rrule, 'PEAR_Error')) {
            $this->recurrence = new Horde_Date_Recurrence($this->start);
            if (strpos($rrule, '=') !== false) {
                $this->recurrence->fromRRule20($rrule);
            } else {
                $this->recurrence->fromRRule10($rrule);
            }

            // Exceptions.
            $exdates = $vEvent->getAttributeValues('EXDATE');
            if (is_array($exdates)) {
                foreach ($exdates as $exdate) {
                    if (is_array($exdate)) {
                        $this->recurrence->addException((int)$exdate['year'],
                                                        (int)$exdate['month'],
                                                        (int)$exdate['mday']);
                    }
                }
            }
        }

        $this->initialized = true;
    }

    /**
     * Imports the values for this event from an array of values.
     *
     * @param array $hash  Array containing all the values.
     */
    function fromHash($hash)
    {
        // See if it's a new event.
        if ($this->getId() === null) {
            $this->setCreatorId(Auth::getAuth());
        }
        if (!empty($hash['title'])) {
            $this->setTitle($hash['title']);
        } else {
            return PEAR::raiseError(_("Events must have a title."));
        }
        if (!empty($hash['description'])) {
            $this->setDescription($hash['description']);
        }
        if (!empty($hash['category'])) {
            global $cManager;
            $categories = $cManager->get();
            if (!in_array($hash['category'], $categories)) {
                $cManager->add($hash['category']);
            }
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
                $this->start = new Horde_Date(array('year' => $date[0],
                                                    'month' => $date[1],
                                                    'mday' => $date[2],
                                                    'hour' => $time[0],
                                                    'min' => $time[1],
                                                    'sec' => $time[2]));
            }
        } else {
            return PEAR::raiseError(_("Events must have a start date."));
        }
        if (empty($hash['duration'])) {
            if (empty($hash['end_date'])) {
                $hash['end_date'] = $hash['start_date'];
            }
            if (empty($hash['end_time'])) {
                $hash['end_time'] = $hash['start_time'];
            }
        } else {
            $weeks = str_replace('W', '', $hash['duration'][1]);
            $days = str_replace('D', '', $hash['duration'][2]);
            $hours = str_replace('H', '', $hash['duration'][4]);
            $minutes = isset($hash['duration'][5]) ? str_replace('M', '', $hash['duration'][5]) : 0;
            $seconds = isset($hash['duration'][6]) ? str_replace('S', '', $hash['duration'][6]) : 0;
            $hash['duration'] = ($weeks * 60 * 60 * 24 * 7) + ($days * 60 * 60 * 24) + ($hours * 60 * 60) + ($minutes * 60) + $seconds;
            $this->end = new Horde_Date($this->start->timestamp() + $hash['duration']);
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
                $this->end = new Horde_Date(array('year' => $date[0],
                                                  'month' => $date[1],
                                                  'mday' => $date[2],
                                                  'hour' => $time[0],
                                                  'min' => $time[1],
                                                  'sec' => $time[2]));
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
                $this->setAlarm(($this->start->timestamp() - mktime($time[0], $time[1], $time[2], $date[1], $date[2], $date[0])) / 60);
            }
        }
        if (!empty($hash['recur_type'])) {
            $this->recurrence = new Horde_Date_Recurrence($this->start);
            $this->recurrence->setRecurType($hash['recur_type']);
            if (!empty($hash['recur_end_date'])) {
                $date = explode('-', $hash['recur_end_date']);
                $this->recurrence->setRecurEnd(new Horde_Date(array('year' => $date[0], 'month' => $date[1], 'mday' => $date[2])));
            }
            if (!empty($hash['recur_interval'])) {
                $this->recurrence->setRecurInterval($hash['recur_interval']);
            }
            if (!empty($hash['recur_data'])) {
                $this->recurrence->setRecurOnDay($hash['recur_data']);
            }
        }

        $this->initialized = true;
    }

    /**
     * Returns an alarm hash of this event suitable for Horde_Alarm.
     *
     * @param Horde_Date $time  Time of alarm.
     * @param string $user      The user to return alarms for.
     * @param Prefs $prefs      A Prefs instance.
     *
     * @return array  Alarm hash or null.
     */
    function toAlarm($time, $user = null, $prefs = null)
    {
        if (!$this->getAlarm()) {
            return;
        }

        if ($this->recurs()) {
            $eventDate = $this->recurrence->nextRecurrence($time);
            if ($eventDate && $this->recurrence->hasException($eventDate->year, $eventDate->month, $eventDate->mday)) {
                return;
            }
        }

        if (empty($user)) {
            $user = Auth::getAuth();
        }
        if (empty($prefs)) {
            $prefs = $GLOBALS['prefs'];
        }

        $methods = @unserialize($prefs->getValue('event_alarms'));
        $start = Util::cloneObject($this->start);
        $start->min -= $this->getAlarm();
        $start->correct();
        if (isset($methods['notify'])) {
            $methods['notify']['show'] = array(
                '__app' => $GLOBALS['registry']->getApp(),
                'event' => $this->getId(),
                'calendar' => $this->getCalendar());
            if (!empty($methods['notify']['sound'])) {
                if ($methods['notify']['sound'] == 'on') {
                    // Handle boolean sound preferences.
                    $methods['notify']['sound'] = $GLOBALS['registry']->get('themesuri') . '/sounds/theetone.wav';
                } else {
                    // Else we know we have a sound name that can be
                    // served from Horde.
                    $methods['notify']['sound'] = $GLOBALS['registry']->get('themesuri', 'horde') . '/sounds/' . $methods['notify']['sound'];
                }
            }
        }
        if (isset($methods['popup'])) {
            $methods['popup']['message'] = $this->getTitle($user);
            $description = $this->getDescription();
            if (!empty($description)) {
                $methods['popup']['message'] .= "\n\n" . $description;
            }
        }
        if (isset($methods['mail'])) {
            $methods['mail']['body'] = sprintf(
                _("We would like to remind you of this upcoming event.\n\n%s\n\nLocation: %s\n\nDate: %s\nTime: %s\n\n%s"),
                $this->getTitle($user),
                $this->location,
                strftime($prefs->getValue('date_format'), $this->start->timestamp()),
                date($prefs->getValue('twentyFour') ? 'H:i' : 'h:ia', $this->start->timestamp()),
                $this->getDescription());
        }

        return array(
            'id' => $this->getUID(),
            'user' => $user,
            'start' => $start->timestamp(),
            'end' => $this->end->timestamp(),
            'methods' => array_keys($methods),
            'params' => $methods,
            'title' => $this->getTitle($user),
            'text' => $this->getDescription());
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
     * Checks if the current event is already present in the calendar.
     *
     * Does the check based on the uid.
     *
     * @return boolean  True if event exists, false otherwise.
     */
    function exists()
    {
        if (!isset($this->_uid) || !isset($this->_calendar)) {
            return false;
        }

        $eventID = $GLOBALS['kronolith_driver']->exists($this->_uid, $this->_calendar);
        if (is_a($eventID, 'PEAR_Error') || !$eventID) {
            return false;
        } else {
            $this->eventID = $eventID;
            return true;
        }
    }

    function getDuration()
    {
        static $duration = null;
        if (isset($duration)) {
            return $duration;
        }

        if ($this->isInitialized()) {
            require_once 'Date/Calc.php';
            $dur_day_match = Date_Calc::dateDiff($this->start->mday,
                                                 $this->start->month,
                                                 $this->start->year,
                                                 $this->end->mday,
                                                 $this->end->month,
                                                 $this->end->year);
            $dur_hour_match = $this->end->hour - $this->start->hour;
            $dur_min_match = $this->end->min - $this->start->min;
            while ($dur_min_match < 0) {
                $dur_min_match += 60;
                --$dur_hour_match;
            }
            while ($dur_hour_match < 0) {
                $dur_hour_match += 24;
                --$dur_day_match;
            }
            if ($dur_hour_match == 0 && $dur_min_match == 0
                && $this->end->mday - $this->start->mday == 1) {
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

        $duration = new stdClass;
        $duration->day = $dur_day_match;
        $duration->hour = $dur_hour_match;
        $duration->min = $dur_min_match;
        $duration->wholeDay = $whole_day_match;

        return $duration;
    }

    /**
     * Returns whether this event is a recurring event.
     *
     * @return boolean  True if this is a recurring event.
     */
    function recurs()
    {
        return isset($this->recurrence) &&
            !$this->recurrence->hasRecurType(HORDE_DATE_RECUR_NONE);
    }

    /**
     * Returns a description of this event's recurring type.
     *
     * @return string  Human readable recurring type.
     */
    function getRecurName()
    {
        return $this->recurs()
            ? $this->recurrence->getRecurName()
            : _("No recurrence");
    }

    /**
     * Returns a correcty formatted exception date for recurring events and a
     * link to delete this exception.
     *
     * @param string $date  Exception in the format Ymd.
     *
     * @return string  The formatted date and delete link.
     */
    function exceptionLink($date)
    {
        $formatted = strftime($GLOBALS['prefs']->getValue('date_format'), strtotime($date));
        return $formatted
            . Horde::link(Util::addParameter(Horde::applicationUrl('edit.php'), array('calendar' => $this->getCalendar(), 'eventID' => $this->eventID, 'del_exception' => $date, 'url' => Util::getFormData('url'))), sprintf(_("Delete exception on %s"), $formatted))
            . Horde::img('delete-small.png', _("Delete"), '', $GLOBALS['registry']->getImageDir('horde'))
            . '</a>';
    }

    /**
     * Returns a list of exception dates for recurring events including links
     * to delete them.
     *
     * @return string  List of exception dates and delete links.
     */
    function exceptionsList()
    {
        return implode(', ', array_map(array($this, 'exceptionLink'), $this->recurrence->getExceptions()));
    }

    function getCalendar()
    {
        return $this->_calendar;
    }

    function setCalendar($calendar)
    {
        $this->_calendar = $calendar;
    }

    function isRemote()
    {
        return (bool)$this->remoteCal;
    }

    /**
     * Returns the locally unique identifier for this event.
     *
     * @return string  The local identifier for this event.
     */
    function getId()
    {
        return $this->eventID;
    }

    /**
     * Sets the locally unique identifier for this event.
     *
     * @param string $eventId  The local identifier for this event.
     */
    function setId($eventId)
    {
        if (substr($eventId, 0, 10) == 'kronolith:') {
            $eventId = substr($eventId, 10);
        }
        $this->eventID = $eventId;
    }

    /**
     * Returns the global UID for this event.
     *
     * @return string  The global UID for this event.
     */
    function getUID()
    {
        return $this->_uid;
    }

    /**
     * Sets the global UID for this event.
     *
     * @param string $uid  The global UID for this event.
     */
    function setUID($uid)
    {
        $this->_uid = $uid;
    }

    /**
     * Returns the iCalendar SEQUENCE for this event.
     *
     * @return integer  The sequence for this event.
     */
    function getSequence()
    {
        return $this->_sequence;
    }

    /**
     * Returns the id of the user who created the event.
     *
     * @return string  The creator id
     */
    function getCreatorId()
    {
        return !empty($this->creatorID) ? $this->creatorID : Auth::getAuth();
    }

    /**
     * Sets the id of the creator of the event.
     *
     * @param string $creatorID  The user id for the user who created the event
     */
    function setCreatorId($creatorID)
    {
        $this->creatorID = $creatorID;
    }

    /**
     * Returns the title of this event.
     *
     * @param string $user  The current user.
     *
     * @return string  The title of this event.
     */
    function getTitle($user = null)
    {
        if (isset($this->external) ||
            isset($this->contactID) ||
            $this->remoteCal) {
            return !empty($this->title) ? $this->title : _("[Unnamed event]");
        }

        if (!$this->isInitialized()) {
            return '';
        }

        if ($user === null) {
            $user = Auth::getAuth();
        }

        $start = date($GLOBALS['prefs']->getValue('twentyFour') ? 'G:i' : 'g:ia', $this->start->timestamp());
        $end = date($GLOBALS['prefs']->getValue('twentyFour') ? 'G:i' : 'g:ia', $this->end->timestamp());

        // We explicitly allow admin access here for the alarms
        // notifications.
        if (!Auth::isAdmin() && $this->isPrivate() &&
            $this->getCreatorId() != $user) {
            return sprintf(_("Private Event from %s to %s"), $start, $end);
        } elseif (Auth::isAdmin() || $this->hasPermission(PERMS_READ, $user)) {
            return strlen($this->title) ? $this->title : _("[Unnamed event]");
        } else {
            return sprintf(_("Event from %s to %s"), $start, $end);
        }
    }

    /**
     * Sets the title of this event.
     *
     * @param string  The new title for this event.
     */
    function setTitle($title)
    {
        $this->title = $title;
    }

    /**
     * Returns the description of this event.
     *
     * @return string  The description of this event.
     */
    function getDescription()
    {
        return $this->description;
    }

    /**
     * Sets the description of this event.
     *
     * @param string $description  The new description for this event.
     */
    function setDescription($description)
    {
        $this->description = $description;
    }

    /**
     * Returns the category of this event.
     *
     * @return string  The category of this event.
     */
    function getCategory()
    {
        return $this->category;
    }

    /**
     * Sets the category of this event.
     *
     * @param string $category  The category of this event.
     */
    function setCategory($category)
    {
        $this->category = $category;
    }

    /**
     * Returns the location this event occurs at.
     *
     * @return string  The location of this event.
     */
    function getLocation()
    {
        return $this->location;
    }

    /**
     * Sets the location this event occurs at.
     *
     * @param string $location  The new location for this event.
     */
    function setLocation($location)
    {
        $this->location = $location;
    }

    /**
     * Returns whether this event is private.
     *
     * @return boolean  Whether this even is private.
     */
    function isPrivate()
    {
        return $this->private;
    }

    /**
     * Sets the private flag of this event.
     *
     * @param boolean $private  Whether this event should be marked private.
     */
    function setPrivate($private)
    {
        $this->private = !empty($private);
    }

    /**
     * Returns the event status.
     *
     * @return integer  The status of this event.
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
     * @return boolean  True if the events status is the same as $status.
     */
    function hasStatus($status)
    {
        return ($status == $this->status);
    }

    /**
     * Sets the status of this event.
     *
     * @param integer $status  The new event status.
     */
    function setStatus($status)
    {
        $this->status = $status;
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
     * @param string $email  The email address of the attendee.
     *
     * @return boolean  True if the specified attendee is present for this
     *                  event.
     */
    function hasAttendee($email)
    {
        $email = String::lower($email);
        return isset($this->attendees[$email]);
    }

    /**
     * Sets the entire attendee array.
     *
     * @param array $attendees  The new attendees array. This should be of the
     *                          correct format to avoid driver problems.
     */
    function setAttendees($attendees)
    {
        $this->attendees = array_change_key_case($attendees);
    }

    /**
     * Adds a new attendee to the current event.
     *
     * This will overwrite an existing attendee if one exists with the same
     * email address.
     *
     * @param string $email        The email address of the attendee.
     * @param integer $attendance  The attendance code of the attendee.
     * @param integer $response    The response code of the attendee.
     * @param string $name         The name of the attendee.
     */
    function addAttendee($email, $attendance, $response, $name = null)
    {
        $email = String::lower($email);
        if ($attendance == KRONOLITH_PART_IGNORE) {
            if (isset($this->attendees[$email])) {
                $attendance = $this->attendees[$email]['attendance'];
            } else {
                $attendance = KRONOLITH_PART_REQUIRED;
            }
        }
        if (empty($name) && isset($this->attendees[$email]) &&
            !empty($this->attendees[$email]['name'])) {
            $name = $this->attendees[$email]['name'];
        }

        $this->attendees[$email] = array(
            'attendance' => $attendance,
            'response' => $response,
            'name' => $name
        );
    }

    /**
     * Removes the specified attendee from the current event.
     *
     * @param string $email  The email address of the attendee.
     */
    function removeAttendee($email)
    {
        $email = String::lower($email);
        if (isset($this->attendees[$email])) {
            unset($this->attendees[$email]);
        }
    }

    function getKeywords()
    {
        return $this->keywords;
    }

    function hasKeyword($keyword)
    {
        return in_array($keyword, $this->keywords);
    }

    function setKeywords($keywords)
    {
        $this->keywords = $keywords;
    }

    function isAllDay()
    {
        return ($this->start->hour == 0 && $this->start->min == 0 && $this->start->sec == 0 &&
                (($this->end->hour == 23 && $this->end->min == 59) ||
                 ($this->end->hour == 0 && $this->end->min == 0 && $this->end->sec == 0 &&
                  ($this->end->mday > $this->start->mday ||
                   $this->end->month > $this->start->month ||
                   $this->end->year > $this->start->year))));
    }

    function getAlarm()
    {
        return $this->alarm;
    }

    function setAlarm($alarm)
    {
        $this->alarm = $alarm;
    }

    function readForm()
    {
        global $prefs, $cManager;

        // Event owner.
        $targetcalendar = Util::getFormData('targetcalendar');
        if (strpos($targetcalendar, ':')) {
            list(, $creator) = explode(':', $targetcalendar, 2);
        } else {
            $creator = isset($this->eventID) ? $this->getCreatorId() : Auth::getAuth();
        }
        $this->setCreatorId($creator);

        // Basic fields.
        $this->setTitle(Util::getFormData('title', $this->title));
        $this->setDescription(Util::getFormData('description', $this->description));
        $this->setLocation(Util::getFormData('location', $this->location));
        $this->setPrivate(Util::getFormData('private'));
        $this->setKeywords(Util::getFormData('keywords', $this->keywords));

        // Category.
        if ($new_category = Util::getFormData('new_category')) {
            $new_category = $cManager->add($new_category);
            $category = $new_category ? $new_category : '';
        } else {
            $category = Util::getFormData('category', $this->category);
        }
        $this->setCategory($category);

        // Status.
        $this->setStatus(Util::getFormData('status', $this->status));

        // Attendees.
        if (isset($_SESSION['kronolith']['attendees']) && is_array($_SESSION['kronolith']['attendees'])) {
            $this->setAttendees($_SESSION['kronolith']['attendees']);
        }

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
                $dur_day = (int)Util::getFormData('dur_day');
                $dur_hour = (int)Util::getFormData('dur_hour');
                $dur_min = (int)Util::getFormData('dur_min');
            }
        }

        $this->start = new Horde_Date(array('hour' => $start_hour,
                                            'min' => $start_min,
                                            'month' => $start_month,
                                            'mday' => $start_day,
                                            'year' => $start_year));
        $this->start->correct();

        if (Util::getFormData('end_or_dur') == 1) {
            // Event duration.
            $this->end = new Horde_Date(array('hour' => $start_hour + $dur_hour,
                                              'min' => $start_min + $dur_min,
                                              'month' => $start_month,
                                              'mday' => $start_day + $dur_day,
                                              'year' => $start_year));
            $this->end->correct();
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

            $this->end = new Horde_Date(array('hour' => $end_hour,
                                              'min' => $end_min,
                                              'month' => $end_month,
                                              'mday' => $end_day,
                                              'year' => $end_year));
            $this->end->correct();
            if ($this->end->timestamp() < $this->start->timestamp()) {
                $this->end = Util::cloneObject($this->start);
            }
        }

        // Alarm.
        if (Util::getFormData('alarm') == 1) {
            $this->setAlarm(Util::getFormData('alarm_value') * Util::getFormData('alarm_unit'));
        } else {
            $this->setAlarm(0);
        }

        // Recurrence.
        $recur = Util::getFormData('recur');
        if ($recur !== null && $recur !== '') {
            if (!isset($this->recurrence)) {
                $this->recurrence = new Horde_Date_Recurrence($this->start);
            } else {
                $this->recurrence->setRecurStart($this->start);
            }
            if (Util::getFormData('recur_enddate_type') == 'date') {
                $recur_enddate = Util::getFormData('recur_enddate');
                $this->recurrence->setRecurEnd(new Horde_Date(
                    array('hour' => 1,
                          'min' => 1,
                          'sec' => 1,
                          'month' => $recur_enddate['month'],
                          'mday' => $recur_enddate['day'],
                          'year' => $recur_enddate['year'])));
            } elseif (Util::getFormData('recur_enddate_type') == 'count') {
                $this->recurrence->setRecurCount(Util::getFormData('recur_count'));
            } elseif (Util::getFormData('recur_enddate_type') == 'none') {
                $this->recurrence->setRecurCount(0);
                $this->recurrence->setRecurEnd(null);
            }

            $this->recurrence->setRecurType($recur);
            switch ($recur) {
            case HORDE_DATE_RECUR_DAILY:
                $this->recurrence->setRecurInterval(Util::getFormData('recur_daily_interval', 1));
                break;

            case HORDE_DATE_RECUR_WEEKLY:
                $weekly = Util::getFormData('weekly');
                $weekdays = 0;
                if (is_array($weekly)) {
                    foreach ($weekly as $day) {
                        $weekdays |= $day;
                    }
                }

                if ($weekdays == 0) {
                    // Sunday starts at 0.
                    switch ($this->start->dayOfWeek()) {
                    case 0: $weekdays |= HORDE_DATE_MASK_SUNDAY; break;
                    case 1: $weekdays |= HORDE_DATE_MASK_MONDAY; break;
                    case 2: $weekdays |= HORDE_DATE_MASK_TUESDAY; break;
                    case 3: $weekdays |= HORDE_DATE_MASK_WEDNESDAY; break;
                    case 4: $weekdays |= HORDE_DATE_MASK_THURSDAY; break;
                    case 5: $weekdays |= HORDE_DATE_MASK_FRIDAY; break;
                    case 6: $weekdays |= HORDE_DATE_MASK_SATURDAY; break;
                    }
                }

                $this->recurrence->setRecurInterval(Util::getFormData('recur_weekly_interval', 1));
                $this->recurrence->setRecurOnDay($weekdays);
                break;

            case HORDE_DATE_RECUR_MONTHLY_DATE:
                $this->recurrence->setRecurInterval(Util::getFormData('recur_day_of_month_interval', 1));
                break;

            case HORDE_DATE_RECUR_MONTHLY_WEEKDAY:
                $this->recurrence->setRecurInterval(Util::getFormData('recur_week_of_month_interval', 1));
                break;

            case HORDE_DATE_RECUR_YEARLY_DATE:
                $this->recurrence->setRecurInterval(Util::getFormData('recur_yearly_interval', 1));
                break;

            case HORDE_DATE_RECUR_YEARLY_DAY:
                $this->recurrence->setRecurInterval(Util::getFormData('recur_yearly_day_interval', 1));
                break;

            case HORDE_DATE_RECUR_YEARLY_WEEKDAY:
                $this->recurrence->setRecurInterval(Util::getFormData('recur_yearly_weekday_interval', 1));
                break;
            }

            if ($exceptions = Util::getFormData('exceptions')) {
                foreach ($exceptions as $exception) {
                    $this->recurrence->addException((int)substr($exception, 0, 4),
                                                    (int)substr($exception, 4, 2),
                                                    (int)substr($exception, 6, 2));
                }
            }
        }

        $this->initialized = true;
    }

    function html($property)
    {
        global $prefs;

        $options = array();
        $attributes = '';
        $sel = false;
        $label = '';

        switch ($property) {
        case 'start[year]':
            return  '<label for="' . $this->_formIDEncode($property) . '" class="hidden">' . _("Start Year") . '</label>' .
                '<input name="' . $property . '" value="' . $this->start->year .
                '" type="text" onchange="' . $this->js($property) .
                '" id="' . $this->_formIDEncode($property) . '" size="4" maxlength="4" />';

        case 'start[month]':
            $sel = $this->start->month;
            for ($i = 1; $i < 13; ++$i) {
                $options[$i] = strftime('%b', mktime(1, 1, 1, $i, 1));
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            $label = _("Start Month");
            break;

        case 'start[day]':
            $sel = $this->start->mday;
            for ($i = 1; $i < 32; ++$i) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            $label = _("Start Day");
            break;

        case 'start_hour':
            $sel = (int)date($prefs->getValue('twentyFour') ? 'G' : 'g', $this->start->timestamp());
            $hour_min = $prefs->getValue('twentyFour') ? 0 : 1;
            $hour_max = $prefs->getValue('twentyFour') ? 24 : 13;
            for ($i = $hour_min; $i < $hour_max; ++$i) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="document.eventform.whole_day.checked = false; updateEndDate();"';
            $label = _("Start Hour");
            break;

        case 'start_min':
            $sel = sprintf('%02d', $this->start->min);
            for ($i = 0; $i < 12; ++$i) {
                $min = sprintf('%02d', $i * 5);
                $options[$min] = $min;
            }
            $attributes = ' onchange="document.eventform.whole_day.checked = false; updateEndDate();"';
            $label = _("Start Minute");
            break;

        case 'end[year]':
            return  '<label for="' . $this->_formIDEncode($property) . '" class="hidden">' . _("End Year") . '</label>' .
                '<input name="' . $property . '" value="' . $this->end->year .
                '" type="text" onchange="' . $this->js($property) .
                '" id="' . $this->_formIDEncode($property) . '" size="4" maxlength="4" />';

        case 'end[month]':
            $sel = $this->end ? $this->end->month : $this->start->month;
            for ($i = 1; $i < 13; ++$i) {
                $options[$i] = strftime('%b', mktime(1, 1, 1, $i, 1));
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            $label = _("End Month");
            break;

        case 'end[day]':
            $sel = $this->end ? $this->end->mday : $this->start->mday;
            for ($i = 1; $i < 32; ++$i) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            $label = _("End Day");
            break;

        case 'end_hour':
            $sel = $this->end
                ? (int)date($prefs->getValue('twentyFour') ? 'G' : 'g', $this->end->timestamp())
                : (int)date($prefs->getValue('twentyFour') ? 'G' : 'g', $this->start->timestamp()) + 1;
            $hour_min = $prefs->getValue('twentyFour') ? 0 : 1;
            $hour_max = $prefs->getValue('twentyFour') ? 24 : 13;
            for ($i = $hour_min; $i < $hour_max; ++$i) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="updateDuration(); document.eventform.end_or_dur[0].checked = true"';
            $label = _("End Hour");
            break;

        case 'end_min':
            $sel = $this->end ? $this->end->min : $this->start->min;
            $sel = sprintf('%02d', $sel);
            for ($i = 0; $i < 12; ++$i) {
                $min = sprintf('%02d', $i * 5);
                $options[$min] = $min;
            }
            $attributes = ' onchange="updateDuration(); document.eventform.end_or_dur[0].checked = true"';
            $label = _("End Minute");
            break;

        case 'dur_day':
            $dur = $this->getDuration();
            return  '<label for="' . $property . '" class="hidden">' . _("Duration Day") . '</label>' .
                '<input name="' . $property . '" value="' . $dur->day .
                '" type="text" onchange="' . $this->js($property) .
                '" id="' . $property . '" size="4" maxlength="4" />';

        case 'dur_hour':
            $dur = $this->getDuration();
            $sel = $dur->hour;
            for ($i = 0; $i < 24; ++$i) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            $label = _("Duration Hour");
            break;

        case 'dur_min':
            $dur = $this->getDuration();
            $sel = $dur->min;
            for ($i = 0; $i < 13; ++$i) {
                $min = sprintf('%02d', $i * 5);
                $options[$min] = $min;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            $label = _("Duration Minute");
            break;

        case 'recur_enddate[year]':
            if ($this->end) {
                $end = ($this->recurs() && $this->recurrence->hasRecurEnd())
                        ? $this->recurrence->recurEnd->year
                        : $this->end->year;
            } else {
                $end = $this->start->year;
            }
            return  '<label for="' . $this->_formIDEncode($property) . '" class="hidden">' . _("Recurrence End Year") . '</label>' .
                '<input name="' . $property . '" value="' . $end .
                '" type="text" onchange="' . $this->js($property) .
                '" id="' . $this->_formIDEncode($property) . '" size="4" maxlength="4" />';

        case 'recur_enddate[month]':
            if ($this->end) {
                $sel = ($this->recurs() && $this->recurrence->hasRecurEnd())
                    ? $this->recurrence->recurEnd->month
                    : $this->end->month;
            } else {
                $sel = $this->start->month;
            }
            for ($i = 1; $i < 13; ++$i) {
                $options[$i] = strftime('%b', mktime(1, 1, 1, $i, 1));
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            $label = _("Recurrence End Month");
            break;

        case 'recur_enddate[day]':
            if ($this->end) {
                $sel = ($this->recurs() && $this->recurrence->hasRecurEnd())
                    ? $this->recurrence->recurEnd->mday
                    : $this->end->mday;
            } else {
                $sel = $this->start->mday;
            }
            for ($i = 1; $i < 32; ++$i) {
                $options[$i] = $i;
            }
            $attributes = ' onchange="' . $this->js($property) . '"';
            $label = _("Recurrence End Day");
            break;
        }

        if (!$this->_varRenderer) {
            require_once 'Horde/UI/VarRenderer.php';
            $this->_varRenderer = Horde_UI_VarRenderer::factory('html');
        }

        return '<label for="' . $this->_formIDEncode($property) . '" class="hidden">' . $label . '</label>' .
            '<select name="' . $property . '"' . $attributes . ' id="' . $this->_formIDEncode($property) . '">' .
            $this->_varRenderer->_selectOptions($options, $sel) .
            '</select>';
    }

    function js($property)
    {
        switch ($property) {
        case 'start[month]':
        case 'start[year]':
        case 'start[day]':
        case 'start':
            return 'updateWday(\'start_wday\'); document.eventform.whole_day.checked = false; updateEndDate();';

        case 'end[month]':
        case 'end[year]':
        case 'end[day]':
        case 'end':
            return 'updateWday(\'end_wday\'); updateDuration(); document.eventform.end_or_dur[0].checked = true;';

        case 'recur_enddate[month]':
        case 'recur_enddate[year]':
        case 'recur_enddate[day]':
        case 'recur_enddate':
            return 'updateWday(\'recur_end_wday\'); document.eventform.recur_enddate_type[1].checked = true;';

        case 'dur_day':
        case 'dur_hour':
        case 'dur_min':
            return 'document.eventform.whole_day.checked = false; updateEndDate(); document.eventform.end_or_dur[1].checked = true;';
        }
    }

    /**
     * @param array $params
     *
     * @return string
     */
    function getViewUrl($params = array(), $full = false)
    {
        $params['eventID'] = $this->eventID;
        if ($this->remoteUrl) {
            return $this->remoteUrl;
        } elseif ($this->remoteCal) {
            $params['calendar'] = '**remote';
            $params['remoteCal'] = $this->remoteCal;
        } else {
            $params['calendar'] = $this->getCalendar();
        }

        return Horde::applicationUrl(Util::addParameter('event.php', $params), $full);
    }

    /**
     * @param array $params
     *
     * @return string
     */
    function getEditUrl($params = array())
    {
        $params['view'] = 'EditEvent';
        $params['eventID'] = $this->eventID;
        if ($this->remoteCal) {
            $params['calendar'] = '**remote';
            $params['remoteCal'] = $this->remoteCal;
        } else {
            $params['calendar'] = $this->getCalendar();
        }

        return Horde::applicationUrl(Util::addParameter('event.php', $params));
    }

    /**
     * @param array $params
     *
     * @return string
     */
    function getDeleteUrl($params = array())
    {
        $params['view'] = 'DeleteEvent';
        $params['eventID'] = $this->eventID;
        $params['calendar'] = $this->getCalendar();
        return Horde::applicationUrl(Util::addParameter('event.php', $params));
    }

    /**
     * @param array $params
     *
     * @return string
     */
    function getExportUrl($params = array())
    {
        $params['view'] = 'ExportEvent';
        $params['eventID'] = $this->eventID;
        if ($this->remoteCal) {
            $params['calendar'] = '**remote';
            $params['remoteCal'] = $this->remoteCal;
        } else {
            $params['calendar'] = $this->getCalendar();
        }

        return Horde::applicationUrl(Util::addParameter('event.php', $params));
    }

    function getLink($timestamp = null, $icons = true, $from_url = null, $full = false)
    {
        global $prefs, $registry;

        if (is_null($timestamp)) {
            $timestamp = $this->start->timestamp();
        }
        if (is_null($from_url)) {
            $from_url = Horde::selfUrl(true, false, true);
        }

        $event_title = $this->getTitle();
        $view_url = $this->getViewUrl(array('timestamp' => $timestamp, 'url' => $from_url), $full);
        $read_permission = $this->hasPermission(PERMS_READ);

        $link = '';
        if (isset($this->external)) {
            $link = $registry->link($this->external . '/show', $this->external_params);
            $link = Horde::linkTooltip(Horde::url($link), '', 'event-tentative', '', '', String::wrap($this->description));
        } elseif (isset($this->eventID) && $read_permission) {
            $link = Horde::linkTooltip($view_url,
                                       $event_title,
                                       $this->getStatusClass(), '', '',
                                       $this->getTooltip());
        }

        $link .= @htmlspecialchars($event_title, ENT_QUOTES, NLS::getCharset());

        if ($read_permission && (isset($this->eventID) || isset($this->external))) {
            $link .= '</a>';
        }

        if ($icons && $prefs->getValue('show_icons')) {
            $icon_color = isset($GLOBALS['cManager_fgColors'][$this->category]) ?
                ($GLOBALS['cManager_fgColors'][$this->category] == '#000' ? '000' : 'fff') :
                ($GLOBALS['cManager_fgColors']['_default_'] == '#000' ? '000' : 'fff');
            $image_dir = Horde::url($registry->getImageDir(), true, -1);

            $status = '';
            if ($this->alarm) {
                if ($this->alarm % 10080 == 0) {
                    $alarm_value = $this->alarm / 10080;
                    $title = $alarm_value == 1 ?
                        _("Alarm 1 week before") :
                        sprintf(_("Alarm %d weeks before"), $alarm_value);
                } elseif ($this->alarm % 1440 == 0) {
                    $alarm_value = $this->alarm / 1440;
                    $title = $alarm_value == 1 ?
                        _("Alarm 1 day before") :
                        sprintf(_("Alarm %d days before"), $alarm_value);
                } elseif ($this->alarm % 60 == 0) {
                    $alarm_value = $this->alarm / 60;
                    $title = $alarm_value == 1 ?
                        _("Alarm 1 hour before") :
                        sprintf(_("Alarm %d hours before"), $alarm_value);
                } else {
                    $alarm_value = $this->alarm;
                    $title = $alarm_value == 1 ?
                        _("Alarm 1 minute before") :
                        sprintf(_("Alarm %d minutes before"), $alarm_value);
                }
                $status .= Horde::img('alarm-' . $icon_color . '.png', $title,
                                      array('title' => $title,
                                            'class' => 'iconAlarm'),
                                      $image_dir);
            }

            if ($this->recurs()) {
                $title = Kronolith::recurToString($this->recurrence->getRecurType());
                $status .= Horde::img('recur-' . $icon_color . '.png', $title,
                                      array('title' => $title,
                                            'class' => 'iconRecur'),
                                      $image_dir);
            }

            if ($this->isPrivate()) {
                $title = _("Private event");
                $status .= Horde::img('private-' . $icon_color . '.png', $title,
                                      array('title' => $title,
                                            'class' => 'iconPrivate'),
                                      $image_dir);
            }

            if (!empty($this->attendees)) {
                $title = count($this->attendees) == 1
                    ? _("1 attendee")
                    : sprintf(_("%s attendees"), count($this->attendees));
                $status .= Horde::img('attendees.png', $title,
                                      array('title' => $title,
                                            'class' => 'iconPeople'),
                                      $image_dir);
            }

            if (!empty($status)) {
                $link .= ' ' . $status;
            }

            if (!$this->eventID || !empty($this->external)) {
                return $link;
            }

            $edit = '';
            $delete = '';
            if ((!$this->isPrivate() || $this->getCreatorId() == Auth::getAuth())
                && $this->hasPermission(PERMS_EDIT)) {
                $editurl = Util::addParameter($view_url, 'view', 'EditEvent', !$full);
                $edit = Horde::link($editurl, sprintf(_("Edit %s"), $event_title), 'iconEdit')
                    . Horde::img('edit-' . $icon_color . '.png', _("Edit"), '', $image_dir)
                    . '</a>';
            }
            if ($this->hasPermission(PERMS_DELETE)) {
                $delurl = Util::addParameter($view_url, 'view', 'DeleteEvent', !$full);
                $delete = Horde::link($delurl, sprintf(_("Delete %s"), $event_title), 'iconDelete')
                    . Horde::img('delete-' . $icon_color . '.png', _("Delete"), '', $image_dir)
                    . '</a>';
            }

            if ($edit || $delete) {
                $link .= $edit . $delete;
            }
        }

        return $link;
    }

    /**
     * @return string  A tooltip for quick descriptions of this event.
     */
    function getTooltip()
    {
        $tooltip = $this->getTimeRange()
            . "\n" . sprintf(_("Owner: %s"), ($this->getCreatorId() == Auth::getAuth() ?
                                              _("Me") : Kronolith::getUserName($this->getCreatorId())));

        if (!$this->isPrivate() || $this->getCreatorId() == Auth::getAuth()) {
            if ($this->location) {
                $tooltip .= "\n" . _("Location") . ': ' . $this->location;
            }

            if ($this->description) {
                $tooltip .= "\n\n" . String::wrap($this->description);
            }
        }

        return $tooltip;
    }

    /**
     * @return string The time range of the event ("All Day",
     * "1:00pm-3:00pm", "08:00-22:00").
     */
    function getTimeRange()
    {
        if ($this->isAllDay()) {
            return _("All day");
        } elseif (($cmp = $this->start->compareDate($this->end)) > 0) {
            $df = $GLOBALS['prefs']->getValue('date_format');
            if ($cmp > 0) {
                return strftime($df, $this->end->timestamp()) . '-'
                    . strftime($df, $this->start->timestamp());
            } else {
                return strftime($df, $this->start->timestamp()) . '-'
                    . strftime($df, $this->end->timestamp());
            }
        } else {
            $tf = $GLOBALS['prefs']->getValue('twentyFour') ? 'G:i' : 'g:ia';
            return date($tf, $this->start->timestamp()) . '-'
                . date($tf, $this->end->timestamp());
        }
    }

    /**
     * @return string  The CSS class for the event based on its status.
     */
    function getStatusClass()
    {
        switch ($this->status) {
        case KRONOLITH_STATUS_CANCELLED:
            return 'event-cancelled';

        case KRONOLITH_STATUS_TENTATIVE:
        case KRONOLITH_STATUS_FREE:
            return 'event-tentative';
        }

        return 'event';
    }

    function _formIDEncode($id)
    {
        return str_replace(array('[', ']'),
                           array('_', ''),
                           $id);
    }

}
