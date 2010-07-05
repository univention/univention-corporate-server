<?php
/**
 * The Kronolith_Driver_sql:: class implements the Kronolith_Driver
 * API for a SQL backend.
 *
 * $Horde: kronolith/lib/Driver/sql.php,v 1.136.2.46 2009-11-11 07:59:18 jan Exp $
 *
 * @author  Luc Saillard <luc.saillard@fr.alcove.com>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 0.3
 * @package Kronolith
 */
class Kronolith_Driver_sql extends Kronolith_Driver {

    /**
     * The object handle for the current database connection.
     *
     * @var DB
     */
    var $_db;

    /**
     * Handle for the current database connection, used for writing. Defaults
     * to the same handle as $_db if a separate write database is not required.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * Cache events as we fetch them to avoid fetching the same event from the
     * DB twice.
     *
     * @var array
     */
    var $_cache = array();

    function listAlarms($date, $fullevent = false)
    {
        require_once 'Date/Calc.php';

        $allevents = $this->listEvents($date, null, true);
        if (is_a($allevents, 'PEAR_Error')) {
            return $allevents;
        }

        $events = array();
        foreach ($allevents as $eventId) {
            $event = &$this->getEvent($eventId);
            if (is_a($event, 'PEAR_Error')) {
                continue;
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
                    $diff = Date_Calc::dateDiff($event->start->mday,
                                                $event->start->month,
                                                $event->start->year,
                                                $event->end->mday,
                                                $event->end->month,
                                                $event->end->year);
                    if ($diff == -1) {
                        $diff = 0;
                    }
                    $end = new Horde_Date(array('year' => $next->year,
                                                'month' => $next->month,
                                                'mday' => $next->mday + $diff,
                                                'hour' => $event->end->hour,
                                                'min' => $event->end->min,
                                                'sec' => $event->end->sec));
                    $end->correct();
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

    function search($query)
    {
        require_once 'Horde/SQL.php';

        /* Build SQL conditions based on the query string. */
        $cond = '((';
        $values = array();

        if (!empty($query->title)) {
            $binds = Horde_SQL::buildClause($this->_db, 'event_title', 'LIKE', $this->convertToDriver($query->title), true);
            if (is_array($binds)) {
                $cond .= $binds[0] . ' AND ';
                $values = array_merge($values, $binds[1]);
            } else {
                $cond .= $binds;
            }
        }
        if (!empty($query->location)) {
            $binds = Horde_SQL::buildClause($this->_db, 'event_location', 'LIKE', $this->convertToDriver($query->location), true);
            if (is_array($binds)) {
                $cond .= $binds[0] . ' AND ';
                $values = array_merge($values, $binds[1]);
            } else {
                $cond .= $binds;
            }
        }
        if (!empty($query->description)) {
            $binds = Horde_SQL::buildClause($this->_db, 'event_description', 'LIKE', $this->convertToDriver($query->description), true);
            if (is_array($binds)) {
                $cond .= $binds[0] . ' AND ';
                $values = array_merge($values, $binds[1]);
            } else {
                $cond .= $binds;
            }
        }
        if (isset($query->category)) {
            $binds = Horde_SQL::buildClause($this->_db, 'event_category', '=', $this->convertToDriver($query->category), true);
            if (is_array($binds)) {
                $cond .= $binds[0] . ' AND ';
                $values = array_merge($values, $binds[1]);
            } else {
                $cond .= $binds;
            }
        }
        if (isset($query->status)) {
            $binds = Horde_SQL::buildClause($this->_db, 'event_status', '=', $query->status, true);
            if (is_array($binds)) {
                $cond .= $binds[0] . ' AND ';
                $values = array_merge($values, $binds[1]);
            } else {
                $cond .= $binds;
            }
        }

        if (!empty($query->creatorID)) {
            $binds = Horde_SQL::buildClause($this->_db, 'event_creator_id', '=', $query->creatorID, true);
            if (is_array($binds)) {
                $cond .= $binds[0] . ' AND ';
                $values = array_merge($values, $binds[1]);
            } else {
                $cond .= $binds;
            }
        }

        if ($cond == '((') {
            $cond = '';
        } else {
            $cond = substr($cond, 0, strlen($cond) - 5) . '))';
        }

        $eventIds = $this->listEventsConditional($query->start,
                                                 $query->end,
                                                 $cond,
                                                 $values);
        if (is_a($eventIds, 'PEAR_Error')) {
            return $eventIds;
        }

        $events = array();
        foreach ($eventIds as $eventId) {
            $event = &$this->getEvent($eventId);
            if (is_a($event, 'PEAR_Error')) {
                return $event;
            }
            $events[] = $event;
        }

        return $events;
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
        $query = 'SELECT event_id  FROM ' . $this->_params['table'] . ' WHERE event_uid = ?';
        $values = array($uid);

        if (!is_null($calendar_id)) {
            $query .= ' AND calendar_id = ?';
            $values[] = $calendar_id;
        }

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Kronolith_Driver_sql::exists(): user = "%s"; query = "%s"',
                                  Auth::getAuth(), $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $event = $this->_db->getRow($query, $values, DB_FETCHMODE_ASSOC);
        if (is_a($event, 'PEAR_Error')) {
            Horde::logMessage($event, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $event;
        }

        if ($event) {
            return $event['event_id'];
        } else {
            return false;
        }
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
        $endInterval = $startInterval = null;
        if (!empty($endDate)) {
            list($endInterval->mday, $endInterval->month, $endInterval->year) = explode('/', Date_Calc::nextDay($endDate->mday, $endDate->month, $endDate->year, '%d/%m/%Y'));
        }
        if (!empty($startDate)) {
            $startInterval = new Horde_Date($startDate);
            if ($startInterval->month == 0) {
                $startInterval->month = 1;
            }
            if ($startInterval->mday == 0) {
                $startInterval->mday = 1;
            }
        }

        return $this->listEventsConditional($startInterval, $endInterval,
                                            $hasAlarm ? 'event_alarm > ?' : '',
                                            $hasAlarm ? array(0) : array());
    }

    /**
     * Lists all events that satisfy the given conditions.
     *
     * @param Horde_Date $startInterval  Start of range date object.
     * @param Horde_Date $endInterval    End of range data object.
     * @param string $conditions         Conditions, given as SQL clauses.
     * @param array $vals                SQL bind variables for use with
     *                                   $conditions clauses.
     *
     * @return array  Events in the given time range satisfying the given
     *                conditions.
     */
    function listEventsConditional($startInterval = null, $endInterval = null,
                                   $conditions = '', $vals = array())
    {
        $q = 'SELECT event_id, event_uid, event_description, event_location,' .
            ' event_private, event_status, event_attendees,' .
            ' event_keywords, event_title, event_category, event_recurcount,' .
            ' event_recurtype, event_recurenddate, event_recurinterval,' .
            ' event_recurdays, event_start, event_end, event_alarm,' .
            ' event_modified, event_exceptions, event_creator_id' .
            ' FROM ' . $this->_params['table'] .
            ' WHERE calendar_id = ?';
        $values = array($this->_calendar);

        if ($conditions) {
            $q .= ' AND ' . $conditions;
            $values = array_merge($values, $vals);
        }

        if (!is_null($startInterval) && !is_null($endInterval)) {
            $endInterval = new Horde_Date(array('mday' => $endInterval->mday + 1,
                                                'month' => $endInterval->month,
                                                'year' => $endInterval->year));
            $endInterval->correct();
            $etime = sprintf('%04d-%02d-%02d 00:00:00', $endInterval->year, $endInterval->month, $endInterval->mday);
            $stime = sprintf('%04d-%02d-%02d 00:00:00', $startInterval->year, $startInterval->month, $startInterval->mday);
            $q .= ' AND ((event_end >= ? AND event_start <= ?) OR (event_recurenddate >= ? AND event_start <= ? AND event_recurtype <> ?))';
            array_push($values, $stime, $etime, $stime, $etime, HORDE_DATE_RECUR_NONE);
        } elseif (!is_null($startInterval)) {
            $stime = sprintf('%04d-%02d-%02d 00:00:00', $startInterval->year, $startInterval->month, $startInterval->mday);
            $q .= ' AND ((event_end >= ?) OR (event_recurenddate >= ? AND event_recurtype <> ?))';
            array_push($values, $stime, $stime, HORDE_DATE_RECUR_NONE);
        } elseif (!is_null($endInterval)) {
            $endInterval = new Horde_Date(array('mday' => $endInterval->mday + 1,
                                                'month' => $endInterval->month,
                                                'year' => $endInterval->year));
            $endInterval->correct();
            $q .= ' AND (event_start <= ?)';
            $values[] = sprintf('%04d-%02d-%02d 00:00:00', $endInterval->year, $endInterval->month, $endInterval->mday);
        }

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Kronolith_Driver_sql::listEventsConditional(): user = "%s"; query = "%s"; values = "%s"',
                                  Auth::getAuth(), $q, implode(',', $values)),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Run the query. */
        $qr = $this->_db->query($q, $values);
        if (is_a($qr, 'PEAR_Error')) {
            Horde::logMessage($qr, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $qr;
        }

        $events = array();
        $row = $qr->fetchRow(DB_FETCHMODE_ASSOC);
        while ($row && !is_a($row, 'PEAR_Error')) {
            /* If the event did not have a UID before, we need to give
             * it one. */
            if (empty($row['event_uid'])) {
                $row['event_uid'] = $this->generateUID();

                /* Save the new UID for data integrity. */
                $query = 'UPDATE ' . $this->_params['table'] . ' SET event_uid = ? WHERE event_id = ?';
                $values = array($row['event_uid'], $row['event_id']);

                /* Log the query at a DEBUG log level. */
                Horde::logMessage(sprintf('Kronolith_Driver_sql::listEventsConditional(): user = %s; query = "%s"; values = "%s"',
                                          Auth::getAuth(), $query, implode(',', $values)),
                                  __FILE__, __LINE__, PEAR_LOG_DEBUG);

                $result = $this->_write_db->query($query, $values);
                if (is_a($result, 'PEAR_Error')) {
                    Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                }
            }

            /* We have all the information we need to create an event
             * object for this event, so go ahead and cache it. */
            $this->_cache[$this->_calendar][$row['event_id']] = &new Kronolith_Event_sql($this, $row);
            if ($row['event_recurtype'] == HORDE_DATE_RECUR_NONE) {
                $events[$row['event_uid']] = $row['event_id'];
            } else {
                $next = $this->nextRecurrence($row['event_id'], $startInterval);
                if ($next &&
                    (is_null($endInterval) ||
                     $next->compareDate($endInterval) < 0)) {
                    $events[$row['event_uid']] = $row['event_id'];
                }
            }

            $row = $qr->fetchRow(DB_FETCHMODE_ASSOC);
        }

        return $events;
    }

    function &getEvent($eventId = null)
    {
        if (is_null($eventId)) {
            $event = &new Kronolith_Event_sql($this);
            return $event;
        }

        if (isset($this->_cache[$this->_calendar][$eventId])) {
            return $this->_cache[$this->_calendar][$eventId];
        }

        $query = 'SELECT event_id, event_uid, event_description,' .
            ' event_location, event_private, event_status, event_attendees,' .
            ' event_keywords, event_title, event_category, event_recurcount,' .
            ' event_recurtype, event_recurenddate, event_recurinterval,' .
            ' event_recurdays, event_start, event_end, event_alarm,' .
            ' event_modified, event_exceptions, event_creator_id' .
            ' FROM ' . $this->_params['table'] . ' WHERE event_id = ? AND calendar_id = ?';
        $values = array($eventId, $this->_calendar);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Kronolith_Driver_sql::getEvent(): user = "%s"; query = "%s"; values = "%s"',
                                  Auth::getAuth(), $query, implode(',', $values)),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $event = $this->_db->getRow($query, $values, DB_FETCHMODE_ASSOC);
        if (is_a($event, 'PEAR_Error')) {
            Horde::logMessage($event, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $event;
        }

        if ($event) {
            $this->_cache[$this->_calendar][$eventId] = &new Kronolith_Event_sql($this, $event);
            return $this->_cache[$this->_calendar][$eventId];
        } else {
            return PEAR::raiseError(_("Event not found"));
        }
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
        $query = 'SELECT event_id, event_uid, calendar_id, event_description,' .
            ' event_location, event_private, event_status, event_attendees,' .
            ' event_keywords, event_title, event_category, event_recurcount,' .
            ' event_recurtype, event_recurenddate, event_recurinterval,' .
            ' event_recurdays, event_start, event_end, event_alarm,' .
            ' event_modified, event_exceptions, event_creator_id' .
            ' FROM ' . $this->_params['table'] . ' WHERE event_uid = ?';
        $values = array($uid);

        /* Optionally filter by calendar */
        if (!is_null($calendars)) {
            if (!count($calendars)) {
                return PEAR::raiseError(_("No calendars to search"));
            }
            $query .= ' AND calendar_id IN (?' . str_repeat(', ?', count($calendars) - 1) . ')';
            $values = array_merge($values, $calendars);
        }

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Kronolith_Driver_sql::getByUID(): user = "%s"; query = "%s"; values = "%s"',
                                  Auth::getAuth(), $query, implode(',', $values)),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $events = $this->_db->getAll($query, $values, DB_FETCHMODE_ASSOC);
        if (is_a($events, 'PEAR_Error')) {
            Horde::logMessage($events, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $events;
        }
        if (!count($events)) {
            return PEAR::raiseError($uid . ' not found');
        }

        $eventArray = array();
        foreach ($events as $event) {
            $this->open($event['calendar_id']);
            $this->_cache[$this->_calendar][$event['event_id']] = &new Kronolith_Event_sql($this, $event);
            $eventArray[] = &$this->_cache[$this->_calendar][$event['event_id']];
        }

        if ($getAll) {
            return $eventArray;
        }

        /* First try the user's own calendars. */
        $ownerCalendars = Kronolith::listCalendars(true, PERMS_READ);
        $event = null;
        foreach ($eventArray as $ev) {
            if (isset($ownerCalendars[$ev->getCalendar()])) {
                $event = $ev;
                break;
            }
        }

        /* If not successful, try all calendars the user has access too. */
        if (empty($event)) {
            $readableCalendars = Kronolith::listCalendars(false, PERMS_READ);
            foreach ($eventArray as $ev) {
                if (isset($readableCalendars[$ev->getCalendar()])) {
                    $event = $ev;
                    break;
                }
            }
        }

        if (empty($event)) {
            $event = $eventArray[0];
        }

        return $event;
    }

    /**
     * Saves an event in the backend.
     * If it is a new event, it is added, otherwise the event is updated.
     *
     * @param Kronolith_Event $event  The event to save.
     */
    function saveEvent(&$event)
    {
        if ($event->isStored() || $event->exists()) {
            $values = array();

            $query = 'UPDATE ' . $this->_params['table'] . ' SET ';

            foreach ($event->getProperties() as $key => $val) {
                $query .= " $key = ?,";
                $values[] = $val;
            }
            $query = substr($query, 0, -1);
            $query .= ' WHERE event_id = ?';
            $values[] = $event->getId();

            /* Log the query at a DEBUG log level. */
            Horde::logMessage(sprintf('Kronolith_Driver_sql::saveEvent(): user = "%s"; query = "%s"; values = "%s"',
                                      Auth::getAuth(), $query, implode(',', $values)),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $result = $this->_write_db->query($query, $values);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            }

            /* Log the modification of this item in the history log. */
            if ($event->getUID()) {
                $history = &Horde_History::singleton();
                $history->log('kronolith:' . $this->_calendar . ':' . $event->getUID(), array('action' => 'modify'), true);
            }

            /* Notify users about the changed event. */
            $result = Kronolith::sendNotification($event, 'edit');
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            }

            return $event->getId();
        } else {
            if ($event->getId()) {
                $id = $event->getId();
            } else {
                $id = md5(uniqid(mt_rand(), true));
                $event->setId($id);
            }

            if ($event->getUID()) {
                $uid = $event->getUID();
            } else {
                $uid = $this->generateUID();
                $event->setUID($uid);
            }

            $query = 'INSERT INTO ' . $this->_params['table'];
            $cols_name = ' (event_id, event_uid,';
            $cols_values = ' VALUES (?, ?,';
            $values = array($id, $uid);

            foreach ($event->getProperties() as $key => $val) {
                $cols_name .= " $key,";
                $cols_values .= ' ?,';
                $values[] = $val;
            }

            $cols_name .= ' calendar_id)';
            $cols_values .= ' ?)';
            $values[] = $this->_calendar;

            $query .= $cols_name . $cols_values;

            /* Log the query at a DEBUG log level. */
            Horde::logMessage(sprintf('Kronolith_Driver_sql::saveEvent(): user = "%s"; query = "%s"; values = "%s"',
                                Auth::getAuth(), $query, implode(',', $values)),
                                __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $result = $this->_write_db->query($query, $values);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            }

            /* Log the creation of this item in the history log. */
            $history = &Horde_History::singleton();
            $history->log('kronolith:' . $this->_calendar . ':' . $uid, array('action' => 'add'), true);

            /* Notify users about the new event. */
            $result = Kronolith::sendNotification($event, 'add');
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            }

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
        /* Fetch the event for later use. */
        $event = &$this->getEvent($eventId);
        if (is_a($event, 'PEAR_Error')) {
            return $event;
        }

        $query = 'UPDATE ' . $this->_params['table'] . ' SET calendar_id = ? WHERE calendar_id = ? AND event_id = ?';
        $values = array($newCalendar, $this->_calendar, $eventId);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Kronolith_Driver_sql::move(): %s; values = "%s"',
                                  $query, implode(',', $values)),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Attempt the move query. */
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        /* Log the moving of this item in the history log. */
        $uid = $event->getUID();
        if ($uid) {
            $history = &Horde_History::singleton();
            $history->log('kronolith:' . $this->_calendar . ':' . $uid, array('action' => 'delete'), true);
            $history->log('kronolith:' . $newCalendar . ':' . $uid, array('action' => 'add'), true);
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
        $query = 'DELETE FROM ' . $this->_params['table'] . ' WHERE calendar_id = ?';
        $values = array($calendar);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Kronolith_Driver_sql::delete(): user = "%s"; query = "%s"; values = "%s"',
                                  Auth::getAuth(), $query, implode(',', $values)),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $this->_write_db->query($query, $values);
    }

    /**
     * Delete an event.
     *
     * @param string $eventId  The ID of the event to delete.
     * @param boolean $silent  Don't send notifications, used when deleting
     *                         events in bulk from maintenance tasks.
     *
     * @return mixed  True or a PEAR_Error on failure.
     */
    function deleteEvent($eventId, $silent = false)
    {
        /* Fetch the event for later use. */
        $event = &$this->getEvent($eventId);
        if (is_a($event, 'PEAR_Error')) {
            return $event;
        }

        $query = 'DELETE FROM ' . $this->_params['table'] . ' WHERE event_id = ? AND calendar_id = ?';
        $values = array($eventId, $this->_calendar);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Kronolith_Driver_sql::deleteEvent(): user = "%s"; query = "%s"; values = "%s"',
                                  Auth::getAuth(), $query, implode(',', $values)),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        /* Log the deletion of this item in the history log. */
        if ($event->getUID()) {
            $history = &Horde_History::singleton();
            $history->log('kronolith:' . $this->_calendar . ':' . $event->getUID(), array('action' => 'delete'), true);
        }

        /* Remove any pending alarms. */
        if (@include_once 'Horde/Alarm.php') {
            $alarm = Horde_Alarm::factory();
            $alarm->delete($event->getUID());
        }

        /* Notify about the deleted event. */
        if (!$silent) {
            $result = Kronolith::sendNotification($event, 'delete');
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }
        return true;
    }

    /**
     * Attempts to open a connection to the SQL server.
     *
     * @return boolean True.
     */
    function initialize()
    {
        Horde::assertDriverConfig($this->_params, 'calendar',
            array('phptype'));

        if (!isset($this->_params['database'])) {
            $this->_params['database'] = '';
        }
        if (!isset($this->_params['username'])) {
            $this->_params['username'] = '';
        }
        if (!isset($this->_params['hostspec'])) {
            $this->_params['hostspec'] = '';
        }
        if (!isset($this->_params['table'])) {
            $this->_params['table'] = 'kronolith_events';
        }

        /* Connect to the SQL server using the supplied parameters. */
        require_once 'DB.php';
        $this->_write_db = &DB::connect($this->_params,
                                        array('persistent' => !empty($this->_params['persistent']),
                                              'ssl' => !empty($this->_params['ssl'])));
        if (is_a($this->_write_db, 'PEAR_Error')) {
            return $this->_write_db;
        }
        $this->_initConn($this->_write_db);

        /* Check if we need to set up the read DB connection
         * seperately. */
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($this->_params, $this->_params['read']);
            $this->_db = &DB::connect($params,
                                      array('persistent' => !empty($params['persistent']),
                                            'ssl' => !empty($params['ssl'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                return $this->_db;
            }
            $this->_initConn($this->_db);
        } else {
            /* Default to the same DB handle for the writer too. */
            $this->_db = &$this->_write_db;
        }

        return true;
    }

    /**
     */
    function _initConn(&$db)
    {
        // Set DB portability options.
        switch ($db->phptype) {
        case 'mssql':
            $db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
            break;
        default:
            $db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
        }

        /* Handle any database specific initialization code to run. */
        switch ($db->dbsyntax) {
        case 'oci8':
            $query = "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'";

            /* Log the query at a DEBUG log level. */
            Horde::logMessage(sprintf('Kronolith_Driver_sql::_initConn(): user = "%s"; query = "%s"',
                                      Auth::getAuth(), $query),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $db->query($query);
            break;

        case 'pgsql':
            $query = "SET datestyle TO 'iso'";

            /* Log the query at a DEBUG log level. */
            Horde::logMessage(sprintf('Kronolith_Driver_sql::_initConn(): user = "%s"; query = "%s"',
                                      Auth::getAuth(), $query),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $db->query($query);
            break;
        }
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

    /**
     * Remove all events owned by the specified user in all calendars.
     *
     *
     * @param string $user  The user name to delete events for.
     *
     * @param mixed  True | PEAR_Error
     */
    function removeUserData($user)
    {
        if (!Auth::isAdmin()) {
            return PEAR::raiseError(_("Permission Denied"));
        }

        $shares = $GLOBALS['kronolith_shares']->listShares($user, PERMS_EDIT);
        if (is_a($shares, 'PEAR_Error')) {
            return $shares;
        }

        foreach (array_keys($shares) as $calendar) {
            $ids = Kronolith::listEventIds(null, null, $calendar);
            if (is_a($ids, 'PEAR_Error')) {
                return $ids;
            }
            $uids = array();
            foreach ($ids as $cal) {
                $uids = array_merge($uids, array_keys($cal));
            }

            foreach ($uids as $uid) {
                $event = $this->getByUID($uid);
                if (is_a($event, 'PEAR_Error')) {
                    return $event;
                }

                $this->deleteEvent($event->getId());
            }
        }
        return true;
    }
}

/**
 * @package Kronolith
 */
class Kronolith_Event_sql extends Kronolith_Event {

    /**
     * @var array
     */
    var $_properties = array();

    function fromDriver($SQLEvent)
    {
        $driver = &$this->getDriver();

        $this->start = new Horde_Date();
        $this->end = new Horde_Date();
        list($this->start->year, $this->start->month, $this->start->mday, $this->start->hour, $this->start->min, $this->start->sec) = sscanf($SQLEvent['event_start'], '%04d-%02d-%02d %02d:%02d:%02d');
        list($this->end->year, $this->end->month, $this->end->mday, $this->end->hour, $this->end->min, $this->end->sec) = sscanf($SQLEvent['event_end'], '%04d-%02d-%02d %02d:%02d:%02d');

        $this->durMin = ($this->end->timestamp() - $this->start->timestamp()) / 60;

        $this->title = $driver->convertFromDriver($SQLEvent['event_title']);
        $this->eventID = $SQLEvent['event_id'];
        $this->setUID($SQLEvent['event_uid']);
        $this->creatorID = $SQLEvent['event_creator_id'];

        if (!empty($SQLEvent['event_recurtype'])) {
            $this->recurrence = new Horde_Date_Recurrence($this->start);
            $this->recurrence->setRecurType((int)$SQLEvent['event_recurtype']);
            $this->recurrence->setRecurInterval((int)$SQLEvent['event_recurinterval']);
            if (isset($SQLEvent['event_recurenddate'])) {
                $recur_end = new Horde_Date();
                list($recur_end->year, $recur_end->month, $recur_end->mday) = sscanf($SQLEvent['event_recurenddate'], '%04d-%02d-%02d 00:00:00');
                $recur_end->hour = 23;
                $recur_end->min = 59;
                $recur_end->sec = 59;
                $this->recurrence->setRecurEnd($recur_end);
            }
            if (isset($SQLEvent['event_recurcount'])) {
                $this->recurrence->setRecurCount((int)$SQLEvent['event_recurcount']);
            }
            if (isset($SQLEvent['event_recurdays'])) {
                $this->recurrence->recurData = (int)$SQLEvent['event_recurdays'];
            }
            if (!empty($SQLEvent['event_exceptions'])) {
                $this->recurrence->exceptions = explode(',', $SQLEvent['event_exceptions']);
            }
        }

        if (isset($SQLEvent['event_category'])) {
            $this->category = $driver->convertFromDriver($SQLEvent['event_category']);
        }
        if (isset($SQLEvent['event_location'])) {
            $this->location = $driver->convertFromDriver($SQLEvent['event_location']);
        }
        if (isset($SQLEvent['event_private'])) {
            $this->private = !empty($SQLEvent['event_private']);
        }
        if (isset($SQLEvent['event_status'])) {
            $this->status = $SQLEvent['event_status'];
        }
        if (isset($SQLEvent['event_attendees'])) {
            $this->attendees = array_change_key_case($driver->convertFromDriver(unserialize($SQLEvent['event_attendees'])));
        }
        if (isset($SQLEvent['event_keywords'])) {
            $this->keywords = explode(',', $driver->convertFromDriver($SQLEvent['event_keywords']));
        }
        if (isset($SQLEvent['event_description'])) {
            $this->description = $driver->convertFromDriver($SQLEvent['event_description']);
        }
        if (isset($SQLEvent['event_alarm'])) {
            $this->alarm = (int)$SQLEvent['event_alarm'];
        }

        $this->initialized = true;
        $this->stored = true;
    }

    function toDriver()
    {
        $driver = &$this->getDriver();

        /* Basic fields. */
        $this->_properties['event_creator_id'] = $driver->convertToDriver($this->getCreatorId());
        $this->_properties['event_title'] = $driver->convertToDriver($this->title);
        $this->_properties['event_description'] = $driver->convertToDriver($this->getDescription());
        $this->_properties['event_category'] = $driver->convertToDriver((string)String::substr($this->getCategory(), 0, 80));
        $this->_properties['event_location'] = $driver->convertToDriver($this->getLocation());
        $this->_properties['event_private'] = (int)$this->isPrivate();
        $this->_properties['event_status'] = $this->getStatus();
        $this->_properties['event_attendees'] = serialize($driver->convertToDriver($this->getAttendees()));
        $this->_properties['event_keywords'] = $driver->convertToDriver(implode(',', $this->getKeywords()));
        $this->_properties['event_modified'] = $_SERVER['REQUEST_TIME'];

        $this->_properties['event_start'] = date('Y-m-d H:i:s', $this->start->timestamp());

        /* Event end. */
        $this->_properties['event_end'] = date('Y-m-d H:i:s', $this->end->timestamp());

        /* Alarm. */
        $this->_properties['event_alarm'] = (int)$this->getAlarm();

        /* Recurrence. */
        if (!$this->recurs()) {
            $this->_properties['event_recurtype'] = 0;
        } else {
            $recur = $this->recurrence->getRecurType();
            if ($this->recurrence->hasRecurEnd()) {
                $recur_end = explode(':', date('Y:n:j', $this->recurrence->recurEnd->timestamp()));
            } else {
                $recur_end = null;
            }
            if (empty($recur_end[0]) || $recur_end[0] <= 1970) {
                $recur_end[0] = 9999;
                $recur_end[1] = 12;
                $recur_end[2] = 31;
            }

            $this->_properties['event_recurtype'] = $recur;
            $this->_properties['event_recurinterval'] = $this->recurrence->getRecurInterval();
            $this->_properties['event_recurenddate'] = sprintf('%04d-%02d-%02d', $recur_end[0],
                                                               $recur_end[1], $recur_end[2]);
            $this->_properties['event_recurcount'] = $this->recurrence->getRecurCount();

            switch ($recur) {
            case HORDE_DATE_RECUR_WEEKLY:
                $this->_properties['event_recurdays'] = $this->recurrence->getRecurOnDays();
                break;
            }
            $this->_properties['event_exceptions'] = implode(',', $this->recurrence->getExceptions());
        }
    }

    function getProperties()
    {
        return $this->_properties;
    }

}
