#!/usr/bin/php -q
<?php
/**
 * $Horde: horde/scripts/upgrades/convert_datatree_perms_to_sql.php,v 1.1.2.1 2008-05-02 16:46:01 jan Exp $
 *
 * A script to migrate permissions from the DataTree backend to the
 * new (Horde 3.2+) native SQL Perms backend.
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

require_once HORDE_BASE . '/lib/base.php';

$p = &Perms::factory('datatree');

$query = '
INSERT INTO
    horde_perms (perm_id, perm_name, perm_parents, perm_data)
VALUES
    (?, ?, ?, ?)
';

$db = DB::connect($conf['sql']);

foreach ($p->getTree() as $id => $row) {
    if ($id == -1) {
        continue;
    }

    $object = $p->getPermissionById($id);
    echo $id . "\n";

    $parents = $object->datatree->getParentList($id);
    asort($parents);
    $parents = implode(':', array_keys($parents));

    $params = array($id, $object->name, $parents, serialize($object->data));
    $db->query($query, $params);
}

$max = (int)$db->getOne('SELECT MAX(perm_id) FROM horde_perms');
while ($max > $db->nextId('horde_perms'));

echo "\nDone.\n";
