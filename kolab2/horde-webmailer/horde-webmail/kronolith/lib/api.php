<?php
/**
 * Kronolith external API interface.
 *
 * $Horde: kronolith/lib/api.php,v 1.126.2.65 2009-10-14 13:43:11 jan Exp $
 *
 * This file defines Kronolith's external API interface. Other applications
 * can interact with Kronolith through this API.
 *
 * @package Kronolith
 */

$_services['show'] = array(
    'link' => '%application%/event.php?calendar=|calendar|' .
              '&eventID=|event|&uid=|uid|'
);

$_services['perms'] = array(
    'args' => array(),
    'type' => '{urn:horde}stringArray'
);

$_services['removeUserData'] = array(
    'args' => array('user' => 'string'),
    'type' => 'boolean'
);

$_services['shareHelp'] = array(
    'args' => array(),
    'type' => 'string');

$_services['modified'] = array(
    'args' => array('uid' => 'string'),
    'type' => 'int',
);

$_services['browse'] = array(
    'args' => array('path' => 'string', 'properties' => '{urn:horde}stringArray'),
    'type' => '{urn:horde}hashHash',
);

$_services['put'] = array(
    'args' => array('path' => 'string', 'content' => 'string', 'content_type' => 'string'),
    'type' => '{urn:horde}stringArray',
);

$_services['path_delete'] = array(
    'args' => array('path' => 'string'),
    'type' => 'boolean',
);

$_services['getFreeBusy'] = array(
    'args' => array('startstamp' => 'int', 'endstamp' => 'int', 'calendar' => 'string'),
    'type' => '{urn:horde}stringArray'
);

$_services['listCalendars'] = array(
    'args' => array('owneronly' => 'boolean', 'permission' => 'int'),
    'type' => '{urn:horde}stringArray'
);

$_services['listEvents'] = array(
    'args' => array('startstamp' => 'int', 'endstamp' => 'int', 'calendar' => 'string', 'showRecurrence' => 'string', 'alarmsOnly' => 'boolean'),
    'type' => '{urn:horde}hashHash'
);

$_services['listAlarms'] = array(
    'args' => array('time' => 'int', 'user' => 'string'),
    'type' => '{urn:horde}hashHash'
);

$_services['list'] = array(
    'args' => array(),
    'type' => '{urn:horde}stringArray'
);

$_services['listBy'] = array(
    'args' => array('action' => 'string', 'timestamp' => 'int', 'calendar' => 'string'),
    'type' => '{urn:horde}stringArray'
);

$_services['getActionTimestamp'] = array(
    'args' => array('uid' => 'string', 'action' => 'string', 'calendar' => 'string'),
    'type' => 'int',
);

$_services['import'] = array(
    'args' => array('content' => 'string', 'contentType' => 'string', 'calendar' => 'string'),
    'type' => 'string'
);

$_services['export'] = array(
    'args' => array('uid' => 'string', 'contentType' => 'string'),
    'type' => 'string'
);

$_services['exportCalendar'] = array(
    'args' => array('calendar' => 'string', 'contentType' => 'string'),
    'type' => 'string'
);

$_services['delete'] = array(
    'args' => array('uid' => 'string'),
    'type' => 'boolean'
);

$_services['replace'] = array(
    'args' => array('uid' => 'string', 'content' => 'string', 'contentType' => 'string'),
    'type' => 'boolean'
);

// FIXME: create complex type definition for SOAP calls.
$_services['eventFromUID'] = array(
    'args' => array('uid' => 'string'),
    'type' => 'object'
);

// FIXME: create complex type definition for SOAP calls.
$_services['updateAttendee'] = array(
    'args' => array('response' => 'object', 'sender' => 'string'),
    'type' => 'boolean'
);

$_services['subscribe'] = array(
    'args' => array('calendar' => '{urn:horde}stringArray'),
    'type' => 'boolean',
);

$_services['unsubscribe'] = array(
    'args' => array('calendar' => '{urn:horde}stringArray'),
    'type' => 'boolean',
);

$_services['synchronize'] = array(
    'args' => array(),
    'type' => 'boolean'
);

/**
 * Returns a list of available permissions.
 *
 * @return array  An array describing all available permissions.
 */
function _kronolith_perms()
{
    $perms = array();
    $perms['tree']['kronolith']['max_events'] = false;
    $perms['title']['kronolith:max_events'] = _("Maximum Number of Events");
    $perms['type']['kronolith:max_events'] = 'int';

    return $perms;
}

/**
 * Removes user data.
 *
 * @param string $user  Name of user to remove data for.
 *
 * @return mixed  true on success | PEAR_Error on failure
 */
function _kronolith_removeUserData($user)
{
    if (!Auth::isAdmin() && $user != Auth::getAuth()) {
        return PEAR::raiseError(_("You are not allowed to remove user data."));
    }

    require_once dirname(__FILE__) . '/base.php';
    global $kronolith_driver;

    /* Remove all events owned by the user in all calendars. */
    $result = $kronolith_driver->removeUserData($user);

    /* Now delete history as well. */
    $history = &Horde_History::singleton();
    if (method_exists($history, 'removeByParent')) {
        $histories = $history->removeByParent('kronolith:' . $user);
    } else {
        /* Remove entries 100 at a time. */
        $all = $history->getByTimestamp('>', 0, array(), 'kronolith:' . $user);
        if (is_a($all, 'PEAR_Error')) {
            Horde::logMessage($all, __FILE__, __LINE__, PEAR_LOG_ERR);
        } else {
            $all = array_keys($all);
            while (count($d = array_splice($all, 0, 100)) > 0) {
                $history->removebyNames($d);
            }
        }
    }

    if (is_a($result, 'PEAR_Error')) {
        return $result;
    }

    /* Get the user's default share */
    $share = $GLOBALS['kronolith_shares']->getShare($user);
    if (is_a($share, 'PEAR_Error')) {
        Horde::logMessage($share, __FILE__, __LINE__, PEAR_LOG_ERR);
    } else {
        $result = $GLOBALS['kronolith_shares']->removeShare($share);
        if (is_a($result, 'PEAR_Error')) {
            $hasError = true;
            Horde::logMessage($result->getMessage(), __FILE__, __LINE__, PEAR_LOG_ERR);
        }
    }

    /* Get a list of all shares this user has perms to and remove the perms */
    $shares = $GLOBALS['kronolith_shares']->listShares($user);
    if (is_a($shares, 'PEAR_Error')) {
        Horde::logMessage($shares, __FILE__, __LINE__, PEAR_LOG_ERR);
    }
    foreach ($shares as $share) {
        $share->removeUser($user);
    }

    return true;
}

