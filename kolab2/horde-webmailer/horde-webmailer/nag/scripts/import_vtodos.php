#!/usr/bin/php
<?php
/**
 * This script imports vTodo data into Nag tasklists.
 * The data is read from standard input, the tasklist and user name passed as
 * parameters.
 *
 * $Horde: nag/scripts/import_vtodos.php,v 1.3.2.7 2009-01-06 15:25:09 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../..');

// Do CLI checks and environment setup first.
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/CLI.php';

// Make sure no one runs this from the web.
if (!Horde_CLI::runningFromCLI()) {
    exit("Must be run from the command line\n");
}

// Load the CLI environment - make sure there's no time limit, init some
// variables, etc.
$cli = &Horde_CLI::singleton();
$cli->init();

// Read command line parameters.
if (count($argv) != 3) {
    $cli->message('Too many or too few parameters.', 'cli.error');
    usage();
}
$tasklist = $argv[1];
$user = $argv[2];

// Read standard input.
$vtodo = $cli->readStdin();
if (empty($vtodo)) {
    $cli->message('No import data provided.', 'cli.error');
    usage();
}

// Registry.
$registry = &Registry::singleton();

// Set user.
$auth = &Auth::singleton($conf['auth']['driver']);
$auth->setAuth($user, array());

// Import data.
$result = $registry->call('tasks/import',
                          array($vtodo, 'text/calendar', $tasklist));
if (is_a($result, 'PEAR_Error')) {
    $cli->fatal($result->toString());
}

$cli->message('Imported successfully ' . count($result) . ' tasks', 'cli.success');

function usage()
{
    $GLOBALS['cli']->writeln('Usage: import_vtodos.php tasklist user');
    exit;
}

