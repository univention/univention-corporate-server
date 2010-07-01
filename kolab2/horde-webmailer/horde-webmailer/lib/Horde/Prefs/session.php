<?php
/**
 * Preferences storage implementation for PHP's session implementation.
 *
 * $Horde: framework/Prefs/Prefs/session.php,v 1.32.12.12 2009-01-06 15:23:31 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @since   Horde 1.3.4
 * @package Horde_Prefs
 */
class Prefs_session extends Prefs {

    /**
     * Constructs a new session preferences object.
     *
     * @param string $user      The user who owns these preferences.
     * @param string $password  The password associated with $user. (Unused)
     * @param string $scope     The current preferences scope.
     * @param array $params     A hash containing connection parameters.
     *                           (Unused)
     * @param boolean $caching  Should caching be used?
     *
     */
    function Prefs_session($user, $password = '', $scope = '',
                           $params = null, $caching = true)
    {
        $this->_user = $user;
        $this->_scope = $scope;
        $this->_caching = $caching;

        parent::Prefs();
    }

    /**
     * Retrieves the requested set of preferences from the current session.
     *
     * @param $scope Scope specifier.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _retrieve($scope)
    {
        if (isset($_SESSION['horde_prefs'][$scope])) {
            $this->_scopes[$scope] = $_SESSION['horde_prefs'][$scope];
        }
    }

    /**
     * Stores preferences in the current session.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function store()
    {
        // Create and register the preferences array, if necessary.
        if (!isset($_SESSION['horde_prefs'])) {
            $_SESSION['horde_prefs'] = array();
        }

        // Copy the current preferences into the session variable.
        foreach ($this->_scopes as $scope => $prefs) {
            $pref_keys = array_keys($prefs);
            foreach ($pref_keys as $pref_name) {
                // Clean the pref since it was just saved.
                $prefs[$pref_name]['m'] &= ~_PREF_DIRTY;
            }

            $_SESSION['horde_prefs'][$scope] = $prefs;
        }
    }

    /**
     * Perform cleanup operations.
     *
     * @param boolean $all  Cleanup all Horde preferences.
     */
    function cleanup($all = false)
    {
        // Perform a Horde-wide cleanup?
        if ($all) {
            unset($_SESSION['horde_prefs']);
        } else {
            unset($_SESSION['horde_prefs'][$this->_scope]);
            $_SESSION['horde_prefs']['_filled'] = false;
        }

        parent::cleanup($all);
    }

}