/**
 * Returns the share helper prefix
 *
 * @return string
 */
function _kronolith_shareHelp()
{
    return 'shares';
}

/**
 * Returns the last modification timestamp for the given uid.
 *
 * @param string $uid      The uid to look for.
 *
 * @return integer  The timestamp for the last modification of $uid.
 */
function _kronolith_modified($uid)
{
    $modified = _kronolith_getActionTimestamp($uid, 'modify');
    if (empty($modified)) {
        $modified = _kronolith_getActionTimestamp($uid, 'add');
    }
    return $modified;
}

/**
 * Browse through Kronolith's object tree.
 *
 * @param string $path       The level of the tree to browse.
 * @param array $properties  The item properties to return. Defaults to 'name',
 *                           'icon', and 'browseable'.
 *
 * @return array  The contents of $path
 */
function _kronolith_browse($path = '', $properties = array())
{
    require_once dirname(__FILE__) . '/base.php';
    global $registry, $kronolith_driver;

    // Default properties.
    if (!$properties) {
        $properties = array('name', 'icon', 'browseable');
    }

    if (substr($path, 0, 9) == 'kronolith') {
        $path = substr($path, 9);
    }
    $path = trim($path, '/');
    $parts = explode('/', $path);

    if (empty($path)) {
        //
        // This request is for a list of all users who have calendars visible
        // to the requesting user.
        //
        $calendars = Kronolith::listCalendars(false, PERMS_READ);
        $owners = array();
        foreach ($calendars as $calendar) {
            $owners[$calendar->get('owner')] = true;
        }

        $results = array();
        foreach (array_keys($owners) as $owner) {
            if (in_array('name', $properties)) {
                $results['kronolith/' . $owner]['name'] = $owner;
            }
            if (in_array('icon', $properties)) {
                $results['kronolith/' . $owner]['icon'] =
                    $registry->getImageDir('horde') . '/user.png';
            }
            if (in_array('browseable', $properties)) {
                $results['kronolith/' . $owner]['browseable'] = true;
            }
            if (in_array('contenttype', $properties)) {
                $results['kronolith/' . $owner]['contenttype'] =
                    'httpd/unix-directory';
            }
            if (in_array('contentlength', $properties)) {
                $results['kronolith/' . $owner]['contentlength'] = 0;
            }
            if (in_array('modified', $properties)) {
                $results['kronolith/' . $owner]['modified'] =
                    $_SERVER['REQUEST_TIME'];
            }
            if (in_array('created', $properties)) {
                $results['kronolith/' . $owner]['created'] = 0;
            }
        }
        return $results;

    } elseif (count($parts) == 1) {
        //
        // This request is for all calendars owned by the requested user
        //
        $calendars = $GLOBALS['kronolith_shares']->listShares(Auth::getAuth(),
                                                              PERMS_SHOW,
                                                              $parts[0]);
        $results = array();
        foreach ($calendars as $calendarId => $calendar) {
            $retpath = 'kronolith/' . $parts[0] . '/' . $calendarId;
            if (in_array('name', $properties)) {
                $results[$retpath]['name'] = sprintf(_("Events from %s"), $calendar->get('name'));
                $results[$retpath . '.ics']['name'] = $calendar->get('name');
            }
            if (in_array('displayname', $properties)) {
                $results[$retpath]['displayname'] = rawurlencode($calendar->get('name'));
                $results[$retpath . '.ics']['displayname'] = rawurlencode($calendar->get('name')) . '.ics';
            }
            if (in_array('icon', $properties)) {
                $results[$retpath]['icon'] = $registry->getImageDir() . '/kronolith.png';
                $results[$retpath . '.ics']['icon'] = $registry->getImageDir() . '/mime/icalendar.png';
            }
            if (in_array('browseable', $properties)) {
                $results[$retpath]['browseable'] = $calendar->hasPermission(Auth::getAuth(), PERMS_READ);
                $results[$retpath . '.ics']['browseable'] = false;
            }
            if (in_array('contenttype', $properties)) {
                $results[$retpath]['contenttype'] = 'httpd/unix-directory';
                $results[$retpath . '.ics']['contenttype'] = 'text/calendar';
            }
            if (in_array('contentlength', $properties)) {
                $results[$retpath]['contentlength'] = 0;
                // FIXME:  This is a hack.  If the content length is longer
                // than the actual data then some WebDAV clients will report
                // an error when the file EOF is received.  Ideally we should
                // determine the actual size of the .ics and report it here, but
                // the performance hit may be prohibitive.  This requires
                // further investigation.
                $results[$retpath . '.ics']['contentlength'] = 1;
            }
            if (in_array('modified', $properties)) {
                $results[$retpath]['modified'] = $_SERVER['REQUEST_TIME'];
                $results[$retpath . '.ics']['modified'] = $_SERVER['REQUEST_TIME'];
            }
            if (in_array('created', $properties)) {
                $results[$retpath]['created'] = 0;
                $results[$retpath . '.ics']['created'] = 0;
            }
        }
        return $results;

    } elseif (count($parts) == 2 &&
              array_key_exists($parts[1],
                               Kronolith::listCalendars(false, PERMS_READ))) {
        //
        // This request is browsing into a specific calendar.  Generate the list
        // of items and represent them as files within the directory.
        //
        $kronolith_driver->open($parts[1]);
        $events = $kronolith_driver->listEvents();
        if (is_a($events, 'PEAR_Error')) {
            return $events;
        }

        $icon = $registry->getImageDir('horde') . '/mime/icalendar.png';
        $results = array();
        foreach ($events as $uid => $eventId) {
            $event = $kronolith_driver->getEvent($eventId);
            if (is_a($event, 'PEAR_Error')) {
                continue;
            }
            $key = 'kronolith/' . $path . '/' . $eventId;
            if (in_array('name', $properties)) {
                $results[$key]['name'] = $event->getTitle();
            }
            if (in_array('icon', $properties)) {
                $results[$key]['icon'] = $icon;
            }
            if (in_array('browseable', $properties)) {
                $results[$key]['browseable'] = false;
            }
            if (in_array('contenttype', $properties)) {
                $results[$key]['contenttype'] = 'text/calendar';
            }
            if (in_array('contentlength', $properties)) {
                // FIXME:  This is a hack.  If the content length is longer
                // than the actual data then some WebDAV clients will report
                // an error when the file EOF is received.  Ideally we should
                // determine the actual size of the data and report it here, but
                // the performance hit may be prohibitive.  This requires
                // further investigation.
                $results[$key]['contentlength'] = 1;
            }
            if (in_array('modified', $properties)) {
                $results[$key]['modified'] = _kronolith_modified($uid);
            }
            if (in_array('created', $properties)) {
                $results[$key]['created'] = _kronolith_getActionTimestamp($uid, 'add');
            }
        }
        return $results;
    } else {
        //
        // The only valid request left is for either a specific event
        // or for the entire calendar.
        //
        if (count($parts) == 3 &&
            array_key_exists($parts[1],
                             Kronolith::listCalendars(false, PERMS_READ))) {
            //
            // This request is for a specific item within a given calendar.
            //
            global $kronolith_driver;
            if ($kronolith_driver->getCalendar() != $parts[1]) {
                $kronolith_driver->open($parts[1]);
            }
            $event = &$kronolith_driver->getEvent($parts[2]);
            if (is_a($event, 'PEAR_Error')) {
                return $event;
            }

            $result = array(
                'data' => _kronolith_export($event->getUID(), 'text/calendar'),
                'mimetype' => 'text/calendar');
            $modified = _kronolith_modified($event->getUID());
            if (!empty($modified)) {
                $result['mtime'] = $modified;
            }
            return $result;
        } elseif (count($parts) == 2 &&
                  substr($parts[1], -4, 4) == '.ics' &&
                  array_key_exists(
                      substr($parts[1], 0, -4),
                      Kronolith::listCalendars(false, PERMS_READ))) {
            //
            // This request is for an entire calendar (calendar.ics).
            //
            $ical_data = _kronolith_exportCalendar(substr($parts[1], 0, -4), 'text/calendar');
            $result = array('data'          => $ical_data,
                            'mimetype'      => 'text/calendar',
                            'contentlength' => strlen($ical_data),
                            'mtime'         => $_SERVER['REQUEST_TIME']);

            return $result;
        } else {
            //
            // All other requests are a 404: Not Found
            //
            return false;
        }
    }
}

