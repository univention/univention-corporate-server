<?php

require_once KRONOLITH_BASE . '/lib/Driver.php';

define('KRONOLITH_RECUR_NONE',          0);
define('KRONOLITH_RECUR_DAILY',         1);
define('KRONOLITH_RECUR_WEEKLY',        2);
define('KRONOLITH_RECUR_DAY_OF_MONTH',  3);
define('KRONOLITH_RECUR_WEEK_OF_MONTH', 4);
define('KRONOLITH_RECUR_YEARLY',        5);

define('KRONOLITH_MONDAY',    0);
define('KRONOLITH_TUESDAY',   1);
define('KRONOLITH_WEDNESDAY', 2);
define('KRONOLITH_THURSDAY',  3);
define('KRONOLITH_FRIDAY',    4);
define('KRONOLITH_SATURDAY',  5);
define('KRONOLITH_SUNDAY',    6);

define('KRONOLITH_MASK_SUNDAY',    1);
define('KRONOLITH_MASK_MONDAY',    2);
define('KRONOLITH_MASK_TUESDAY',   4);
define('KRONOLITH_MASK_WEDNESDAY', 8);
define('KRONOLITH_MASK_THURSDAY',  16);
define('KRONOLITH_MASK_FRIDAY',    32);
define('KRONOLITH_MASK_SATURDAY',  64);
define('KRONOLITH_MASK_WEEKDAYS',  62);
define('KRONOLITH_MASK_WEEKEND',   65);
define('KRONOLITH_MASK_ALLDAYS',   127);

define('KRONOLITH_JANUARY',    1);
define('KRONOLITH_FEBRUARY',   2);
define('KRONOLITH_MARCH',      3);
define('KRONOLITH_APRIL',      4);
define('KRONOLITH_MAY',        5);
define('KRONOLITH_JUNE',       6);
define('KRONOLITH_JULY',       7);
define('KRONOLITH_AUGUST',     8);
define('KRONOLITH_SEPTEMBER',  9);
define('KRONOLITH_OCTOBER',   10);
define('KRONOLITH_NOVEMBER',  11);
define('KRONOLITH_DECEMBER',  12);

define('KRONOLITH_STATUS_NONE', 0);
define('KRONOLITH_STATUS_TENTATIVE', 1);
define('KRONOLITH_STATUS_CONFIRMED', 2);
define('KRONOLITH_STATUS_CANCELLED', 3);

define('KRONOLITH_RESPONSE_NONE',      1);
define('KRONOLITH_RESPONSE_ACCEPTED',  2);
define('KRONOLITH_RESPONSE_DECLINED',  3);
define('KRONOLITH_RESPONSE_TENTATIVE', 4);

define('KRONOLITH_PART_REQUIRED', 1);
define('KRONOLITH_PART_OPTIONAL', 2);
define('KRONOLITH_PART_NONE',     3);
define('KRONOLITH_PART_IGNORE',   4);

define('KRONOLITH_ACTIONID_ADD',       1);
define('KRONOLITH_ACTIONID_REMOVE',    2);
define('KRONOLITH_ACTIONID_CHANGEATT', 3);
define('KRONOLITH_ACTIONID_DISMISS',   4);
define('KRONOLITH_ACTIONID_SAVE',      5);
define('KRONOLITH_ACTIONID_CLEAR',     6);
define('KRONOLITH_ACTIONID_VIEW',      7);

define('KRONOLITH_ITIP_REQUEST', 1);
define('KRONOLITH_ITIP_CANCEL',  2);

define('KRONOLITH_ERROR_FB_NOT_FOUND', 1);

