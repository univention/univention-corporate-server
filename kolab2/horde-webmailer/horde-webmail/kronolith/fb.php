<?php
/**
 * $Horde: kronolith/fb.php,v 1.25.10.11 2009-01-06 15:24:43 jan Exp $
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
require_once KRONOLITH_BASE . '/lib/FreeBusy.php';
require_once 'Horde/Cache.php';

// We want to always generate UTF-8 iCalendar data.
NLS::setCharset('UTF-8');

// Determine the username to show free/busy time for.
$cal = Util::getFormData('c');
$user = Util::getFormData('u');
if (!empty($cal)) {
    if (is_array($cal)) {
        $cal = implode('|', $cal);
    }
} elseif (!empty($_SERVER['PATH_INFO'])) {
    $user = basename($_SERVER['PATH_INFO']);
}

$cache = Horde_Cache::factory($conf['cache']['driver'], Horde::getDriverConfig('cache', $conf['cache']['driver']));
$key = 'kronolith.fb.' . ($user ? 'u.' . $user : 'c.' . $cal);
$fb = $cache->get($key, 360);
if (!$fb) {
    if ($user) {
        $prefs = &Prefs::singleton($conf['prefs']['driver'], 'kronolith', $user, '', null, false);
        $prefs->retrieve();
        NLS::setTimeZone();
        $cal = @unserialize($prefs->getValue('fb_cals'));
        if (is_array($cal)) {
            $cal = implode('|', $cal);
        }

        // If the free/busy calendars preference is empty, default to
        // the user's default_share preference, and if that's empty,
        // to their username.
        if (!$cal) {
            $cal = $prefs->getValue('default_share');
            if (!$cal) {
                $cal = $user;
            }
        }
    }

    $fb = Kronolith_FreeBusy::generate(explode('|', $cal), null, null, false, $user);
    if (is_a($fb, 'PEAR_Error')) {
        Horde::logMessage($fb, __FILE__, __LINE__, PEAR_LOG_ERR);
        exit;
    }
    $cache->set($key, $fb);
}

$browser->downloadHeaders(($user ? $user : $cal) . '.vfb',
                          'text/calendar; charset=' . NLS::getCharset(),
                          true,
                          strlen($fb));
echo $fb;
