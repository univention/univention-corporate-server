#!/usr/bin/php -q
<?php
/**
 * $Horde: horde/scripts/upgrades/migrate_user_categories.php,v 1.1.2.3 2008-04-08 14:29:47 chuck Exp $
 *
 * A script to update users preferences to combine their categories
 * and category colors from Genie, Kronolith, Mnemo, and Nag into the
 * new Horde-wide preferences. Expects to be given a list of users on
 * STDIN, one username per line, to convert. Usernames need to match
 * the values stored in the preferences backend.
 */

// Find the base file path of Horde.
@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../..');

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

require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Prefs/CategoryManager.php';
$cli = &Horde_CLI::singleton();
$auth = &Auth::singleton($conf['auth']['driver']);
$cManager = new Prefs_CategoryManager();
$apps = $registry->listApps(array('hidden', 'notoolbar', 'active', 'admin'));

// Read in the list of usernames on STDIN.
$users = array();
while (!feof(STDIN)) {
    $line = fgets(STDIN);
    $line = trim($line);
    if (!empty($line)) {
        $users[] = $line;
    }
}

// Loop through users and convert prefs for Genie, Mnemo, Nag, and
// Kronolith.
foreach ($users as $user) {
    echo 'Migrating prefs for ' . $cli->bold($user);

    // Set $user as the current user.
    $auth->setAuth($user, array(), '');

    // Fetch current categories and colors.
    $colors = $cManager->colors();

    // Genie.
    if (in_array('genie', $apps)) {
        echo ' . genie';
        $result = $registry->pushApp('genie', false);
        if (!is_a($result, 'PEAR_Error')) {
            $g_categories = listCategories('wish_categories');
            foreach ($g_categories as $category) {
                $cManager->add($category);
            }
        }
    }

    // Mnemo.
    if (in_array('mnemo', $apps)) {
        echo ' . mnemo';
        $result = $registry->pushApp('mnemo', false);
        if (!is_a($result, 'PEAR_Error')) {
            $m_categories = listCategories('memo_categories');
            $m_colors = listColors('memo_colors');
            foreach ($m_categories as $key => $category) {
                if (isset($m_colors[$key])) {
                    $colors[$category] = $m_colors[$key];
                }
                $cManager->add($category);
            }
        }
    }

    // Nag.
    if (in_array('nag', $apps)) {
        echo ' . nag';
        $result = $registry->pushApp('nag', false);
        if (!is_a($result, 'PEAR_Error')) {
            $n_categories = listCategories('task_categories');
            foreach ($n_categories as $category) {
                $cManager->add($category);
            }
        }
    }

    // Kronolith.
    if (in_array('kronolith', $apps)) {
        echo ' . kronolith';
        $result = $registry->pushApp('kronolith', false);
        if (!is_a($result, 'PEAR_Error')) {
            $k_categories = listCategories('event_categories');
            if (count($k_categories)) var_dump($k_categories);
            $k_colors = listColors('event_colors');
            foreach ($k_categories as $key => $category) {
                if (isset($k_colors[$key])) {
                    $colors[$category] = $k_colors[$key];
                }
                $cManager->add($category);
            }
        }
    }

    $cManager->setColors($colors);
    $prefs->store();
    $cli->writeln();
}

$cli->writeln();
$cli->writeln($cli->green('DONE'));
exit;

function listCategories($prefname)
{
    global $prefs;

    $string = $prefs->getValue($prefname);
    if (empty($string)) {
        return array();
    }

    $cats = explode('|', $string);
    foreach ($cats as $cat) {
        list($key, $val) = explode(':', $cat);
        $categories[$key] = $val;
    }

    return $categories;
}

function listColors($prefname)
{
    global $prefs;

    $string = $prefs->getValue($prefname);
    if (empty($string)) {
        return array();
    }
    $cols = explode('|', $string);
    $colors = array();
    foreach ($cols as $col) {
        list($key, $val) = explode(':', $col);
        $colors[$key] = $val;
    }

    return $colors;
}
