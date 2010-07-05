#!/usr/bin/php
<?php
/**
 * This script imports SquirrelMail database calendars into Kronolith.
 *
 * The first argument must be a DSN to the database containing the calendar
 * and event tables, e.g.: "mysql://root:password@localhost/squirrelmail".
 *
 * $Horde: kronolith/scripts/import_squirrelmail_calendar.php,v 1.1.2.3 2009-01-06 15:24:50 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../..');
@define('KRONOLITH_BASE', dirname(__FILE__) . '/..');

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
$default_tz = getenv('TZ');

// Make sure we load Horde base to get the auth config
require_once HORDE_BASE . '/lib/base.php';
if ($conf['auth']['admins']) {
    $auth = Auth::singleton($conf['auth']['driver']);
    $auth->setAuth($conf['auth']['admins'][0], array());
}

// Now that we are authenticated, we can load Kronolith's base. Otherwise, the
// share code breaks, causing a new, completely empty share to be created with
// no owner.
require_once KRONOLITH_BASE . '/lib/base.php';
require_once 'Horde/iCalendar.php';

// Connect to database.
$db = &DB::connect($dsn);
if (is_a($db, 'PEAR_Error')) {
    $cli->fatal($db->toString());
}

// Loop through SquirrelMail calendars.
$read_stmt = $db->prepare('SELECT reader_name FROM calendar_readers WHERE calendar_id = ?');
$write_stmt = $db->prepare('SELECT writer_name FROM calendar_writers WHERE calendar_id = ?');
$handle = $db->query('SELECT id, name, owner_name FROM calendars, calendar_owners WHERE calendars.id = calendar_owners.calendar_id');
if (is_a($handle, 'PEAR_Error')) {
    $cli->fatal($handle->toString());
}
$auth = &Auth::singleton($conf['auth']['driver']);
while ($row = $handle->fetchRow(DB_FETCHMODE_ASSOC)) {
    $user = $row['owner_name'];
    $auth->setAuth($user, array());
    $cli->message('Creating calendar ' . $row['name']);
    $share = $kronolith_shares->newShare($row['id']);
    $share->set('name', $row['name']);
    $kronolith_shares->addShare($share);

    // Add permissions.
    $permissions = array();
    $result = $db->execute($read_stmt, array($row['id']));
    if (is_a($result, 'PEAR_Error')) {
        $cli->fatal($result->toString());
    }
    while ($perm_row = $result->fetchRow()) {
        $permissions[$perm_row[0]] = PERMS_READ | PERMS_SHOW;
    }
    $result = $db->execute($write_stmt, array($row['id']));
    if (is_a($result, 'PEAR_Error')) {
        $cli->fatal($result->toString());
    }
    while ($perm_row = $result->fetchRow()) {
        if (isset($permissions[$perm_row[0]])) {
            $permissions[$perm_row[0]] |= PERMS_EDIT;
        } else {
            $permissions[$perm_row[0]] = PERMS_EDIT;
        }
    }
    if (count($permissions)) {
        $perm = $share->getPermission();
        $perm->addUserPermission($user, PERMS_ALL, false);
        foreach ($permissions as $key => $value) {
            $perm->addUserPermission($key, $value, false);
        }
        $share->setPermission($perm);
        $share->save();
    }
}

$handle = $db->query('SELECT event_id, calendar_id, ical_raw, owner_name, prefval FROM events, event_owners LEFT JOIN userprefs ON event_owners.owner_name = userprefs.user AND userprefs.prefkey = \'timezone\' WHERE events.id = event_owners.event_key ORDER BY calendar_id, userprefs.prefval, event_owners.owner_name');
if (is_a($handle, 'PEAR_Error')) {
    $cli->fatal($handle->toString());
}
$auth = &Auth::singleton($conf['auth']['driver']);
$ical = new Horde_iCalendar();
$tz = $calendar = $user = $count = null;
while ($row = $handle->fetchRow(DB_FETCHMODE_ASSOC)) {
    // Open calendar.
    if ($calendar != $row['calendar_id']) {
        if (!is_null($count)) {
            $cli->message('  Added ' . $count . ' events', 'cli.success');
        }
        $calendar = $row['calendar_id'];
        $cli->message('Importing events into ' . $calendar);
        $kronolith_driver->open($calendar);
        $count = 0;
    }
    // Set timezone.
    if ($tz != $row['prefval']) {
        $tz = $row['prefval'];
        putenv('TZ=' . ($tz ? $tz : $default_tz));
    }
    // Set user.
    if ($user != $row['owner_name']) {
        $user = $row['owner_name'];
        $auth->setAuth($user, array());
    }
    // Parse event.                                                            
    $parsed = $ical->parsevCalendar($row['ical_raw']);                         
    if (is_a($parsed, 'PEAR_Error')) {                                         
        $cli->message('  ' . $parsed->getMessage(), 'cli.warning');            
        continue;                                                              
    }                                                                          
    $components = $ical->getComponents();                                      
    if (!count($components)) {                                                 
        $cli->message('  No iCalendar data was found.', 'cli.warning');        
        continue;                                                              
    }                                                                          
                                                                               
    // Save event.                                                             
    $event = &$kronolith_driver->getEvent();                                   
    $event->fromiCalendar($components[0]);                                     
    $result = $event->save();                                                  
    if (is_a($result, 'PEAR_Error')) {                                         
        $cli->message('  ' . $result->getMessage(), 'cli.error');              
        continue;
    }
    $count++;
}
if (!is_null($count)) {
    $cli->message('  Added ' . $count . ' events', 'cli.success');
}
