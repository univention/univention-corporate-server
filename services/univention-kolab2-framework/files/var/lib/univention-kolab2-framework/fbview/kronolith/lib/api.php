<?php
/**
 * Kronolith external API interface.
 *
 * $Horde: kronolith/lib/api.php,v 1.113 2004/05/29 21:12:47 jan Exp $
 *
 * This file defines Kronolith's external API interface. Other
 * applications can interact with Kronolith through this API.
 *
 * @package Kronolith
 */

$_services['show'] = array(
    'link' => '%application%/viewevent.php?calendar=|calendar|' .
                ini_get('arg_separator.output') . 'eventID=|event|' .
                ini_get('arg_separator.output') . 'guid=|guid|'
);

$_services['block'] = array(
    'args' => array('type' => 'string', 'params' => 'stringArray'),
    'type' => 'stringArray'
);

$_services['defineBlock'] = array(
    'args' => array('type' => 'string'),
    'type' => 'string'
);

$_services['getFreeBusy'] = array(
    'args' => array('startstamp' => 'int', 'endstamp' => 'int', 'calendar' => 'string'),
    'type' => 'stringArray'
);

$_services['listCalendars'] = array(
    'args' => array('owneronly' => 'boolean', 'permission' => 'int'),
    'type' => 'stringArray'
);

$_services['list'] = array(
    'args' => array(),
    'type' => 'stringArray'
);

$_services['listBy'] = array(
    'args' => array('action' => 'string', 'timestamp' => 'int'),
    'type' => 'stringArray'
);

$_services['import'] = array(
    'args' => array('content' => 'string', 'contentType' => 'string', 'calendar' => 'string'),
    'type' => 'integer'
);

$_services['export'] = array(
    'args' => array('guid' => 'string', 'contentType' => 'string'),
    'type' => 'string'
);

$_services['remove'] = array(
    'args' => array('guid' => 'string'),
    'type' => 'boolean'
);

$_services['replace'] = array(
    'args' => array('guid' => 'string', 'content' => 'string', 'contentType' => 'string'),
    'type' => 'boolean'
);

$_services['eventFromGUID'] = array(
    'args' => array('guid' => 'string'),
    'type' => 'object'
);

$_services['updateAttendee'] = array(
    'args' => array('response' => 'object'),
    'type' => 'boolean'
);


/**
 * Return the requested block and include needed libs.
 */
function &_kronolith_block($block, $params)
{
    @define('KRONOLITH_BASE', dirname(__FILE__) . '/..');
    require_once KRONOLITH_BASE . '/lib/base.php';

    if (is_a(($blockClass = _kronolith_defineBlock($block)), 'PEAR_Error')) {
        return $blockClass;
    }

    return $ret = &new $blockClass($params);
}

function _kronolith_defineBlock($block)
{
    @define('KRONOLITH_BASE', dirname(__FILE__) . '/..');

    $blockClass = 'Horde_Block_Kronolith_' . $block;
    include_once KRONOLITH_BASE . '/lib/Block/' . $block . '.php';
    if (class_exists($blockClass)) {
        return $blockClass;
    } else {
        return PEAR::raiseError(sprintf(_("%s not found."), $blockClass));
    }
}

function _kronolith_listCalendars($owneronly = false, $permission = null)
{
    require_once dirname(__FILE__) . '/base.php';
    if (!isset($permission)) {
        $permission = PERMS_SHOW;
    }
    return array_keys(Kronolith::listCalendars($owneronly, $permission));
}

function _kronolith_list()
{
    require_once dirname(__FILE__) . '/base.php';
    $ids = Kronolith::listEventIds(0, new Kronolith_Date(array('year' => 9999, 'month' => 12, 'day' => 31)));
    if (is_a($ids, 'PEAR_Error')) {
        return $ids;
    }

    $guids = array();
    foreach ($ids as $cal) {
        $guids = array_merge($guids, array_keys($cal));
    }

    return $guids;
}

/**
 * Returns an array of GUIDs for events that have had $action happen
 * since $timestamp.
 *
 * @param integer $timestamp  The time to start the search.
 * @param string  $action     The action to check for - add, modify, or delete.
 *
 * @return array  An array of GUIDs matching the action and time criteria.
 */
