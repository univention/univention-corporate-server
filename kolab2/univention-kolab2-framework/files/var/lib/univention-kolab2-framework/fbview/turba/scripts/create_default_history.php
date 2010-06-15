#!/usr/local/bin/php
<?php
/**
 * $Horde: turba/scripts/create_default_history.php,v 1.6 2004/04/07 14:43:53 chuck Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('AUTH_HANDLER', true);
@define('TURBA_BASE', dirname(__FILE__) . '/..');
require_once TURBA_BASE . '/lib/base.php';
require_once TURBA_BASE . '/lib/Source.php';
require_once 'Horde/History.php';

$history = &Horde_History::singleton();

// Run through every contact source.
foreach ($cfgSources as $key => $curSource) {
    if (empty($curSource['export']) || !empty($curSource['readonly'])) {
        continue;
    }

    $driver = &Turba_Source::singleton($key, $curSource);
    if (is_a($driver, 'PEAR_Error')) {
        var_dump($driver);
        exit;
    }

    echo "Creating default histories for $key ...\n";

    // List all contacts.
    $results = $driver->search(array(), 'name', 'AND', 0);
    while ($object = $results->next()) {
        /* Get the contact's history. */
        $guid = $driver->getGUID($object->getValue('__key'));
        $log = $history->getHistory($guid);
        $created = false;
        foreach ($log->getData() as $entry) {
            if ($entry['action'] == 'add') {
                $created = true;
                break;
            }
        }

        // If there isn't an add entry, add one at the current time.
        if (!$created) {
            $result = $history->log($guid, array('action' => 'add'), true);
            if (is_a($result, 'PEAR_Error')) {
                var_dump($result);
                exit;
            }
        }
    }
}

echo "\n** Default histories successfully created ***\n";
