<?php
/**
 * $Horde: framework/Prefs/Prefs/kolab_imap.php,v 1.3.2.4 2009-01-06 15:23:31 jan Exp $
 *
 * @package Horde_Prefs
 */

/** This requires the Kolab module */
require_once 'Horde/Kolab.php';

/** The share system is used to handle the config container */
require_once 'Horde/Share.php';

/**
 * Preferences storage implementation for a Kolab IMAP server
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @since   Horde 3.2
 * @package Horde_Prefs
 */

class Prefs_kolab_imap extends Prefs {

    /**
     * ID of the config default share
     *
     * @var string
     */
    var $_share;

    /**
     * Handle for the current Kolab connection.
     *
     * @var Kolab
     */
    var $_connection;

    /**
     * Constructs a new kolab_imap preferences object.
     *
     * @param string $user      The user who owns these preferences.
     * @param string $password  The password associated with $user. (Unused)
     * @param string $scope     The current preferences scope.
     * @param array $params     A hash containing connection parameters.
     *                           (Unused)
     * @param boolean $caching  Should caching be used?
     *
     */
    function Prefs_kolab_imap($user, $password = '', $scope = '',
                           $params = null, $caching = true)
    {
        $this->_user = $user;
        $this->_scope = $scope;
        $this->_caching = $caching;

        parent::Prefs();
    }

    /**
     * Opens a connection to the Kolab server.
     *
     * @access private
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _connect()
    {
        if (!isset($this->_connection)) {
            $shares = &Horde_Share::singleton('h-prefs');
            $default = $shares->getDefaultShare();
            if (is_a($default, 'PEAR_Error')) {
                Horde::logMessage($default, __FILE__, __LINE__, PEAR_LOG_ERR);
                $this->_connection = $default;
                return $this->_connection;
            }
            $this->_share = $default->getName();

            $connection = &new Kolab('h-prefs');
            if (is_a($connection, 'PEAR_Error')) {
                Horde::logMessage($connection, __FILE__, __LINE__, PEAR_LOG_ERR);
                $this->_connection = $connection;
                return $this->_connection;
            }
            $this->_connection = $connection;
        } elseif (is_a($this->_connection, 'PEAR_Error')) {
            return $this->_connection;
        }
        return $this->_connection->open($this->_share, 1);
    }

    /**
     * Retrieves the requested set of preferences from the user's config folder.
     *
     * @param $scope Scope specifier.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _retrieve($scope)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            if (empty($_SESSION['prefs_cache']['unavailable'])) {
                $_SESSION['prefs_cache']['unavailable'] = true;
                $GLOBALS['notification']->push(_("The preferences backend is currently unavailable and your preferences have not been loaded. You may continue to use the system with default settings."));
            }
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        $pref = $this->_getPref($scope);
        if (is_a($pref, 'PEAR_Error')) {
            Horde::logMessage($pref, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        if (is_null($pref)) {
            /* No preferences saved yet */
            return;
        }

        foreach ($pref['pref'] as $prefstr) {
            // If the string doesn't contain a colon delimiter, skip it.
            if (strpos($prefstr, ':') === false) {
                continue;
            }
            
            // Split the string into its name:value components.
            list($name, $val) = explode(':', $prefstr, 2);
            if (isset($this->_scopes[$scope][$name])) {
                $this->_scopes[$scope][$name]['v'] = base64_decode($val);
                $this->_scopes[$scope][$name]['m'] &= ~_PREF_DEFAULT;
            } else {
                // This is a shared preference.
                $this->_scopes[$scope][$name] = array('v' => base64_decode($val),
                                                      'm' => 0,
                                                      'd' => null);
            }
        }
        
    }
    
    /**
     * Retrieves the requested preference from the user's config folder.
     *
     * @param $scope Scope specifier.
     *
     * @return array  The preference value or a PEAR_Error object on failure.
     */
    function &_getPref($scope)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        $prefs = $this->_connection->getObjects();
        if (is_a($prefs, 'PEAR_Error')) {
            return $prefs;
        }

        foreach ($prefs as $pref) {
            if ($pref['application'] == $scope) {
                return $pref;
            }
        }
        $pref = null;
        return $pref;
    }
    
    /**
     * Stores preferences to the Kolab server.
     */
    function store()
    {
        // Get the list of preferences that have changed. If there are
        // none, no need to hit the backend.
        $dirty_prefs = $this->_dirtyPrefs();
        if (!$dirty_prefs) {
            return;
        }
        $dirty_scopes = array_keys($dirty_prefs);

        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        // Build a hash of the preferences and their values that need
        // to be stored on the IMAP server. Because we have to update
        // all of the values of a multi-value entry wholesale, we
        // can't just pick out the dirty preferences; we must update
        // every scope that has dirty preferences.
        foreach ($dirty_scopes as $scope) {
            $new_values = array();
            foreach ($this->_scopes[$scope] as $name => $pref) {
                // Don't store locked preferences.
                if (!($pref['m'] & _PREF_LOCKED)) {
                    $new_values[] =
                        $name . ':' . base64_encode($pref['v']);
                }
            }
            $pref = $this->_getPref($scope);
            if (is_a($pref, 'PEAR_Error')) {
                Horde::logMessage($pref, __FILE__, __LINE__, PEAR_LOG_ERR);
                return;
            }

            if (is_null($pref)) {
                $old_uid = null;
                $prefs_uid = $this->_connection->_storage->generateUID();
            } else {
                $old_uid = $pref['uid'];
                $prefs_uid = $pref['uid'];
            }

            $object = array('uid' => $prefs_uid,
                            'application' => $scope,
                            'pref' => $new_values);

            $result = $this->_connection->_storage->save($object, $old_uid);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return;
            }
        }

        // Clean the preferences since they were just saved.
        foreach ($dirty_prefs as $scope => $prefs) {
            foreach ($prefs as $name => $pref) {
                $this->_scopes[$scope][$name]['m'] &= ~_PREF_DIRTY;
            }

            // Update the cache for this scope.
            $this->_cacheUpdate($scope, array_keys($prefs));
        }
    }

    /**
     * Clears all preferences from the kolab_imap backend.
     */
    function clear()
    {
        return $this->_connection->deleteAll();
    }
}

?>