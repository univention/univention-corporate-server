<?php
/**
 * The Kronolith_Driver_sql:: class implements the Kronolith_Driver
 * API for a SQL backend.
 *
 * $Horde: kronolith/lib/Driver/sql.php,v 1.121 2004/05/22 13:02:13 mdjukic Exp $
 *
 * @author  Luc Saillard <luc.saillard@fr.alcove.com>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Kronolith 0.3
 * @package Kronolith
 */
class Kronolith_Driver_sql extends Kronolith_Driver {

    /**
     * The object handle for the current database connection.
     *
     * @var object DB $_db
     */
    var $_db;

    /**
     * Boolean indicating whether or not we're currently connected to
     * the SQL server.
     *
     * @var boolean $_connected
     */
    var $_connected = false;

    /**
     * Cache events as we fetch them to avoid fetching the same event
     * from the DB twice.
     *
     * @var array $_cache
     */
    var $_cache = array();

    function open($calendar)
    {
        $this->_calendar = $calendar;
        $this->_connect();
    }

    function listAlarms($date)
    {
        $allevents = $this->listEvents($date, $date, true);
        $events = array();

        foreach ($allevents as $eventId) {
            $event = &$this->getEvent($eventId);

            if ($event->getRecurType() == KRONOLITH_RECUR_NONE) {
                $start = &Kronolith::dateObject($event->start);
                $start->min -= $event->getAlarm();
                $start->correct();
                if (Kronolith::compareDateTimes($start, $date) <= 0 &&
                    Kronolith::compareDateTimes($date, $event->end) <= -1) {
                    $events[] = $eventId;
                }
            } else {
                if ($next = $this->nextRecurrence($eventId, $date)) {
                    $start = &Kronolith::dateObject($next);
                    $start->min -= $event->getAlarm();
                    $start->correct();
                    if (Kronolith::compareDateTimes($start, $date) <= 0 &&
                        Kronolith::compareDateTimes($date, Kronolith::dateObject(array('year' => $next->year,
                                                                                       'month' => $next->month,
                                                                                       'mday' => $next->mday,
                                                                                       'hour' => $event->end->hour,
                                                                                       'min' => $event->end->min,
                                                                                       'sec' => $event->end->sec)) <= -1)) {
                        $events[] = $eventId;
                    }
                }
            }
        }

        return is_array($events) ? $events : array();
    }

    function listEvents($startDate = null, $endDate = null, $hasAlarm = false)
    {
        $endInterval = &new Kronolith_Date($endDate);
        if (!isset($endDate)) {
            $endInterval = Kronolith::dateObject(array('mday' => 31, 'month' => 12, 'year' => 9999));
        } else {
            list($endInterval->mday, $endInterval->month, $endInterval->year) = explode('/', Date_Calc::nextDay($endDate->mday, $endDate->month, $endDate->year, '%d/%m/%Y'));
        }
        $etime = sprintf('%04d-%02d-%02d 00:00:00', $endInterval->year, $endInterval->month, $endInterval->mday);

        $startInterval = &new Kronolith_Date($startDate);
        if (isset($startDate)) {
            if ($startDate === 0) {
                $startInterval = Kronolith::dateObject(array('mday' => 1, 'month' => 1, 'year' => 0000));
            }
            if ($startInterval->month == 0) {
                $startInterval->month = 1;
            }
            if ($startInterval->mday == 0) {
                $startInterval->mday = 1;
            }
            $stime = sprintf('%04d-%02d-%02d 00:00:00', $startInterval->year, $startInterval->month, $startInterval->mday);
        }

        $q = 'SELECT DISTINCT event_id, event_description, event_location,' .
            ' event_status, event_attendees,' .
            ' event_keywords, event_title, event_category,' .
            ' event_recurtype, event_recurenddate, event_recurinterval,' .
            ' event_recurdays, event_start, event_end, event_alarm,' .
            ' event_modified, event_exceptions, event_creator_id FROM ' . $this->_params['table'] .
            ' WHERE calendar_id = ' . $this->_db->quote($this->_calendar) . ' AND ((';

        if ($hasAlarm) {
            $q .= 'event_alarm > 0)) AND ((';
        }

        if (isset($stime)) {
            $q .= 'event_end > ' . $this->_db->quote($stime) . ' AND ';
        }
        $q .= 'event_start < ' . $this->_db->quote($etime) . ') OR (';
        if (isset($stime)) {
            $q .= 'event_recurenddate >= ' . $this->_db->quote($stime) . ' AND ';
        }
        $q .= 'event_start <= ' . $this->_db->quote($etime) .
            ' AND event_recurtype != ' . KRONOLITH_RECUR_NONE . '))';

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL event list by %s: query = "%s"',
                                  Auth::getAuth(), $q),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Run the query. */
        $qr = $this->_db->query($q);

