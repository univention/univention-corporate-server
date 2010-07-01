#!/usr/bin/php -q
<?php
/**
 * $Horde: imp/scripts/upgrades/convert_vfolders.php,v 1.1.2.1 2007-12-20 14:00:36 jan Exp $
 *
 * A script to update Virtual Folders from IMP 4.0.x format to IMP 4.1+
 * format. Expects to be given a list of users on STDIN, one username per
 * line, to convert. Usernames need to match the values stored in the
 * preferences backend.
 */

// Find the base file path of Horde.
@define('AUTH_HANDLER', true);
@define('IMP_BASE', dirname(__FILE__) . '/../..');

// Do CLI checks and environment setup first.
require_once IMP_BASE . '/lib/base.php';
require_once 'Horde/CLI.php';

// Make sure no one runs this from the web.
if (!Horde_CLI::runningFromCLI()) {
    exit("Must be run from the command line\n");
}

// Load the CLI environment - make sure there's no time limit, init
// some variables, etc.
Horde_CLI::init();

$cli = &Horde_CLI::singleton();
$auth = &Auth::singleton($conf['auth']['driver']);

// Read in the list of usernames on STDIN.
$users = array();
while (!feof(STDIN)) {
    $line = fgets(STDIN);
    $line = trim($line);
    if (!empty($line)) {
        $users[] = $line;
    }
}

// Loop through users.
foreach ($users as $user) {
    echo 'Converting Virtual Folders for ' . $cli->bold($user);

    // Set $user as the current user.
    $auth->setAuth($user, array(), '');

    $vfolder = $imp_search->_getVFolderList();
    if (empty($vfolder)) {
        $cli->writeln();
        continue;
    }

    $elt = reset($vfolder);
    if (!isset($elt['ob'])) {
        // Already in 4.1+ format.
        $cli->writeln();
        continue;
    }

    // Convert from 4.0 format to 4.1+ format
    $convert = array();
    foreach ($vfolder as $key => $val) {
        $convert[$key] = array(
            'query' => $val['ob'],
            'folders' => $val['search']['folders'],
            'uiinfo' => $val['search'],
            'label' => $val['search']['vfolder_label'],
            'vfolder' => true
        );
    }

    $imp_search->_saveVFolderList($convert);
    $prefs->store();
    $cli->writeln();
}

$cli->writeln();
$cli->writeln($cli->green('DONE'));
exit;
