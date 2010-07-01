<?php
/**
 * $Horde: kronolith/calendars/info.php,v 1.2.2.4 2009-01-06 15:24:44 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('KRONOLITH_BASE', dirname(dirname(__FILE__)));
require_once KRONOLITH_BASE . '/lib/base.php';
require_once 'Horde/RPC.php';
if (@include_once 'HTTP/WebDAV/Server.php') {
    require_once 'Horde/RPC/webdav.php';
}

// Exit if this isn't an authenticated user.
if (!Auth::getAuth()) {
    exit;
}

$calendar = null;
$calendarId = Util::getFormData('c');
if (strncmp($calendarId, 'remote_', 7) === 0) {
    $calendarId = substr($calendarId, 7);
    $remote_calendars = unserialize($prefs->getValue('remote_cals'));
    foreach ($remote_calendars as $remote_calendar) {
        if ($remote_calendar['url'] == $calendarId) {
            $calendar = $remote_calendar;
            break;
        }
    }
} elseif (isset($GLOBALS['all_calendars'][$calendarId])) {
    $calendar = $GLOBALS['all_calendars'][$calendarId];

    $webdav = is_callable(array('HTTP_WebDAV_Server_Horde', 'DELETE'));
    $rewrite = isset($conf['urls']['pretty']) &&
        $conf['urls']['pretty'] == 'rewrite';
    $subscribe_url = $webdav
        ? Horde::url($registry->get('webroot', 'horde')
                     . ($rewrite ? '/rpc/kronolith/' : '/rpc.php/kronolith/'),
                     true, -1)
          . $calendar->get('owner') . '/' . $calendar->getName() . '.ics'
        : Util::addParameter(Horde::applicationUrl('ics.php', true, -1), 'c',
                             $calendar->getName());
}

if (is_null($calendar)) {
    exit;
}

require KRONOLITH_TEMPLATES . '/calendar_info.php';
