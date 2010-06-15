#!/usr/bin/php -q
<?php
/**
 * $Horde: horde/scripts/migrate_links.php,v 1.5 2004/04/07 14:43:44 chuck Exp $
 *
 * This is a script to migrate old Horde_Links to the 
 * horde_category_attributes table. 
 *
 * Note that this script currently only migrates whups links (modules, tickets)
 * to the new categories structure.
 *
 */

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
require_once 'Horde/Links.php';

$category = &DataTree::factory('sql');
$db = &$category->_db;

$links = &Horde_Links::singleton('horde');

$old_links = $db->getAll('SELECT link_id, link_type, link_from_provider, link_from_parameter, 
                                 link_to_provider, link_to_parameter
                          FROM horde_links');
$category->_params['group'] = 'horde.links';
$category->_load();
foreach ($old_links as $id => $params) {
    $link_id = $params[0];
    $link_type = $params[1];
    $link_from_provider = $params[2];
    $link_from_parameter = @unserialize($params[3]);
    $link_to_provider = $params[4];
    $link_to_parameter = @unserialize($params[5]);

    // workaround for Whups client data previously saved with provider 'contacts'
    // now standardise these as 'clients'
    if (strstr($link_type, 'client') && $link_to_provider == 'contacts') {
        $link_to_provider = 'clients';
    }

    // now build the new attributes structure (NOTE: only Whups links are currently fully implemented here)
    if ($link_from_provider == 'tickets') {
        if (!empty($link_from_parameter['module_id'])) {
            $link_from_parameter = array('from_key' => 'module_id', 
                                         'from_value' => $link_from_parameter['module_id']);
        } elseif (!empty($link_from_parameter['ticket_id'])) {
            $link_from_parameter = array('from_key' => 'ticket_id', 
                                         'from_value' => $link_from_parameter['ticket_id']);
        }
    }

    if ($link_to_provider == 'clients') {
        $link_to_parameter = array('source' => $link_to_parameter['source'], 
                                   'to_value' => $link_to_parameter['id']);
    }

    $link_data = array('from_params' => $link_from_parameter, 
                       'to_params' => $link_to_parameter, 
                       'link_params' => array('link_type' => $link_type, 
                                              'from_application' => $link_from_provider, 
                                              'to_application' => $link_to_provider));

    $status = $links->addLink($link_data);

    if (is_a($status, 'PEAR_Error')) {
        var_dump($status);
        exit;
    }

}

echo "Links successfully migrated\n";


