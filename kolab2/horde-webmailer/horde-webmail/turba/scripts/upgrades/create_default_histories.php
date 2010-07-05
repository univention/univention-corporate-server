#!/usr/bin/php
<?php
/**
 * $Horde: turba/scripts/upgrades/create_default_histories.php,v 1.1.2.5 2008-03-31 17:06:52 jan Exp $
 *
 * Copyright 1999-2007 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../../..');
@define('TURBA_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/core.php';

// Do CLI checks and environment setup first.
require_once 'Horde/CLI.php';

// Make sure no one runs this from the web.
if (!Horde_CLI::runningFromCLI()) {
    exit("Must be run from the command line\n");
}

// Load the CLI environment - make sure there's no time limit, init
// some variables, etc.
Horde_CLI::init();

// Load Horde's base.php to ensure we have a pushed application on
// the registry stack, and to load the authentication configuration
// without having to load Turba's base.php before we are authenticated.
require_once HORDE_BASE . '/lib/base.php';

// Authenticate as administrator. We need to authenticate *before* we
// include Turba's base.php since Turba_Driver objects will be created
// during that script.  The drivers will, of course be cached by using
// the singleton pattern, so the factory method would never be called after
// we are authenticated...which breaks the code dealing with shares in
// Turba_Driver.
if ($conf['auth']['admins']) {
    $auth = Auth::singleton($conf['auth']['driver']);
    $auth->setAuth($conf['auth']['admins'][0], array());
}

// Load Turba's base.php and get a fresh copy of cfgSources if we are
// authenticated.
require_once TURBA_BASE . '/lib/base.php';
if ($auth->isAuthenticated()) {
    require TURBA_BASE . '/config/sources.php';
}

$history = &Horde_History::singleton();

// Make sure we grab any shares.
$shares = $GLOBALS['turba_shares']->listAllShares();

// Run through every contact source.
$sources = Turba::permissionsFilter($cfgSources, 'source', PERMS_EDIT);

// Add the shared sources
foreach ($shares as $share) {
    $name = $share->get('sourceType') . ':' . $share->get('uid');
    if (!isset($sources[$name])) {
        list($srcType, $user) = explode(':', $name, 2);
        if ($user != Auth::getAuth()) {
            $newSrc = $cfgSources[$srcType];
            $newSrc['title'] = $share->get('name');
            $cfgSources[$name] = $sources[$name] = $newSrc;
        }
    }
}

foreach ($sources as $key => $curSource) {
    $driver = &Turba_Driver::singleton($key);
    if (is_a($driver, 'PEAR_Error')) {
        var_dump($driver);
        exit;
    }

    echo "Creating default histories for $key ...\n";

    // List all contacts.
    $results = $driver->search(array());
    if (is_a($results, 'PEAR_Error')) {
        var_dump($results);
        exit;
    }
    while ($object = $results->next()) {
        $id = 'turba:' . ($object->getValue('__owner') ? $object->getValue('__owner') : Auth::getAuth()) . ':' . $object->getValue('__uid');
        /* Get the contact's history. */
        $log = $history->getHistory($id);
        foreach ($log->getData() as $entry)
        {
            if ($entry['action'] == 'add') {
                continue 2;
            }
        }

        // If there isn't an add entry, add one at the current time.
        $result = $history->log($id, array('action' => 'add'), true);
        if (is_a($result, 'PEAR_Error')) {
            var_dump($result);
            exit;
        }
    }
}

echo "\n** Default histories successfully created ***\n";
