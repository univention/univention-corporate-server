#!/usr/local/bin/php
<?php
/**
 * $Horde: horde/scripts/rename_category.php,v 1.6 2004/04/07 14:43:44 chuck Exp $
 *
 * Copyright 2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

/* Change this variable to false. */
$live = false;

/* Configure your table names here, these are the default values. */
$category['table'] = 'horde_categories';
$category['table_attributes'] = 'horde_category_attributes';
$datatree['table'] = 'horde_datatree';
$datatree['table_attributes'] = 'horde_datatree_attributes';

/* 
 * Nothing to see below this line. 
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/..');

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

require_once HORDE_BASE . '/lib/base.php';

if (!$live) {
    echo "TEST MODE. No data will be changed.\nChange the \$live setting in this script to apply the changes.\n\n";
}

// DB setup for the category table.
$params = Horde::getDriverConfig('datatree', 'sql');
if (!isset($params['password'])) {
    $params['password'] = '';
}
$dbh = &DB::connect($params);

// Get the current max id.
$max = $dbh->getOne('SELECT MAX(category_id) FROM ' . $category['table']);
if (is_a($max, 'PEAR_Error')) {
    echo "Fatal error: ", $max->getMessage(), "\n";
    exit(1);
}

// Make sure the sequence is at least that high.
if ($live) {
    echo "Setting DataTree sequence to $max.\n";
    while ($dbh->nextId($datatree['table']) < $max);
} else {
    echo "NOT setting DataTree sequence to $max.\n";
}

// Get the old values...
$result = $dbh->query('SELECT category_id, group_uid, user_uid, category_name, category_parents, category_order, category_data, category_serialized, category_updated from ' . $category['table']);
if (is_a($result, 'PEAR_Error')) {
    var_dump($result);
    exit(1);
}

// ...and stuff them into the new table.
$sth = $dbh->prepare('INSERT INTO ' . $datatree['table'] . ' (datatree_id, group_uid, user_uid, datatree_name, datatree_parents, datatree_order, datatree_data, datatree_serialized, datatree_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');
$count = 0;
while ($row = $result->fetchRow()) {
    if ($live) {
        $exec_result = $dbh->execute($sth, $row);
        if (is_a($exec_result, 'PEAR_Error')) {
            echo "Error \"", $exec_result->getMessage(), "\" while copying rows to horde_datatree table (does it exist?)\n";
            exit(1);
        }
    }
    $count++;
}
if ($live) {
    echo "Copied $count row(s) from {$category['table']} to {$datatree['table']}.\n";
} else {
    echo "NOT copied $count row(s) from {$category['table']} to {$datatree['table']}.\n";
}

// Get the old attribute values...
$result = $dbh->query('SELECT * from ' . $category['table_attributes']);
if (is_a($result, 'PEAR_Error')) {
    var_dump($result);
    exit(1);
}

// ...and stuff them into the new table.
$sth = $dbh->prepare('INSERT INTO ' . $datatree['table_attributes'] . ' (datatree_id, attribute_name, attribute_key, attribute_value) VALUES (?, ?, ?, ?)');
$count = 0;
while ($row = $result->fetchRow()) {
    if ($live) {
        $exec_result = $dbh->execute($sth, $row);
        if (is_a($exec_result, 'PEAR_Error')) {
            echo "Fatal error: ", $exec_result->getMessage(), "\n";
            exit(1);
        }
    }
    $count++;
}
if ($live) {
    echo "Copied $count row(s) from {$category['table_attributes']} to {$datatree['table_attributes']}.\n\n";
    echo "You can now delete the {$category['table']} and {$category['table_attributes']} tables.\n";
} else {
    echo "NOT copied $count row(s) from {$category['table_attributes']} to {$datatree['table_attributes']}.\n";
}
