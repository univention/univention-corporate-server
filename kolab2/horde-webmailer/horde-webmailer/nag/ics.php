<?php
/**
 * $Horde: nag/ics.php,v 1.4.2.7 2009-01-06 15:25:04 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('NAG_BASE', dirname(__FILE__));
$session_control = 'none';
require_once NAG_BASE . '/lib/base.php';
require_once 'Horde/Cache.php';
require_once 'Horde/iCalendar.php';
require_once 'Horde/Identity.php';

// We want to always generate UTF-8 iCalendar data.
NLS::setCharset('UTF-8');

// Determine which tasklist to export.
$tasklist = Util::getFormData('t');
if (empty($tasklist) && !empty($_SERVER['PATH_INFO'])) {
    $tasklist = basename($_SERVER['PATH_INFO']);
}

$share = $nag_shares->getShare($tasklist);
if (is_a($share, 'PEAR_Error')) {
    header('HTTP/1.0 400 Bad Request');
    echo '400 Bad Request';
    exit;
}

// First try guest permissions.
if (!$share->hasPermission('', PERMS_READ)) {
    // Authenticate.
    $auth = &Auth::singleton($conf['auth']['driver']);
    if (!isset($_SERVER['PHP_AUTH_USER']) ||
        !$auth->authenticate($_SERVER['PHP_AUTH_USER'],
                             array('password' => isset($_SERVER['PHP_AUTH_PW']) ? $_SERVER['PHP_AUTH_PW'] : null)) ||
        !$share->hasPermission(Auth::getAuth(), PERMS_READ)) {
        header('WWW-Authenticate: Basic realm="Nag iCalendar Interface"');
        header('HTTP/1.0 401 Unauthorized');
        echo '401 Unauthorized';
        exit;
    }
}

$cache = &Horde_Cache::singleton($conf['cache']['driver'], Horde::getDriverConfig('cache', $conf['cache']['driver']));
$key = 'nag.ics.' . $tasklist;

$ics = $cache->get($key, 360);
if (!$ics) {
    $iCal = new Horde_iCalendar();
    $iCal->setAttribute('X-WR-CALNAME', $share->get('name'));

    $storage = &Nag_Driver::singleton($tasklist);
    $result = $storage->retrieve();
    if (is_a($result, 'PEAR_Error')) {
        Horde::fatal($result, __FILE__, __LINE__);
    }

    $identity = &Identity::singleton('none', $share->get('owner'));
    $storage->tasks->reset();
    while ($task = $storage->tasks->each() ) {
        $iCal->addComponent($task->toiCalendar($iCal));
    }

    $ics = $iCal->exportvCalendar();
    $cache->set($key, $ics);
}

$browser->downloadHeaders($tasklist . '.ics',
                          'text/calendar; charset=' . NLS::getCharset(),
                          true,
                          strlen($ics));
echo $ics;
