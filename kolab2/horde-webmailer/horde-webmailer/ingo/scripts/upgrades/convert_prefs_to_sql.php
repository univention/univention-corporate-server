#!/usr/bin/php
<?php
/**
 * Converts a user's filter rules from the preferences storage backend to the
 * new SQL storage backend that has been added in Ingo 1.2.
 *
 * Usage: php convert_prefs_to_sql.php < filename
 * Filename is a file that contains a list of users, one username per line.
 * The username should be the same as how the preferences are stored in
 * the preferences backend (e.g. usernames may have to be in the form
 * user@example.com).
 *
 * $Horde: ingo/scripts/upgrades/convert_prefs_to_sql.php,v 1.2.2.5 2009-08-02 13:45:50 mrubinsk Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../../..');
@define('INGO_BASE', dirname(__FILE__) . '/../..');

/* Do CLI checks and environment setup first. */
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/CLI.php';

/* Make sure no one runs this from the web. */
if (!Horde_CLI::runningFromCLI()) {
    exit("Must be run from the command line\n");
}

/* Load the CLI environment - make sure there's no time limit, init some
 * variables, etc. */
Horde_CLI::init();
$cli = &Horde_CLI::singleton();

/* Initialize the needed libraries. */
require_once INGO_BASE . '/lib/base.php';

/* Initialize authentication backend. */
$auth = &Auth::singleton($conf['auth']['driver']);

/* Initialize storage backends. */
if ($conf['storage']['driver'] != 'sql') {
    $cli->fatal('You need to configure an SQL storage backend in Ingo\'s configuration', __FILE__, __LINE__);
}
$prefs_storage = Ingo_Storage::factory('prefs');
$sql_storage = Ingo_Storage::factory('sql');
if (is_a($sql_storage, 'PEAR_Error')) {
    $cli->fatal($sql_storage, __FILE__, __LINE__);
}

/* Rules to convert. */
$rules = array(INGO_STORAGE_ACTION_FILTERS,
               INGO_STORAGE_ACTION_BLACKLIST,
               INGO_STORAGE_ACTION_WHITELIST,
               INGO_STORAGE_ACTION_VACATION,
               INGO_STORAGE_ACTION_FORWARD,
               INGO_STORAGE_ACTION_SPAM);

/* Update each user. */
while (!feof(STDIN)) {
    $user = fgets(STDIN);
    $count = 0;
    $user = trim($user);
    if (empty($user)) {
        continue;
    }

    echo 'Converting filters for user: ' . $user;

    $auth->setAuth($user, array());
    $_SESSION['ingo']['current_share'] = ':' . $user;

    foreach ($rules as $rule) {
        $filter = $prefs_storage->retrieve($rule, false);
        if ($rule == INGO_STORAGE_ACTION_FILTERS) {
            $new_filter = &$sql_storage->retrieve(INGO_STORAGE_ACTION_FILTERS, true, true);
            if (is_a($new_filter, 'PEAR_Error')) {
                // If we can't create the filter, fatal out and notify the user.
                $cli->fatal($new_filter->getMessage(), 'cli.error');
            }
            foreach ($filter->getFilterlist() as $rule) {
                $new_filter->addRule($rule);
                echo '.';
            }
        }
        $result = $sql_storage->store($filter, false);
        if (is_a($result, 'PEAR_Error')) {
            $cli->writeln();
            $cli->message($result->getMessage(), 'cli.error');
        }
    }
    $cli->writeln($cli->green('done'));
}
