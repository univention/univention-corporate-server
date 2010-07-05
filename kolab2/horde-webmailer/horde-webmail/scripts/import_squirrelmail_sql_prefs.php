#!/usr/bin/php
<?php
/**
 * This script imports SquirrelMail database preferences into Horde.
 *
 * The first argument must be a DSN to the database containing the "userprefs"
 * table, e.g.: "mysql://root:password@localhost/squirrelmail".
 *
 * $Horde: horde/scripts/import_squirrelmail_sql_prefs.php,v 1.2.2.2 2009-01-06 15:26:19 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Ben Chavet <ben@horde.org>
 * @author Jan Schneider <jan@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/..');

// Do CLI checks and environment setup first.
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/CLI.php';

// Makre sure no one runs this from the web.
if (!Horde_CLI::runningFromCli()) {
    exit("Must be run from the command line\n");
}

// Load the CLI environment - make sure there's no time limit, init some
// variables, etc.
$cli = &Horde_CLI::singleton();
$cli->init();

// Read command line parameters.
if ($argc != 2) {
    $cli->message('Too many or too few parameters.', 'cli.error');
    $cli->writeln('Usage: import_squirrelmail_prefs.php DSN');
    exit;
}
$dsn = $argv[1];

// Make sure we load Horde base to get the auth config
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Identity.php';
require_once dirname(__FILE__) . '/import_squirrelmail_prefs.php';

// Connect to database.
$db = &DB::connect($dsn);
if (is_a($db, 'PEAR_Error')) {
    $cli->fatal($db->toString());
}

// Loop through SquirrelMail address books.
$handle = $db->query('SELECT user, prefkey, prefval FROM userprefs ORDER BY user');
if (is_a($handle, 'PEAR_Error')) {
    $cli->fatal($handle->toString());
}
$auth = &Auth::singleton($conf['auth']['driver']);
$user = null;
$prefs_cache = array();
while ($row = $handle->fetchRow(DB_FETCHMODE_ASSOC)) {
    if (is_null($user)) {
        $user = $row['user'];
    }
    if ($row['user'] != $user) {
        importPrefs();
        $prefs_cache = array();
        $user = $row['user'];
    }

    $prefs_cache[$row['prefkey']] = $row['prefval'];
}
importPrefs();

function importPrefs()
{
    global $auth, $cli, $conf, $user, $prefs_cache;

    $auth->setAuth($user, array());
    $cli->message('Importing ' . $user . '\'s preferences');
    $prefs = &Prefs::factory($conf['prefs']['driver'], 'horde', $user, null, null, false);
    savePrefs($user, null, $prefs_cache);
}

function getSignature($basename, $number = 'nature')
{
    global $prefs_cache;

    $key = '___sig' . $number . '___';
    return isset($prefs_cache[$key]) ? $prefs_cache[$key] : '';
}