/**
 * The Kronolith:: class provides functionality common to all of
 * Kronolith.
 *
 * $Horde: kronolith/lib/Kronolith.php,v 1.216 2004/05/25 21:10:00 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith {

    function &dateObject($date = null)
    {
        if (is_a($date, 'Kronolith_Date')) {
            return $date;
        }
        return $ret = &new Kronolith_Date($date);
    }

    /**
     * Returns all the events that happen each day within a time period
     *
     * @param object $startDate    The start of the time range.
     * @param object $endDate      The end of the time range.
     * @param array  $calendars    The calendars to check for events.
     *
     * @return array  The events happening in this time period.
     */
    function listEventIds($startDate = null, $endDate = null, $calendars = null)
    {
        global $kronolith;

        if (!isset($startDate)) {
            $startDate = Kronolith::timestampToObject(time());
        } elseif (!is_object($startDate)) {
            $startDate = Kronolith::timestampToObject($startDate);
        }
        if (!isset($endDate)) {
            $endDate = Kronolith::timestampToObject(time());
        } elseif (!is_object($endDate)) {
            $endDate = Kronolith::timestampToObject($endDate);
        }
        if (!isset($calendars)) {
            $calendars = $GLOBALS['display_calendars'];
        }

        $eventIds = array();
        foreach ($calendars as $cal) {
            if ($kronolith->getCalendar() != $cal) {
                $kronolith->close();
                $kronolith->open($cal);
            }
            $eventIds[$cal] = $kronolith->listEvents($startDate, $endDate);
        }

        return $eventIds;
    }

    /**
     * Returns all the alarms active right on $date.
     *
     * @param object $date         The start of the time range.
     * @param array  $calendars    The calendars to check for events.
     *
     * @return array  The alarms active on $date.
     */
    function listAlarms($date, $calendars)
    {
        global $kronolith;

        $alarms = array();
        foreach ($calendars as $cal) {
            if ($kronolith->getCalendar() != $cal) {
                $kronolith->close();
                $kronolith->open($cal);
            }
            $alarms[$cal] = $kronolith->listAlarms($date);
        }

        return $alarms;
    }

    /**
     * Fetch a remote calendar into the session and return the data.
     *
     * @param string $url  The location of the remote calendar.
     *
     * @return mixed  Either the calendar data, or an error on failure.
     */
    function getRemoteCalendar($url)
    {
        if (empty($_SESSION['kronolith']['remote'][$url])) {
            $options['method'] = 'GET';
            $options['timeout'] = 5;
            $options['allowRedirects'] = true;

            require_once 'HTTP/Request.php';
            $http = &new HTTP_Request($url, $options);
            @$http->sendRequest();
            if ($http->getResponseCode() != 200) {
                Horde::logMessage(sprintf('Failed to retrieve remote calendar: url = "%s", status = %s',
                                          $url, $http->getResponseCode()), __FILE__, __LINE__, PEAR_LOG_ERR);
                return PEAR::raiseError(sprintf(_("Could not open %s."), $url));
            }
            $_SESSION['kronolith']['remote'][$url] = $http->getResponseBody();

            /* Log fetch at DEBUG level */
            Horde::logMessage(sprintf('Retrieved remote calendar for %s: url = "%s"',
                                      Auth::getAuth(), $url), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }

        return $_SESSION['kronolith']['remote'][$url];
    }

    /**
     * Returns all the events from a remote calendar.
     *
     * @param string $url       The url of the remote calendar.
     *
     */
    function listRemoteEvents($url)
    {
        global $kronolith;

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
                $event = &$kronolith->getEvent();
                $event->fromiCalendar($component);
                $event->remoteCal = $url;
                $event->eventIndex = $i;
                $events[] = $event;
            }
        }

        return $events;
    }

    /**
     * Returns an event object for an event on a remote calendar.
     *
     * This is kind of a temorary solution until we can have multiple
     * drivers in use at the same time.
     *
     * @param $url      The url of the remote calendar.
     * @param $eventId  The index of the event on the remote calenar.
     *
     * @return object Kronolith_Event   The event object.
     */
    function getRemoteEventObject($url, $eventId)
    {
        global $kronolith;

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
            $event = &$kronolith->getEvent();
            $event->fromiCalendar($components[$eventId]);
            $event->remoteCal = $url;
            $event->eventIndex = $eventId;

            return $event;
        }

        return false;
    }

    /**
     * Returns all the events that happen each day within a time period
     *
     * @param mixed   $startDate       The start of the time range. Either a unix
     *                                 timestamp, or a Kronolith date object.
     * @param mixed   $endDate         The end of the time range. Either a unix
     *                                 timestamp, or a Kronolith date object.
     * @param array   $calendars       The calendars to check for events.
     * @param boolean $showRecurrence  Return every instance of a recurring event?
     *                                 If false, will only return recurring events
     *                                 once inside the $startDate - $endDate range.
     *
     * @return array  The events happening in this time period.
     */
    function listEvents($startDate = null, $endDate = null, $calendars = null, $showRecurrence = true)
    {
        global $kronolith, $prefs, $registry;

        if (!isset($startDate)) {
            $startDate = Kronolith::timestampToObject(time());
        } elseif (!is_object($startDate)) {
            $startDate = Kronolith::timestampToObject($startDate);
        }
        if (!isset($endDate)) {
            $endDate = Kronolith::timestampToObject(time());
        } elseif (!is_object($endDate)) {
            $endDate = Kronolith::timestampToObject($endDate);
        }
        if (!isset($calendars)) {
            $calendars = $GLOBALS['display_calendars'];
        }

        $eventIds = Kronolith::listEventIds($startDate, $endDate, $calendars);

        $startOfPeriodTimestamp = mktime(0, 0, 0, $startDate->month, $startDate->mday, $startDate->year);
        $endOfPeriodTimestamp = mktime(23, 59, 59, $endDate->month, $endDate->mday, $endDate->year);
        $daysInPeriod = Date_Calc::dateDiff($startDate->mday, $startDate->month, $startDate->year, $endDate->mday, $endDate->month, $endDate->year);

        $results = array();
        foreach ($eventIds as $cal => $events) {
            if ($kronolith->getCalendar() != $cal) {
                $kronolith->close();
                $kronolith->open($cal);
            }
            foreach ($events as $id) {
                // We MUST fetch each event right before getting its
                // recurrences; this is due to the way MCAL
                // works. MCAL's nextRecurrence() function gives you
                // the next recurrence for the event most recently
                // fetched. So if you fetch all events and then loop
                // through them, every recurrence you get will be for
                // the last event that you fetched.
                $event = &$kronolith->getEvent($id);

                if (!$event->hasRecurType(KRONOLITH_RECUR_NONE) && $showRecurrence) {
                    /* Recurring Event */

                    if ($event->getStartTimestamp() < $startOfPeriodTimestamp) {
                        // The first time the event happens was before the
                        // period started. Start searching for recurrences
                        // from the start of the period.
                        $next = array('year' => $startDate->year, 'month' => $startDate->month, 'mday' => $startDate->mday);
                    } else {
                        // The first time the event happens is in the
                        // range; unless there is an exception for
                        // this ocurrence, add it.
                        if (!$event->hasException($event->getStartDate('Y'),
                                                  $event->getStartDate('n'),
                                                  $event->getStartDate('j'))) {
                            $results[$event->getStartDatestamp()][$id] = $event;
                        }

                        // Start searching for recurrences from the day
                        // after it starts.
                        $next = array('year' => $event->getStartDate('Y'), 'month' => $event->getStartDate('n'), 'mday' => $event->getStartDate('j') + 1);
                    }

                    // Add all recurences of the event.
                    $next = $event->nextRecurrence($next);
                    while ($next !== false && (Kronolith::compareDates($next, $endDate) <= 0)) {
                        if (!$event->hasException($next->year, $next->month, $next->mday)) {
                            $results[Kronolith::objectToDatestamp($next)][$id] = $event;
                        }
                        $next = $event->nextRecurrence(array('year' => $next->year,
                                                             'month' => $next->month,
                                                             'mday' => $next->mday + 1,
                                                             'hour' => $next->hour,
                                                             'min' => $next->min,
                                                             'sec' => $next->sec));
                    }
                } else {
                    /* Event only occurs once. */

                    // Work out what day it starts on.
                    if ($event->getStartTimestamp() < $startOfPeriodTimestamp) {
                        // It started before the beginning of the period.
                        $eventStartStamp = $startOfPeriodTimestamp;
                    } else {
                        $eventStartStamp = $event->getStartTimestamp();
                    }

                    // Work out what day it ends on.
                    if ($event->getEndTimestamp() >= $endOfPeriodTimestamp) {
                        // Ends after the end of the period.
                        $eventEndStamp = $endOfPeriodTimestamp;
                    } else {
                        // If the event doesn't end at 12am set the
                        // end date to the current end date. If it
                        // ends at 12am and does not end at the same
                        // time that it starts (0 duration), set the
                        // end date to the previous day's end date.
                        if ($event->getEndDate('G') != 0 ||
                            $event->getEndDate('i') != 0 ||
                            $event->getStartTimestamp() == $event->getEndTimestamp()) {
                            $eventEndStamp = $event->getEndTimestamp();
                        } else {
                            $eventEndStamp = mktime(23, 59, 59,
                                                    $event->getEndDate('n'),
                                                    $event->getEndDate('j') - 1,
                                                    $event->getEndDate('Y'));
                        }
                    }

                    // Add the event to all the days it covers.
                    $i = date('j', $eventStartStamp);
                    $loopStamp = mktime(0, 0, 0,
                                        date('n', $eventStartStamp),
                                        $i,
                                        date('Y', $eventStartStamp));
                    while ($loopStamp <= $eventEndStamp) {
                        if (!($event->isAllDay() && $loopStamp == $eventEndStamp)) {
                            $results[$loopStamp][$id] = $event;
                        }
                        $loopStamp = mktime(0, 0, 0,
                                            date('n', $eventStartStamp),
                                            ++$i,
                                            date('Y', $eventStartStamp));
                    }
                }
            }
        }

        /* Nag Tasks. */
        if ($prefs->getValue('show_tasks') && $registry->hasMethod('tasks/listTasks')) {
            $taskList = $registry->call('tasks/listTasks');
            $dueEndStamp = mktime(0, 0, 0, $endDate->month, $endDate->mday + 1, $endDate->year);
            if (!is_a($taskList, 'PEAR_Error')) {
                $kronolith->open(Kronolith::getDefaultCalendar(PERMS_SHOW));
                foreach ($taskList as $task) {
                    if ($task['due'] >= $startOfPeriodTimestamp && $task['due'] < $dueEndStamp) {
                        $event = &$kronolith->getEvent();
                        $event->setTitle(sprintf(_("Due: %s"), $task['name']));
                        $event->taskID = $task['task_id'];
                        $event->tasklistID = $task['tasklist_id'];
                        $event->setStartTimestamp($task['due']);
                        $event->setEndTimestamp($task['due'] + 1);
                        $dayStamp = mktime(0, 0, 0,
                                           date('n', $task['due']),
                                           date('j', $task['due']),
                                           date('Y', $task['due']));
                        $results[$dayStamp]['_task' . $task['task_id']] = $event;
                    }
                }
            }
        }

        /* Remote Calendars. */
        foreach ($GLOBALS['display_remote_calendars'] as $url) {
            $events = Kronolith::listRemoteEvents($url);
            if (!is_a($events, 'PEAR_Error')) {
                $kronolith->open(Kronolith::getDefaultCalendar(PERMS_SHOW));
                foreach ($events as $event) {
                    // Event is not in period.
                    if ($event->getEndTimestamp() < $startOfPeriodTimestamp ||
                        $event->getStartTimestamp() > $endOfPeriodTimestamp) {
                        continue;
                    }

                    // Work out what day it starts on.
                    if ($event->getStartTimestamp() < $startOfPeriodTimestamp) {
                        // It started before the beginning of the
                        // period.
                        $eventStartDay = date('j', $startOfPeriodTimestamp);
                    } else {
                        $eventStartDay = $event->getStartDate('j');
                    }

                    // Work out what day it ends on.
                    if ($event->getEndTimestamp() >= $endOfPeriodTimestamp) {
                        // Ends after the end of the period.
                        $eventEndDay = date('j', $endOfPeriodTimestamp);
                    } else {
                        // If the event doesn't end at 12am set the
                        // end date to the current end date. If it
                        // ends at 12am set the end date to the
                        // previous days end date.
                        if ($event->getEndDate('G') != 0 ||
                            $event->getEndDate('i') != 0) {
                            $eventEndDay = $event->getEndDate('j');
                        } else {
                            $eventEndDay = $event->getEndDate('j') - 1;
                        }
                    }

                    // Add the event to all the days it covers.  TODO:
                    // this needs to handle the month (or year)
                    // wrapping.
                    for ($i = $eventStartDay; $i <= $eventEndDay; $i++) {
                        $dayStamp = mktime(0, 0, 0,
                                           $event->getStartDate('n'),
                                           $i,
                                           $event->getStartDate('Y'));

                        $results[$dayStamp]['_remote' . $url . $startOfPeriodTimestamp . $i] = $event;
                    }
                }
            }
        }

        foreach ($results as $day => $devents) {
            if (count($devents)) {
                uasort($devents, array('Kronolith', '_sortEventStartTime'));
                $results[$day] = $devents;
            }
        }

        return $results;
    }

    /**
     * Maps a Kronolith recurrence value to a translated string
     * suitable for display.
     *
     * @param integer $type   The recurrence value; one of the
     *                        KRONOLITH_RECUR_XXX constants.
     *
     * @return string   The translated displayable recurrence value string.
     */
    function recurToString($type)
    {
        switch ($type) {
        case KRONOLITH_RECUR_NONE:
            return _("Does not recur");

        case KRONOLITH_RECUR_DAILY:
            return _("Recurs daily");

        case KRONOLITH_RECUR_WEEKLY:
            return _("Recurs weekly");

        case KRONOLITH_RECUR_DAY_OF_MONTH:
        case KRONOLITH_RECUR_WEEK_OF_MONTH:
            return _("Recurs monthly");

        case KRONOLITH_RECUR_YEARLY:
            return _("Recurs yearly");
        }
    }

    /**
     * Maps a Kronolith meeting status string to a translated string
     * suitable for display.
     *
     * @param integer $status   The meeting status; one of the
     *                          KRONOLITH_STATUS_XXX constants.
     *
     * @return string   The translated displayable meeting status string.
     */
    function statusToString($status)
    {
        switch ($status) {
        case KRONOLITH_STATUS_CONFIRMED:
            return _("Confirmed");

        case KRONOLITH_STATUS_CANCELLED:
            return _("Cancelled");

        case KRONOLITH_STATUS_TENTATIVE:
        default:
            return _("Tentative");
        }
    }

    /**
     * Maps a Kronolith attendee response string to a translated
     * string suitable for display.
     *
     * @param integer $response  The attendee response; one of the
     *                           KRONOLITH_RESPONSE_XXX constants.
     *
     * @return string   The translated displayable attendee response string.
     */
    function responseToString($response)
    {
        switch ($response) {
        case KRONOLITH_RESPONSE_ACCEPTED:
            return _("Accepted");

        case KRONOLITH_RESPONSE_DECLINED:
            return _("Declined");

        case KRONOLITH_RESPONSE_TENTATIVE:
            return _("Tentative");

        case KRONOLITH_RESPONSE_NONE:
        default:
            return _("None");
        }
    }

    /**
     * Maps a Kronolith attendee participation string to a translated
     * string suitable for display.
     *
     * @param integer $part     The attendee participation; one of the
     *                          KRONOLITH_PART_XXX constants.
     *
     * @return string   The translated displayable attendee participation string.
     */
    function partToString($part)
    {
        switch ($part) {
        case KRONOLITH_PART_OPTIONAL:
            return _("Optional");

        case KRONOLITH_PART_NONE:
            return _("None");

        case KRONOLITH_PART_REQUIRED:
        default:
            return _("Required");
        }
    }

    /**
     * Maps an iCalendar attendee response string to the corresponding
     * Kronolith value.
     *
     * @param string $response   The attendee response.
     *
     * @return string   The Kronolith response value.
     */
    function responseFromICal($response)
    {
        switch (String::upper($response)) {
        case 'ACCEPTED':
            return KRONOLITH_RESPONSE_ACCEPTED;

        case 'DECLINED':
            return KRONOLITH_RESPONSE_DECLINED;

        case 'TENTATIVE':
            return KRONOLITH_RESPONSE_TENTATIVE;

        case 'NEEDS-ACTION':
        default:
            return KRONOLITH_RESPONSE_NONE;
        }
    }

    /**
     * Return the day of the week (0 = Monday, 6 = Sunday) of the
     * specified date.
     *
     * @param integer $day
     * @param integer $month
     * @param integer $year
     *
     * @return integer  The day of the week.
     */
    function dayOfWeek($day = null, $month = null, $year = null)
    {
        $day = (int)Date_Calc::dayOfWeek($day, $month, $year);
        $weekday_number = (($day - 7 * floor($day / 7))) - 1;
        if ($weekday_number == -1) {
            // Wrap check.
            $weekday_number = 6;
        }

        return $weekday_number;
    }

    /**
     * Returns week of the year, first Monday is first day of first
     * week.
     *
     * @param optional string $day    in format DD
     * @param optional string $month  in format MM
     * @param optional string $year   in format CCYY
     *
     * @return integer $week_number
     */
    function weekOfYear($day = null, $month = null, $year = null)
    {
        global $prefs;

        if (!isset($year)) $year = date('Y');
        if (!isset($month)) $month = date('n');
        if (!isset($day)) $day = date('j');
        if (!$prefs->getValue('week_start_monday') && Kronolith::dayOfWeek($day, $month, $year) == KRONOLITH_SUNDAY) {
            $day++;
        }

        $dayOfYear = 0;
        for ($i = 1; $i < $month; $i++) {
            $dayOfYear += Date_Calc::daysInMonth($i, $year);
        }
        $dayOfYear += $day;

        $dayOfWeek = Kronolith::dayOfWeek($day, $month, $year);
        $dayOfWeekJan1 = Kronolith::dayOfWeek(1, 1, $year);

        if ($dayOfYear <= 7 - $dayOfWeekJan1 && $dayOfWeekJan1 > 3 ) {
            if ($dayOfWeekJan1 == 4 || ($dayOfWeekJan1 == 5 && Kronolith::isLeapYear($year - 1))) {
                return '53';
            } else {
                return '52';
            }
        }

        if (Kronolith::isLeapYear($year)) {
            $daysInYear = 366;
        } else {
            $daysInYear = 365;
        }

        if ($daysInYear - $dayOfYear < 3 - $dayOfWeek) {
            return 1;
        }

        $WeekNumber = floor(($dayOfYear + (6 - $dayOfWeek) + $dayOfWeekJan1) / 7);
        if ($dayOfWeekJan1 > 3) {
            $WeekNumber -= 1;
        }

        return $WeekNumber;
    }

    /**
     * Return the number of weeks in the given year (52 or 53).
     *
     * @param optional integer $year  The year to count the number of weeks in.
     *
     * @return integer $numWeeks      The number of weeks in $year.
     */
    function weeksInYear($year = null)
    {
        if (!isset($year)) {
            $year = date('Y');
        }

        // Find the last Thursday of the year.
        $day = 31;
        while (date('w', mktime(0, 0, 0, 12, $day, $year)) != 4) {
            $day--;
        }
        return Kronolith::weekOfYear($day, 12, $year);
    }

    /**
     * Returns the day of the year (1-366) that corresponds to the
     * first day of the given week.
     *
     * @param integer $week  The week of the year to find the first day of.
     *
     * @return integer  The day of the year of the first day of the given week.
     */
    function firstDayOfWeek($week = null, $year = null)
    {
        if (!isset($year)) $year = date('Y');
        if (!isset($week)) $week = Kronolith::weekOfYear(null, null, $year);

        $start = Kronolith::dayOfWeek(1, 1, $year);
        if ($start > 3) {
            $start -= 7;
        }
        return ((($week * 7) - (7 + $start)) + 1);
    }

    function isLeapYear($year = null)
    {
        if (!isset($year)) {
            $year = date('Y');
        } elseif (strlen($year) != 4 || preg_match('/\D/', $year)) {
            return false;
        }

        return (($year % 4 == 0 && $year % 100 != 0) || $year % 400 == 0);
    }

    /**
     * Compare two date objects to see which one is greater
     * (later). Assumes that the dates are in the same timezone.
     *
     * @param mixed $first   The 1st date to compare.
     * @param mixed $second  The 2nd date to compare.
     *
     * @return integer  ==  0 if the dates are equal
     *                  >=  1 if $first is greater (later)
     *                  <= -1 if $second is greater (later)
     */
    function compareDates($first, $second)
    {
        $first = Kronolith::dateObject($first);
        $second = Kronolith::dateObject($second);

        if ($first->year != $second->year) {
            return $first->year - $second->year;
        } elseif ($first->month != $second->month) {
            return $first->month - $second->month;
        } else {
            return $first->mday - $second->mday;
        }
    }

    /**
     * Compare two date objects, including times, to see which one is
     * greater (later). Assumes that the dates are in the same
     * timezone.
     *
     * @param mixed $first   The 1st date to compare.
     * @param mixed $second  The 2nd date to compare.
     *
     * @return integer  ==  0 if the dates are equal
     *                  >=  1 if $first is greater (later)
     *                  <= -1 if $second is greater (later)
     */
    function compareDateTimes($first, $second)
    {
        $first = Kronolith::dateObject($first);
        $second = Kronolith::dateObject($second);

        if ($diff = Kronolith::compareDates($first, $second)) {
            return $diff;
        } elseif ($first->hour != $second->hour) {
            return $first->hour - $second->hour;
        } elseif ($first->min != $second->min) {
            return $first->min - $second->min;
        } else {
            return $first->sec - $second->sec;
        }
    }

    function &timestampToObject($timestamp)
    {
        $date = &new Kronolith_Date();
        list($date->hour, $date->min, $date->sec, $date->mday, $date->month, $date->year) = explode('/', date('H/i/s/j/n/Y', $timestamp));
        return $date;
    }

    function objectToTimestamp($obj)
    {
        return @mktime($obj->hour, $obj->min, $obj->sec, $obj->month, $obj->mday, $obj->year);
    }

    function objectToDatestamp($obj)
    {
        return @mktime(0, 0, 0, $obj->month, $obj->mday, $obj->year);
    }

    /**
     * Builds the HTML for an event status widget.
     *
     * @param string  $name     The name of the widget.
     * @param string  $current  (optional) The selected status value.
     *
     * @return string       The HTML <select> widget.
     */
    function buildStatusWidget($name, $current = KRONOLITH_STATUS_TENTATIVE)
    {
        $html = "<select id=\"$name\" name=\"$name\">";

        $statii = array(
            KRONOLITH_STATUS_TENTATIVE,
            KRONOLITH_STATUS_CONFIRMED,
            KRONOLITH_STATUS_CANCELLED
        );

        foreach ($statii as $status) {
            $html .= "<option value=\"$status\"";
            $html .= ($status == $current) ? ' selected="selected">' : '>';
            $html .= Kronolith::statusToString($status) . "</option>\n";
        }
        $html .= '</select>';

        return $html;
    }

    /**
     * List all calendars a user has access to, according to several
     * parameters/permission levels.
     *
     * @param optional boolean $owneronly  Only return calenders that this
     *                                     user owns? Defaults to false.
     * @param optional integer $permission The permission to filter calendars by.
     *
     * @return array  The calendar list.
     */
    function listCalendars($owneronly = false, $permission = PERMS_SHOW)
    {
        $calendars = $GLOBALS['kronolith_shares']->listShares(Auth::getAuth(), $permission, $owneronly);
        if (is_a($calendars, 'PEAR_Error')) {
            Horde::logMessage($calendars, __FILE__, __LINE__, PEAR_LOG_ERR);
            return array();
        }

        return $calendars;
    }

    /**
     * Get the default calendar for the current user at the specified
     * permissions level.
     */
    function getDefaultCalendar($permission = PERMS_SHOW)
    {
        global $prefs;

        $default_share = $prefs->getValue('default_share');
        $calendars = Kronolith::listCalendars(false, $permission);

        if (isset($calendars[$default_share])) {
            return $default_share;
        } elseif ($prefs->isLocked('default_share')) {
            return '';
        } elseif (count($calendars)) {
            return array_shift($calendars);
        }

        return false;
    }

    /**
     * Calculate the border (darker) version of a color.
     *
     * @param string $color   An HTML color, e.g.: ffffcc.
     *
     * @return string  A darker html color.
     */
    function borderColor($color)
    {
        return Horde_Image::modifyColor($color, -0x44);
    }

    /**
     * Calculate the highlight (lighter) version of a color.
     *
     * @param string $color   An HTML color, e.g.: ffffcc.
     *
     * @return string  A lighter html color.
     */
    function highlightColor($color)
    {
        return Horde_Image::modifyColor($color, 0x44);
    }

    /**
     * Generate the free/busy text for $calendar. Cache it for at
     * least an hour, as well.
     *
     * @access public
     *
     * @param string  $calendar    The calendar to view free/busy slots for.
     * @param integer $startstamp  The start of the time period to retrieve.
     * @param integer $endstamp    The end of the time period to retrieve.
     * @param boolean $returnObj   (optional) Default false. Return a vFreebusy
     *                             object instead of text.
     *
     * @return string  The free/busy text.
     */
    function generateFreeBusy($calendar, $startstamp = null, $endstamp = null, $returnObj = false)
    {
        global $kronolith_shares, $prefs;

        require_once 'Horde/Identity.php';
        require_once 'Horde/iCalendar.php';
        require_once KRONOLITH_BASE . '/lib/version.php';

        // Fetch the appropriate share and check permissions.
        $share = &$kronolith_shares->getShare($calendar);
        if (is_a($share, 'PEAR_Error')) {
            return '';
        }

        // Default the start date to today.
        if (is_null($startstamp)) {
            $month = date('n');
            $year = date('Y');
            $day = date('j');

            $startstamp = mktime(0, 0, 0, $month, $day, $year);
        }

        // Default the end date to the start date + freebusy_days.
        if (is_null($endstamp) || $endstamp < $startstamp) {
            $month = date('n', $startstamp);
            $year = date('Y', $startstamp);
            $day = date('j', $startstamp);

            $endstamp = mktime(0, 0, 0, $month,
                               $day + $prefs->getValue('freebusy_days'), $year);
        }

        // Get the Identity for the owner of the share.
        $identity = &Identity::singleton('none', $share->get('owner'));
        $email = $identity->getValue('from_addr');
        $cn = $identity->getValue('fullname');

        // Fetch events.
        $startDate = Kronolith::timestampToObject($startstamp);
        $endDate = Kronolith::timestampToObject($endstamp);
        $busy = Kronolith::listEvents($startDate, $endDate, array($calendar));

        // Create the new iCalendar.
        $vCal = &new Horde_iCalendar();
        $vCal->setAttribute('PRODID', '-//The Horde Project//Kronolith ' . KRONOLITH_VERSION . '//EN');
        $vCal->setAttribute('METHOD', 'PUBLISH');

        // Create new vFreebusy.
        $vFb = &Horde_iCalendar::newComponent('vfreebusy', $vCal);
        $params = array();
        if (!empty($cn)) {
            $params['CN'] = $cn;
        }
        if (!empty($email)) {
            $vFb->setAttribute('ORGANIZER', 'MAILTO:' . $email, $params);
        } else {
            $vFb->setAttribute('ORGANIZER', '', $params);
        }

        $vFb->setAttribute('DTSTAMP', time());
        $vFb->setAttribute('DTSTART', $startDate);
        $vFb->setAttribute('DTEND', $endDate);
        $vFb->setAttribute('URL', Horde::applicationUrl('fb.php?c=' . $calendar, true, -1));

        // Add all the busy periods.
        foreach ($busy as $day => $events) {
            foreach ($events as $event) {
                $start = $event->getStartTimestamp();
                $end = $event->getEndTimestamp();
                $duration = $end - $start;

                // Make sure that we're using the current date for
                // recurring events.
                if (!$event->hasRecurType(KRONOLITH_RECUR_NONE)) {
                    $startThisDay = mktime($event->getStartDate('G'),
                                           $event->getStartDate('i'),
                                           $event->getStartDate('s'),
                                           date('n', $day),
                                           date('j', $day),
                                           date('Y', $day));
                } else {
                    $startThisDay = $event->getStartTimestamp();
                }
                $vFb->addBusyPeriod('BUSY', $startThisDay, null, $duration);
            }
        }

        // Remove the overlaps.
        $vFb->simplify();
        $vCal->addComponent($vFb);

        // Return the vFreebusy object if requested.
        if ($returnObj) {
            return $vFb;
        }

        // Generate the vCal file.
        return $vCal->exportvCalendar();
    }

    /**
     * Retrieves the free/busy information for a given email address,
     * if any information is available.
     *
     * @params String   $email  The email address to look for.
     *
     * @return resource   Horde_iCalendar_vfreebusy on success
     *                    PEAR_Error on failure
     */
    function getFreeBusy($email)
    {
        global $prefs;

        require_once 'Horde/iCalendar.php';
        require_once 'Mail/RFC822.php';
        require_once 'Horde/MIME.php';

        // Properly handle RFC822-compliant email addresses.
        static $rfc822;
        if (is_null($rfc822)) {
            $rfc822 = &new Mail_RFC822();
        }

        $res = $rfc822->parseAddressList($email);
        if (is_a('PEAR_Error', $res)) {
            return $res;
        }
        if (!count($res)) {
            return PEAR::raiseError(_("No valid email address found"));
        }

        $email = MIME::rfc822WriteAddress($res[0]->mailbox, $res[0]->host);

        // Check if we can retrieve a VFB from the Free/Busy URL, if
        // one is set.
        $url = Kronolith::getFreeBusyUrl($email);
        if ($url !== false) {
            $lines = file($url);

            if ($lines !== false) {
                $data = implode('', $lines);
                $vCal = &new Horde_iCalendar();
                $vCal->parsevCalendar($data);

                $vFb = &$vCal->findComponent('VFREEBUSY');
                if ($vFb !== false) {
                    return $vFb;
                }
            }
        }

        // Check storage driver.
        global $conf;
        require_once KRONOLITH_BASE . '/lib/Storage.php';
        $storage = &Kronolith_Storage::singleton();

        $res = $storage->search($email);
        if (!is_a($res, 'PEAR_Error') ||
            !PEAR::isError($res, KRONOLITH_ERROR_FB_NOT_FOUND)) {
            return $res;
        }

        // Or else return an empty VFB object
        $vCal = &new Horde_iCalendar();
        $vFb = &Horde_iCalendar::newComponent('vfreebusy', $vCal);
        $vFb->setAttribute('ORGANIZER', $email);

        return $vFb;
    }

    /**
     * Search address books for the freebusy URL for a given email
     * address.
     *
     * @params String   $email  The email address to look for.
     *
     * @return Mixed    (string) The url on success
     *                  (boolean) False on failure
     */
    function getFreeBusyUrl($email)
    {
        global $registry;

        /* Get the list of address books through the API. */
        $source_list = $registry->call('contacts/sources');
        if (is_a($source_list, 'PEAR_Error')) {
            return false;
        }

        /* Try retrieving by e-mail only first. */
        $result = $registry->call('contacts/getField', array($email, 'freebusyUrl', array_keys($source_list)));
        if (is_a($result, 'PEAR_Error')) {
            return false;
        }

        return $result;
    }

    /**
     * Sends out iTip event notifications to all attendees of a specific
     * event. Can be used to send event invitations, event updates as well
     * as event cancellations.
     *
     * @params object   $event         The event in question.
     * @params object   $notification  A notification object used to show
     *                                 result status.
     * @params integer  $action        The type of notification to send.
     *                                 One of the KRONOLITH_ITIP_XXX values.
     */
    function sendITipNotifications(&$event, &$notification, $action)
    {
        require_once 'Horde/Identity.php';
        $ident = &Identity::singleton();

        $myemail = $ident->getValue('from_addr');
        if (empty($myemail)) {
            $notification->push(_("You do not have an email address configured in your identity preferences. You must set one before event notifications can be sent."), 'horde.error');
            return;
        }

        require_once 'Horde/Text.php';
        require_once 'Horde/MIME.php';
        require_once 'Horde/MIME/Headers.php';
        require_once 'Horde/MIME/Message.php';

        list($mailbox, $host) = preg_split('/@/', $myemail);
        $from = MIME::rfc822WriteAddress($mailbox, $host, $ident->getValue('fullname'));

        $attendees = $event->getAttendees();
        foreach ($attendees as $email => $status) {
            // Don't bother sending an invitation/update if the recipient
            // does not need to participate, or has declined participating
            if ($status['attendance'] == KRONOLITH_PART_NONE ||
                $status['response'] == KRONOLITH_RESPONSE_DECLINED) continue;

            // Determine all notification-specific strings.
            switch ($action) {
            case KRONOLITH_ITIP_CANCEL:
                // Cancellation
                $method = 'CANCEL';
                $filename = 'event-cancellation.ics';
                $subject = sprintf(_("Cancelled: %s"), $event->getTitle()) . "\n\n";
                break;

            case KRONOLITH_ITIP_REQUEST:
            default:
                $method = 'REQUEST';
                if ($status['response'] == KRONOLITH_RESPONSE_NONE) {
                    // Invitation
                    $filename = 'event-invitation.ics';
                    $subject = $event->getTitle();
                } else {
                    // Update
                    $filename = 'event-update.ics';
                    $subject = sprintf(_("Updated: %s."), $event->getTitle()) . "\n\n";
                }
                break;
            }

            $message = $subject;

            if ($event->getDescription() != '') {
                $message .= _("The following is a more detailed description of the event:") . "\n\n" . $event->getDescription() . "\n\n";
            }
            $message .= _("Attached is an iCalendar file with more information about the event. If your mail client supports iTip requests you can use this file to easily update your local copy of the event.");

            $mime = &new MIME_Message();
            $body = &new MIME_Part('text/plain', Text::wrap($message, 80, "\n"));

            require_once 'Horde/Data.php';
            $vcs = &Horde_Data::singleton('icalendar');
            $ics = &new MIME_Part(
                'text/calendar',
                $vcs->exportData(array($event->toiCalendar($vcs, $ident)), $method)
            );
            $ics->setName($filename);
            $ics->setContentTypeParameter('METHOD', $method);

            $mime->addPart($body);
            $mime->addPart($ics);

            // Build the notification headers.
            $msg_headers = &new MIME_Headers();
            $msg_headers->addReceivedHeader();
            $msg_headers->addMessageIdHeader();
            $msg_headers->addHeader('Date', date('r'));
            $msg_headers->addHeader('From', $from);
            $msg_headers->addHeader('To', $email);
            $msg_headers->addHeader('Subject', $subject);
            $msg_headers->addHeader('User-Agent', 'Kronolith Calendaring System');
            $msg_headers->addMIMEHeaders($mime);

            $status = $mime->send($email, $msg_headers);
            if (!is_a($status, 'PEAR_Error')) {
                $notification->push(
                    sprintf(_("The event notification to %s was successfully sent."), $email),
                    'horde.success'
                );
            } else {
                $notification->push(
                    sprintf(_("There was an error sending an event notification to %s: %s"), $email, $status->getMessage()),
                    'horde.error'
                );
            }
        }
    }

    function menu()
    {
        global $conf, $notification, $kronolith, $registry, $kronolith_shares,
            $prefs, $browser, $display_calendars,
            $display_remote_calendars, $print_link;
        require_once 'Horde/Menu.php';

        $timestamp = Util::getFormData('timestamp');
        if (!$timestamp) {
            $year = Util::getFormData('year', date('Y'));
            $month = Util::getFormData('month', date('n'));
            $day = Util::getFormData('mday', date('d'));
            if ($week = Util::getFormData('week')) {
                $month = 1;
                $day = Kronolith::firstDayOfWeek($week, $year);
            }
            $hour = date('H');
            $min = date('i');
            $timestamp = mktime(0, 0, 0, $month, $day, $year);
        }
        $append = "?timestamp=$timestamp";

        $remote_calendars = unserialize($prefs->getValue('remote_cals'));
        $current_user = Auth::getAuth();
        $my_calendars = array();
        $shared_calendars = array();
        foreach (Kronolith::listCalendars() as $id => $cal) {
            if ($cal->get('owner') == $current_user) {
                $my_calendars[$id] = $cal;
            } else {
                $shared_calendars[$id] = $cal;
            }
        }
        require KRONOLITH_TEMPLATES . '/menu/menu.inc';

        /* Include the JavaScript for the help system. */
        Help::javascript();

        // Check here for guest calendars so that we don't get
        // multiple messages after redirects, etc.
        if (!Auth::getAuth() && !count($GLOBALS['all_calendars'])) {
            $notification->push(_("No calendars are available to guests."));
        }

        // Display all notifications.
        $notification->notify(array('listeners' => 'status'));
    }

    /**
     * Used with usort() to sort events based on their start times.
     * This function ignores the date component so recuring events can
     * be sorted correctly on a per day basis.
     */
    function _sortEventStartTime($a, $b)
    {
        return ((int)date('Gis', $a->startTimestamp) - (int)date('Gis', $b->startTimestamp));
    }

    function _sortEvents($a, $b)
    {
        return $a->startTimestamp - $b->startTimestamp;
    }

}

