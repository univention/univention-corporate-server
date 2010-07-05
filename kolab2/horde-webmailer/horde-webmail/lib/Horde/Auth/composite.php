<?php
/**
 * The Auth_composite class provides a wrapper around
 * application-provided Horde authentication which fits inside the
 * Horde Auth:: API.
 *
 * Required parameters:<pre>
 *   None.</pre>
 *
 *
 * $Horde: framework/Auth/Auth/composite.php,v 1.26.10.15 2009-07-27 12:19:56 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_composite extends Auth {

    /**
     * Hash containing any instantiated drivers.
     *
     * @var array
     */
    var $_drivers = array();

    /**
     * Constructs a new Composite authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_composite($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Return the named parameter for the current auth driver.
     *
     * @param string $param  The parameter to fetch.
     *
     * @return string  The parameter's value.
     */
    function getParam($param)
    {
        if (($login_driver = Auth::_getDriverByParam('loginscreen_switch', $this->_params)) &&
            $this->_loadDriver($login_driver)) {
            return $this->_drivers[$login_driver]->getParam($param);
        }

        return null;
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  The credentials to use.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        if (($auth_driver = Auth::_getDriverByParam('loginscreen_switch', $this->_params)) &&
            $this->_loadDriver($auth_driver)) {
            return $this->_drivers[$auth_driver]->authenticate($userId, $credentials);
        }

        if (($auth_driver = Auth::_getDriverByParam('username_switch', $this->_params, array($userId))) &&
            $this->_loadDriver($auth_driver)) {
            return $this->_drivers[$auth_driver]->hasCapability('transparent');
        }

        $this->_setAuthError(AUTH_REASON_FAILED);
        return false;
    }

    /**
     * Query the current Auth object to find out if it supports the given
     * capability.
     *
     * @param string $capability  The capability to test for.
     *
     * @return boolean  Whether or not the capability is supported.
     */
    function hasCapability($capability)
    {
        switch ($capability) {
        case 'add':
        case 'update':
        case 'remove':
        case 'list':
        case 'resetpassword':
            if (!empty($this->_params['admin_driver']) &&
                $this->_loadDriver($this->_params['admin_driver'])) {
                return $this->_drivers[$this->_params['admin_driver']]->hasCapability($capability);
            } else {
                return false;
            }
            break;

        case 'transparent':
            if (($login_driver = Auth::_getDriverByParam('loginscreen_switch', $this->_params)) &&
                $this->_loadDriver($login_driver)) {
                return $this->_drivers[$login_driver]->hasCapability('transparent');
            }
            return false;
            break;

        default:
            return false;
        }
    }

    /**
     * Automatic authentication: Find out if the client matches an allowed IP
     * block.
     *
     * @return boolean  Whether or not the client is allowed.
     */
    function transparent()
    {
        if (($login_driver = Auth::_getDriverByParam('loginscreen_switch', $this->_params)) &&
            $this->_loadDriver($login_driver)) {
            return $this->_drivers[$login_driver]->transparent();
        }

        return false;
    }

    /**
     * Return the URI of the login screen for this authentication object.
     *
     * @access private
     *
     * @param string $app  The application to use.
     * @param string $url  The URL to redirect to after login.
     *
     * @return string  The login screen URI.
     */
    function _getLoginScreen($app = 'horde', $url = '')
    {
        if (($login_driver = Auth::_getDriverByParam('loginscreen_switch', $this->_params)) &&
            $this->_loadDriver($login_driver)) {
            return $this->_drivers[$login_driver]->_getLoginScreen($app, $url);
        } else {
            return parent::_getLoginScreen($app, $url);
        }
    }

    /**
     * Add a set of authentication credentials.
     *
     * @param string $userId       The userId to add.
     * @param array  $credentials  The credentials to use.
     *
     * @return mixed        True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        if (!empty($this->_params['admin_driver']) &&
            $this->_loadDriver($this->_params['admin_driver'])) {
            return $this->_drivers[$this->_params['admin_driver']]->addUser($userId, $credentials);
        } else {
            return PEAR::raiseError('Unsupported');
        }
    }

    /**
     * Update a set of authentication credentials.
     *
     * @param string $oldID       The old userId.
     * @param string $newID       The new userId.
     * @param array $credentials  The new credentials
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function updateUser($oldID, $newID, $credentials)
    {
        if (!empty($this->_params['admin_driver']) &&
            $this->_loadDriver($this->_params['admin_driver'])) {
            return $this->_drivers[$this->_params['admin_driver']]->updateUser($oldID, $newID, $credentials);
        } else {
            return PEAR::raiseError('Unsupported');
        }
    }

    /**
     * Reset a user's password. Used for example when the user does not
     * remember the existing password.
     *
     * @param string $userId  The user id for which to reset the password.
     *
     * @return mixed  The new password on success or a PEAR_Error object on
     *                failure.
     */
    function resetPassword($userId)
    {
        if (!empty($this->_params['admin_driver']) &&
            $this->_loadDriver($this->_params['admin_driver'])) {
            return $this->_drivers[$this->_params['admin_driver']]->resetPassword($userId);
        } else {
            return PEAR::raiseError('Unsupported');
        }
    }

    /**
     * Delete a set of authentication credentials.
     *
     * @param string $userId  The userId to delete.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function removeUser($userId)
    {
        if (!empty($this->_params['admin_driver']) &&
            $this->_loadDriver($this->_params['admin_driver'])) {
            return $this->_drivers[$this->_params['admin_driver']]->removeUser($userId);
        } else {
            return PEAR::raiseError('Unsupported');
        }
    }

    /**
     * List all users in the system.
     *
     * @return mixed  The array of userIds, or a PEAR_Error object on failure.
     */
    function listUsers()
    {
        if (!empty($this->_params['admin_driver']) &&
            $this->_loadDriver($this->_params['admin_driver'])) {
            return $this->_drivers[$this->_params['admin_driver']]->listUsers();
        } else {
            return PEAR::raiseError('Unsupported');
        }
    }

    /**
     * Checks if a userId exists in the system.
     *
     * @param string $userId  User ID to check
     *
     * @return boolean  Whether or not the userId already exists.
     */
    function exists($userId)
    {
        if (!empty($this->_params['admin_driver']) &&
            $this->_loadDriver($this->_params['admin_driver'])) {
            return $this->_drivers[$this->_params['admin_driver']]->exists($userId);
        } else {
            return PEAR::raiseError('Unsupported');
        }
    }

    /**
     * Loads one of the drivers in our configuration array, if it isn't already
     * loaded.
     *
     * @access private
     *
     * @param string $driver  The name of the driver to load.
     *
     * @return boolean True if driver successfully initializes.
     */
    function _loadDriver($driver)
    {
        if (empty($this->_drivers[$driver])) {
            // This is a bit specialized for Horde::getDriverConfig(),
            // so localize it here:
            global $conf;
            if (!empty($this->_params['drivers'][$driver]['params'])) {
                $params = $this->_params['drivers'][$driver]['params'];
                if (isset($conf[$this->_params['drivers'][$driver]['driver']])) {
                    $params = array_merge($conf[$this->_params['drivers'][$driver]['driver']], $params);
                }
            } elseif (!empty($conf[$driver])) {
                $params = $conf[$driver];
            } else {
                $params = null;
            }

            $this->_drivers[$driver] = &Auth::singleton($this->_params['drivers'][$driver]['driver'], $params);
        }

        return isset($this->_drivers[$driver]);
    }

}