function &_kronolith_listBy($action, $timestamp)
{
    require_once dirname(__FILE__) . '/base.php';
    require_once 'Horde/History.php';

    $history = &Horde_History::singleton();
    $histories = $history->getByTimestamp('>', $timestamp, array(array('op' => '=', 'field' => 'action', 'value' => $action)), 'kronolith');
    if (is_a($histories, 'PEAR_Error')) {
        return $histories;
    }

    return array_keys($histories);
}

/**
 * Import an event represented in the specified contentType.
 *
 * @param string $content      The content of the event.
 * @param string $contentType  What format is the data in? Currently supports:
 *                             text/x-icalendar
 *                             text/x-vcalendar
 *                             text/x-vevent
 * @param string $calendar     (optional) What calendar should the event be added to?
 *
 * @return string  The new GUID, or false on failure.
 */
function _kronolith_import($content, $contentType, $calendar = null)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith;

    if (!isset($calendar)) {
        $calendar = Kronolith::getDefaultCalendar(PERMS_EDIT);
    }
    if (!array_key_exists($calendar, Kronolith::listCalendars(false, PERMS_EDIT))) {
        return PEAR::raiseError(_("Permission Denied"));
    }
    $kronolith->open($calendar);

    switch ($contentType) {
    case 'text/calendar':
    case 'text/x-icalendar':
    case 'text/x-vcalendar':
    case 'text/x-vevent':
        if (!is_a($content, 'Horde_iCalendar_vevent')) {
            require_once 'Horde/iCalendar.php';
            $iCal = &new Horde_iCalendar();
            if (!$iCal->parsevCalendar($content)) {
                return PEAR::raiseError(_("There was an error importing the iCalendar data."));
            }

            $components = $iCal->getComponents();
            switch (count($components)) {
            case 0:
                return PEAR::raiseError(_("No iCalendar data was found."));

            case 1:
                $content = $components[0];
                if (!is_a($content, 'Horde_iCalendar_vevent')) {
                    return PEAR::raiseError(_("vEvent not found."));
                }
                break;

            default:
                return PEAR::raiseError(_("Multiple iCalendar components found; only one vEvent is supported."));
            }
        }

        $event = &$kronolith->getEvent();
        $event->fromiCalendar($content);

        $guid = $content->getAttribute('UID');
        if (!is_a($guid, 'PEAR_Error')) {
            $event->setID($guid);
        }

        $eventId = $event->save();
        break;

    default:
        return false;
    }

    if (is_a($eventId, 'PEAR_Error')) {
        return $eventId;
    }

    return $kronolith->getGUID($eventId);
}

/**
 * Export an event, identified by GUID, in the requested contentType.
 *
 * @param string $guid         Identify the event to export.
 * @param string $contentType  What format should the data be in? Currently supports:
 *                             text/x-icalendar
 *                             text/x-vcalendar
 *
 * @return string  The requested data.
 */
function _kronolith_export($guid, $contentType)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith, $kronolith_shares;

    $event = $kronolith->getByGUID($guid);
    if (is_a($event, 'PEAR_Error')) {
        return $event;
    }

    if (!array_key_exists($event->getCalendar(), Kronolith::listCalendars(false, PERMS_EDIT))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    switch ($contentType) {
    case 'text/calendar':
    case 'text/x-icalendar':
    case 'text/x-vcalendar':
        require_once 'Horde/Data.php';
        $vcs = &Horde_Data::singleton('icalendar');
        $identity = &$kronolith_shares->getIdentityByShare($kronolith_shares->getShare($event->getCalendar()));
        $data = array($event->toiCalendar($vcs, $identity));
        return $vcs->exportData($data);
    }

    return false;
}

/**
 * Delete an event identified by GUID.
 *
 * @param string $guid  Identify the event to delete.
 *
 * @return boolean  Success or failure.
 */
function _kronolith_remove($guid)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith;

    $event = $kronolith->getByGUID($guid);
    if (is_a($event, 'PEAR_Error')) {
        return $event;
    }

    if (!array_key_exists($event->getCalendar(), Kronolith::listCalendars(false, PERMS_DELETE))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    return $kronolith->deleteEvent($event->getID());
}

/**
 * Replace the event identified by GUID with the content represented
 * in the specified contentType.
 *
 * @param string $guid         Idenfity the event to replace.
 * @param string $content      The content of the event.
 * @param string $contentType  What format is the data in? Currently supports:
 *                             text/x-icalendar
 *                             text/x-vcalendar
 *                             text/x-vevent
 *
 * @return boolean  Success or failure.
 */
