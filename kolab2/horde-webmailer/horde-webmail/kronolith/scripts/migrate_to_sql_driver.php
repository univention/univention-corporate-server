#!/usr/local/bin/php
<?php
/**
 * $Horde: kronolith/scripts/migrate_to_sql_driver.php,v 1.1.10.3 2007-01-02 13:55:06 jan Exp $
 *
 * Copyright 1999-2007 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('AUTH_HANDLER', true);
@define('KRONOLITH_BASE', dirname(__FILE__) . '/..');
require_once KRONOLITH_BASE . '/lib/base.php';

// Set these as required.
$sqlparams = $conf['sql'];

// Create a calendar backend object.
$sqlcal = &Kronolith_Driver::factory('sql', $sqlparams);
$mcal = $kronolith;

// Run through every calendar.
$cals = $kronolith_shares->listAllShares();
foreach ($cals as $calid => $calshare) {
    echo "Converting $calid ...\n";

    if ($mcal->getCalendar() != $calid) {
        $mcal->close();
        $mcal->open($calid);
    }
    if ($sqlcal->getCalendar() != $calid) {
        $sqlcal->close();
        $sqlcal->open($calid);
    }

    // List all events.
    $events = $mcal->listEvents();
    echo count($events) . "\n\n";

    foreach ($events as $eventId) {
        $event = $mcal->getEvent($eventId);
        $newevent = $sqlcal->getEvent();

        foreach ((array)$event as $key => $value) {
            if ($key != 'eventID') {
                $newevent->$key = $value;
            }
        }

        $kronolith = $sqlcal;
        $success = $newevent->save();
        if (is_a($success, 'PEAR_Error')) {
            var_dump($success);
        }
        $kronolith = $mcal;
    }
}
