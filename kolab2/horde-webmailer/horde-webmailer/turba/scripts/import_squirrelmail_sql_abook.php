#!/usr/bin/php
<?php
/**
 * This script imports SquirrelMail database addressbooks into Turba.
 *
 * The first argument must be a DSN to the database containing the "address"
 * table, e.g.: "mysql://root:password@localhost/squirrelmail".
 *
 * $Horde: turba/scripts/import_squirrelmail_sql_abook.php,v 1.4.2.3 2009-01-06 15:28:01 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Ben Chavet <ben@horde.org>
 * @author Jan Schneider <jan@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../..');
@define('TURBA_BASE', dirname(__FILE__) . '/..');

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
    $cli->writeln('Usage: import_squirrelmail_file_abook.php DSN');
    exit;
}
$dsn = $argv[1];

// Make sure we load Horde base to get the auth config
require_once HORDE_BASE . '/lib/base.php';
if ($conf['auth']['admins']) {
    $auth = Auth::singleton($conf['auth']['driver']);
    $auth->setAuth($conf['auth']['admins'][0], array());
}

// Now that we are authenticated, we can load Turba's base. Otherwise, the
// share code breaks, causing a new, completely empty share to be created on
// the DataTree with no owner.
require_once TURBA_BASE . '/lib/base.php';
require_once TURBA_BASE . '/lib/Object/Group.php';
require_once 'Horde/MIME.php';

// Connect to database.
$db = &DB::connect($dsn);
if (is_a($db, 'PEAR_Error')) {
    $cli->fatal($db->toString());
}

// Loop through SquirrelMail address books.
$handle = $db->query('SELECT owner, nickname, firstname, lastname, email, label FROM address ORDER BY owner');
if (is_a($handle, 'PEAR_Error')) {
    $cli->fatal($handle->toString());
}
$auth = &Auth::singleton($conf['auth']['driver']);
$turba_shares = &Horde_Share::singleton('turba');
$user = null;
$count = 0;
while ($row = $handle->fetchRow(DB_FETCHMODE_ASSOC)) {
    // Set current user
    if ($row['owner'] != $user) {
        if (!is_null($user)) {
            $cli->message('  Added ' . $count . ' contacts', 'cli.success');
            $count = 0;
        }
        $user = $row['owner'];
        $auth->setAuth($user, array());
        $cli->message('Importing ' . $user . '\'s address book');

        // Reset user prefs
        unset($prefs);
        $prefs = &Prefs::factory($conf['prefs']['driver'], 'turba', $user, null, null, false);

        // Reset $cfgSources for current user.
        unset($cfgSources);
        $hasShares = false;
        include TURBA_BASE . '/config/sources.php';
        foreach ($cfgSources as $key => $cfg) {
            if (!empty($cfg['use_shares'])) {
                $has_share = true;
                break;
            }
        }
        if ($has_share) {
            $cfgSources = Turba::getConfigFromShares($cfgSources);
        }
        $cfgSources = Turba::permissionsFilter($cfgSources);
        if (!count($cfgSources)) {
            $cli->message('No address book available for ' . $user, 'cli.error');
            continue;
        }

        // Get user's default addressbook
        $import_source = $prefs->getValue('default_dir');
        if (empty($import_source)) {
            $import_source = array_keys($cfgSources);
            $import_source = $import_source[0];
        }

        // Check existance of the specified source.
        if (!isset($cfgSources[$import_source])) {
            $cli->message('  ' . sprintf(_("Invalid address book: %s"), $import_source), 'cli.error');
            continue;
        }

        // Initiate driver
        $driver = &Turba_Driver::singleton($import_source);
        if (is_a($driver, 'PEAR_Error')) {
            $cli->message('  ' . sprintf(_("Connection failed: %s"), $driver->getMessage()), 'cli.error');
            continue;
        }
    }

    if (!count($cfgSources)) {
        continue;
    }

    $members = MIME::rfc822Explode($row['email'], ',;');
    if (count($members) > 1) {
        // Entry is a list of contacts, import each individually and create a
        // group that contains them.
        $attributes = array('alias' => $row['nickname'],
                            'firstname' => $row['firstname'],
                            'lastname' => $row['lastname'],
                            'notes' => $row['label']);
        $gid = $driver->add($attributes);
        $group = new Turba_Object_Group($driver, array_merge($attributes, array('__key' => $gid)));
        $count++;
        foreach ($members as $member) {
            $result = $driver->add(array('firstname' => $member, 'email' => $member));
            if ($result && !is_a($result, 'PEAR_Error')) {
                $added = $group->addMember($result, $import_source);
                if (is_a($added, 'PEAR_Error')) {
                    $cli->message('  ' . $added->getMessage(), 'cli.error');
                } else {
                    $count++;
                }
            }
        }
        $group->store();
    } else {
        // Entry only contains one contact, import it.
        $contact = array('alias' => $row['nickname'],
                         'firstname' => $row['firstname'],
                         'lastname' => $row['lastname'],
                         'email' => $row['email'],
                         'notes' => $row['label']);
        $added = $driver->add($contact);
        if (is_a($added, 'PEAR_Error')) {
            $cli->message('  ' . $added->getMessage(), 'cli.error');
        } else {
            $count++;
        }
    }
}
$cli->message('  Added ' . $count . ' contacts', 'cli.success');