/**
 * Date wrapping class, including some calculation functions.
 */
class Kronolith_Date {

    /**
     * Year
     * @var integer $year
     */
    var $year;

    /**
     * Month
     * @var integer $month
     */
    var $month;

    /**
     * Day
     * @var integer $mday
     */
    var $mday;

    /**
     * Hour
     * @var integer $hour
     */
    var $hour = 0;

    /**
     * Minute
     * @var integer $min
     */
    var $min = 0;

    /**
     * Second
     * @var integer $sec
     */
    var $sec = 0;

    /**
     * Build a new date object. If $date contains date parts, use them
     * to initialize the object.
     */
    function Kronolith_Date($date = null)
    {
        if (is_array($date) || is_object($date)) {
            foreach ($date as $key => $val) {
                if (in_array($key, array('year', 'month', 'mday', 'hour', 'min', 'sec'))) {
                    $this->$key = (int)$val;
                }
            }
        }
    }

    /**
     * Return the timestamp that this object currently represents.
     *
     * @return integer  A unix timestamp.
     */
    function timestamp()
    {
        return @mktime($this->hour, $this->min, $this->sec, $this->month, $this->mday, $this->year);
    }

    /**
     * Return the day of the week (0 = Monday, 6 = Sunday) of this
     * object's current date.
     *
     * @return integer  The day of the week.
     */
    function dayOfWeek()
    {
        return Kronolith::dayOfWeek($this->mday, $this->month, $this->year);
    }