/**
 * Saves a file into the Kronolith tree.
 *
 * @param string $path          The path where to PUT the file.
 * @param string $content       The file content.
 * @param string $content_type  The file's content type.
 *
 * @return array  The event UIDs, or a PEAR_Error on failure.
 */
function _kronolith_put($path, $content, $content_type)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith_driver;

    if (substr($path, 0, 9) == 'kronolith') {
        $path = substr($path, 9);
    }
    $path = trim($path, '/');
    $parts = explode('/', $path);

    if (count($parts) == 2 &&
        substr($parts[1], -4) == '.ics') {

        // Workaround for WebDAV clients that are not smart enough to send
        // the right content type.  Assume text/calendar.
        if ($content_type == 'application/octet-stream') {
            $content_type = 'text/calendar';
        }
        $calendar = substr($parts[1], 0, -4);
    } elseif (count($parts) == 3) {
        $calendar = $parts[1];

        // Workaround for WebDAV clients that are not smart enough to send
        // the right content type.  Assume text/calendar.
        if ($content_type == 'application/octet-stream') {
            $content_type = 'text/calendar';
        }
    } else {
        return PEAR::raiseError("Invalid calendar data supplied.");
    }

    if (!array_key_exists($calendar, Kronolith::listCalendars(false, PERMS_EDIT))) {
        // FIXME: Should we attempt to create a calendar based on the filename
        // in the case that the requested calendar does not exist?
        return PEAR::raiseError("Calendar does not exist or no permission to edit");
    }

    // Store all currently existings UIDs. Use this info to delete UIDs not
    // present in $content after processing.
    $ids = array();
    $uids_remove = array_flip(_kronolith_list($calendar));

    switch ($content_type) {
    case 'text/calendar':
    case 'text/x-vcalendar':
        require_once 'Horde/iCalendar.php';
        $iCal = new Horde_iCalendar();
        if (!is_a($content, 'Horde_iCalendar_vevent')) {
            if (!$iCal->parsevCalendar($content)) {
                return PEAR::raiseError(_("There was an error importing the iCalendar data."));
            }
        } else {
            $iCal->addComponent($content);
        }

        foreach ($iCal->getComponents() as $content) {
            if (is_a($content, 'Horde_iCalendar_vevent')) {
                $event = &$kronolith_driver->getEvent();
                $event->fromiCalendar($content);
                $event->setCalendar($calendar);
                $uid = $event->getUID();
                // Remove from uids_remove list so we won't delete in
                // the end.
                if (isset($uids_remove[$uid])) {
                    unset($uids_remove[$uid]);
                }
                $existing_event = &$kronolith_driver->getByUID(
                    $uid, array($calendar));
                if (!is_a($existing_event, 'PEAR_Error')) {
                    // Check if our event is newer then the existing - get the
                    // event's history.
                    $history = &Horde_History::singleton();
                    $created = $modified = null;
                    $log = $history->getHistory('kronolith:' . $calendar . ':'
                                                . $uid);
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
                    if (empty($modified) && !empty($created)) {
                        $modified = $created;
                    }
                    if (!empty($modified) &&
                        $modified >= $content->getAttribute('LAST-MODIFIED')) {
                        // LAST-MODIFIED timestamp of existing entry is newer:
                        // don't replace it.
                        continue;
                    }

                    // Don't change creator/owner.
                    $event->setCreatorId($existing_event->getCreatorId());
                }

                // Save entry.
                $saved = $event->save();
                if (is_a($saved, 'PEAR_Error')) {
                    return $saved;
                }
                $ids[] = $event->getUID();
            }
        }
        break;

    default:
        return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"), $content_type));
    }

    if (array_key_exists($calendar, Kronolith::listCalendars(false, PERMS_DELETE))) {
        foreach (array_keys($uids_remove) as $uid) {
            _kronolith_delete($uid);
        }
    }

    return $ids;
}

