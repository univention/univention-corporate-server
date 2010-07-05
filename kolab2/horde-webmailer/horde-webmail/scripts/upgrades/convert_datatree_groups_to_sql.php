#!/usr/bin/php -q
<?php
/**
 * $Horde: horde/scripts/upgrades/convert_datatree_groups_to_sql.php,v 1.1.2.2 2009-07-20 11:36:02 jan Exp $
 *
 * A script to migrate groups from the DataTree backend to the new
 * (Horde 3.2+) native SQL Group backend.
 */

// Find the base file path of Horde.
@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../..');

// Do CLI checks and environment setup first.
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/CLI.php';
require_once 'Horde/Group.php';

// Make sure no one runs this from the web.
if (!Horde_CLI::runningFromCLI()) {
    exit("Must be run from the command line\n");
}

// Load the CLI environment - make sure there's no time limit, init
// some variables, etc.
Horde_CLI::init();

require_once HORDE_BASE . '/lib/base.php';

$g = Group::factory();

$group_query = '
INSERT INTO
    horde_groups (group_uid, group_name, group_parents, group_email)
VALUES
    (?, ?, ?, ?)
';

$member_query = '
INSERT INTO
    horde_groups_members (group_uid, user_uid)
VALUES
    (?, ?)
';

$db = DB::connect($conf['sql']);

foreach ($g->listGroups(true) as $id => $name) {
    if ($id == -1) {
        continue;
    }

    echo $id . "\n";

    $object = $g->getGroupById($id);

    $parents = $object->datatree->getParentList($id);
    asort($parents);
    $parents = implode(':', array_keys($parents));

    $params = array($id,
                    String::convertCharset($object->name, NLS::getCharset(), $conf['sql']['charset']),
                    String::convertCharset($parents, NLS::getCharset(), $conf['sql']['charset']),
                    String::convertCharset($object->get('email'), NLS::getCharset(), $conf['sql']['charset']),
    );
    $result = $db->query($group_query, $params);
    if (is_a($result, 'PEAR_Error')) {
        echo $result->toString();
        continue;
    }

    $members = $object->listUsers();
    foreach ($members as $user_uid) {
        $params = array($id, $user_uid);
        $result = $db->query($member_query, $params);
        if (is_a($result, 'PEAR_Error')) {
            echo $result->toString();
        }
    }
}

$max = (int)$db->getOne('SELECT MAX(group_uid) FROM horde_groups');
while ($max > $db->nextId('horde_groups'));

echo "\nDone.\n";
