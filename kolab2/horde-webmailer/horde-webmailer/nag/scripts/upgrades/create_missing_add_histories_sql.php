#!/usr/bin/php
<?php
/**
 * $Horde: nag/scripts/upgrades/create_missing_add_histories_sql.php,v 1.8.2.3 2009-01-06 15:25:09 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../../..');

// Do CLI checks and environment setup first.
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/CLI.php';

// Make sure no one runs this from the web.
if (!Horde_CLI::runningFromCLI()) {
    exit("Must be run from the command line\n");
}

// Load the CLI environment - make sure there's no time limit, init some
// variables, etc.
$cli = &Horde_CLI::singleton();
$cli->init();

@define('NAG_BASE', dirname(__FILE__) . '/../..');
require_once NAG_BASE . '/lib/base.php';

$history = &Horde_History::singleton();

// Run through every tasklist.
$tasklists = $nag_shares->listAllShares();
foreach ($tasklists as $tasklist => $share) {
    echo "Creating default histories for $tasklist ...\n";

    // List all tasks.
    $storage = Nag_Driver::singleton($tasklist);
    $storage->retrieve();
    $tasks = $storage->listTasks();

    foreach ($tasks as $taskId => $task) {
        $log = $history->getHistory('nag:' . $tasklist . ':' . $task['uid']);
        $created = false;
        foreach ($log->getData() as $entry) {
            if ($entry['action'] == 'add') {
                $created = true;
                break;
            }
        }
        if (!$created) {
            $history->log('nag:' . $tasklist . ':' . $task['uid'], array('action' => 'add'), true);
        }
    }
}

echo "\n** Default histories successfully created ***\n";
