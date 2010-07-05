<?php
/**
 * Functions required to start a Ingo session.
 *
 * $Horde: ingo/lib/Session.php,v 1.2.10.11 2009-01-06 15:24:35 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Ingo
 */
class Ingo_Session {

    /**
     * Create an ingo session.
     * This function should only be called once, when the user first uses
     * Ingo in a session.
     *
     * Creates the $ingo session variable with the following entries:
     * 'backend' (array) - The backend configuration to use.
     * 'change' (integer) - The timestamp of the last time the rules were
     *                      altered.
     * 'storage' (array) - Used by Ingo_Storage:: for caching data.
     * 'script_categories' (array) - The list of available categories for the
     *                               Ingo_Script driver in use.
     * 'script_generate' (boolean) - Is the Ingo_Script::generate() call
     *                               available?
     *
     * @return boolean  True on success, false on failure.
     */
    function createSession()
    {
        global $prefs;

        $_SESSION['ingo'] = array(
            'change' => 0,
            'storage' => array(),
            /* Get the backend. */
            'backend' => Ingo::getBackend());

        /* Determine if the Ingo_Script:: generate() method is available. */
        $ingo_script = Ingo::loadIngoScript();
        $_SESSION['ingo']['script_generate'] = $ingo_script->generateAvailable();

        /* Disable categories as specified in preferences */
        $disabled = array();
        if ($prefs->isLocked('blacklist')) {
            $disabled[] = INGO_STORAGE_ACTION_BLACKLIST;
        }
        if ($prefs->isLocked('whitelist')) {
            $disabled[] = INGO_STORAGE_ACTION_WHITELIST;
        }
        if ($prefs->isLocked('vacation')) {
            $disabled[] = INGO_STORAGE_ACTION_VACATION;
        }
        if ($prefs->isLocked('forward')) {
            $disabled[] = INGO_STORAGE_ACTION_FORWARD;
        }
        if ($prefs->isLocked('spam')) {
            $disabled[] = INGO_STORAGE_ACTION_SPAM;
        }

        /* Set the list of categories this driver supports. */
        $_SESSION['ingo']['script_categories'] =
            array_merge($ingo_script->availableActions(),
                        array_diff($ingo_script->availableCategories(),
                                   $disabled));
    }

}
