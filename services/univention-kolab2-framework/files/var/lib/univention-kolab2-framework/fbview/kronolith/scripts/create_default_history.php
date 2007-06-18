#!/usr/local/bin/php
<?php
/**
 * $Horde: kronolith/scripts/create_default_history.php,v 1.7 2004/04/07 14:43:29 chuck Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('AUTH_HANDLER', true);
@define('KRONOLITH_BASE', dirname(__FILE__) . '/..');
require_once KRONOLITH_BASE . '/lib/base.php';
require_once 'Horde/History.php';

$history = &Horde_History::singleton();

// Run through every calendar.
$cals = $kronolith_shares->listAllShares();
foreach ($cals as $calid => $calshare) {
    echo "Creating default histories for $calid ...\n";

    if ($kronolith->getCalendar() != $calid) {
        $kronolith->close();
        $kronolith->open($calid);
    }

    // List all events.
    $events = $kronolith->listEvents();
    foreach ($events as $eventId) {
        /* Get the event's history. */
        $log = $history->getHistory($kronolith->getGUID($eventId));
        $created = false;
        foreach ($log->getData() as $entry) {
            if ($entry['action'] == 'add') {
                $created = true;
                break;
            }
        }

        // If there isn't an add entry, add one at the current time.
        if (!$created) {
            $history->log($kronolith->getGUID($eventId), array('action' => 'add'), true);
        }
    }
}

echo "\n** Default histories successfully created ***\n";