/**
 * Deletes a file from the Kronolith tree.
 *
 * @param string $path  The path to the file.
 *
 * @return mixed  The event's UID, or a PEAR_Error on failure.
 */
function _kronolith_path_delete($path)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith_driver;

    if (substr($path, 0, 9) == 'kronolith') {
        $path = substr($path, 9);
    }
    $path = trim($path, '/');
    $parts = explode('/', $path);

    if (substr($parts[1], -4) == '.ics') {
        $calendarId = substr($parts[1], 0, -4);
    } else {
        $calendarId = $parts[1];
    }

    if (!(count($parts) == 2 || count($parts) == 3) ||
        !array_key_exists($calendarId, Kronolith::listCalendars(false, PERMS_DELETE))) {
        return PEAR::raiseError("Calendar does not exist or no permission to delete");
    }

    if (count($parts) == 3) {
        // Delete just a single entry
        $kronolith_driver->open($calendarId);
        return $kronolith_driver->deleteEvent($parts[2]);
    } else {
        // Delete the entire calendar
        $result = $kronolith_driver->delete($calendarId);
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to delete calendar \"%s\": %s"), $calendarId, $result->getMessage()));
        } else {
            // Remove share and all groups/permissions.
            $share = $GLOBALS['kronolith_shares']->getShare($calendarId);
            $result = $GLOBALS['kronolith_shares']->removeShare($share);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
    }
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
function _kronolith_listCalendars($owneronly = false, $permission = null)
{
    require_once dirname(__FILE__) . '/base.php';
    if (is_null($permission)) {
        $permission = PERMS_SHOW;
    }
    return array_keys(Kronolith::listCalendars($owneronly, $permission));
}

/**
 * Returns all the events that happen within a time period.
 *
 * @param string $calendar      The calendar to check for events.
 * @param object $startstamp    The start of the time range.
 * @param object $endstamp      The end of the time range.
 *
 * @return array  The events happening in this time period.
 */
