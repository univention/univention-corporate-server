#!/usr/bin/php
<?php
/**
 * $Horde: horde/scripts/upgrades/move_history_out_of_datatree.php,v 1.3.2.3 2007-12-20 15:03:04 jan Exp $
 *
 * This is a script to migrate History information out of the datatree
 * tables and into its own database table.
 */

// Find the base file path of Horde.
@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../..');

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
$cli = Horde_CLI::singleton();

$cli->writeln($cli->yellow("Beginning migration. This may take a very long time to complete."));
$cli->writeln();

require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/DataTree.php';

$datatree = &DataTree::factory('sql', array_merge(Horde::getDriverConfig('datatree', 'sql'),
                                                  array('group' => 'horde.history')));
$db = &$datatree->_db;

$cli->writeln('Fetching all history objects from the data tree.'); ob_flush();
$objects = $db->getAll("SELECT c.datatree_id, c.datatree_name, c.datatree_parents, c.datatree_order FROM horde_datatree c WHERE c.group_uid = 'horde.history' order by datatree_id",DB_FETCHMODE_ASSOC);
$numObjects = count($objects);
$totalObjects = $numObjects;
$cli->writeln("Found $numObjects history objects."); ob_flush();

$insertQuery = 'INSERT INTO horde_histories (history_id, object_uid, history_action, history_desc, history_who, history_ts, history_extra) VALUES (?, ?, ?, ?, ?, ?, ?)';
$i = 0;
$previousPercent = null;

// Do the actual work: loop through the history objects and reinsert them into
// the database under the new table/schema.
foreach ($objects as $object) {
    // Output some stats so we know the script is actually working.
    $currentPercent = round(($i / $totalObjects) * 100);
    if (is_null($previousPercent) || ($previousPercent != $currentPercent)) {
        $cli->writeln("Working on object $i of $totalObjects ({$currentPercent}% finished)");
        ob_flush();
    }
    $previousPercent = $currentPercent;
    $attributes = $db->getAll('SELECT attribute_name AS name, attribute_key AS "key", attribute_value AS value FROM horde_datatree_attributes WHERE datatree_id = ' . $object['datatree_id'] . ' order by name', DB_FETCHMODE_ASSOC);

    // The above result set contains multiple rows that go together
    // based on the "name" column. Here we format the data so that it
    // consists of an array based on the name column, e.g. [0,1,2],
    // each value an array itself with the data for that name
    // contained within. Yeah that made sense.
    $tmpAttributes = array();
    foreach ($attributes as $attribute) {
        if (!isset($tmpAttributes[$attribute['name']])) {
            $tmpAttributes[$attribute['name']] = array();
        }
        $tmpAttributes[$attribute['name']][$attribute['key']] = $attribute['value'];
    }

    // Now the data is formatted based on "name", one array for each
    // "name" and one row for each attribute key (from the result set
    // above). Now we move certain keys to the output array and
    // convert any remaining rows into an "extra" array which is
    // serialized into one value.
    foreach ($tmpAttributes as $tmpAttribute) {
        $outAttribute = array();

        // Copy our requires values over from the old data to the new.
        $outAttribute['history_id'] = $db->nextId('horde_histories');
        $outAttribute['object_uid'] = $object['datatree_name'];
        $outAttribute['history_action'] = isset($tmpAttribute['action']) ? $tmpAttribute['action'] : null;
        $outAttribute['history_desc'] = isset($tmpAttribute['desc']) ? $tmpAttribute['desc'] : null;
        $outAttribute['history_ts'] = isset($tmpAttribute['ts']) ? $tmpAttribute['ts'] : null;
        $outAttribute['history_who'] = isset($tmpAttribute['who']) ? $tmpAttribute['who'] : null;

        // Remove the required attributes we've copied, leaving only optional values.
        unset($tmpAttribute['action']);
        unset($tmpAttribute['desc']);
        unset($tmpAttribute['ts']);
        unset($tmpAttribute['who']);

        // Anything else goes into a serialized "extra" value.
        $outAttribute['history_extra'] = (count($tmpAttribute) > 0) ? serialize($tmpAttribute) : null;

        // Insert the new data into the new table.
        check($db->query($insertQuery, array($outAttribute['history_id'], $outAttribute['object_uid'], $outAttribute['history_action'], $outAttribute['history_desc'], $outAttribute['history_who'], $outAttribute['history_ts'], $outAttribute['history_extra'])));
    }

    // Delete the old data from the old tables.
    check($db->query('DELETE FROM horde_datatree_attributes WHERE datatree_id = ?', array($object['datatree_id'])));
    check($db->query('DELETE FROM horde_datatree WHERE datatree_id = ?', array($object['datatree_id'])));

    // Proceed to the next object in the datatree.
    $i++;
}

function check($result)
{
    if (is_a($result, 'PEAR_Error')) {
        var_dump($result);
        exit;
    }
}