        $events = array();
        if (!is_a($qr, 'PEAR_Error')) {
            $row = $qr->fetchRow(DB_FETCHMODE_ASSOC);
            while ($row && !is_a($row, 'PEAR_Error')) {
                // We have all the information we need to create an
                // event object for this event, so go ahead and cache
                // it.
                $this->_cache[$this->_calendar][$row['event_id']] = &new Kronolith_Event_sql($this, $row);

                if ($row['event_recurtype'] == KRONOLITH_RECUR_NONE) {
                    $events[$this->getGUID($row['event_id'])] = $row['event_id'];
                } else {
                    $next = $this->nextRecurrence($row['event_id'], $startInterval);
                    if ($next && Kronolith::compareDates($next, $endInterval) < 0) {
                        $events[$this->getGUID($row['event_id'])] = $row['event_id'];
                    }
                }

                $row = $qr->fetchRow(DB_FETCHMODE_ASSOC);
            }
        }

        return $events;
    }

    function &getEvent($eventId = null)
    {
        if (is_null($eventId)) {
            return $ret = &new Kronolith_Event_sql($this);
        }

        if (isset($this->_cache[$this->_calendar][$eventId])) {
            return $this->_cache[$this->_calendar][$eventId];
        }

        $query = 'SELECT event_id, event_description, event_location,' .
            ' event_status, event_attendees,' .
            ' event_keywords, event_title, event_category,' .
            ' event_recurtype, event_recurenddate, event_recurinterval,' .
            ' event_recurdays, event_start, event_end, event_alarm,' .
            ' event_modified, event_exceptions, event_creator_id' .
            ' FROM ' . $this->_params['table'] .
            ' WHERE event_id = ' . $this->_db->quote($eventId) .
            ' AND calendar_id = ' . $this->_db->quote($this->_calendar);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL event fetch by %s: query = "%s"',
                                  Auth::getAuth(), $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $event = &$this->_db->getRow($query, DB_FETCHMODE_ASSOC);
        if (is_a($event, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $event;
        }

        if ($event) {
            $this->_cache[$this->_calendar][$eventId] = &new Kronolith_Event_sql($this, $event);
            return $this->_cache[$this->_calendar][$eventId];
        } else {
            return false;
        }
    }

    function &getByGUID($guid)
    {
        /* Validate the GUID. */
        if (substr($guid, 0, 10) != 'kronolith:') {
            return PEAR::raiseError('Invalid GUID');
        }
        $guid = substr($guid, 10);

        $this->_connect();

        $query = 'SELECT event_id, calendar_id, event_description, event_location,' .
            ' event_status, event_attendees,' .
            ' event_keywords, event_title, event_category,' .
            ' event_recurtype, event_recurenddate, event_recurinterval,' .
            ' event_recurdays, event_start, event_end, event_alarm,' .
            ' event_modified, event_exceptions, event_creator_id' .
            ' FROM ' . $this->_params['table'] .
            ' WHERE event_id = ' . $this->_db->quote($guid);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL event fetch by %s: query = "%s"',
                                  Auth::getAuth(), $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $event = &$this->_db->getRow($query, DB_FETCHMODE_ASSOC);
        if (is_a($event, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $event;
        }

        if ($event) {
            $this->open($event['calendar_id']);
            $this->_cache[$this->_calendar][$event['event_id']] = &new Kronolith_Event_sql($this, $event);
            return $this->_cache[$this->_calendar][$event['event_id']];
        } else {
            return PEAR::raiseError($guid . ' not found');
        }
    }

    function saveEvent($event)
    {
        if ($event->isStored()) {
            $query = 'UPDATE ' . $this->_params['table'] . ' SET ';

            foreach ($event->getProperties() as $key => $val) {
                $query .= " $key = " . $this->_db->quote($val) . ',';
            }
            $query = substr($query, 0, -1);
            $query .= ' WHERE event_id = ' . $this->_db->quote($event->getID());

            /* Log the query at a DEBUG log level. */
            Horde::logMessage(sprintf('SQL event update by %s: query = "%s"',
                                      Auth::getAuth(), $query),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $res = $this->_db->query($query);
            if (is_a($res, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $res;
            }

            /* Log the modification of this item in the history
             * log. */
            $history = &Horde_History::singleton();
            $history->log($this->getGUID($event->getID()), array('action' => 'modify'), true);

            return $event->getID();
        } else {
            if ($event->getID()) {
                $id = $event->getID();
            } else {
                $id = md5(uniqid(mt_rand(), true));
            }

            $query = 'INSERT INTO ' . $this->_params['table'] . ' ';
            $cols_name = '(event_id,';
            $cols_values = 'values (' . $this->_db->quote($id) . ',';

            foreach ($event->getProperties() as $key => $val) {
                $cols_name .= " $key,";
                $cols_values .= $this->_db->quote($val) . ',';
            }

            $cols_name .= ' calendar_id)';
            $cols_values .= $this->_db->quote($this->_calendar) . ') ';

            $query .= $cols_name . $cols_values;

            /* Log the query at a DEBUG log level. */
            Horde::logMessage(sprintf('SQL event store by %s: query = "%s"',
                                Auth::getAuth(), $query),
                                __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $res = $this->_db->query($query);
            if (is_a($res, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $res;
            }

            /* Log the creation of this item in the history log. */
            $history = &Horde_History::singleton();
            $history->log($this->getGUID($id), array('action' => 'add'), true);

            return $id;
        }
    }

    /**
     * Move an event to a new calendar.
     *
     * @param string $eventId      The event to move.
     * @param string $newCalendar  The new calendar.
     */
    function move($eventId, $newCalendar)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        $query = sprintf('UPDATE %s SET calendar_id = %s WHERE calendar_id = %s AND event_id = %s',
                         $this->_params['table'],
                         $this->_db->quote($newCalendar),
                         $this->_db->quote($this->_calendar),
                         $this->_db->quote($eventId));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Kronolith_Driver_sql::move(): %s', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Attempt the move query. */
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

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
        $this->_connect();

        $query = sprintf('DELETE FROM %s WHERE calendar_id = %s',
                         $this->_params['table'],
                         $this->_db->quote($calendar));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Calender Delete by %s: query = "%s"',
                                  Auth::getAuth(), $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $this->_db->query($query);
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
        $query = sprintf('DELETE FROM %s WHERE event_id = %s AND calendar_id = %s',
                         $this->_params['table'],
                         $this->_db->quote($eventId),
                         $this->_db->quote($this->_calendar));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Event Delete by %s: query = "%s"',
                                  Auth::getAuth(), $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        /* Log the deletion of this item in the history log. */
        $history = &Horde_History::singleton();
        $history->log($this->getGUID($eventId), array('action' => 'delete'), true);

        return true;
    }

    /**
     * Attempts to open a persistent connection to the SQL server.
     *
     * @return boolean True.
     */
    function _connect()
    {
        if (!$this->_connected) {
            Horde::assertDriverConfig($this->_params, 'calendar',
                array('phptype', 'hostspec', 'username', 'database'));

            if (!isset($this->_params['table'])) {
                $this->_params['table'] = 'kronolith_events';
            }

            /* Connect to the SQL server using the supplied parameters. */
            require_once 'DB.php';
            $this->_db = &DB::connect($this->_params,
                                      array('persistent' => !empty($this->_params['persistent'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                Horde::fatal($this->_db, __FILE__, __LINE__);
            }

            /* Enable the "portability" option. */
            $this->_db->setOption('optimize', 'portability');

            $this->_connected = true;

            /* Handle any database specific initialization code to
             * run. */
            switch ($this->_db->dbsyntax) {
            case 'oci8':
                $query = "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'";

                /* Log the query at a DEBUG log level. */
                Horde::logMessage(sprintf('SQL session setup by %s: query = "%s"',
                                          Auth::getAuth(), $query),
                                  __FILE__, __LINE__, PEAR_LOG_DEBUG);

                $this->_db->query($query);
                break;
            }
        }

        return true;
    }

    function close()
    {
        return true;
    }

    /**
     * Converts a value from the driver's charset to the default
     * charset.
     *
     * @param mixed $value  A value to convert.
     *
     * @return mixed  The converted value.
     */
    function convertFromDriver($value)
    {
        return String::convertCharset($value, $this->_params['charset']);
    }

    /**
     * Converts a value from the default charset to the driver's
     * charset.
     *
     * @param mixed $value  A value to convert.
     *
     * @return mixed  The converted value.
     */
    function convertToDriver($value)
    {
        return String::convertCharset($value, NLS::getCharset(), $this->_params['charset']);
    }

}

class Kronolith_Event_sql extends Kronolith_Event {

    var $_properties = array();

    function fromDriver($SQLEvent)
    {
        $driver = &$this->getDriver();

        $this->start = &new stdClass();
        $this->end = &new stdClass();
        list($this->start->year, $this->start->month, $this->start->mday, $this->start->hour, $this->start->min, $this->start->sec) = sscanf($SQLEvent['event_start'], '%04d-%02d-%02d %02d:%02d:%02d');
        list($this->end->year, $this->end->month, $this->end->mday, $this->end->hour, $this->end->min, $this->end->sec) = sscanf($SQLEvent['event_end'], '%04d-%02d-%02d %02d:%02d:%02d');

        $this->startTimestamp = mktime($this->start->hour, $this->start->min, $this->start->sec, $this->start->month, $this->start->mday, $this->start->year);
        $this->endTimestamp = mktime($this->end->hour, $this->end->min, $this->end->sec, $this->end->month, $this->end->mday, $this->end->year);

        $this->durMin = ($this->endTimestamp - $this->startTimestamp) / 60;

        if (isset($SQLEvent['event_recurenddate'])) {
            $this->recurEnd = &new stdClass();
            list($this->recurEnd->year, $this->recurEnd->month, $this->recurEnd->mday, $this->recurEnd->hour, $this->recurEnd->min, $this->recurEnd->sec) = sscanf($SQLEvent['event_recurenddate'], '%04d-%02d-%02d %02d:%02d:%02d');
            $this->recurEndTimestamp = @mktime($this->recurEnd->hour, $this->recurEnd->min, $this->recurEnd->sec, $this->recurEnd->month, $this->recurEnd->mday, $this->recurEnd->year);
        }

        $this->title = $driver->convertFromDriver($SQLEvent['event_title']);
        $this->eventID = $SQLEvent['event_id'];
        $this->creatorID = $SQLEvent['event_creator_id'];
        $this->recurType = (int)$SQLEvent['event_recurtype'];
        $this->recurInterval = (int)$SQLEvent['event_recurinterval'];

        if (isset($SQLEvent['event_category'])) {
            $this->category = $SQLEvent['event_category'];
        }
        if (isset($SQLEvent['event_location'])) {
            $this->location = $driver->convertFromDriver($SQLEvent['event_location']);
        }
        if (isset($SQLEvent['event_status'])) {
            $this->status = $SQLEvent['event_status'];
        }
        if (isset($SQLEvent['event_attendees'])) {
            $this->attendees = unserialize($driver->convertFromDriver($SQLEvent['event_attendees']));
        }
        if (isset($SQLEvent['event_keywords'])) {
            $this->keywords = explode(',', $driver->convertFromDriver($SQLEvent['event_keywords']));
        }
        if (isset($SQLEvent['event_exceptions'])) {
            $this->exceptions = explode(',', $SQLEvent['event_exceptions']);
        }
        if (isset($SQLEvent['event_description'])) {
            $this->description = $driver->convertFromDriver($SQLEvent['event_description']);
        }
        if (isset($SQLEvent['event_alarm'])) {
            $this->alarm = (int)$SQLEvent['event_alarm'];
        }
        if (isset($SQLEvent['event_recurdays'])) {
            $this->recurData = (int)$SQLEvent['event_recurdays'];
        }

        $this->initialized = true;
        $this->stored = true;
    }

    function toDriver()
    {
        $driver = &$this->getDriver();

        // Basic fields.
        $this->_properties['event_creator_id'] = $driver->convertToDriver($this->getCreatorID());
        $this->_properties['event_title'] = $driver->convertToDriver($this->title);
        $this->_properties['event_description'] = $driver->convertToDriver($this->getDescription());
        $this->_properties['event_category'] = $driver->convertToDriver($this->getCategory());
        $this->_properties['event_location'] = $driver->convertToDriver($this->getLocation());
        $this->_properties['event_status'] = $this->getStatus();
        $this->_properties['event_attendees'] = $driver->convertToDriver(serialize($this->getAttendees()));
        $this->_properties['event_keywords'] = $driver->convertToDriver(implode(',', $this->getKeywords()));
        $this->_properties['event_exceptions'] = implode(',', $this->getExceptions());
        $this->_properties['event_modified'] = time();

        $this->_properties['event_start'] = date('Y-m-d H:i:s', $this->getStartTimestamp());

        // Event end.
        $this->_properties['event_end'] = date('Y-m-d H:i:s', $this->getEndTimestamp());

        // Alarm.
        $this->_properties['event_alarm'] = $this->getAlarm();

        // Recurrence.
        $recur_end = explode(':', @date('Y:n:j', $this->getRecurEndTimestamp()));
        if (empty($recur_end[0]) || $recur_end[0] <= 1970) {
            $recur_end[0] = 9999;
            $recur_end[1] = 12;
            $recur_end[2] = 31;
        }

        $recur = $this->getRecurType();
        $this->_properties['event_recurtype'] = $recur;
        if ($recur != KRONOLITH_RECUR_NONE) {
            $this->_properties['event_recurinterval'] = $this->getRecurInterval();
            $this->_properties['event_recurenddate'] = sprintf('%04d%02d%02d', $recur_end[0],
                                                               $recur_end[1], $recur_end[2]);

            switch ($recur) {
            case KRONOLITH_RECUR_WEEKLY:
                $this->_properties['event_recurdays'] = $this->getRecurOnDays();
                break;
            }
        }
    }

    function getProperties()
    {
        return $this->_properties;
    }

}
