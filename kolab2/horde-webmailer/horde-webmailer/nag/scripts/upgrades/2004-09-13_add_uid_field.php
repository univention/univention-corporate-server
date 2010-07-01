#!/usr/bin/php
<?php
/**
 * $Horde: nag/scripts/upgrades/2004-09-13_add_uid_field.php,v 1.2.8.5 2007-01-02 13:55:13 jan Exp $
 *
 * This script maintains existing Nag task IDs as GUIDs.
 *
 * Copyright 2004-2007 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
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

// Load the CLI environment - make sure there's no time limit, init
// some variables, etc.
Horde_CLI::init();

@define('NAG_BASE', dirname(__FILE__) . '/../..');
require_once NAG_BASE . '/lib/base.php';

if ($conf['storage']['driver'] != 'sql') {
    exit('No conversion for Kolab, DataTree, etc. currently.');
}

$storage = &Nag_Driver::singleton('');
$storage->_connect();
$db = &$storage->_db;

// Add/drop db fields. We don't check for success/failure here in case
// someone did this manually.
$db->query('ALTER TABLE nag_tasks ADD COLUMN task_uid VARCHAR(255)');
$db->query('ALTER TABLE nag_tasks ADD COLUMN task_private INT NOT NULL DEFAULT 0');
$db->query('ALTER TABLE nag_tasks DROP COLUMN task_modified');
$db->query('CREATE INDEX nag_uid_idx ON nag_tasks (task_uid)');

// Run through every tasklist.
$tasklists = $nag_shares->listAllShares();
foreach ($tasklists as $tasklist => $share) {
    echo "Storing UIDs for $tasklist ...\n";

    // List all tasks.
    $storage = &Nag_Driver::singleton($tasklist);
    $storage->retrieve();
    $tasks = $storage->listTasks();

    foreach ($tasks as $taskId => $task) {
        $sql = sprintf('UPDATE nag_tasks SET task_uid = %s WHERE task_id = %s AND task_owner = %s',
                       $db->quote('nag:' . $taskId),
                       $db->quote($taskId),
                       $db->quote($task['tasklist_id']));
        $result = $db->query($sql);
        if (is_a($result, 'PEAR_Error')) {
            Horde::fatal($result);
        }
    }
}

echo "\n** UIDs successfully stored. ***\n";
