<?php
/**
 * $Horde: kronolith/lib/Kronolith.php,v 1.263.2.84 2009-11-25 10:21:36 jan Exp $
 *
 * @package Kronolith
 */

/** Event status */
define('KRONOLITH_STATUS_NONE', 0);
define('KRONOLITH_STATUS_TENTATIVE', 1);
define('KRONOLITH_STATUS_CONFIRMED', 2);
define('KRONOLITH_STATUS_CANCELLED', 3);
define('KRONOLITH_STATUS_FREE', 4);

/** Invitation responses */
define('KRONOLITH_RESPONSE_NONE',      1);
define('KRONOLITH_RESPONSE_ACCEPTED',  2);
define('KRONOLITH_RESPONSE_DECLINED',  3);
define('KRONOLITH_RESPONSE_TENTATIVE', 4);

/** Attendee status */
define('KRONOLITH_PART_REQUIRED', 1);
define('KRONOLITH_PART_OPTIONAL', 2);
define('KRONOLITH_PART_NONE',     3);
define('KRONOLITH_PART_IGNORE',   4);

/** iTip requests */
define('KRONOLITH_ITIP_REQUEST', 1);
define('KRONOLITH_ITIP_CANCEL',  2);

/** Free/Busy not found */
define('KRONOLITH_ERROR_FB_NOT_FOUND', 1);

/** The event can be delegated. */
define('PERMS_DELEGATE', 1024);

