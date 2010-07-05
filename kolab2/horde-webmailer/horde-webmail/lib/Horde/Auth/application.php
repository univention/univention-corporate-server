<?php
/**
 * The Auth_application class provides a wrapper around
 * application-provided Horde authentication which fits inside the
 * Horde Auth:: API.
 *
 * Required parameters:<pre>
 *   'app'  The application which is providing authentication.</pre>
 *
 *
 * $Horde: framework/Auth/Auth/application.php,v 1.27.10.18 2009-02-13 05:45:36 chuck Exp $
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
class Auth_application extends Auth {

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array
     */
    var $capabilities = array('add'           => false,
                              'update'        => false,
                              'resetpassword' => false,
                              'remove'        => false,
                              'exists'        => false,
                              'list'          => false,
                              'transparent'   => false);

    /**
     * Constructs a new Application authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_application($params = array())
    {
        $this->_setParams($params);
    }

    /**
     * Queries the current Auth object to find out if it supports the given
     * capability.
     *
     * @param string $capability  The capability to test for.
     *
     * @return boolean  Whether or not the capability is supported.
     */
    function hasCapability($capability)
    {
        static $loaded = array();

        $methods = array('list' => 'userList',
                         'exists' => 'userExists',
                         'add' => 'addUser',
                         'update' => 'updateUser',
                         'remove' => 'removeUser');

        if (empty($loaded[$capability]) && isset($methods[$capability])) {
            $this->capabilities[$capability] = $GLOBALS['registry']->hasMethod($methods[$capability], $this->_params['app']);
            $loaded[$capability] = true;
        }

        return !empty($this->capabilities[$capability]);
    }

    /**
     * Set connection parameters.
     *
     * @access private
     *
     * @param array $params  A hash containing connection parameters.
     */
    function _setParams($params)
    {
        Horde::assertDriverConfig($params, 'auth',
                                  array('app'),
                                  'authentication application');

        $this->_params = $params;
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
        if (!$GLOBALS['registry']->hasMethod('authenticate', $this->_params['app'])) {
            $this->_setAuthError(AUTH_REASON_MESSAGE,
                                 $this->_params['app'] . ' does not provide an authenticate() method.');
            return false;
        }

        $ret = $GLOBALS['registry']->callByPackage($this->_params['app'], 'authenticate',
                                                   array('userId' => $userId,
                                                         'credentials' => $credentials,
                                                         'params' => $this->_params));

        // Horrific hack.  Avert your eyes.  Since an application may already
        // set the authentication information necessary, we don't want to
        // overwrite that info.  Coming into this function, we know that
        // the authentication has not yet been set in this session.  So after
        // calling the app-specific auth handler, if authentication
        // information has suddenly appeared, it follows that the information
        // has been stored already in the session and we shouldn't overwrite.
        // So grab the authentication ID set and stick it in $_authCredentials
        // this will eventually cause setAuth() in authenticate() to exit
        // before re-setting the auth info values.
        if ($ret && ($authid = Auth::getAuth())) {
            $this->_authCredentials['userId'] = $authid;
        }

        return $ret;
    }

    /**
     * Return the URI of the login screen for this authentication method.
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
        return parent::_getLoginScreen($this->_params['app'], $url);
    }

    /**
     * List all users in the system.
     *
     * @return mixed  The array of userIds, or a PEAR_Error object on failure.
     */
    function listUsers()
    {
        if ($this->hasCapability('list')) {
            return $GLOBALS['registry']->callByPackage($this->_params['app'], 'userList');
        } else {
            return PEAR::raiseError('unsupported');
        }
    }

    /**
     * Checks if $userId exists in the system.
     *
     * @param string $userId User ID for which to check
     *
     * @return boolean  Whether or not $userId already exists.
     */
    function exists($userId)
    {
        if ($this->hasCapability('exists')) {
            return $GLOBALS['registry']->callByPackage($this->_params['app'], 'userExists', array($userId));
        } else {
            return parent::exists($userId);
        }
    }

    /**
     * Add a set of authentication credentials.
     *
     * @param string $userId      The userId to add.
     * @param array $credentials  The credentials to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        if ($this->hasCapability('add')) {
            return $GLOBALS['registry']->callByPackage($this->_params['app'], 'addUser', array($userId, $credentials));
        } else {
            return PEAR::raiseError('unsupported');
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
        if ($this->hasCapability('update')) {
            return $GLOBALS['registry']->callByPackage($this->_params['app'], 'updateUser', array($oldID, $newID, $credentials));
        } else {
            return PEAR::raiseError('unsupported');
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
        if ($this->hasCapability('remove')) {
            $result = $GLOBALS['registry']->callByPackage($this->_params['app'], 'removeUser', array($userId));
        } else {
            return PEAR::raiseError('unsupported');
        }
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $this->removeUserData($userId);
    }

}
