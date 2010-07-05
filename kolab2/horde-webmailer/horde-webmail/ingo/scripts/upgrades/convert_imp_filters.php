<?php
/**
 * Converts a user's preferences from the "old" IMP 3.x or IMP HEAD
 * (pre 4.x) filter data structure to the "new" Ingo 2.x structure.
 *
 * This script is untested so use at your own risk.
 *
 * Usage: php convert_filters.php < filename
 * Filename is a file that contains a list of users, one username per line.
 * The username should be the same as how the preferences are stored in
 * the preferences backend (e.g. usernames may have to be in the form
 * user@example.com).
 *
 * This script is written to convert SQL databases ONLY.
 * There is no guarantee it will work on other preference backends (e.g. LDAP).
 *
 * $Horde: ingo/scripts/upgrades/convert_imp_filters.php,v 1.1.2.2 2009-01-06 15:24:39 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Michael Slusarz <slusarz@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../..');
@define('INGO_BASE', dirname(__FILE__) . '/..');

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

/* Initialize the needed libraries. */
require_once INGO_BASE . '/lib/base.php';

/* Initialize authentication backend. */
$auth = &Auth::singleton($conf['auth']['driver']);

/* Update each user. */
while (!feof(STDIN)) {
    $user = fgets(STDIN);
    $count = 0;
    $user = trim($user);
    if (empty($user)) {
        continue;
    }

    echo "Converting filters for user: $user\n";

    $auth->setAuth($user, array());
    $_SESSION['ingo']['current_share'] = ':' . $user;

    $userprefs = &Prefs::singleton($conf['prefs']['driver'],
                                   'imp', $user, '', null, false);
    $userprefs->retrieve();
    $oldfilters = @unserialize($userprefs->getValue('filters'));

    if (!is_array($oldfilters)) {
        echo "    Nothing to convert\n";
        continue;
    }

    /* Load the user's preferences. */
    $prefs = &Prefs::factory($conf['prefs']['driver'], 'ingo', $user, null, null, false);
    $prefs->retrieve();

    /* Merge with existing ingo filters. */
    $filters = &$ingo_storage->retrieve(INGO_STORAGE_ACTION_FILTERS, false);

    /* Make sure special rules exist */
    $rule_count = 0;
    $located = array();
    $filterlist = $filters->getFilterList();
    if (!empty($filterlist)) {
        foreach ($filters->getFilterList() as $rule) {
            $located[$rule['action']] = true;
        }
    }

    if (!isset($located[INGO_STORAGE_ACTION_BLACKLIST])) {
        $filters->addRule(array('name' => "Blacklist", 'action' => INGO_STORAGE_ACTION_BLACKLIST), false);
        echo "    Added Blacklist Rule\n";
        $rule_count++;
    }

    if (!isset($located[INGO_STORAGE_ACTION_WHITELIST])) {
        $filters->addRule(array('name' => "Whitelist", 'action' => INGO_STORAGE_ACTION_WHITELIST), false);
        echo "    Added Whitelist Rule\n";
        $rule_count++;
    }

    if (!isset($located[INGO_STORAGE_ACTION_VACATION])) {
        $filters->addRule(array('name' => "Vacation", 'action' => INGO_STORAGE_ACTION_VACATION), false);
        echo "    Added Vacation Rule\n";
        $rule_count++;
    }

    if (!isset($located[INGO_STORAGE_ACTION_FORWARD])) {
        $filters->addRule(array('name' => "Forward", 'action' => INGO_STORAGE_ACTION_FORWARD), false);
        echo "    Added Forward Rule\n";
        $rule_count++;
    }

    if ($rule_count) {
        echo "    Importing " . $rule_count . " existing ingo filters\n";
    }

    /* IMP HEAD filter style
     * Array
     * (
     *   [bl] => Array
     *   (
     *     [BLACKLISTED ADDRESSES]
     *   ),
     *
     *   [rule] => Array
     *   (
     *     [*Filter number*] => Array
     *     (
     *       [flt] => Array
     *       (
     *         [] => Array
     *           (
     *             [fld] => Array(*Field name(s)*)
     *             [txt] => Array(*Text to match*)
     *           )
     *       )
     *       [act] => *Action code*
     *       [fol] => *Folder name to move to*
     *     )
     *   )
     * )
     */
    if (isset($oldfilters['bl'])) {
        if (!empty($oldfilters['bl'])) {
            $ob = &new Ingo_Storage_blacklist();
            $ob->setBlacklist($oldfilters['bl']);
            $ingo_storage->store($ob);
            echo "    Converted Blacklist\n";
        }

        if (!empty($oldfilters['rule'])) {
            foreach ($oldfilters['rule'] as $val) {
                $curr = array(
                    'action' => 0,
                    'name' => 'Converted IMP Filter',
                    'combine' => INGO_STORAGE_COMBINE_ALL,
                    'stop' => false,
                    'flags' => 0,
                    'conditions' => array(),
                    'action-value' => null
                );

                /* IMP_FILTER_DELETE = 1, IMP_FILTER_MOVE = 2,
                   IMP_FILTER_NUKE = 3 */
                if ($val['act'] == 1) {
                    $curr['action'] = INGO_STORAGE_ACTION_MOVE;
                    $curr['combine'] .= ' - DELETE';
                } elseif ($val['act'] == 2) {
                    $curr['action'] = INGO_STORAGE_ACTION_MOVE;
                    $curr['combine'] .= ' - MOVE';
                } elseif ($val['act'] == 3) {
                    $curr['action'] = INGO_STORAGE_ACTION_DISCARD;
                    $curr['combine'] .= ' - NUKE';
                }

                foreach ($val['flt'] as $val2) {
                    foreach ($val2['fld'] as $key => $field) {
                        $curr['conditions'][] = Array(
                            'field' => ucfirst($field),
                            'match' => 'contains',
                            'value' => $val2['txt'][$key],
                            'case' => false,
                            'type' => INGO_STORAGE_TYPE_HEADER
                        );
                    }
                }

                if (isset($val['fol'])) {
                    $curr['action-value'] = $val['fol'];
                }

                $count++;
                $filters->addRule($curr);
            }
        }

        echo "    Converted $count Filters\n";
        $ingo_storage->store($filters);
    }

    /* IMP 3.x filter style
     * Array
     * (
     *   [#] => Array
     *   (
     *     [action] => 'move' -or- 'delete'
     *     [folder] => folder name (may not exist)
     *     [fields] => Array
     *     (
     *     )
     *     [text] => Array
     *     (
     *     )
     *   )
     * )
     */
    else {
        $bl_array = array();

        if (!empty($oldfilters)) {
            foreach ($oldfilters as $rule) {
                if (($rule['action'] == 'delete') &&
                    (count($rule['fields']) == 1) &&
                    ($rule['fields'][0] == 'from')) {
                    if (!in_array($rule['text'], $bl_array)) {
                        $bl_array[] = $rule['text'];
                    }
                } else {
                    $curr = array(
                        'action' => 0,
                        'name' => 'Converted IMP Filter',
                        'combine' => INGO_STORAGE_COMBINE_ANY,
                        'stop' => false,
                        'flags' => 0,
                        'conditions' => array(),
                        'action-value' => null
                    );

                    if ($rule['action'] == 'move') {
                        $curr['action'] = INGO_STORAGE_ACTION_MOVE;
                        $curr['name'] .= ' - MOVE';
                    } elseif ($rule['action'] == 'delete') {
                        $curr['action'] = INGO_STORAGE_ACTION_DISCARD;
                        $curr['name'] .= ' - DISCARD';
                    }

                    if (isset($rule['folder'])) {
                        $curr['action-value'] = $rule['folder'];
                    }

                    foreach ($rule['fields'] as $key => $val) {
                        $curr['conditions'][] = Array(
                            'field' => ucfirst($val),
                            'match' => 'contains',
                            'value' => $rule['text'],
                            'case' => false,
                            'type' => INGO_STORAGE_TYPE_HEADER
                        );
                    }

                    $count++;
                    $filters->addRule($curr);
                }
            }
        }

        $ob = &new Ingo_Storage_blacklist();
        $ob->setBlacklist($bl_array);
        $ingo_storage->store($ob);
        echo "    Converted " . count($bl_array) . " Blacklist Entries\n";

        $ingo_storage->store($filters);
        echo "    Converted $count Filters\n";

        $prefs->store();
    }
}
