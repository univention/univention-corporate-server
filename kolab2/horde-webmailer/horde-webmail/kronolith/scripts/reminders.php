#!/usr/bin/php -q
<?php
/**
 * $Horde: kronolith/scripts/reminders.php,v 1.17.10.10 2009-01-06 15:24:50 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
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

require_once KRONOLITH_BASE . '/lib/Scheduler/kronolith.php';

// Get an instance of the Kronolith scheduler and run it.
$reminder = &Horde_Scheduler::unserialize('Horde_Scheduler_kronolith');
$reminder->run();
