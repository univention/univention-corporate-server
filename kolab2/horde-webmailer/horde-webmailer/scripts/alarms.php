#!/usr/bin/env php
<?php
/**
 * $Horde: horde/scripts/alarms.php,v 1.2.2.5 2009-01-06 15:26:19 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/..');

// Do CLI checks and environment setup first.
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/CLI.php';

// Make sure no one runs this from the web.
if (!Horde_CLI::runningFromCLI()) {
    exit("Must be run from the command line\n");
}

// Load the CLI environment - make sure there's no time limit, init some
// variables, etc.
Horde_CLI::init();

// Include needed libraries.
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Alarm.php';

// Authenticate as administrator.
if (!count($conf['auth']['admins'])) {
    exit("You must have at least one administrator configured to run the alarms.php script.\n");
}
$auth = &Auth::singleton($conf['auth']['driver']);
$auth->setAuth($conf['auth']['admins'][0], array());

// Run
$horde_alarm = Horde_Alarm::factory();
$horde_alarm->notify(null, true, false, array('notify'));