/**
 * The Kronolith:: class provides functionality common to all of Kronolith.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith {

    /**
     * Add inline javascript to the output buffer.
     *
     * @since Kronolith 2.2
     *
     * @param mixed $script  The script text to add (can be stored in an
     *                       array also).
     *
     * @return string  The javascript text to output, or empty if the page
     *                 headers have not yet been sent.
     */
    function addInlineScript($script)
    {
        if (is_array($script)) {
            $script = implode(';', $script);
        }

        $script = trim($script);
        if (empty($script)) {
            return;
        }

        if (!isset($GLOBALS['__kronolith_inline_script'])) {
            $GLOBALS['__kronolith_inline_script'] = array();
        }
        $GLOBALS['__kronolith_inline_script'][] = $script;

        // If headers have already been sent, we need to output a
        // <script> tag directly.
        if (ob_get_length() || headers_sent()) {
            Kronolith::outputInlineScript();
        }
    }

    /**
     * Print inline javascript to the output buffer.
     *
     * @since Kronolith 2.2
     *
     * @return string  The javascript text to output.
     */
    function outputInlineScript()
    {
        if (!empty($GLOBALS['__kronolith_inline_script'])) {
            echo '<script type="text/javascript">//<![CDATA[' . "\n";
            foreach ($GLOBALS['__kronolith_inline_script'] as $val) {
                echo $val . "\n";
            }
            echo "//]]></script>\n";
        }

        $GLOBALS['__kronolith_inline_script'] = array();
    }

    /**
     * Returns all the events that happen each day within a time period.
     *
     * @param object $startDate    The start of the time range.
     * @param object $endDate      The end of the time range.
     * @param array  $calendars    The calendars to check for events.
     * @param boolean $alarmsOnly  Return only events with an alarm set
     *
     * @return array  The events happening in this time period.
     */
    function listEventIds($startDate = null, $endDate = null,
                          $calendars = null, $alarmsOnly = false)
    {
        global $kronolith_driver;

        if (!empty($startDate)) {
            $startDate = new Horde_Date($startDate);
        }
        if (!empty($endDate)) {
            $endDate = new Horde_Date($endDate);
        }
        if (!isset($calendars)) {
            $calendars = $GLOBALS['display_calendars'];
        }
        if (!is_array($calendars)) {
            $calendars = array($calendars);
        }

        $eventIds = array();
        foreach ($calendars as $cal) {
            if ($kronolith_driver->getCalendar() != $cal) {
                $kronolith_driver->open($cal);
            }
            $eventIds[$cal] = $GLOBALS['kronolith_driver']->listEvents(
                $startDate, $endDate, $alarmsOnly);
        }

        return $eventIds;
    }

    /**
     * Returns all the alarms active right on $date.
     *
     * @param Horde_Date $date    The start of the time range.
     * @param array $calendars    The calendars to check for events.
     * @param boolean $fullevent  Whether to return complete alarm objects or
     *                            only alarm IDs.
     *
     * @return array  The alarms active on $date.
     */
    function listAlarms($date, $calendars, $fullevent = false)
    {
        global $kronolith_driver;

        $alarms = array();
        foreach ($calendars as $cal) {
            if ($kronolith_driver->getCalendar() != $cal) {
                $kronolith_driver->open($cal);
            }
            $alarms[$cal] = $kronolith_driver->listAlarms($date, $fullevent);
            if (is_a($alarms[$cal], 'PEAR_Error')) {
                return $alarms[$cal];
            }
        }

        return $alarms;
    }

    /**
     * Search for events with the given properties
     *
     * @param object $query  The search query
     *
     * @return array  The events
     */
    function search($query)
    {
        global $kronolith_driver;

        if (!isset($query->calendars)) {
            $calendars = $GLOBALS['display_calendars'];
        } else {
            $calendars = $query->calendars;
        }

        $events = array();
        foreach ($calendars as $cal) {
            if ($kronolith_driver->getCalendar() != $cal) {
                $kronolith_driver->open($cal);
            }
            $retevents = $kronolith_driver->search($query);
            foreach ($retevents as $event) {
                $events[] = $event;
            }
        }

        return $events;
    }

    /**
     * Initial app setup code.
     */
    function initialize()
    {
        /* Store the request timestamp if it's not already present. */
        if (!isset($_SERVER['REQUEST_TIME'])) {
            $_SERVER['REQUEST_TIME'] = time();
        }

        /* Initialize Kronolith session if we don't have one */
        if (!isset($_SESSION['kronolith_session'])) {
            $_SESSION['kronolith_session'] = array();
            Kronolith::loginTasksFlag(1);
        }

        /* Fetch display preferences. */
        $GLOBALS['display_calendars'] = @unserialize($GLOBALS['prefs']->getValue('display_cals'));
        $GLOBALS['display_remote_calendars'] = @unserialize($GLOBALS['prefs']->getValue('display_remote_cals'));
        $GLOBALS['display_external_calendars'] = @unserialize($GLOBALS['prefs']->getValue('display_external_cals'));

        if (!is_array($GLOBALS['display_calendars'])) {
            $GLOBALS['display_calendars'] = array();
        }
        if (!is_array($GLOBALS['display_remote_calendars'])) {
            $GLOBALS['display_remote_calendars'] = array();
        }
        if (!is_array($GLOBALS['display_external_calendars'])) {
            $GLOBALS['display_external_calendars'] = array();
        }

        /* Update preferences for which calendars to display. If the
         * user doesn't have any selected calendars to view then fall
         * back to an available calendar. */
        if (($calendarId = Util::getFormData('display_cal')) !== null) {
            if (is_array($calendarId)) {
                $calendars = $calendarId;
                $GLOBALS['display_calendars'] = array();
                $GLOBALS['display_remote_calendars'] = array();
                foreach ($calendars as $calendarId) {
                    if (strncmp($calendarId, 'remote_', 7) === 0) {
                        $calendarId = substr($calendarId, 7);
                        $GLOBALS['display_remote_calendars'][] = $calendarId;
                    } elseif (strncmp($calendarId, 'external_', 9) === 0) {
                        $calendarId = substr($calendarId, 9);
                        $GLOBALS['display_external_calendars'][] = $calendarId;
                    } else {
                        $GLOBALS['display_calendars'][] = $calendarId;
                    }
                }
            } else {
                /* Specifying a single calendar is always to make sure
                 * that it's shown. Use the "toggle_calendar" argument
                 * to toggle the state of a single calendar. */
                if (strncmp($calendarId, 'remote_', 7) === 0) {
                    $calendarId = substr($calendarId, 7);
                    if (!in_array($calendarId, $GLOBALS['display_remote_calendars'])) {
                        $GLOBALS['display_remote_calendars'][] = $calendarId;
                    }
                } elseif (strncmp($calendarId, 'external_', 9) === 0) {
                    $calendarId = substr($calendarId, 9);
                    if (!in_array($calendarId, $GLOBALS['display_external_calendars'])) {
                        $GLOBALS['display_external_calendars'][] = $calendarId;
                    }
                } else {
                    if (!in_array($calendarId, $GLOBALS['display_calendars'])) {
                        $GLOBALS['display_calendars'][] = $calendarId;
                    }
                }
            }
        }

        /* Check for single "toggle" calendars. */
        if (($calendarId = Util::getFormData('toggle_calendar')) !== null) {
            if (strncmp($calendarId, 'remote_', 7) === 0) {
                $calendarId = substr($calendarId, 7);
                if (in_array($calendarId, $GLOBALS['display_remote_calendars'])) {
                    $key = array_search($calendarId, $GLOBALS['display_remote_calendars']);
                    unset($GLOBALS['display_remote_calendars'][$key]);
                } else {
                    $GLOBALS['display_remote_calendars'][] = $calendarId;
                }
            } elseif (strncmp($calendarId, 'external_', 9) === 0) {
                $calendarId = substr($calendarId, 9);
                if (in_array($calendarId, $GLOBALS['display_external_calendars'])) {
                    $key = array_search($calendarId, $GLOBALS['display_external_calendars']);
                    unset($GLOBALS['display_external_calendars'][$key]);
                } else {
                    $GLOBALS['display_external_calendars'][] = $calendarId;
                }
            } else {
                if (in_array($calendarId, $GLOBALS['display_calendars'])) {
                    $key = array_search($calendarId, $GLOBALS['display_calendars']);
                    unset($GLOBALS['display_calendars'][$key]);
                } else {
                    $GLOBALS['display_calendars'][] = $calendarId;
                }
            }
        }

        /* Make sure all shares exists now to save on checking later. */
        $GLOBALS['all_calendars'] = Kronolith::listCalendars();
        $calendar_keys = array_values($GLOBALS['display_calendars']);
        $GLOBALS['display_calendars'] = array();
        foreach ($calendar_keys as $id) {
            if (isset($GLOBALS['all_calendars'][$id])) {
                $GLOBALS['display_calendars'][] = $id;
            }
        }

        /* Make sure all the remote calendars still exist. */
        $_temp = $GLOBALS['display_remote_calendars'];
        $GLOBALS['display_remote_calendars'] = array();
        $_all = @unserialize($GLOBALS['prefs']->getValue('remote_cals'));
        if (is_array($_all)) {
            foreach ($_all as $id) {
                if (in_array($id['url'], $_temp)) {
                    $GLOBALS['display_remote_calendars'][] = $id['url'];
                }
            }
        }
        $GLOBALS['prefs']->setValue('display_remote_cals', serialize($GLOBALS['display_remote_calendars']));

        /* Get a list of external calendars. */
        if (isset($_SESSION['all_external_calendars'])) {
            $GLOBALS['all_external_calendars'] = $_SESSION['all_external_calendars'];
        } else {
            $GLOBALS['all_external_calendars'] = array();
            $apis = array_unique($GLOBALS['registry']->listAPIs());
            foreach ($apis as $api) {
                if ($GLOBALS['registry']->hasMethod($api . '/listTimeObjects')) {
                    $categories = $GLOBALS['registry']->call($api . '/listTimeObjectCategories');
                    if (is_a($categories, 'PEAR_Error') || !count($categories)) {
                        continue;
                    }

                    $GLOBALS['all_external_calendars'][$api] = $categories;
                } elseif ($api == 'tasks' && $GLOBALS['registry']->hasMethod('tasks/listTasks')) {
                    $GLOBALS['all_external_calendars'][$api] = array('_listTasks' => $GLOBALS['registry']->get('name', $GLOBALS['registry']->hasInterface($api)));
                }
            }
            $_SESSION['all_external_calendars'] = $GLOBALS['all_external_calendars'];
        }

        /* Make sure all the external calendars still exist. */
        $_temp = $GLOBALS['display_external_calendars'];
        $GLOBALS['display_external_calendars'] = array();
        foreach ($GLOBALS['all_external_calendars'] as $api => $categories) {
            foreach ($categories as $id => $name) {
                $calendarId = $api . '/' . $id;
                /* Forward compatible checking of subscribed external
                 * sources. */
                foreach ($_temp as $_temp_cal) {
                    if (strpos($_temp_cal, $calendarId) === 0 &&
                        !in_array($calendarId, $GLOBALS['display_external_calendars'])) {
                        $GLOBALS['display_external_calendars'][] = $calendarId;
                    }
                }
            }
        }
        $GLOBALS['prefs']->setValue('display_external_cals', serialize($GLOBALS['display_external_calendars']));

        /* If an authenticated user has no calendars visible and their
         * personal calendar doesn't exist, create it. */
        if (Auth::getAuth() &&
            !count($GLOBALS['display_calendars']) &&
            !$GLOBALS['kronolith_shares']->exists(Auth::getAuth())) {
            require_once 'Horde/Identity.php';
            $identity = &Identity::singleton();
            $name = $identity->getValue('fullname');
            if (trim($name) == '') {
                $name = Auth::removeHook(Auth::getAuth());
            }
            $share = &$GLOBALS['kronolith_shares']->newShare(Auth::getAuth());
            $share->set('name', sprintf(_("%s's Calendar"), $name));
            $GLOBALS['kronolith_shares']->addShare($share);
            $GLOBALS['all_calendars'][Auth::getAuth()] = &$share;

            /* Make sure the personal calendar is displayed by default. */
            if (!in_array(Auth::getAuth(), $GLOBALS['display_calendars'])) {
                $GLOBALS['display_calendars'][] = Auth::getAuth();
            }

            /* Calendar auto-sharing with the user's groups */
            if ($GLOBALS['conf']['autoshare']['shareperms'] != 'none') {
                $perm_value = 0;
                switch ($GLOBALS['conf']['autoshare']['shareperms']) {
                case 'read':
                    $perm_value = PERMS_READ | PERMS_SHOW;
                    break;
                case 'edit':
                    $perm_value = PERMS_READ | PERMS_SHOW | PERMS_EDIT;
                    break;
                case 'full':
                    $perm_value = PERMS_READ | PERMS_SHOW | PERMS_EDIT | PERMS_DELETE;
                    break;
                }
                $groups = &Group::singleton();
                $group_list = $groups->getGroupMemberships(Auth::getAuth());
                if (!is_a($group_list, 'PEAR_Error') && count($group_list)) {
                    $perm = $share->getPermission();
                    // Add the default perm, not added otherwise
                    $perm->addUserPermission(Auth::getAuth(), PERMS_ALL, false);
                    foreach ($group_list as $group_id => $group_name) {
                        $perm->addGroupPermission($group_id, $perm_value, false);
                    }
                    $share->setPermission($perm);
                    $share->save();
                    $GLOBALS['notification']->push(sprintf(_("New calendar created and automatically shared with the following group(s): %s."), implode(', ', $group_list)), 'horde.success');
                }
            }
        }

        $GLOBALS['prefs']->setValue('display_cals', serialize($GLOBALS['display_calendars']));

    }

    /**
     * Either sets or checks the value of the logintasks flag.
     *
     * @param integer $set  The value of the flag.
     *
     * @return integer  The value of the flag.
     *                  0 = No login tasks pending
     *                  1 = Login tasks pending
     *                  2 = Login tasks pending, previous tasks interrupted
     */
    function loginTasksFlag($set = null)
    {
        if (($set !== null)) {
            $_SESSION['kronolith_session']['_logintasks'] = $set;
        }

        return isset($_SESSION['kronolith_session']['_logintasks']) ?
            $_SESSION['kronolith_session']['_logintasks'] : 0;
    }

    /**
     * Fetches a remote calendar into the session and return the data.
     *
     * @param string $url  The location of the remote calendar.
     *
     * @return mixed  Either the calendar data, or an error on failure.
     */
    function getRemoteCalendar($url)
    {
        $url = trim($url);

        /* Treat webcal:// URLs as http://. */
        if (substr($url, 0, 9) == 'webcal://') {
            $url = str_replace('webcal://', 'http://', $url);
        }

        if (empty($_SESSION['kronolith']['remote'][$url])) {
            $options['method'] = 'GET';
            $options['timeout'] = 5;
            $options['allowRedirects'] = true;

            if (!empty($GLOBALS['conf']['http']['proxy']['proxy_host'])) {
                $options = array_merge($options, $GLOBALS['conf']['http']['proxy']);
            }

            require_once 'HTTP/Request.php';
            $http = new HTTP_Request($url, $options);
            /* Check for HTTP authentication credentials */
            $cals = unserialize($GLOBALS['prefs']->getValue('remote_cals'));
            foreach ($cals as $cal) {
                if ($cal['url'] == $url) {
                    $user = isset($cal['user']) ? $cal['user'] : '';
                    $password = isset($cal['password']) ? $cal['password'] : '';
                    $key = Auth::getCredential('password');
                    if ($key && $user) {
                        require_once 'Horde/Secret.php';
                        $user = Secret::read($key, base64_decode($user));
                        $password = Secret::read($key, base64_decode($password));
                    }
                    break;
                }
            }
            if (!empty($user)) {
                $http->setBasicAuth($user, $password);
            }
            @$http->sendRequest();
            if ($http->getResponseCode() != 200) {
                Horde::logMessage(sprintf('Failed to retrieve remote calendar: url = "%s", status = %s',
                                          $url, $http->getResponseCode()),
                                  __FILE__, __LINE__, PEAR_LOG_ERR);
                return PEAR::raiseError(sprintf(_("Could not open %s."), $url));
            }
            $_SESSION['kronolith']['remote'][$url] = $http->getResponseBody();

            /* Log fetch at DEBUG level. */
            Horde::logMessage(sprintf('Retrieved remote calendar for %s: url = "%s"',
                                      Auth::getAuth(), $url),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }

        return $_SESSION['kronolith']['remote'][$url];
    }

    /**
     * Returns all the events from a remote calendar.
     *
     * @param string $url  The url of the remote calendar.
     */
    function listRemoteEvents($url)
    {
        global $kronolith_driver;

        $data = Kronolith::getRemoteCalendar($url);
        if (is_a($data, 'PEAR_Error')) {
            return $data;
        }

        require_once 'Horde/iCalendar.php';
        $iCal = new Horde_iCalendar();
        if (!$iCal->parsevCalendar($data)) {
            return array();
        }

        $components = $iCal->getComponents();
        $events = array();
        $count = count($components);
        $exceptions = array();
        for ($i = 0; $i < $count; ++$i) {
            $component = $components[$i];
            if ($component->getType() == 'vEvent') {
                $event = &$kronolith_driver->getEvent();
                if (is_a($event, 'PEAR_Error')) {
                    return $event;
                }
                $event->status = KRONOLITH_STATUS_FREE;
                $event->fromiCalendar($component);
                $event->remoteCal = $url;
                $event->eventID = $i;

                /* Catch RECURRENCE-ID attributes which mark single recurrence
                 * instances. */
                $recurrence_id = $component->getAttribute('RECURRENCE-ID');
                if (is_int($recurrence_id) &&
                    is_string($uid = $component->getAttribute('UID')) &&
                    is_int($seq = $component->getAttribute('SEQUENCE'))) {
                    $exceptions[$uid][$seq] = $recurrence_id;
                }
                $events[] = $event;
            }
        }

        /* Loop through all explicitly defined recurrence intances and create
         * exceptions for those in the event with the matchin recurrence. */
        foreach ($events as $key => $event) {
            if ($event->recurs() &&
                isset($exceptions[$event->getUID()][$event->getSequence()])) {
                $timestamp = $exceptions[$event->getUID()][$event->getSequence()];
                $events[$key]->recurrence->addException(date('Y', $timestamp), date('m', $timestamp), date('d', $timestamp));
            }
        }

        return $events;
    }

    /**
     * Returns an event object for an event on a remote calendar.
     *
     * This is kind of a temorary solution until we can have multiple drivers
     * in use at the same time.
     *
     * @param $url      The url of the remote calendar.
     * @param $eventId  The index of the event on the remote calendar.
     *
     * @return Kronolith_Event  The event object.
     */
    function &getRemoteEventObject($url, $eventId)
    {
        global $kronolith_driver;

        $data = Kronolith::getRemoteCalendar($url);
        if (is_a($data, 'PEAR_Error')) {
            return $data;
        }

        require_once 'Horde/iCalendar.php';
        $iCal = new Horde_iCalendar();
        if (!$iCal->parsevCalendar($data)) {
            return array();
        }

        $components = $iCal->getComponents();
        if (isset($components[$eventId]) &&
            $components[$eventId]->getType() == 'vEvent') {
            $event = &$kronolith_driver->getEvent();
            if (is_a($event, 'PEAR_Error')) {
                return $event;
            }
            $event->status = KRONOLITH_STATUS_FREE;
            $event->fromiCalendar($components[$eventId]);
            $event->remoteCal = $url;
            $event->eventID = $eventId;

            return $event;
        }

        return false;
    }

    /**
     * Returns a list of events containing holidays occuring between
     * <code>$startDate</code> and <code>$endDate</code>. The outcome depends
     * on the user's selection of holiday drivers
     *
     * @param int|Horde_Date $startDate  The start of the datespan to be
     *                                   checked.
     * @param int|Horde_Date $endDate    The end of the datespan.
     *
     * @return array The matching holidays as an array.
     */
    function listHolidayEvents($startDate = null, $endDate = null)
    {
        if (!@include_once('Date/Holidays.php')) {
            Horde::logMessage('Support for Date_Holidays has been enabled but the package seems to be missing.',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return array();
        } else {
            $dhDriver = Kronolith_Driver::factory('holidays');
            return $dhDriver->listEvents($startDate, $endDate);
        }
    }

    /**
     * Returns all the events that happen each day within a time period
     *
     * @param int|Horde_Date $startDate  The start of the time range.
     * @param int|Horde_Date $endDate    The end of the time range.
     * @param array $calendars           The calendars to check for events.
     * @param boolean $showRecurrence    Return every instance of a recurring
     *                                   event? If false, will only return
     *                                   recurring events once inside the
     *                                   $startDate - $endDate range.
     *                                   Defaults to true
     * @param boolean $alarmsOnly        Filter results for events with alarms
     *                                   Defaults to false
     * @param boolean $showRemote        Return events from remote and
     *                                   listTimeObjects as well?
     *
     * @return array  The events happening in this time period.
     */
    function listEvents($startDate = null, $endDate = null, $calendars = null,
                        $showRecurrence = true, $alarmsOnly = false,
                        $showRemote = true)
    {
        global $kronolith_driver, $registry;

        if (!empty($startDate)) {
            $startDate = new Horde_Date($startDate);
        }
        if (!empty($endDate)) {
            $endDate = new Horde_Date($endDate);
        }
        if (!isset($calendars)) {
            $calendars = $GLOBALS['display_calendars'];
        }

        $eventIds = Kronolith::listEventIds($startDate, $endDate, $calendars, $alarmsOnly);

        $startOfPeriod = Util::cloneObject($startDate);
        $startOfPeriod->hour = $startOfPeriod->min = $startOfPeriod->sec = 0;
        $endOfPeriod = Util::cloneObject($endDate);
        $endOfPeriod->hour = 23;
        $endOfPeriod->min = $endOfPeriod->sec = 59;

        $results = array();
        foreach ($eventIds as $cal => $events) {
            if (is_a($events, 'PEAR_Error')) {
                return $events;
            }

            if ($kronolith_driver->getCalendar() != $cal) {
                $kronolith_driver->open($cal);
            }
            foreach ($events as $id) {
                $event = &$kronolith_driver->getEvent($id);
                if (is_a($event, 'PEAR_Error')) {
                    return $event;
                }

                Kronolith::_getEvents($results, $event, $startDate, $endDate,
                                      $startOfPeriod, $endOfPeriod,
                                      $showRecurrence);
            }
        }

        if ($showRemote) {
            /* Check for listTimeObjects */
            $apis = array();
            foreach ($GLOBALS['display_external_calendars'] as $external_cal) {
                list($api, $category) = explode('/', $external_cal, 2);
                if (!isset($apis[$api])) {
                    $apis[$api] = array();
                }
                if (!array_search($category, $apis[$api])) {
                    $apis[$api][] = $category;
                }
            }
            if (!empty($apis)) {
                $endStamp = new Horde_Date(array('month' => $endDate->month,
                                                 'mday' => $endDate->mday + 1,
                                                 'year' => $endDate->year));
                $kronolith_driver->open(Kronolith::getDefaultCalendar(PERMS_SHOW));
                foreach ($apis as $api => $categories) {
                    if (!$registry->hasMethod($api . '/listTimeObjects')) {
                        /* Backwards compatibility with versions of Nag
                         * without the listTimeObjects API call. */
                        if ($api == 'tasks' && $registry->hasMethod('tasks/listTasks')) {
                            $taskList = $registry->call('tasks/listTasks');
                            if (is_a($taskList, 'PEAR_Error')) {
                                continue;
                            }

                            $eventsList = array();
                            foreach ($taskList as $task) {
                                if (!$task['due'] && !empty($task['completed'])) {
                                    continue;
                                }
                                $eventsList[$task['task_id']] = array(
                                    'id' => $task['task_id'],
                                    'title' => sprintf(_("Due: %s"), $task['name']),
                                    'description' => $task['desc'],
                                    'start' => $task['due'],
                                    'end' => $task['due'],
                                    'category' => $task['category'],
                                    'params' => array('task' => $task['task_id'],
                                                      'tasklist' => $task['tasklist_id']));
                            }
                        }
                    } else {
                        $eventsList = $registry->call($api . '/listTimeObjects', array($categories, $startDate, $endDate));
                        if (is_a($eventsList, 'PEAR_Error')) {
                            $GLOBALS['notification']->push($eventsList);
                            continue;
                        }
                    }

                    foreach ($eventsList as $eventsListItem) {
                        $eventStart = new Horde_Date($eventsListItem['start']);
                        $eventEnd = new Horde_Date($eventsListItem['end']);
                        /* Ignore events out of our period. */
                        if (
                            /* Starts after the period. */
                            $eventStart->compareDateTime($endOfPeriod) > 0 ||
                            /* End before the period and doesn't recur. */
                            (!isset($eventsListItem['recurrence']) &&
                             $eventEnd->compareDateTime($startOfPeriod) < 0)) {
                            continue;
                        }

                        $event = &$kronolith_driver->getEvent();
                        $event->setAlarm(0);
                        if ($GLOBALS['prefs']->getValue('show_external_colors') &&
                            isset($eventsListItem['category'])) {
                            $event->category = $eventsListItem['category'];
                        }

                        $event->eventID = '_' . $api . $eventsListItem['id'];
                        $event->external = $api;
                        $event->external_params = $eventsListItem['params'];
                        $event->title = $eventsListItem['title'];
                        $event->description = isset($eventsListItem['description']) ? $eventsListItem['description'] : '';
                        $event->start = $eventStart;
                        $event->end = $eventEnd;
                        $event->status = KRONOLITH_STATUS_FREE;
                        if (isset($eventsListItem['recurrence'])) {
                            $recurrence = new Horde_Date_Recurrence($eventStart);
                            $recurrence->setRecurType($eventsListItem['recurrence']['type']);
                            if (isset($eventsListItem['recurrence']['end'])) {
                                $recurrence->setRecurEnd($eventsListItem['recurrence']['end']);
                                if ($recurrence->recurEnd->compareDateTime($startOfPeriod) < 0) {
                                    continue;
                                }
                            }
                            if (isset($eventsListItem['recurrence']['interval'])) {
                                $recurrence->setRecurInterval($eventsListItem['recurrence']['interval']);
                            }
                            if (isset($eventsListItem['recurrence']['count'])) {
                                $recurrence->setRecurCount($eventsListItem['recurrence']['count']);
                            }
                            if (isset($eventsListItem['recurrence']['days'])) {
                                $recurrence->setRecurOnDay($eventsListItem['recurrence']['days']);
                            }
                            if (isset($eventsListItem['recurrence']['exceptions'])) {
                                foreach ($eventsListItem['recurrence']['exceptions'] as $exception) {
                                    $recurrence->addException(new Horde_Date($exception));
                                }
                            }
                            $event->recurrence = $recurrence;
                        }
                        Kronolith::_getEvents($results, $event, $startDate, $endDate,
                                              $startOfPeriod, $endOfPeriod,
                                              $showRecurrence);
                    }
                }
            }

            /* Remote Calendars. */
            foreach ($GLOBALS['display_remote_calendars'] as $url) {
                $events = Kronolith::listRemoteEvents($url);
                if (is_a($events, 'PEAR_Error')) {
                    $GLOBALS['notification']->push($events, 'horde.warning');
                } else {
                    $kronolith_driver->open(Kronolith::getDefaultCalendar(PERMS_SHOW));
                    foreach ($events as $event) {

                        /* Ignore events out of our period. */
                        if (
                            /* Starts after the period. */
                            $event->start->compareDateTime($endOfPeriod) > 0 ||
                            /* End before the period and doesn't recur. */
                            (!$event->recurs() &&
                             $event->end->compareDateTime($startOfPeriod) < 0) ||
                            /* Recurs and ... */
                            ($event->recurs() &&
                             /* ... we don't show recurring events or ... */
                             (!$showRecurrence ||
                              /* ... has a recurrence end before the period. */
                              ($event->recurrence->hasRecurEnd() &&
                               $event->recurrence->recurEnd->compareDateTime($startOfPeriod) < 0)))) {
                            continue;
                        }
                        Kronolith::_getEvents($results, $event, $startDate,
                                              $endDate, $startOfPeriod,
                                              $endOfPeriod, $showRecurrence);
                    }
                }
            }
        }

        /* Holidays */
        if (!empty($GLOBALS['conf']['holidays']['enable'])) {
            $events = Kronolith::listHolidayEvents($startDate, $endDate);
            if (!is_a($events, 'PEAR_Error')) {
                $kronolith_driver->open(Kronolith::getDefaultCalendar(PERMS_SHOW));
                foreach ($events as $event) {
                    Kronolith::_getEvents($results, $event, $startDate,
                                          $endDate, $startOfPeriod,
                                          $endOfPeriod, $showRecurrence);
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
     * Calculates recurrences of an event during a certain period.
     *
     * @access private
     */
    function _getEvents(&$results, &$event, $startDate, $endDate,
                        $startOfPeriod, $endOfPeriod,
                        $showRecurrence)
    {
        global $kronolith_driver;

        if ($event->recurs() && $showRecurrence) {
            /* Recurring Event. */

            /* We can't use the event duration here because we might cover a
             * daylight saving time switch. */
            $diff = array($event->end->year - $event->start->year,
                          $event->end->month - $event->start->month,
                          $event->end->mday - $event->start->mday,
                          $event->end->hour - $event->start->hour,
                          $event->end->min - $event->start->min);
            while ($diff[4] < 0) {
                --$diff[3];
                $diff[4] += 60;
            }
            while ($diff[3] < 0) {
                --$diff[2];
                $diff[3] += 24;
            }
            while ($diff[2] < 0) {
                --$diff[1];
                $diff[2] += Horde_Date::daysInMonth($event->start->month, $event->start->year);
            }
            while ($diff[1] < 0) {
                --$diff[0];
                $diff[1] += 12;
            }

            if ($event->start->compareDateTime($startOfPeriod) < 0) {
                /* The first time the event happens was before the period
                 * started. Start searching for recurrences from the start of
                 * the period. */
                $next = array('year' => $startDate->year,
                              'month' => $startDate->month,
                              'mday' => $startDate->mday);
            } else {
                /* The first time the event happens is in the range; unless
                 * there is an exception for this ocurrence, add it. */
                if (!$event->recurrence->hasException($event->start->year,
                                                      $event->start->month,
                                                      $event->start->mday)) {
                    Kronolith::_addCoverDates($results, $event, $event->start, $event->end);
                }

                /* Start searching for recurrences from the day after it
                 * starts. */
                $next = Util::cloneObject($event->start);
                ++$next->mday;
                $next->correct();
            }

            /* Add all recurrences of the event. */
            $next = $event->recurrence->nextRecurrence($next);
            while ($next !== false && $next->compareDate($endDate) <= 0) {
                if (!$event->recurrence->hasException($next->year, $next->month, $next->mday)) {
                    /* Add the event to all the days it covers. */
                    $nextEnd = Util::cloneObject($next);
                    $nextEnd->year  += $diff[0];
                    $nextEnd->month += $diff[1];
                    $nextEnd->mday  += $diff[2];
                    $nextEnd->hour  += $diff[3];
                    $nextEnd->min   += $diff[4];
                    $nextEnd->correct();
                    Kronolith::_addCoverDates($results, $event, $next, $nextEnd);
                }
                $next = $event->recurrence->nextRecurrence(
                    array('year' => $next->year,
                          'month' => $next->month,
                          'mday' => $next->mday + 1,
                          'hour' => $next->hour,
                          'min' => $next->min,
                          'sec' => $next->sec));
            }
        } else {
            /* Event only occurs once. */

            /* Work out what day it starts on. */
            if ($event->start->compareDateTime($startOfPeriod) < 0) {
                /* It started before the beginning of the period. */
                $eventStart = Util::cloneObject($startOfPeriod);
            } else {
                $eventStart = Util::cloneObject($event->start);
            }

            /* Work out what day it ends on. */
            if ($event->end->compareDateTime($endOfPeriod) > 0) {
                /* Ends after the end of the period. */
                $eventEnd = Util::cloneObject($event->end);
            } else {
                /* If the event doesn't end at 12am set the end date to the
                 * current end date. If it ends at 12am and does not end at
                 * the same time that it starts (0 duration), set the end date
                 * to the previous day's end date. */
                if ($event->end->hour != 0 ||
                    $event->end->min != 0 ||
                    $event->end->sec != 0 ||
                    $event->start->compareDateTime($event->end) == 0 ||
                    $event->isAllDay()) {
                    $eventEnd = Util::cloneObject($event->end);
                } else {
                    $eventEnd = new Horde_Date(
                        array('hour' =>  23,
                              'min' =>   59,
                              'sec' =>   59,
                              'month' => $event->end->month,
                              'mday' =>  $event->end->mday - 1,
                              'year' =>  $event->end->year));
                }
            }

            /* Add the event to all the days it covers. This is
             * similar to Kronolith::_addCoverDates(), but for days in
             * between the start and end day, the range is midnight to
             * midnight, and for the edge days it's start to midnight,
             * and midnight to end. */
            $i = $eventStart->mday;
            $loopDate = new Horde_Date(array('month' => $eventStart->month,
                                             'mday' => $i,
                                             'year' => $eventStart->year));
            while ($loopDate->compareDateTime($eventEnd) <= 0) {
                if (!$event->isAllDay() ||
                    $loopDate->compareDateTime($eventEnd) != 0) {
                    $addEvent = Util::cloneObject($event);

                    /* If this is the start day, set the start time to
                     * the real start time, otherwise set it to
                     * 00:00 */
                    if ($loopDate->compareDate($eventStart) == 0) {
                        $addEvent->start = $eventStart;
                    } else {
                        $addEvent->start = new Horde_Date(array(
                            'hour' => 0, 'min' => 0, 'sec' => 0,
                            'month' => $loopDate->month, 'mday' => $loopDate->mday, 'year' => $loopDate->year));
                    }

                    /* If this is the end day, set the end time to the
                     * real event end, otherwise set it to 23:59. */
                    if ($loopDate->compareDate($eventEnd) == 0) {
                        $addEvent->end = $eventEnd;
                    } else {
                        $addEvent->end = new Horde_Date(array(
                            'hour' => 23, 'min' => 59, 'sec' => 59,
                            'month' => $loopDate->month, 'mday' => $loopDate->mday, 'year' => $loopDate->year));
                    }

                    $results[$loopDate->timestamp()][$addEvent->getId()] = $addEvent;
                }

                $loopDate = new Horde_Date(
                    array('month' => $eventStart->month,
                          'mday' => ++$i,
                          'year' => $eventStart->year));
                $loopDate->correct();
            }
        }
        ksort($results);
    }

    /**
     * Adds an event to all the days it covers.
     *
     * @param array $result           The current result list.
     * @param Kronolith_Event $event  An event object.
     * @param Horde_Date $eventStart  The event's start at the actual
     *                                recurrence.
     * @param Horde_Date $eventEnd    The event's end at the actual recurrence.
     */
    function _addCoverDates(&$results, $event, $eventStart, $eventEnd)
    {
        $i = $eventStart->mday;
        $loopDate = new Horde_Date(array('month' => $eventStart->month,
                                         'mday' => $i,
                                         'year' => $eventStart->year));
        while ($loopDate->compareDateTime($eventEnd) <= 0) {
            if (!$event->isAllDay() ||
                $loopDate->compareDateTime($eventEnd) != 0) {
                $addEvent = Util::cloneObject($event);
                $addEvent->start = $eventStart;
                $addEvent->end = $eventEnd;
                $results[$loopDate->timestamp()][$addEvent->getId()] = $addEvent;
            }
            $loopDate = new Horde_Date(
                array('month' => $eventStart->month,
                      'mday' => ++$i,
                      'year' => $eventStart->year));
            $loopDate->correct();
        }
    }

    /**
     * Returns the number of events in calendars that the current user owns.
     *
     * @return integer  The number of events.
     */
    function countEvents()
    {
        global $kronolith_driver;

        static $count;
        if (isset($count)) {
            return $count;
        }

        $calendars = Kronolith::listCalendars(true, PERMS_ALL);
        $current_calendar = $kronolith_driver->getCalendar();

        $count = 0;
        foreach (array_keys($calendars) as $calendar) {
            if ($kronolith_driver->getCalendar() != $calendar) {
                $kronolith_driver->open($calendar);
            }

            /* Retrieve the event list from storage. */
            $count += count($kronolith_driver->listEvents());
        }

        /* Reopen last calendar. */
        if ($kronolith_driver->getCalendar() != $current_calendar) {
            $kronolith_driver->open($current_calendar);
        }

        return $count;
    }

    /**
     * Returns the real name, if available, of a user.
     */
    function getUserName($uid)
    {
        static $names = array();

        if (!isset($names[$uid])) {
            require_once 'Horde/Identity.php';
            $ident = &Identity::singleton('none', $uid);
            $ident->setDefault($ident->getDefault());
            $names[$uid] = $ident->getValue('fullname');
            if (empty($names[$uid])) {
                $names[$uid] = $uid;
            }
        }

        return $names[$uid];
    }

    /**
     * Returns the email address, if available, of a user.
     */
    function getUserEmail($uid)
    {
        static $emails = array();

        if (!isset($emails[$uid])) {
            require_once 'Horde/Identity.php';
            $ident = &Identity::singleton('none', $uid);
            $emails[$uid] = $ident->getValue('from_addr');
            if (empty($emails[$uid])) {
                $emails[$uid] = $uid;
            }
        }

        return $emails[$uid];
    }

    /**
     * Checks if an email address belongs to a user.
     */
    function isUserEmail($uid, $email)
    {
        static $emails = array();

        if (!isset($emails[$uid])) {
            require_once 'Horde/Identity.php';
            $ident = &Identity::singleton('none', $uid);

            $addrs = $ident->getAll('from_addr');
            $addrs[] = $uid;

            $emails[$uid] = $addrs;
        }

        return in_array($email, $emails[$uid]);
    }

    /**
     * Maps a Kronolith recurrence value to a translated string suitable for
     * display.
     *
     * @param integer $type  The recurrence value; one of the
     *                       HORDE_DATE_RECUR_XXX constants.
     *
     * @return string  The translated displayable recurrence value string.
     */
    function recurToString($type)
    {
        switch ($type) {
        case HORDE_DATE_RECUR_NONE:
            return _("Does not recur");

        case HORDE_DATE_RECUR_DAILY:
            return _("Recurs daily");

        case HORDE_DATE_RECUR_WEEKLY:
            return _("Recurs weekly");

        case HORDE_DATE_RECUR_MONTHLY_DATE:
        case HORDE_DATE_RECUR_MONTHLY_WEEKDAY:
            return _("Recurs monthly");

        case HORDE_DATE_RECUR_YEARLY_DATE:
        case HORDE_DATE_RECUR_YEARLY_DAY:
        case HORDE_DATE_RECUR_YEARLY_WEEKDAY:
            return _("Recurs yearly");
        }
    }

    /**
     * Maps a Kronolith meeting status string to a translated string suitable
     * for display.
     *
     * @param integer $status  The meeting status; one of the
     *                         KRONOLITH_STATUS_XXX constants.
     *
     * @return string  The translated displayable meeting status string.
     */
    function statusToString($status)
    {
        switch ($status) {
        case KRONOLITH_STATUS_CONFIRMED:
            return _("Confirmed");

        case KRONOLITH_STATUS_CANCELLED:
            return _("Cancelled");

        case KRONOLITH_STATUS_FREE:
            return _("Free");

        case KRONOLITH_STATUS_TENTATIVE:
        default:
            return _("Tentative");
        }
    }

    /**
     * Maps a Kronolith attendee response string to a translated string
     * suitable for display.
     *
     * @param integer $response  The attendee response; one of the
     *                           KRONOLITH_RESPONSE_XXX constants.
     *
     * @return string  The translated displayable attendee response string.
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
     * Maps a Kronolith attendee participation string to a translated string
     * suitable for display.
     *
     * @param integer $part  The attendee participation; one of the
     *                       KRONOLITH_PART_XXX constants.
     *
     * @return string  The translated displayable attendee participation
     *                 string.
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
     * @param string $response  The attendee response.
     *
     * @return string  The Kronolith response value.
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
     * Builds the HTML for an event status widget.
     *
     * @param string $name     The name of the widget.
     * @param string $current  The selected status value.
     * @param string $any      Whether an 'any' item should be added
     *
     * @return string  The HTML <select> widget.
     */
    function buildStatusWidget($name, $current = KRONOLITH_STATUS_CONFIRMED,
                               $any = false)
    {
        $html = "<select id=\"$name\" name=\"$name\">";

        $statii = array(
            KRONOLITH_STATUS_FREE,
            KRONOLITH_STATUS_TENTATIVE,
            KRONOLITH_STATUS_CONFIRMED,
            KRONOLITH_STATUS_CANCELLED
        );

        if (!isset($current)) {
            $current = KRONOLITH_STATUS_NONE;
        }

        if ($any) {
            $html .= "<option value=\"" . KRONOLITH_STATUS_NONE . "\"";
            $html .= ($current == KRONOLITH_STATUS_NONE) ? ' selected="selected">' : '>';
            $html .= _("Any") . "</option>";
        }

        foreach ($statii as $status) {
            $html .= "<option value=\"$status\"";
            $html .= ($status == $current) ? ' selected="selected">' : '>';
            $html .= Kronolith::statusToString($status) . "</option>";
        }
        $html .= '</select>';

        return $html;
    }

    /**
     * Returns all calendars a user has access to, according to several
     * parameters/permission levels.
     *
     * @param boolean $owneronly   Only return calenders that this user owns?
     *                             Defaults to false.
     * @param integer $permission  The permission to filter calendars by.
     *
     * @return array  The calendar list.
     */
    function listCalendars($owneronly = false, $permission = PERMS_SHOW)
    {
        // Work around BC break in listShares() parameters (http://bugs.horde.org/ticket/7820)
        include_once $GLOBALS['registry']->get('fileroot', 'horde') . '/lib/version.php';
        if (version_compare(HORDE_VERSION, '3.2', '<')) {
            $calendars = $GLOBALS['kronolith_shares']->listShares(Auth::getAuth(), $permission, $owneronly ? Auth::getAuth() : null, DATATREE_ROOT, true, 0, 0, 'name');
        } else {
            $calendars = $GLOBALS['kronolith_shares']->listShares(Auth::getAuth(), $permission, $owneronly ? Auth::getAuth() : null, 0, 0, 'name');
        }
        if (is_a($calendars, 'PEAR_Error')) {
            Horde::logMessage($calendars, __FILE__, __LINE__, PEAR_LOG_ERR);
            return array();
        }

        return $calendars;
    }

    /**
     * Returns the default calendar for the current user at the specified
     * permissions level.
     */
    function getDefaultCalendar($permission = PERMS_SHOW)
    {
        global $prefs;

        $default_share = $prefs->getValue('default_share');
        $calendars = Kronolith::listCalendars(false, $permission);

        if (isset($calendars[$default_share]) ||
            $prefs->isLocked('default_share')) {
            return $default_share;
        } elseif (isset($GLOBALS['all_calendars'][Auth::getAuth()]) &&
                  $GLOBALS['all_calendars'][Auth::getAuth()]->hasPermission(Auth::getAuth(), $permission)) {
            return Auth::getAuth();
        } elseif (count($calendars)) {
            return key($calendars);
        }

        return false;
    }

    /**
     * Returns the feed URL for a calendar.
     *
     * @param string $calendar  A calendar name.
     *
     * @return string  The calendar's feed URL.
     */
    function feedUrl($calendar)
    {
        if (isset($GLOBALS['conf']['urls']['pretty']) &&
            $GLOBALS['conf']['urls']['pretty'] == 'rewrite') {
            $feed_url = 'feed/' . $calendar;
        } else {
            $feed_url = Util::addParameter('feed/index.php', 'c', $calendar);
        }
        return Horde::applicationUrl($feed_url, true, -1);
    }

    /**
     * Returs the HTML/javascript snippit needed to embed a calendar in an
     * external website.
     *
     * @param string $calendar  A calendar name.
     *
     * @return string  The calendar's embed snippit.
     */
    function embedCode($calendar)
    {
        /* Get the base url */
        $url = Horde::applicationURL('imple.php', true, -1);

        $html = '<div id="kronolithCal"></div><script src="' . $url
            . '?imple=Embed/container=kronolithCal/view=month/calendar='
            . $calendar . '" type="text/javascript"></script>';

        return $html;
    }

    /**
     * Returns a comma separated list of attendees.
     *
     * @return string  Attendee list.
     */
    function attendeeList()
    {
        if (!isset($_SESSION['kronolith']['attendees']) ||
            !is_array($_SESSION['kronolith']['attendees'])) {
            return '';
        }

        require_once 'Horde/MIME.php';
        $attendees = array();
        foreach ($_SESSION['kronolith']['attendees'] as $email => $attendee) {
            $attendees[] = empty($attendee['name']) ? $email : MIME::trimEmailAddress($attendee['name'] . (strpos($email, '@') === false ? '' : ' <' . $email . '>'));
        }

        return implode(', ', $attendees);
    }

    /**
     * Sends out iTip event notifications to all attendees of a specific
     * event. Can be used to send event invitations, event updates as well as
     * event cancellations.
     *
     * @param Kronolith_Event $event      The event in question.
     * @param Notification $notification  A notification object used to show
     *                                    result status.
     * @param integer $action             The type of notification to send.
     *                                    One of the KRONOLITH_ITIP_* values.
     * @param Horde_Date $instance        If cancelling a single instance of a
     *                                    recurring event, the date of this
     *                                    intance.
     */
    function sendITipNotifications(&$event, &$notification, $action,
                                   $instance = null)
    {
        global $conf;

        $attendees = $event->getAttendees();
        if (!$attendees) {
            return;
        }

        require_once 'Horde/Identity.php';
        $ident = &Identity::singleton('none', $event->getCreatorId());

        $myemail = $ident->getValue('from_addr');
        if (!$myemail) {
            $notification->push(sprintf(_("You do not have an email address configured in your Personal Information Options. You must set one %shere%s before event notifications can be sent."), Horde::link(Util::addParameter(Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/prefs.php'), array('app' => 'horde', 'group' => 'identities'))), '</a>'), 'horde.error', array('content.raw'));
            return;
        }

        require_once 'Horde/MIME.php';
        require_once 'Horde/MIME/Headers.php';
        require_once 'Horde/MIME/Message.php';

        $myemail = explode('@', $myemail);
        $from = MIME::rfc822WriteAddress($myemail[0], isset($myemail[1]) ? $myemail[1] : '', $ident->getValue('fullname'));

        $mail_driver = $conf['mailer']['type'];
        $mail_params = $conf['mailer']['params'];
        if ($mail_driver == 'smtp' && $mail_params['auth'] &&
            empty($mail_params['username'])) {
            $mail_params['username'] = Auth::getAuth();
            $mail_params['password'] = Auth::getCredential('password');
        }

        $share = &$GLOBALS['kronolith_shares']->getShare($event->getCalendar());

        foreach ($attendees as $email => $status) {
            /* Don't bother sending an invitation/update if the recipient does
             * not need to participate, or has declined participating, or
             * doesn't have an email address. */
            if (strpos($email, '@') === false ||
                $status['attendance'] == KRONOLITH_PART_NONE ||
                $status['response'] == KRONOLITH_RESPONSE_DECLINED) {
                continue;
            }

            /* Determine all notification-specific strings. */
            switch ($action) {
            case KRONOLITH_ITIP_CANCEL:
                /* Cancellation. */
                $method = 'CANCEL';
                $filename = 'event-cancellation.ics';
                $subject = sprintf(_("Cancelled: %s"), $event->getTitle());
                break;

            case KRONOLITH_ITIP_REQUEST:
            default:
                if ($status['response'] == KRONOLITH_RESPONSE_NONE) {
                    /* Invitation. */
                    $method = 'REQUEST';
                    $filename = 'event-invitation.ics';
                    $subject = $event->getTitle();
                } else {
                    /* Update. */
                    $method = 'ADD';
                    $filename = 'event-update.ics';
                    $subject = sprintf(_("Updated: %s."), $event->getTitle());
                }
                break;
            }

            $message = $subject . ' (' .
                sprintf(_("on %s at %s"), strftime('%x', $event->start->timestamp()), date('H:i', $event->start->timestamp())) .
                ")\n\n";

            if ($event->getLocation() != '') {
                $message .= sprintf(_("Location: %s"), $event->getLocation()) . "\n\n";
            }

            if ($event->getAttendees()) {
                require_once 'Horde/MIME.php';
                $attendee_list = array();
                foreach ($event->getAttendees() as $mail => $attendee) {
                    $attendee_list[] = empty($attendee['name']) ? $mail : MIME::trimEmailAddress($attendee['name'] . (strpos($mail, '@') === false ? '' : ' <' . $mail . '>'));
                }
                $message .= sprintf(_("Attendees: %s"), implode(', ', $attendee_list)) . "\n\n";
            }

            if ($event->getDescription() != '') {
                $message .= _("The following is a more detailed description of the event:") . "\n\n" . $event->getDescription() . "\n\n";
            }
            $message .= _("Attached is an iCalendar file with more information about the event. If your mail client supports iTip requests you can use this file to easily update your local copy of the event.");

            if ($action == KRONOLITH_ITIP_REQUEST) {
                $attend_link = Util::addParameter(Horde::applicationUrl('attend.php', true, -1), array('c' => $event->getCalendar(), 'e' => $event->getId(), 'u' => $email), null, false);
                $message .= "\n\n" . sprintf(_("If your email client doesn't support iTip requests you can use one of the following links to accept or decline the event.\n\nTo accept the event:\n%s\n\nTo accept the event tentatively:\n%s\n\nTo decline the event:\n%s\n"), Util::addParameter($attend_link, 'a', 'accept', false), Util::addParameter($attend_link, 'a', 'tentative', false), Util::addParameter($attend_link, 'a', 'decline', false));
            }

            $mime = new MIME_Part('multipart/alternative');
            $body = new MIME_Part('text/plain', $message, NLS::getCharset());
            $body->setTransferEncoding('quoted-printable');

            require_once 'Horde/Data.php';
            require_once 'Horde/iCalendar.php';

            $iCal = new Horde_iCalendar();
            $iCal->setAttribute('METHOD', $method);
            $iCal->setAttribute('X-WR-CALNAME', String::convertCharset($share->get('name'), NLS::getCharset(), 'utf-8'));
            $vevent = $event->toiCalendar($iCal);
            if ($action == KRONOLITH_ITIP_CANCEL && !empty($instance)) {
                $vevent->setAttribute('RECURRENCE-ID', $instance, array('VALUE' => 'DATE'));
            }
            $iCal->addComponent($vevent);
            $ics = new MIME_Part('text/calendar', $iCal->exportvCalendar());
            $ics->setName($filename);
            $ics->setContentTypeParameter('METHOD', $method);
            $ics->setCharset(NLS::getCharset());

            $mime->addPart($body);
            $mime->addPart($ics);
            $mime = &MIME_Message::convertMimePart($mime);

            /* Build the notification headers. */
            $recipient = empty($status['name']) ? $email : MIME::trimEmailAddress($status['name'] . ' <' . $email . '>');

            $msg_headers = new MIME_Headers();
            $msg_headers->addReceivedHeader();
            $msg_headers->addMessageIdHeader();
            $msg_headers->addHeader('Date', date('r'));
            $msg_headers->addHeader('From', MIME::encodeAddress($from, NLS::getCharset()));
            $msg_headers->addHeader('To', MIME::encodeAddress($recipient, NLS::getCharset()));
            $msg_headers->addHeader('Subject', MIME::encode($subject, NLS::getCharset()));
            require_once KRONOLITH_BASE . '/lib/version.php';
            $msg_headers->addHeader('User-Agent', 'Kronolith ' . KRONOLITH_VERSION);
            $msg_headers->addMIMEHeaders($mime);

            $status = $mime->send($email, $msg_headers, $mail_driver, $mail_params);
            if (!is_a($status, 'PEAR_Error')) {
                $notification->push(
                    sprintf(_("The event notification to %s was successfully sent."), $recipient),
                    'horde.success'
                );
            } else {
                $notification->push(
                    sprintf(_("There was an error sending an event notification to %s: %s"), $recipient, $status->getMessage()),
                    'horde.error'
                );
            }
        }
    }

    /**
     * Sends email notifications that a event has been added, edited, or
     * deleted to users that want such notifications.
     *
     * @param Kronolith_Event $event  An event.
     * @param string $action          The event action. One of "add", "edit",
     *                                or "delete".
     */
    function sendNotification(&$event, $action)
    {
        global $conf;

        if (!in_array($action, array('add', 'edit', 'delete'))) {
            return PEAR::raiseError('Unknown event action: ' . $action);
        }

        require_once 'Horde/Group.php';
        require_once 'Horde/Identity.php';
        require_once 'Horde/MIME.php';
        require_once 'Horde/MIME/Headers.php';
        require_once 'Horde/MIME/Message.php';

        $groups = &Group::singleton();
        $calendar = $event->getCalendar();
        $recipients = array();
        $share = &$GLOBALS['kronolith_shares']->getShare($calendar);
        if (is_a($share, 'PEAR_Error')) {
            return $share;
        }

        $identity = &Identity::singleton();
        $from = $identity->getDefaultFromAddress(true);

        $owner = $share->get('owner');
        $recipients[$owner] = Kronolith::_notificationPref($owner, 'owner');

        foreach ($share->listUsers(PERMS_READ) as $user) {
            if (!isset($recipients[$user])) {
                $recipients[$user] = Kronolith::_notificationPref($user, 'read', $calendar);
            }
        }
        foreach ($share->listGroups(PERMS_READ) as $group) {
            $group = $groups->getGroupById($group);
            if (is_a($group, 'PEAR_Error')) {
                continue;
            }
            $group_users = $group->listAllUsers();
            if (is_a($group_users, 'PEAR_Error')) {
                Horde::logMessage($group_users, __FILE__, __LINE__, PEAR_LOG_ERR);
                continue;
            }
            foreach ($group_users as $user) {
                if (!isset($recipients[$user])) {
                    $recipients[$user] = Kronolith::_notificationPref($user, 'read', $calendar);
                }
            }
        }

        $addresses = array();
        foreach ($recipients as $user => $vals) {
            if (!$vals) {
                continue;
            }
            $identity = &Identity::singleton('none', $user);
            $email = $identity->getValue('from_addr');
            if (strpos($email, '@') !== false) {
                list($mailbox, $host) = explode('@', $email);
                if (!isset($addresses[$vals['lang']][$vals['tf']][$vals['df']])) {
                    $addresses[$vals['lang']][$vals['tf']][$vals['df']] = array();
                }
                $addresses[$vals['lang']][$vals['tf']][$vals['df']][] = MIME::rfc822WriteAddress($mailbox, $host, $identity->getValue('fullname'));
            }
        }

        if (!$addresses) {
            return;
        }

        $mail_driver = $conf['mailer']['type'];
        $mail_params = $conf['mailer']['params'];
        if ($mail_driver == 'smtp' && $mail_params['auth'] &&
            empty($mail_params['username'])) {
            $mail_params['username'] = Auth::getAuth();
            $mail_params['password'] = Auth::getCredential('password');
        }

        $msg_headers = new MIME_Headers();
        $msg_headers->addMessageIdHeader();
        $msg_headers->addAgentHeader();
        $msg_headers->addHeader('Date', date('r'));
        $msg_headers->addHeader('From', $from);

        foreach ($addresses as $lang => $twentyFour) {
            NLS::setLang($lang);

            switch ($action) {
            case 'add':
                $subject = _("Event added:");
                $notification_message = _("You requested to be notified when events are added to your calendars.") . "\n\n" . _("The event \"%s\" has been added to \"%s\" calendar, which is on %s at %s.");
                break;

            case 'edit':
                $subject = _("Event edited:");
                $notification_message = _("You requested to be notified when events are edited in your calendars.") . "\n\n" . _("The event \"%s\" has been edited on \"%s\" calendar, which is on %s at %s.");
                break;

            case 'delete':
                $subject = _("Event deleted:");
                $notification_message = _("You requested to be notified when events are deleted from your calendars.") . "\n\n" . _("The event \"%s\" has been deleted from \"%s\" calendar, which was on %s at %s.");
                break;
            }

            $msg_headers->removeHeader('Subject');
            $msg_headers->addHeader('Subject', $subject . ' ' . $event->title);

            foreach ($twentyFour as $tf => $dateFormat) {
                foreach ($dateFormat as $df => $df_recipients) {
                    $message = "\n" . sprintf($notification_message, $event->title, $share->get('name'), strftime($df, $event->start->timestamp()), date($tf ? 'H:i' : 'h:ia', $event->start->timestamp())) . "\n\n" . $event->getDescription();

                    $mime = new MIME_Message();
                    $body = new MIME_Part('text/plain', String::wrap($message, 76, "\n"), NLS::getCharset());

                    $mime->addPart($body);
                    $msg_headers->addMIMEHeaders($mime);

                    Horde::logMessage(sprintf('Sending event notifications for %s to %s', $event->title, implode(', ', $df_recipients)), __FILE__, __LINE__, PEAR_LOG_DEBUG);
                    $sent = $mime->send(implode(', ', $df_recipients), $msg_headers, $mail_driver, $mail_params);
                    if (is_a($sent, 'PEAR_Error')) {
                        return $sent;
                    }
                }
            }
        }

        return true;
    }

    /**
     * Returns whether a user wants email notifications for a calendar.
     *
     * @access private
     *
     * @todo This method is causing a memory leak somewhere, noticeable if
     *       importing a large amount of events.
     *
     * @param string $user      A user name.
     * @param string $mode      The check "mode". If "owner", the method checks
     *                          if the user wants notifications only for
     *                          calendars he owns. If "read", the method checks
     *                          if the user wants notifications for all
     *                          calendars he has read access to, or only for
     *                          shown calendars and the specified calendar is
     *                          currently shown.
     * @param string $calendar  The name of the calendar if mode is "read".
     *
     * @return mixed  The user's email, time, and language preferences if they want
     *                a notification for this calendar.
     */
    function _notificationPref($user, $mode, $calendar = null)
    {
        $prefs = &Prefs::singleton($GLOBALS['conf']['prefs']['driver'],
                                   'kronolith', $user, '', null,
                                   false);
        $prefs->retrieve();
        $vals = array('lang' => $prefs->getValue('language'),
                      'tf' => $prefs->getValue('twentyFour'),
                      'df' => $prefs->getValue('date_format'));

        if ($prefs->getValue('event_notification_exclude_self') && $user == Auth::getAuth()) {
            return false;
        }

        switch ($prefs->getValue('event_notification')) {
        case 'owner':
            return $mode == 'owner' ? $vals : false;

        case 'read':
            return $mode == 'read' ? $vals : false;

        case 'show':
            if ($mode == 'read') {
                $display_calendars = unserialize($prefs->getValue('display_cals'));
                return in_array($calendar, $display_calendars) ? $vals : false;
            }
        }

        return false;
    }

    function currentTimestamp()
    {
        $timestamp = (int)Util::getFormData('timestamp');
        if (!$timestamp) {
            $year = (int)Util::getFormData('year', date('Y'));
            $month = (int)Util::getFormData('month', date('n'));
            $day = (int)Util::getFormData('mday', date('d'));
            if ($week = (int)Util::getFormData('week')) {
                $month = 1;
                $day = Horde_Date::firstDayOfWeek($week, $year);
                if ($GLOBALS['prefs']->getValue('week_start_monday')) {
                    ++$day;
                }
            }
            $timestamp = empty($year) ? $_SERVER['REQUEST_TIME'] : mktime(0, 0, 0, $month, $day, $year);
        }

        return $timestamp;
    }

    /**
     * Returns the specified permission for the current user.
     *
     * @since Kronolith 2.1
     *
     * @param string $permission  A permission, currently only 'max_events'.
     *
     * @return mixed  The value of the specified permission.
     */
    function hasPermission($permission)
    {
        global $perms;

        if (!$perms->exists('kronolith:' . $permission)) {
            return true;
        }

        $allowed = $perms->getPermissions('kronolith:' . $permission);
        if (is_array($allowed)) {
            switch ($permission) {
            case 'max_events':
                $allowed = max($allowed);
                break;
            }
        }

        return $allowed;
    }

    /**
     * @param string $tabname
     */
    function tabs($tabname = null)
    {
        $timestamp = Kronolith::currentTimestamp();

        require_once 'Horde/UI/Tabs.php';
        require_once 'Horde/Variables.php';
        $tabs = new Horde_UI_Tabs('view', Variables::getDefaultVariables());
        $tabs->preserve('timestamp', $timestamp);

        $tabs->addTab(_("Day"), Horde::applicationUrl('day.php'),
                      array('tabname' => 'day', 'id' => 'tabday', 'onclick' => 'return ShowView(\'Day\', ' . $timestamp . ');'));
        $tabs->addTab(_("Work Week"), Horde::applicationUrl('workweek.php'),
                      array('tabname' => 'workweek', 'id' => 'tabworkweek', 'onclick' => 'return ShowView(\'WorkWeek\', ' . $timestamp . ');'));
        $tabs->addTab(_("Week"), Horde::applicationUrl('week.php'),
                      array('tabname' => 'week', 'id' => 'tabweek', 'onclick' => 'return ShowView(\'Week\', ' . $timestamp . ');'));
        $tabs->addTab(_("Month"), Horde::applicationUrl('month.php'),
                      array('tabname' => 'month', 'id' => 'tabmonth', 'onclick' => 'return ShowView(\'Month\', ' . $timestamp . ');'));
        $tabs->addTab(_("Year"), Horde::applicationUrl('year.php'),
                      array('tabname' => 'year', 'id' => 'tabyear', 'onclick' => 'return ShowView(\'Year\', ' . $timestamp . ');'));

        if ($tabname === null) {
            $tabname = basename($_SERVER['PHP_SELF']) == 'index.php' ? $GLOBALS['prefs']->getValue('defaultview') : str_replace('.php', '', basename($_SERVER['PHP_SELF']));
        }
        echo $tabs->render($tabname);
    }

    /**
     * @param string $tabname
     * @param Kronolith_Event $event
     */
    function eventTabs($tabname, $event)
    {
        if (!$event->isInitialized()) {
            return;
        }

        require_once 'Horde/UI/Tabs.php';
        require_once 'Horde/Variables.php';
        $tabs = new Horde_UI_Tabs('event', Variables::getDefaultVariables());
        $tabs->preserve('timestamp', Kronolith::currentTimestamp());

        $tabs->addTab(
            htmlspecialchars($event->getTitle()),
            $event->getViewUrl(),
            array('tabname' => 'Event',
                  'id' => 'tabEvent',
                  'onclick' => 'return ShowTab(\'Event\');'));
        if ((!$event->isPrivate() ||
             $event->getCreatorId() == Auth::getAuth()) &&
            $event->hasPermission(PERMS_EDIT)) {
            $tabs->addTab(
                $event->isRemote() ? _("Save As New") : _("_Edit"),
                $event->getEditUrl(),
                array('tabname' => 'EditEvent',
                      'id' => 'tabEditEvent',
                      'onclick' => 'return ShowTab(\'EditEvent\');'));
        }
        if ($event->hasPermission(PERMS_DELETE)) {
            $tabs->addTab(
                _("De_lete"),
                $event->getDeleteUrl(array('confirm' => 1)),
                array('tabname' => 'DeleteEvent',
                      'id' => 'tabDeleteEvent',
                      'onclick' => 'return ShowTab(\'DeleteEvent\');'));
        }
        $tabs->addTab(
            _("Export"),
            $event->getExportUrl(),
            array('tabname' => 'ExportEvent',
                  'id' => 'tabExportEvent'));

        echo $tabs->render($tabname);
    }

    /**
     * Get a named Kronolith_View_* object and load it with the
     * appropriate date parameters.
     *
     * @param string $view The name of the view.
     */
    function getView($view)
    {
        switch ($view) {
        case 'Day':
            require_once KRONOLITH_BASE . '/lib/Views/Day.php';

            if ($timestamp = (int)Util::getFormData('timestamp')) {
                $day = new Horde_Date($timestamp);
                list($year, $month, $day) = array($day->year,
                                                  $day->month,
                                                  $day->mday);
            } else {
                $year = (int)Util::getFormData('year');
                $month = (int)Util::getFormData('month');
                $day = (int)Util::getFormData('mday');
            }
            return new Kronolith_View_Day($month, $day, $year);

        case 'Month':
            require_once KRONOLITH_BASE . '/lib/Views/Month.php';

            if ($timestamp = (int)Util::getFormData('timestamp')) {
                $month = date('n', $timestamp);
                $year = date('Y', $timestamp);
            } else {
                $month = (int)Util::getFormData('month', date('n'));
                $year = (int)Util::getFormData('year', date('Y'));
            }
            return new Kronolith_View_Month($month, $year);
            break;

        case 'Week':
        case 'WorkWeek':
            require_once KRONOLITH_BASE . '/lib/Views/' . basename($view)
                . '.php';

            $week = (int)Util::getFormData('week');
            $year = (int)Util::getFormData('year');
            if ($timestamp = (int)Util::getFormData('timestamp')) {
                $date = new Horde_Date($timestamp);
                $year = $date->year;
                $week = $date->weekOfYear();
                if (!$GLOBALS['prefs']->getValue('week_start_monday') &&
                    $date->dayOfWeek() == HORDE_DATE_SUNDAY) {
                    ++$week;
                }
                if ($week > 51 && $date->month == 1) {
                    --$year;
                }
            }

            $class = 'Kronolith_View_' . $view;
            return new $class($week, $year);

        case 'Year':
            require_once KRONOLITH_BASE . '/lib/Views/Year.php';

            if ($timestamp = (int)Util::getFormData('timestamp')) {
                $year = date('Y', $timestamp);
            } else {
                $year = (int)Util::getFormData('year', date('Y'));
            }
            return new Kronolith_View_Year($year);

        case 'Event':
            require_once KRONOLITH_BASE . '/lib/Views/Event.php';

            if (Util::getFormData('calendar') == '**remote') {
                $event = &Kronolith::getRemoteEventObject(
                    Util::getFormData('remoteCal'),
                    Util::getFormData('eventID'));
            } elseif ($uid = Util::getFormData('uid')) {
                $event = &$GLOBALS['kronolith_driver']->getByUID($uid);
            } else {
                $GLOBALS['kronolith_driver']->open(Util::getFormData('calendar'));
                $event = &$GLOBALS['kronolith_driver']->getEvent(
                    Util::getFormData('eventID'));
            }
            if (!is_a($event, 'PEAR_Error') &&
                !$event->hasPermission(PERMS_READ)) {
                $event = PEAR::raiseError(_("Permission Denied"));
            }

            return new Kronolith_View_Event($event);

        case 'EditEvent':
            require_once KRONOLITH_BASE . '/lib/Views/EditEvent.php';

            if (Util::getFormData('calendar') == '**remote') {
                $event = &Kronolith::getRemoteEventObject(
                    Util::getFormData('remoteCal'),
                    Util::getFormData('eventID'));
            } else {
                $GLOBALS['kronolith_driver']->open(Util::getFormData('calendar'));
                $event = &$GLOBALS['kronolith_driver']->getEvent(
                    Util::getFormData('eventID'));
            }
            if (!is_a($event, 'PEAR_Error') &&
                !$event->hasPermission(PERMS_EDIT)) {
                $event = PEAR::raiseError(_("Permission Denied"));
            }

            return new Kronolith_View_EditEvent($event);

        case 'DeleteEvent':
            require_once KRONOLITH_BASE . '/lib/Views/DeleteEvent.php';

            $GLOBALS['kronolith_driver']->open(Util::getFormData('calendar'));
            $event = &$GLOBALS['kronolith_driver']->getEvent
                (Util::getFormData('eventID'));
            if (!is_a($event, 'PEAR_Error') &&
                !$event->hasPermission(PERMS_DELETE)) {
                $event = PEAR::raiseError(_("Permission Denied"));
            }

            return new Kronolith_View_DeleteEvent($event);

        case 'ExportEvent':
            require_once KRONOLITH_BASE . '/lib/Views/ExportEvent.php';

            if (Util::getFormData('calendar') == '**remote') {
                $event = &Kronolith::getRemoteEventObject(
                    Util::getFormData('remoteCal'),
                    Util::getFormData('eventID'));
            } elseif ($uid = Util::getFormData('uid')) {
                $event = &$GLOBALS['kronolith_driver']->getByUID($uid);
            } else {
                $GLOBALS['kronolith_driver']->open(Util::getFormData('calendar'));
                $event = &$GLOBALS['kronolith_driver']->getEvent(
                    Util::getFormData('eventID'));
            }
            if (!is_a($event, 'PEAR_Error') &&
                !$event->hasPermission(PERMS_READ)) {
                $event = PEAR::raiseError(_("Permission Denied"));
            }

            return new Kronolith_View_ExportEvent($event);
        }
    }

    /**
     * Should we show event location, based on the show_location
     * preference and $print_view?
     */
    function viewShowLocation()
    {
        $show = @unserialize($GLOBALS['prefs']->getValue('show_location'));
        if (!empty($GLOBALS['print_view'])) {
            return @in_array('print', $show);
        } else {
            return @in_array('screen', $show);
        }
    }

    /**
     * Should we show event time, based on the show_time preference
     * and $print_view?
     */
    function viewShowTime()
    {
        $show = @unserialize($GLOBALS['prefs']->getValue('show_time'));
        if (!empty($GLOBALS['print_view'])) {
            return @in_array('print', $show);
        } else {
            return @in_array('screen', $show);
        }
    }

    /**
     * Builds Kronolith's list of menu items.
     */
    function getMenu($returnType = 'object')
    {
        global $conf, $registry, $browser, $prefs;

        /* Check here for guest calendars so that we don't get multiple
         * messages after redirects, etc. */
        if (!Auth::getAuth() && !count($GLOBALS['all_calendars'])) {
            $GLOBALS['notification']->push(_("No calendars are available to guests."));
        }

        require_once 'Horde/Menu.php';
        $menu = new Menu();

        $menu->add(Horde::applicationUrl($prefs->getValue('defaultview') . '.php'), _("_Today"), 'today.png', null, null, null, '__noselection');
        if (Kronolith::getDefaultCalendar(PERMS_EDIT) &&
            (!empty($conf['hooks']['permsdenied']) ||
             Kronolith::hasPermission('max_events') === true ||
             Kronolith::hasPermission('max_events') > Kronolith::countEvents())) {
            $menu->add(Util::addParameter(Horde::applicationUrl('new.php'), 'url', Horde::selfUrl(true, false, true)), _("_New Event"), 'new.png');
        }
        if ($browser->hasFeature('dom')) {
            Horde::addScriptFile('goto.js', 'kronolith');
            $menu->add('#', _("_Goto"), 'goto.png', null, '', 'openKGoto(kronolithTimestamp, event); return false;');
        }
        $menu->add(Horde::applicationUrl('search.php'), _("_Search"), 'search.png', $registry->getImageDir('horde'));

        /* Import/Export. */
        if ($conf['menu']['import_export']) {
            $menu->add(Horde::applicationUrl('data.php'), _("_Import/Export"), 'data.png', $registry->getImageDir('horde'));
        }

        /* Print. */
        if ($conf['menu']['print'] && ($view = Util::nonInputVar('view'))) {
            $menu->add(Util::addParameter($view->link(), 'print', 1), _("_Print"), 'print.png', $registry->getImageDir('horde'), '_blank', 'popup(kronolithPrintLink ? kronolithPrintLink : this.href); return false;', '__noselection');
        }

        if ($returnType == 'object') {
            return $menu;
        } else {
            return $menu->render();
        }
    }

    /**
     * Used with usort() to sort events based on their start times.
     */
    function _sortEventStartTime($a, $b)
    {
        $diff = $a->start->timestamp() - $b->start->timestamp();
        if ($diff == 0) {
            return strcoll($a->title, $b->title);
        } else {
            return $diff;
        }
    }

}
