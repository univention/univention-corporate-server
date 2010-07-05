<?php
/**
 * @package Horde_Prefs
 */

/**
 * IMSP driver class.
 */
require_once 'Net/IMSP.php';

/**
 * Preference storage implementation for an IMSP server.
 *
 * $Horde: framework/Prefs/Prefs/imsp.php,v 1.1.10.15 2009-01-06 15:23:31 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @package Horde_Prefs
 */
class Prefs_imsp extends Prefs {

    /**
     * Handle for the IMSP server connection.
     *
     * @var Net_IMSP
     */
    var $_imsp;

    /**
     * User password.
     *
     * @var string
     */
    var $_password;

    /**
     * Boolean indicating whether or not we're connected to the IMSP server.
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * Holds the driver specific parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Constructor function.
     * $params must contain:
     * 'auth_method', 'server', 'port'
     *
     * @param string  $user     Username of current user.
     * @param string  $password Password for current user.
     * @param string  $scope    The scope for these preferences.
     * @param array   $params   The parameters needed for this object.
     * @param boolean $caching  Are we using session cache?
     */
    function Prefs_imsp($user, $password = '', $scope = '',
                        $params = null, $caching = true)
    {
        $this->_scope    = $scope;
        $this->_caching  = $caching;
        $this->_user     = $user;
        $this->_password = $password;
        $this->_params   = $params;

        parent::Prefs();
    }

    /**
     * Retrieves the requested set of preferences from the IMSP server.
     *
     * @param $scope Scope specifier.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _retrieve($scope)
    {
        /* Now connect to the IMSP server. */
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            if (empty($_SESSION['prefs_cache']['unavailable'])) {
                $_SESSION['prefs_cache']['unavailable'] = true;
                $GLOBALS['notification']->push(_("The preferences backend is currently unavailable and your preferences have not been loaded. You may continue to use the system with default settings."));
            }
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        $prefs = $this->_imsp->get($scope . '.*');
        if (is_a($prefs, 'PEAR_Error')) {
            Horde::logMessage($prefs, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        foreach ($prefs as $name => $val) {
            $name = str_replace($scope . '.', '', $name);
            if ($val != '-') {
                if (isset($this->_scopes[$scope][$name])) {
                    $this->_scopes[$scope][$name]['v'] = $val;
                    $this->_scopes[$scope][$name]['m'] &= ~_PREF_DEFAULT;
                } else {
                    // This is a shared preference.
                    $this->_scopes[$scope][$name] = array('v' => $val,
                                                          'm' => 0,
                                                          'd' => null);
                }
            }
        }
    }

    /**
     * Stores all dirty prefs to IMSP server.
     */
    function store()
    {
        // Get the list of preferences that have changed. If there are
        // none, no need to hit the backend.
        $dirty_prefs = $this->_dirtyPrefs();
        if (!$dirty_prefs) {
            return;
        }

        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        foreach ($dirty_prefs as $scope => $prefs) {
            foreach ($prefs as $name => $pref) {
                // Don't store locked preferences.
                if ($this->_scopes[$scope][$name]['m'] & _PREF_LOCKED) {
                    continue;
                }

                $value = $pref['v'];
                if (empty($value)) {
                    $value = '-';
                }

                $result = $this->_imsp->set($scope . '.' . $name, $value);
                if (is_a($result, 'PEAR_Error')) {
                    Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                    return;
                }

                // Clean the pref since it was just saved.
                $this->_scopes[$scope][$name]['m'] &= ~_PREF_DIRTY;
            }

            // Update the cache for this scope.
            $this->_cacheUpdate($scope, array_keys($prefs));
        }
    }

    /**
     * Attempts to set up a connection to the IMSP server.
     *
     * @access private
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _connect()
    {
        if ($this->_connected) {
            return true;
        }

        if (preg_match('/(^.*)@/', $this->_user, $matches)) {
            $this->_params['username'] = $matches[1];
        } else {
            $this->_params['username'] = $this->_user;
        }
        $this->_params['password'] = $this->_password;
        if (isset($this->_params['socket'])) {
            $this->_params['socket'] = $params['socket'] . 'imsp_' . $this->_params['username'] . '.sck';
        }

        $this->_imsp = Net_IMSP::factory('Options', $this->_params);
        $result = $this->_imsp->init();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_imsp->setLogger($GLOBALS['conf']['log']);
        $this->_connected = true;

        return true;
    }

}