function _kronolith_replace($guid, $content, $contentType)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith;

    $event = $kronolith->getByGUID($guid);
    if (is_a($event, 'PEAR_Error')) {
        return $event;
    }

    if (!array_key_exists($event->getCalendar(), Kronolith::listCalendars(false, PERMS_EDIT))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    switch ($contentType) {
    case 'text/calendar':
    case 'text/x-icalendar':
    case 'text/x-vcalendar':
    case 'text/x-vevent':
        if (!is_a($content, 'Horde_iCalendar_vevent')) {
            require_once 'Horde/iCalendar.php';
            $iCal = &new Horde_iCalendar();
            if (!$iCal->parsevCalendar($content)) {
                return PEAR::raiseError(_("There was an error importing the iCalendar data."));
            }

            $components = $iCal->getComponents();
            switch (count($components)) {
            case 0:
                return PEAR::raiseError(_("No iCalendar data was found."));

            case 1:
                $content = $components[0];
                if (!is_a($content, 'Horde_iCalendar_vevent')) {
                    return PEAR::raiseError(_("vEvent not found."));
                }
                break;

            default:
                return PEAR::raiseError(_("Multiple iCalendar components found; only one vEvent is supported."));
            }
        }

        $event->fromiCalendar($content);

        $guid = $content->getAttribute('UID');
        if (!is_a($guid, 'PEAR_Error')) {
            $event->setID($guid);
        }

        $eventId = $event->save();
        break;

    default:
        return false;
    }

    return is_a($eventId, 'PEAR_Error') ? $eventId : true;
}

/**
 * Generate FreeBusy information for a given time period.
 *
 * @param integer $startstamp  (optional) The start of the time period to retrieve.
 * @param integer $endstamp    (optional) The end of the time period to retrieve.
 * @param string  $calendar    (optional) The calendar to view free/busy
 *                             slots for. Defaults to the user's default calendar.
 *
 * @return object Horde_iCalendar_vfreebusy  A freebusy object that covers the
 *                                           specified time period.
 */
function _kronolith_getFreeBusy($startstamp = null, $endstamp = null, $calendar = null)
{
    require_once dirname(__FILE__) . '/base.php';

    if (is_null($calendar)) {
        $calendar = Kronolith::getDefaultCalendar();
    }

    return Kronolith::generateFreeBusy($calendar, $startstamp, $endstamp, true);
}

/**
 * Retrieve a Kronolith_Event object, given an event GUID.
 *
 * @param string $guid    The events' GUID.
 *
 * @return object   A valid Kronolith_Event on success, or a PEAR_Error on failure.
 */
function &_kronolith_eventFromGUID($guid)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith;

    $event = $kronolith->getByGUID($guid);
    if (is_a($event, 'PEAR_Error')) {
        return $event;
    }

    if (!array_key_exists($event->getCalendar(), Kronolith::listCalendars(false, PERMS_SHOW))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    return $event;
}

/**
 * Update an attendees response status for a specified event.
 *
 * @param object $response    A Horde_iCalender_vevent objext, with a valid
 *                            UID attribute that points to an existing event.
 *                            This is typically the vEvent portion of an iTip
 *                            meeting-request response, with the attendees'
 *                            response in an ATTENDEE parameter.
 *
 * @return mixed   (boolean) true on success.
 *                 (object)  PEAR_Error on failure.
 */
function _kronolith_updateAttendee($response)
{
    require_once dirname(__FILE__) . '/base.php';
    global $kronolith;

    $guid = $response->getAttribute('UID');
    if (is_a($guid, 'PEAR_Error')) {
        return $guid;
    }

    $event = $kronolith->getByGUID($guid);
    if (is_a($event, 'PEAR_Error')) {
        return $event;
    }

    if (!array_key_exists($event->getCalendar(), Kronolith::listCalendars(false, PERMS_EDIT))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $atnames = $response->getAttribute('ATTENDEE');
    $atparms = $response->getAttribute('ATTENDEE', true);

    if (!is_array($atnames)) {
        $atnames = array($atnames);
    }
    foreach ($atnames as $index => $attendee) {
        $event->addAttendee(str_replace('MAILTO:', '', $attendee), KRONOLITH_PART_IGNORE, Kronolith::responseFromICal($atparms[$index]['PARTSTAT']));
    }

    $res = $event->save();
    if (is_a($res, 'PEAR_Error')) {
        return $res;
    }

    return true;
}
