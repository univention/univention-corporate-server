#!/usr/local/bin/php
<?php
/**
 * $Horde: horde/scripts/migrate_categories.php,v 1.10 2004/04/07 14:43:44 chuck Exp $
 *
 * This is a script to migrate old categories to the new
 * horde_category_attributes table. You MUST create that table before
 * running this script. Right now, this will migrate the following
 * kinds of categories:
 *
 * - Groups
 * - All Shares (horde.share.*)
 *
 * All other categories currently still use the category_data field.
 */

/**
 ** Set this to true if you want DB inserts done.
 **/
$live = false;

/**
 ** Kinds of categories to convert.
 **/
$groups = true;
$shares = true;


// No auth.
@define('AUTH_HANDLER', true);

// Find the base file path of Horde.
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
require_once 'Horde/DataTree.php';
require_once 'Horde/Group.php';
require_once 'Horde/Share.php';

// Groups.
if ($groups) {
    $category = &DataTree::factory('sql');
    $db = &$category->_db;
    
    $ids = $db->getAssoc('SELECT category_id, category_name FROM horde_categories WHERE group_uid = \'horde.groups\'');
    $category->_params['group'] = 'horde.groups';
    $category->_load();
    foreach ($ids as $id => $name) {
        $categoryOb = &new DataTreeObject_Group($name);
        $categoryOb->data = $category->getCategoryData($id);
        if ($live) {
            $result = $category->updateData($categoryOb);
            if (is_a($result, 'PEAR_Error')) {
                var_dump($result);
                exit;
            }
        }
    }
}


// Shares.
if ($shares) {
    $category = &DataTree::factory('sql');
    $db = &$category->_db;

    $ids = $db->getAssoc('SELECT category_id, category_name, group_uid FROM horde_categories WHERE group_uid LIKE \'horde.shares.%\'');
    foreach ($ids as $id => $row) {
        $category = DataTree::factory('sql');
        $category->_params['group'] = $row[1];
        $category->_load();
        $categoryOb = &new DataTreeObject_Share($row[0]);
        $categoryOb->data = $category->getCategoryData($id);
        if ($live) {
            $result = $category->updateData($categoryOb);
            if (is_a($result, 'PEAR_Error')) {
                var_dump($result);
                exit;
            }
        }
    }
}