function _kronolith_list($calendar = null, $startstamp = 0, $endstamp = 0)
{
    require_once dirname(__FILE__) . '/base.php';

    if (empty($calendar)) {
        $calendar = Kronolith::getDefaultCalendar();
    }
    if (!array_key_exists($calendar,
                          Kronolith::listCalendars(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $ids = Kronolith::listEventIds($startstamp, $endstamp, $calendar);
    if (is_a($ids, 'PEAR_Error')) {
        return $ids;
    }

    $uids = array();
    foreach ($ids as $cal) {
        $uids = array_merge($uids, array_keys($cal));
    }

    return $uids;
}

/**
 * Returns an array of UIDs for events that have had $action happen since
 * $timestamp.
 *
 * @param string  $action     The action to check for - add, modify, or delete.
 * @param integer $timestamp  The time to start the search.
 * @param string  $calendar   The calendar to search in.
 *
 * @return array  An array of UIDs matching the action and time criteria.
 */
function _kronolith_listBy($action, $timestamp, $calendar = null)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith_driver;

    if (empty($calendar)) {
        $calendar = Kronolith::getDefaultCalendar();
    }

    if (!array_key_exists($calendar,
                          Kronolith::listCalendars(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $kronolith_driver->open($calendar);

    $history = &Horde_History::singleton();
    $histories = $history->getByTimestamp('>', $timestamp, array(array('op' => '=', 'field' => 'action', 'value' => $action)), 'kronolith:' . $calendar);
    if (is_a($histories, 'PEAR_Error')) {
        return $histories;
    }

    // Strip leading kronolith:username:.
    return preg_replace('/^([^:]*:){2}/', '', array_keys($histories));
}

/**
 * Returns the timestamp of an operation for a given uid an action
 *
 * @param string $uid      The uid to look for.
 * @param string $action   The action to check for - add, modify, or delete.
 * @param string $calendar The calendar to search in.
 *
 * @return integer  The timestamp for this action.
 */
function _kronolith_getActionTimestamp($uid, $action, $calendar = null)
{
    require_once dirname(__FILE__) . '/base.php';

    if (empty($calendar)) {
        $calendar = Kronolith::getDefaultCalendar();
    }

    if (!array_key_exists($calendar,
                          Kronolith::listCalendars(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $history = &Horde_History::singleton();
    return $history->getActionTimestamp('kronolith:' . $calendar . ':' .
                                        $uid, $action);
}

/**
 * Imports an event represented in the specified content type.
 *
 * @param string $content      The content of the event.
 * @param string $contentType  What format is the data in? Currently supports:
 *                             <pre>
 *                             text/calendar
 *                             text/x-vcalendar
 *                             </pre>
 * @param string $calendar     What calendar should the event be added to?
 *
 * @return mixed  The event's UID, or a PEAR_Error on failure.
 */
function _kronolith_import($content, $contentType, $calendar = null)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith_driver;

    if (!isset($calendar)) {
        $calendar = Kronolith::getDefaultCalendar(PERMS_EDIT);
    }
    if (!array_key_exists($calendar,
                          Kronolith::listCalendars(false, PERMS_EDIT))) {
        return PEAR::raiseError(_("Permission Denied"));
    }
    $kronolith_driver->open($calendar);

    switch ($contentType) {
    case 'text/calendar':
    case 'text/x-vcalendar':
        require_once 'Horde/iCalendar.php';
        $iCal = new Horde_iCalendar();
        if (!is_a($content, 'Horde_iCalendar_vevent')) {
            if (!$iCal->parsevCalendar($content)) {
                return PEAR::raiseError(_("There was an error importing the iCalendar data."));
            }
        } else {
            $iCal->addComponent($content);
        }

        $components = $iCal->getComponents();
        if (count($components) == 0) {
            return PEAR::raiseError(_("No iCalendar data was found."));
        }

        $ids = array();
        foreach ($components as $content) {
            if (is_a($content, 'Horde_iCalendar_vevent')) {
                $event = &$kronolith_driver->getEvent();
                $event->fromiCalendar($content);
                $event->setCalendar($calendar);
                // Check if the entry already exists in the data source, first
                // by UID.
                $uid = $event->getUID();
                $existing_event = &$kronolith_driver->getByUID(
                    $uid, array($calendar));
                if (!is_a($existing_event, 'PEAR_Error')) {
                    return PEAR::raiseError(_("Already Exists"),
                                            'horde.message', null, null, $uid);
                }
                $result = $kronolith_driver->search($event);
                // Check if the match really is an exact match:
                if (is_array($result) && count($result) > 0) {
                    foreach($result as $match) {
                        if ($match->start == $event->start &&
                            $match->end == $event->end &&
                            $match->title == $event->title &&
                            $match->location == $event->location &&
                            $match->hasPermission(PERMS_EDIT)) {
                            return PEAR::raiseError(_("Already Exists"), 'horde.message', null, null, $match->getUID());
                        }
                    }
                }

                $eventId = $event->save();
                if (is_a($eventId, 'PEAR_Error')) {
                    return $eventId;
                }
                $ids[] = $event->getUID();
            }
        }
        if (count($ids) == 0) {
            return PEAR::raiseError(_("No iCalendar data was found."));
        } else if (count($ids) == 1) {
            return $ids[0];
        }
        return $ids;
    }

    return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"), $contentType));
}

/**
 * Exports an event, identified by UID, in the requested content type.
 *
 * @param string $uid         Identify the event to export.
 * @param string $contentType  What format should the data be in?
 *                            A string with one of:
 *                            <pre>
 *                             text/calendar (VCALENDAR 2.0. Recommended as
 *                                            this is specified in rfc2445)
 *                             text/x-vcalendar (old VCALENDAR 1.0 format.
 *                                              Still in wide use)
 *                            </pre>
 *
 * @return string  The requested data.
 */
function _kronolith_export($uid, $contentType)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith_driver, $kronolith_shares;

    $event = $kronolith_driver->getByUID($uid);
    if (is_a($event, 'PEAR_Error')) {
        return $event;
    }
    if (!$event->hasPermission(PERMS_READ)) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $version = '2.0';
    switch ($contentType) {
    case 'text/x-vcalendar':
        $version = '1.0';
    case 'text/calendar':
        $share = &$kronolith_shares->getShare($event->getCalendar());

        require_once 'Horde/iCalendar.php';
        $iCal = new Horde_iCalendar($version);
        $iCal->setAttribute('X-WR-CALNAME', String::convertCharset($share->get('name'), NLS::getCharset(), 'utf-8'));

        // Create a new vEvent.
        $vEvent = &$event->toiCalendar($iCal);
        $iCal->addComponent($vEvent);

        return $iCal->exportvCalendar();

    }

    return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"), $contentType));;
}

/**
 * Exports a calendar in the requested content type.
 *
 * @param string $calendar    The calendar to export.
 * @param string $contentType  What format should the data be in?
 *                             A string with one of:
 *                             <pre>
 *                             text/calendar (VCALENDAR 2.0. Recommended as
 *                                            this is specified in rfc2445)
 *                             text/x-vcalendar (old VCALENDAR 1.0 format.
 *                                              Still in wide use)
 *                             </pre>
 *
 * @return string  The iCalendar representation of the calendar.
 */
function _kronolith_exportCalendar($calendar, $contentType)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith_driver, $kronolith_shares;

    if (!array_key_exists($calendar,
                          Kronolith::listCalendars(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    if ($kronolith_driver->getCalendar() != $calendar) {
        $kronolith_driver->open($calendar);
    }

    $events = $kronolith_driver->listEvents();

    $version = '2.0';
    switch ($contentType) {
    case 'text/x-vcalendar':
        $version = '1.0';
    case 'text/calendar':
        $share = &$kronolith_shares->getShare($calendar);

        require_once 'Horde/iCalendar.php';
        $iCal = new Horde_iCalendar($version);
        $iCal->setAttribute('X-WR-CALNAME', String::convertCharset($share->get('name'), NLS::getCharset(), 'utf-8'));

        foreach ($events as $id) {
            $event = &$kronolith_driver->getEvent($id);
            if (is_a($event, 'PEAR_Error')) {
                return $event;
            }
            $vEvent = &$event->toiCalendar($iCal);
            $iCal->addComponent($vEvent);
        }

        return $iCal->exportvCalendar();
    }

    return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"), $contentType));
}

/**
 * Deletes an event identified by UID.
 *
 * @param string|array $uid  A single UID or an array identifying the event(s)
 *                           to delete.
 *
 * @return boolean  Success or failure.
 */
function _kronolith_delete($uid)
{
    // Handle an array of UIDs for convenience of deleting multiple events at
    // once.
    if (is_array($uid)) {
        foreach ($uid as $g) {
            $result = _kronolith_delete($g);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return true;
    }

    require_once dirname(__FILE__) . '/base.php';
    global $kronolith_driver;

    $events = $kronolith_driver->getByUID($uid, null, true);
    if (is_a($events, 'PEAR_Error')) {
        return $events;
    }

    $event = null;
    if (Auth::isAdmin()) {
        $event = $events[0];
    }

    // First try the user's own calendars.
    if (empty($event)) {
        $ownerCalendars = Kronolith::listCalendars(true, PERMS_DELETE);
        foreach ($events as $ev) {
            if (Auth::isAdmin() || isset($ownerCalendars[$ev->getCalendar()])) {
                $event = $ev;
                break;
            }
        }
    }

    // If not successful, try all calendars the user has access to.
    if (empty($event)) {
        $deletableCalendars = Kronolith::listCalendars(false, PERMS_DELETE);
        foreach ($events as $ev) {
            if (isset($deletableCalendars[$ev->getCalendar()])) {
                $kronolith_driver->open($ev->getCalendar());
                $event = $ev;
                break;
            }
        }
    }

    if (empty($event)) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    return $kronolith_driver->deleteEvent($event->getId());
}

/**
 * Replaces the event identified by UID with the content represented in the
 * specified contentType.
 *
 * @param string $uid          Idenfity the event to replace.
 * @param mixed  $content      The content of the event. String or
 *                             Horde_iCalendar_vevent
 * @param string $contentType  What format is the data in? Currently supports:
 *                             text/calendar
 *                             text/x-vcalendar
 *                             (Ignored if content is Horde_iCalendar_vevent)
 *
 * @return mixed  True on success, PEAR_Error otherwise.
 */
function _kronolith_replace($uid, $content, $contentType)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith_driver;

    $event = $kronolith_driver->getByUID($uid);
    if (is_a($event, 'PEAR_Error')) {
        return $event;
    }

    if (!$event->hasPermission(PERMS_EDIT) ||
        ($event->isPrivate() && $event->getCreatorId() != Auth::getAuth())) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    if (is_a($content, 'Horde_iCalendar_vevent')) {
        $component = $content;
    } else {
        switch ($contentType) {
        case 'text/calendar':
        case 'text/x-vcalendar':
            if (!is_a($content, 'Horde_iCalendar_vevent')) {
                require_once 'Horde/iCalendar.php';
                $iCal = new Horde_iCalendar();
                if (!$iCal->parsevCalendar($content)) {
                    return PEAR::raiseError(_("There was an error importing the iCalendar data."));
                }

                $components = $iCal->getComponents();
                $component = null;
                foreach ($components as $content) {
                    if (is_a($content, 'Horde_iCalendar_vevent')) {
                        if ($component !== null) {
                            return PEAR::raiseError(_("Multiple iCalendar components found; only one vEvent is supported."));
                        }
                        $component = $content;
                    }

                }
                if ($component === null) {
                    return PEAR::raiseError(_("No iCalendar data was found."));
                }
            }
            break;
        default:
            return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"), $contentType));
        }
    }

    $event->fromiCalendar($component);
    // Ensure we keep the original UID, even when content does not
    // contain one and fromiCalendar creates a new one.
    $event->setUID($uid);
    $eventId = $event->save();

    return is_a($eventId, 'PEAR_Error') ? $eventId : true;
}

/**
 * Generates free/busy information for a given time period.
 *
 * @param integer $startstamp  The start of the time period to retrieve.
 * @param integer $endstamp    The end of the time period to retrieve.
 * @param string $calendar     The calendar to view free/busy slots for.
 *                             Defaults to the user's default calendar.
 *
 * @return Horde_iCalendar_vfreebusy  A freebusy object that covers the
 *                                    specified time period.
 */
function _kronolith_getFreeBusy($startstamp = null, $endstamp = null,
                                $calendar = null)
{
    require_once dirname(__FILE__) . '/base.php';
    require_once KRONOLITH_BASE . '/lib/FreeBusy.php';

    if (is_null($calendar)) {
        $calendar = Kronolith::getDefaultCalendar();
    }
    // Free/Busy information is globally available; no permission
    // check is needed.

    return Kronolith_FreeBusy::generate($calendar, $startstamp, $endstamp, true);
}

/**
 * Retrieves a Kronolith_Event object, given an event UID.
 *
 * @param string $uid  The event's UID.
 *
 * @return Kronolith_Event  A valid Kronolith_Event on success, or a PEAR_Error
 *                          on failure.
 */
function &_kronolith_eventFromUID($uid)
{
    require_once dirname(__FILE__) . '/base.php';

    $event = $GLOBALS['kronolith_driver']->getByUID($uid);
    if (is_a($event, 'PEAR_Error')) {
        return $event;
    }
    if (!$event->hasPermission(PERMS_SHOW)) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    return $event;
}

/**
 * Updates an attendee's response status for a specified event.
 *
 * @param Horde_iCalender_vevent $response  A Horde_iCalender_vevent object,
 *                                          with a valid UID attribute that
 *                                          points to an existing event.
 *                                          This is typically the vEvent
 *                                          portion of an iTip meeting-request
 *                                          response, with the attendee's
 *                                          response in an ATTENDEE parameter.
 * @param string $sender                    The email address of the person
 *                                          initiating the update. Attendees
 *                                          are only updated if this address
 *                                          matches.
 *
 * @return mixed  True on success, PEAR_Error on failure.
 */
function _kronolith_updateAttendee($response, $sender = null)
{
    require_once dirname(__FILE__) . '/base.php';

    $uid = $response->getAttribute('UID');
    if (is_a($uid, 'PEAR_Error')) {
        return $uid;
    }

    $events = $GLOBALS['kronolith_driver']->getByUID($uid, null, true);
    if (is_a($events, 'PEAR_Error')) {
        return $events;
    }

    /* First try the user's own calendars. */
    $ownerCalendars = Kronolith::listCalendars(true, PERMS_EDIT);
    $event = null;
    foreach ($events as $ev) {
        if (isset($ownerCalendars[$ev->getCalendar()])) {
            $event = $ev;
            break;
        }
    }

    /* If not successful, try all calendars the user has access to. */
    if (empty($event)) {
        $editableCalendars = Kronolith::listCalendars(false, PERMS_EDIT);
        foreach ($events as $ev) {
            if (isset($editableCalendars[$ev->getCalendar()])) {
                $event = $ev;
                break;
            }
        }
    }

    if (empty($event) ||
        ($event->isPrivate() && $event->getCreatorId() != Auth::getAuth())) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $atnames = $response->getAttribute('ATTENDEE');
    if (!is_array($atnames)) {
        $atnames = array($atnames);
    }
    $atparms = $response->getAttribute('ATTENDEE', true);

    $found = false;
    $error = _("No attendees have been updated because none of the provided email addresses have been found in the event's attendees list.");
    $sender_lcase = String::lower($sender);
    foreach ($atnames as $index => $attendee) {
        $attendee = str_replace('mailto:', '', String::lower($attendee));
        $name = isset($atparms[$index]['CN']) ? $atparms[$index]['CN'] : null;
        if ($event->hasAttendee($attendee)) {
            if (is_null($sender) || $sender_lcase == $attendee) {
                $event->addAttendee($attendee, KRONOLITH_PART_IGNORE, Kronolith::responseFromICal($atparms[$index]['PARTSTAT']), $name);
                $found = true;
            } else {
                $error = _("The attendee hasn't been updated because the update was not sent from the attendee.");
            }
        }
    }

    $result = $event->save();
    if (is_a($result, 'PEAR_Error')) {
        return $result;
    }

    if (!$found) {
        return PEAR::raiseError($error);
    }

    return true;
}

/**
 * Lists events for a given time period.
 *
 * @param integer $startstamp      The start of the time period to retrieve.
 * @param integer $endstamp        The end of the time period to retrieve.
 * @param array   $calendars       The calendars to view events from.
 *                                 Defaults to the user's default calendar.
 * @param boolean $showRecurrence  Return every instance of a recurring event?
 *                                 If false, will only return recurring events
 *                                 once inside the $startDate - $endDate range.
 * @param boolean $alarmsOnly      Filter results for events with alarms.
 *                                 Defaults to false.
 *
 * @return array  A list of event hashes.
 */
function _kronolith_listEvents($startstamp = null, $endstamp = null,
                               $calendars = null, $showRecurrence = true,
                               $alarmsOnly = false)
{
    require_once dirname(__FILE__) . '/base.php';

    if (!isset($calendars)) {
        $calendars = array($GLOBALS['prefs']->getValue('default_share'));
    } elseif (!is_array($calendars)) {
        $calendars = array($calendars);
    }
    $allowed_calendars = Kronolith::listCalendars(false, PERMS_READ);
    foreach ($calendars as $calendar) {
        if (!array_key_exists($calendar, $allowed_calendars)) {
            return PEAR::raiseError(_("Permission Denied"));
        }
    }

    return Kronolith::listEvents($startstamp, $endstamp, $calendars, $showRecurrence, $alarmsOnly);
}

/**
 * Lists alarms for a given moment.
 *
 * @param integer $time  The time to retrieve alarms for.
 * @param string $user   The user to retrieve alarms for. All users if null.
 *
 * @return array  An array of UIDs
 */
function _kronolith_listAlarms($time, $user = null)
{
    require_once dirname(__FILE__) . '/base.php';
    require_once 'Horde/Group.php';

    $current_user = Auth::getAuth();
    if ((empty($user) || $user != $current_user) && !Auth::isAdmin()) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $group = &Group::singleton();
    $alarm_list = array();
    $time = new Horde_Date($time);
    $calendars = is_null($user) ? array_keys($GLOBALS['kronolith_shares']->listAllShares()) : $GLOBALS['display_calendars'];
    $alarms = Kronolith::listAlarms($time, $calendars, true);
    if (is_a($alarms, 'PEAR_Error')) {
        return $alarms;
    }
    foreach ($alarms as $calendar => $cal_alarms) {
        if (!$cal_alarms) {
            continue;
        }
        $share = $GLOBALS['kronolith_shares']->getShare($calendar);
        if (is_a($share, 'PEAR_Error')) {
            continue;
        }
        if (empty($user)) {
            $users = $share->listUsers(PERMS_READ);
            $groups = $share->listGroups(PERMS_READ);
            foreach ($groups as $gid) {
                $group_users = $group->listUsers($gid);
                if (!is_a($group_users, 'PEAR_Error')) {
                    $users = array_merge($users, $group_users);
                }
            }
            $users = array_unique($users);
        } else {
            $users = array($user);
        }
        $owner = $share->get('owner');
        foreach ($cal_alarms as $event) {
            foreach ($users as $alarm_user) {
                if ($alarm_user == $current_user) {
                    $prefs = &$GLOBALS['prefs'];
                } else {
                    $prefs = &Prefs::singleton($GLOBALS['conf']['prefs']['driver'],
                                               'kronolith', $alarm_user, null,
                                               null, false);
                }
                $shown_calendars = unserialize($prefs->getValue('display_cals'));
                $reminder = $prefs->getValue('event_reminder');
                if (($reminder == 'owner' && $alarm_user == $owner) ||
                    ($reminder == 'show' && in_array($calendar, $shown_calendars)) ||
                    $reminder == 'read') {
                    NLS::setLang($prefs->getValue('language'));
                    NLS::setTextdomain('kronolith', KRONOLITH_BASE . '/locale', NLS::getCharset());
                    String::setDefaultCharset(NLS::getCharset());
                    $alarm = $event->toAlarm($time, $alarm_user, $prefs);
                    if ($alarm) {
                        $alarm_list[] = $alarm;
                    }
                }
            }
        }
    }

    return $alarm_list;
}

/**
 * Subscribe to a calendar.
 *
 * @param array $calendar  Calendar description hash, with required 'type'
 *                         parameter. Currently supports 'http' and 'webcal'
 *                         for remote calendars.
 */
function _kronolith_subscribe($calendar)
{
    if (!isset($calendar['type'])) {
        return PEAR::raiseError(_("Unknown calendar protocol"));
    }

    switch ($calendar['type']) {
    case 'http':
    case 'webcal':
        $username = isset($calendar['username']) ? $calendar['username'] : null;
        $password = isset($calendar['password']) ? $calendar['password'] : null;

        $cals = unserialize($GLOBALS['prefs']->getValue('remote_cals'));
        if (!is_array($cals)) {
            $cals = array();
        }
        $array_key = count($cals);
        foreach ($cals as $key => $cal) {
            if ($cal['url'] == $calendar['url']) {
                $array_key = $key;
                break;
            }
        }

        $cals[$array_key] = array('name' => $calendar['name'],
                                  'url'  => $calendar['url'],
                                  'user' => $username,
                                  'password' => $password);
        $GLOBALS['prefs']->setValue('remote_cals', serialize($cals));
        break;

    case 'external':
        $cals = unserialize($GLOBALS['prefs']->getValue('display_external_cals'));
        if (array_search($calendar['name'], $cals) === false) {
            $cals[] = $calendar['name'];
            $GLOBALS['prefs']->setValue('display_external_cals', serialize($cals));
        }

    default:
        return PEAR::raiseError(_("Unknown calendar protocol"));
    }
}

/**
 * Unsubscribe from a calendar.
 *
 * @param array $calendar  Calendar description array, with required 'type'
 *                         parameter. Currently supports 'http' and 'webcal'
 *                         for remote calendars.
 */
function _kronolith_unsubscribe($calendar)
{
    if (!isset($calendar['type'])) {
        return PEAR::raiseError('Unknown calendar specification');
    }

    switch ($calendar['type']) {
    case 'http':
    case 'webcal':
        $cals = unserialize($GLOBALS['prefs']->getValue('remote_cals'));
        foreach ($cals as $key => $cal) {
            if ($cal['url'] == $calendar['url']) {
                unset($cals[$key]);
                break;
            }
        }

        $GLOBALS['prefs']->setValue('remote_cals', serialize($cals));
        break;

    case 'external':
        $cals = unserialize($GLOBALS['prefs']->getValue('display_external_cals'));
        if (($key = array_search($calendar['name'], $cals)) !== false) {
            unset($cals[$key]);
            $GLOBALS['prefs']->setValue('display_external_cals', serialize($cals));
        }

    default:
        return PEAR::raiseError('Unknown calendar specification');
    }
}

/**
 * Synchronizes kronolith with the IMAP backend
 *
 * @return boolean  False if something went wrong
 */
function _kronolith_synchronize()
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith_driver;

    $calendar = Kronolith::getDefaultCalendar();

    if (!array_key_exists($calendar,
                          Kronolith::listCalendars(false, PERMS_READ))) {
        return False;
    }

    $kronolith_driver->open($calendar);

    if (get_class ($kronolith_driver) == 'Kronolith_Driver_kolab' &&
        get_class ($kronolith_driver->_wrapper) == 'Kronolith_Driver_kolab_wrapper_new') {

        $kronolith_driver->_wrapper->synchronize (true);

        if (get_class ($kronolith_driver->_wrapper->_store) == 'Kolab_IMAP') {
            $kronolith_driver->_wrapper->_store->_synchronize ();
        }
    }

    return True;
}
