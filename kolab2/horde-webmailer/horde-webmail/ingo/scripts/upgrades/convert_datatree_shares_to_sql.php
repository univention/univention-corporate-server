#!/usr/bin/env php
<?php
/**
 * This script migrates Ingo's share data from the datatree Horde_Share
 * driver to the new SQL Horde_Share driver. You should run the 1.1_to_1.2.sql
 * upgrade script before executing this script.
 *
 * $Horde: ingo/scripts/upgrades/convert_datatree_shares_to_sql.php,v 1.1.2.6 2009-07-20 11:16:55 jan Exp $
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../../..');

/* Set up the CLI environment */
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/CLI.php';
if (!Horde_CLI::runningFromCli()) {
    exit("Must be run from the command line\n");
}
$cli = &Horde_CLI::singleton();
$cli->init();

/* Grab what we need to steal the DB config */
require_once HORDE_BASE . '/config/conf.php';
require_once 'MDB2.php';

$config = $GLOBALS['conf']['sql'];
unset($config['charset']);
$db = MDB2::factory($config);
$db->setOption('seqcol_name', 'id');

$error_cnt = 0;
$delete_dt_data = false;
$answer = $cli->prompt('Do you want to keep your old datatree data or delete it?', array('Keep', 'Delete'));
if ($answer == 1) {
    $delete_dt_data = true;
}
$answer = $cli->prompt(sprintf("Data will be copied into the new tables, and %s be deleted from the datatree.\n Is this what you want?", (($delete_dt_data) ? 'WILL' : 'WILL NOT')), array('y' => 'Yes', 'n' => 'No'));
if ($answer != 'y') {
    exit;
}

/* Get the share entries */
$shares_result = $db->query('SELECT datatree_id, datatree_name FROM horde_datatree WHERE group_uid = \'horde.shares.ingo\'');
if (is_a($shares_result, 'PEAR_Error')) {
    die($shares_result->toString());
}

$query = $db->prepare('SELECT attribute_name, attribute_key, attribute_value FROM horde_datatree_attributes WHERE datatree_id = ?');
while ($row = $shares_result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
    $share_id = $row['datatree_id'];
    $share_name = $row['datatree_name'];

    /* Build an array to hold the new row data */
    $nextId = $db->nextId('ingo_shares');
    if (is_a($nextId, 'PEAR_Error')) {
        $cli->message($nextId->toString(), 'cli.error');
        $error_cnt++;
        continue;
    }
    $data = array('share_id' => $nextId,
                  'share_name' => $share_name);

    $query_result = $query->execute($share_id);
    $rows = $query_result->fetchAll(MDB2_FETCHMODE_ASSOC);
    $users = array();
    $groups = array();

    foreach ($rows as $row) {
        if ($row['attribute_name'] == 'perm_groups') {
            /* Group table entry */
            $groups[] = array('share_id' => $data['share_id'],
                              'group_uid' => $row['attribute_key'],
                              'perm' => $row['attribute_value']);
        } elseif ($row['attribute_name'] == 'perm_users') {
            /* User table entry */
            $users[] = array('share_id' => $data['share_id'],
                             'user_uid' => $row['attribute_key'],
                             'perm' => $row['attribute_value']);
        } else {
            /* Everything else goes in the main share table */
            switch ($row['attribute_name']) {
            case 'perm_creator':
            case 'perm_default':
            case 'perm_guest':
                $data[$row['attribute_name']] = $row['attribute_value'];
                break;

            case 'owner':
                $data['share_owner'] = $row['attribute_value'];
                break;

            case 'name':
                // Note the key to the $data array is not related to
                // the attribute_name field in the dt_attributes table.
                $data['attribute_name'] = $row['attribute_value'];
                break;

            case 'desc':
                $data['attribute_desc'] = $row['attribute_value'];
                break;
            }
        }
    }

    /* Set flags */
    $data['share_flags'] = 0;
    if (count($users)) {
        $data['share_flags'] |= 1;
    }
    if (count($groups)) {
        $data['share_flags'] |= 2;
    }

    /* Insert the new data */
    $cli->message('Migrating share data for share_id: ' . $share_id, 'cli.message');
    $error = false;
    $db->beginTransaction();
    $result = insertData('ingo_shares', $data);
    if (is_a($result, 'PEAR_Error')) {
        $cli->message($result->toString(), 'cli.error');
        $error = true;
    }
    if (count($groups)) {
        foreach ($groups as $group) {
            $result = insertData('ingo_shares_groups', $group);
            if (is_a($result, 'PEAR_Error')) {
                $cli->message($result->toString(), 'cli.error');
                $error = true;
            }
        }
    }
    if (count($users)) {
        foreach ($users as $user) {
            $result = insertData('ingo_shares_users', $user);
            if (is_a($result, 'PEAR_Error')) {
                $cli->message($result->toString(), 'cli.error');
                $error = true;
            }
        }
    }

    /* Delete the datatree data, but ONLY if it was requested */
    if ($delete_dt_data && !$error) {
        $cli->message('DELETING datatree data for share_id: ' . $share_id, 'cli.message');
        $delete = $db->prepare('DELETE FROM horde_datatree_attributes WHERE datatree_id = ?', null, MDB2_PREPARE_MANIP);
        if (is_a($delete, 'PEAR_Error')) {
            $cli->message($delete->toString(), 'cli.error');
            $error = true;
        } else {
            $delete_result = $delete->execute(array($share_id));
            if (is_a($delete_result, 'PEAR_Error')) {
                $cli->message($delete_result->toString(), 'cli.error');
                $error = true;
            }
        }
        $delete->free();

        $delete = $db->prepare('DELETE FROM horde_datatree WHERE datatree_id = ?', null, MDB2_PREPARE_MANIP);
        if (is_a($delete, 'PEAR_Error')) {
            $cli->message($delete->toString(), 'cli.error');
            $error = true;
        } else {
            $delete_result = $delete->execute(array($share_id));
            if (is_a($delete_result, 'PEAR_Error')) {
                $cli->message($delete_result->toString(), 'cli.error');
                $error = true;
            }
        }
        $delete->free();
    }

    /* Cleanup */
    $query_result->free();
    unset($row, $rows, $data, $groups, $users);
    if ($error) {
        $db->rollback();
        $cli->message('Rollback for share data for share_id: ' . $share_id, 'cli.message');
        ++$error_cnt;
    } else {
        $db->commit();
        $cli->message('Commit for share data for share_id: ' . $share_id, 'cli.message');
    }
}
if ($error_cnt) {
    $cli->message(sprintf("Encountered %u errors.", $error_cnt));
}
echo "\nDone.\n";

/**
 * Helper function
 */
function insertData($table, $data)
{
    $fields = array_keys($data);
    $values = array_values($data);

    $insert = $GLOBALS['db']->prepare('INSERT INTO ' . $table . ' (' . implode(', ', $fields) . ') VALUES (' . str_repeat('?, ', count($values) - 1) . '?)',
                                      null, MDB2_PREPARE_MANIP);
    if (is_a($insert,'PEAR_Error')) {
        return $insert;
    }
    $insert_result = $insert->execute($values);
    $insert->free();
    return $insert_result;
}