    /**
     * Set the date of this object to the $nth weekday of $weekday.
     *
     * @param integer $weekday  The day of the week (0 = Monday, etc).
     * @param integer $nth      The $nth $weekday to set to (defaults to 1).
     */
    function setNthWeekday($weekday, $nth = 1)
    {
        if ($weekday < KRONOLITH_MONDAY || $weekday > KRONOLITH_SUNDAY) {
            return false;
        }

        $this->mday = 1;
        $first = $this->dayOfWeek();
        if ($weekday < $first) {
            $this->mday = 8 + $weekday - $first;
        } else {
            $this->mday = $weekday - $first + 1;
        }
        $this->mday += 7 * $nth - 7;

        $this->correct();

        return true;
    }

    function copy()
    {
        return new Kronolith_Date($this);
    }

    function dump($prefix = '')
    {
        echo ($prefix ? $prefix . ': ' : '') . $this->year . '-' . $this->month . '-' . $this->mday . "<br>\n";
    }

    /**
     * Correct any over- or underflows in any of the date's members.
     */
    function correct()
    {
        while ($this->sec < 0) {
            $this->min--;
            $this->sec += 60;
        }

        while ($this->sec > 59) {
            $this->min++;
            $this->sec -= 60;
        }

        while ($this->min < 0) {
            $this->hour--;
            $this->min += 60;
        }

        while ($this->min > 59) {
            $this->hour++;
            $this->min -= 60;
        }

        while ($this->hour < 0) {
            $this->mday--;
            $this->hour += 24;
        }

        while ($this->hour > 23) {
            $this->mday++;
            $this->hour -= 24;
        }

        while ($this->mday > Date_Calc::daysInMonth($this->month, $this->year)) {
            $this->month++;
            $this->mday -= Date_Calc::daysInMonth($this->month - 1, $this->year);
        }

        while ($this->month > 12) {
            $this->year++;
            $this->month -= 12;
        }
    }

}
