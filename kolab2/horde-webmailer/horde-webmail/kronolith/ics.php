<?php
/**
 * $Horde: kronolith/ics.php,v 1.5.2.11 2009-01-06 15:24:43 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('KRONOLITH_BASE', dirname(__FILE__));
$session_control = 'none';
require_once KRONOLITH_BASE . '/lib/base.php';
require_once 'Horde/Cache.php';
require_once 'Horde/iCalendar.php';

// We want to always generate UTF-8 iCalendar data.
NLS::setCharset('UTF-8');

// Determine which calendar to export.
$calendar = Util::getFormData('c');
if (empty($calendar) && !empty($_SERVER['PATH_INFO'])) {
    $calendar = basename($_SERVER['PATH_INFO']);
}

$share = $kronolith_shares->getShare($calendar);
if (is_a($share, 'PEAR_Error')) {
    header('HTTP/1.0 400 Bad Request');
    echo '400 Bad Request';
    exit;
}

// First try guest permissions.
if (!$share->hasPermission('', PERMS_READ)) {
    // Authenticate.
    $auth = &Auth::singleton($conf['auth']['driver']);
    if (!isset($_SERVER['PHP_AUTH_USER'])
        || !$auth->authenticate($_SERVER['PHP_AUTH_USER'],
                                array('password' => isset($_SERVER['PHP_AUTH_PW']) ? $_SERVER['PHP_AUTH_PW'] : null))
        || !$share->hasPermission(Auth::getAuth(), PERMS_READ)) {
        header('WWW-Authenticate: Basic realm="Kronolith iCalendar Interface"');
        header('HTTP/1.0 401 Unauthorized');
        echo '401 Unauthorized';
        exit;
    }
}

// If we've authenticated, we need to re-load global share variables
// now.
if (Auth::getAuth()) {
    Kronolith::initialize();
}

$cache = &Horde_Cache::singleton($conf['cache']['driver'], Horde::getDriverConfig('cache', $conf['cache']['driver']));
$key = 'kronolith.ics.' . $calendar;

$ics = $cache->get($key, 360);
if (!$ics) {
    $kronolith_driver->open($calendar);
    $events = $kronolith_driver->listEvents();

    $iCal = new Horde_iCalendar();
    $iCal->setAttribute('X-WR-CALNAME', String::convertCharset($share->get('name'), NLS::getCharset(), 'utf-8'));

    foreach ($events as $id) {
        $event = &$kronolith_driver->getEvent($id);
        if (is_a($event, 'PEAR_Error')) {
            continue;
        }
        $iCal->addComponent($event->toiCalendar($iCal));
    }

    $ics = $iCal->exportvCalendar();
    $cache->set($key, $ics);
}

$browser->downloadHeaders($calendar . '.ics',
                          'text/calendar; charset=' . NLS::getCharset(),
                          true,
                          strlen($ics));
echo $ics;
