#!/usr/local/bin/php
<?php
/**
 * $Horde: horde/scripts/remove_prefs.php,v 1.3 2004/04/07 14:43:44 chuck Exp $
 *
 * This script removes a pref from users' settings. Helps when a setting is
 * to be moved from locked = false, to locked = true and there have already
 * been prefs set by the users.
 */

/**
 ** Set this to true if you want DB modifications done.
 **/
$live = false;

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
$cli = &new Horde_CLI();

require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/DataTree.php';
require_once 'Horde/Group.php';
require_once 'Horde/Share.php';

/* Make sure there's no compression. */
ob_end_clean();


$scope = $cli->prompt(_("Enter value for pref_scope:"));
$name = $cli->prompt(_("Enter value for pref_name:"));

/* Open the database. */
$db = &DB::connect($conf['sql']);
if (is_a($db, 'PEAR_Error')) {
   var_dump($db); exit;
}

if ($live) {
    $sql = sprintf('DELETE FROM horde_prefs WHERE pref_scope = %s AND pref_name = %s',
                   $db->quote($scope),
                   $db->quote($name));
    $result = $db->getAll($sql);
    if (is_a($result, 'PEAR_Error')) {
        var_dump($result);
    } elseif (empty($result)) {
        $cli->writeln(sprintf(_("No preference '%s' found in scope '%s'."), $name, $scope));
    } else {
        $cli->writeln(sprintf(_("Preferences '%s' deleted in scope '%s'."), $name, $scope));
    }
} else {
    $sql = sprintf('SELECT * FROM horde_prefs WHERE pref_scope = %s AND pref_name = %s',
                   $db->quote($scope),
                   $db->quote($name));
    $result = $db->getAll($sql);
    if (empty($result)) {
        $cli->writeln(sprintf(_("No preference '%s' found in scope '%s'."), $name, $scope));
    } else {
        var_dump($result);
    }
}
