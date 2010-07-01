#!/usr/bin/env php
<?php
/**
 * $Horde: turba/scripts/upgrades/2007-06-17_flatten_shares.php,v 1.10.2.2 2008-01-02 05:14:39 chuck Exp $
 *
 * This script flattens shared address books out to meet the
 * requirements of the future Share API.
 */

@define('AUTH_HANDLER', true);
@define('TURBA_BASE', dirname(__FILE__) . '/../..');
@define('HORDE_BASE', TURBA_BASE . '/..');

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

require_once TURBA_BASE . '/lib/base.php';

// Re-load source config.
require TURBA_BASE . '/config/sources.php';

// See if any of our sources are configured to use Horde_Share.
if (empty($_SESSION['turba']['has_share'])) {
    echo "No shares to convert. Done.\n";
    exit(0);
}

// Check for multiple share-enabled backends and use the first one
// as a 'primary' source - this is in case multiple backends would
// have children with the same datatree_name (like when using two
// SQL sources with shares for example
foreach ($cfgSources as $type => $config) {
    if (!empty($config['use_shares'])) {
        $sourceTypes[] = $type;
    }
}
$primary_source = $sourceTypes[0];
$datatree = $turba_shares->_datatree;
$db = $datatree->_db;

// Get list of shares.
$sql = "SELECT datatree_id, datatree_name, datatree_parents FROM horde_datatree WHERE group_uid = 'horde.shares.turba'";
$datatree_elts = $db->getAssoc($sql);

$changed_dns = array();

// Look at each share, looking for orphans, old parent shares, etc.
foreach ($datatree_elts as $id => $datatree_elt) {
    $id = (int)$id;
    $attributes = $db->getAll("SELECT * FROM horde_datatree_attributes WHERE datatree_id = $id");

    // If there are no attributes, this will be an orphan. Delete it.
    if (!count($attributes)) {
        $db->query("DELETE FROM horde_datatree_attributes WHERE datatree_id = $id");
        $db->query("DELETE FROM horde_datatree WHERE group_uid = 'horde.shares.turba' AND datatree_id = $id");
        continue;
    }

    $datatree_name = $datatree_elt[0];
    $datatree_parents = $datatree_elt[1];

    // If there are no parents, this share is already flattened; ignore it.
    if (empty($datatree_parents)) {
        continue;
    }

    // Insert a new entry with the required params setting.
    $source = $datatree_elts[substr($datatree_parents, 1)][0];

    // I *really* don't like doing it this way, but I can't think of any other
    // way to get the correct values for the 'name' param (at least without creating
    // 'upgrade drivers' ;)
    // In what way will this will affect kolab sources??
    switch ($cfgSources[$source]['type']) {
    case 'imsp':
        foreach ($attributes as $attribute) {
            if ($attribute[1] == 'name') {
                $name = $attribute[3];
            }

            if ($attribute[1] == 'owner') {
                $owner = $attribute[3];
            }
        }
        $nameparam = $owner . '.' . $name;
        break;

    case 'sql':
        foreach ($attributes as $attribute) {
            if ($attribute[1] == 'uid') {
                $nameparam = $attribute[3];
                break;
            }
        }
        break;
    }

    $db->query('INSERT INTO horde_datatree_attributes (datatree_id, attribute_name, attribute_key, attribute_value) VALUES (?, ?, ?, ?)',
               array($id, 'params', '', serialize(array('source' => $source, 'name' => $nameparam))));

    // Need to check for attribute_name of description and change it desc
    $db->query('ALTER horde_datatree_attributes SET attribute_name = ? WHERE datatree_id = ? AND attribute_name = ?',
               array('desc', $id, 'description'));

    // See if we need to differentiate the datatree_name
    // FIXME: Changing the datatree_name will break any contact lists
    // with contacts from this source. We can update the SQL based lists here,
    // but other sources will still break, and if we change the datatree_name
    // here we will have no way to ever map contact list entries that broke
    // to the correct list, since the original value is lost...maybe persist
    // the original value somewhere in the share params then remove it after
    // some sort of upgrade maint. is run after user's next login.
    if ($source != $primary_source) {
        $db->query('UPDATE horde_datatree SET datatree_name = ? WHERE datatree_id = ?', array($source . $datatree_name, $id));
    }

    // Delete old sourceType and uid settings.
    $statement = $db->prepare('DELETE FROM horde_datatree_attributes WHERE datatree_id = ? AND attribute_name = ?');
    $db->execute($statement, array($id, 'uid'));
    $db->execute($statement, array($id, 'sourceType'));

    // Get rid of the datatree_parents string.
    $db->query('UPDATE horde_datatree SET datatree_parents = ? WHERE group_uid = ? AND datatree_id = ?',
               array('', 'horde.shares.turba', $id));

}

// Done with actual shares
echo "Successfully flattened shared address books.\n";

exit(0);
