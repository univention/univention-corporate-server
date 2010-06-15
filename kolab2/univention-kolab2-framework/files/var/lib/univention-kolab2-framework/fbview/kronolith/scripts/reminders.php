#!/usr/local/bin/php -q
<?php
/**
 * $Horde: kronolith/scripts/reminders.php,v 1.15 2004/05/20 04:06:14 chuck Exp $
 *
 * Copyright 2003-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

// Find the base file path of Horde.
@define('HORDE_BASE', dirname(__FILE__) . '/../..');

// Find the base file path of Kronolith.
@define('KRONOLITH_BASE', dirname(__FILE__) . '/..');

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

// Now load the Registry and setup conf, etc.
$registry = &Registry::singleton();
$registry->pushApp('kronolith', false);

// Include needed libraries.
require_once 'Date/Calc.php';
require_once 'Horde/Scheduler.php';
require_once KRONOLITH_BASE . '/lib/Kronolith.php';
require_once KRONOLITH_BASE . '/lib/Scheduler/kronolith.php';

// Create a share instance. This must exist in the global scope for
// Kronolith's API calls to function properly.
require_once 'Horde/Share.php';
$shares = &Horde_Share::singleton($registry->getApp());

// Create a calendar backend object. This must exist in the global
// scope for Kronolith's API calls to function properly.
$kronolith = &Kronolith_Driver::factory();

// Get an instance of the Kronolith schedulerr.
$reminder = &Horde_Scheduler::unserialize('Horde_Scheduler_kronolith');

// Start the daemon going.
$reminder->run();
