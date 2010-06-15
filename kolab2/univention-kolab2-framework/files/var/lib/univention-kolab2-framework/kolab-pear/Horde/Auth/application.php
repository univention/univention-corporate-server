<?php
/**
 * The Auth_application class provides a wrapper around
 * application-provided Horde authentication which fits inside the
 * Horde Auth:: API.
 *
 * Required parameters:
 * ====================
 *   'app'  --  The application which is providing authentication.
 *
 *
 * $Horde: framework/Auth/Auth/application.php,v 1.24 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_application extends Auth {

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array $capabilities
     */
    var $capabilities = array('add'           => false,
                              'update'        => false,
                              'resetpassword' => false,
                              'remove'        => false,
                              'list'          => false,
                              'transparent'   => false);

    /**
     * Constructs a new Application authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_application($params = array())
    {
        $this->_setParams($params);
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
        global $registry;

        Horde::assertDriverConfig($params, 'auth',
                                  array('app'),
                                  'authentication application');

        if (empty($registry->applications[$params['app']])) {
            Horde::fatal(PEAR::raiseError($params['app'] . ' is not configured in the Horde Registry.'), __FILE__, __LINE__);
        }
        $this->capabilities['list']   = $registry->hasMethod('userlist', $params['app']);
        $this->capabilities['add']    = $registry->hasMethod('adduser', $params['app']);
        $this->capabilities['update'] = $registry->hasMethod('updateuser', $params['app']);
        $this->capabilities['remove'] = $registry->hasMethod('removeuser', $params['app']);

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
        global $registry;

        if (!$registry->hasMethod('authenticate', $this->_params['app'])) {
            Horde::fatal(PEAR::raiseError($this->_params['app'] . ' does not provide an authenticate() method.'), __FILE__, __LINE__);
        }
        return $registry->callByPackage($this->_params['app'], 'authenticate',
                                        array('userId' => $userId,
                                              'credentials' => $credentials,
                                              'params' => $this->_params));
    }

    /**
     * Return the URI of the login screen for this authentication
     * method.
     *
     * @access public
     *
     * @param optional string $app  The application to use.
     * @param optional string $url  The URL to redirect to after login.
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
     * @access public
     *
     * @return mixed  The array of userIds, or a PEAR_Error object on failure.
     */
    function listUsers()
    {
        if ($this->hasCapability('list')) {
            return $GLOBALS['registry']->callByPackage($this->_params['app'], 'userlist');
        } else {
            return PEAR::raiseError('unsupported');
        }
    }

    /**
     * Add a set of authentication credentials.
     *
     * @access public
     *
     * @param string $userId      The userId to add.
     * @param array $credentials  The credentials to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        if ($this->hasCapability('add')) {
            return $GLOBALS['registry']->callByPackage($this->_params['app'], 'adduser', array($userId, $credentials));
        } else {
            return PEAR::raiseError('unsupported');
        }
    }

    /**
     * Update a set of authentication credentials.
     *
     * @access public
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
            return $GLOBALS['registry']->callByPackage($this->_params['app'], 'updateuser', array($oldID, $newID, $credentials));
        } else {
            return PEAR::raiseError('unsupported');
        }
    }

    /**
     * Delete a set of authentication credentials.
     *
     * @access public
     *
     * @param string $userId  The userId to delete.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function removeUser($userId)
    {
        if ($this->hasCapability('remove')) {
            return $GLOBALS['registry']->callByPackage($this->_params['app'], 'removeuser', array($userId));
        } else {
            return PEAR::raiseError('unsupported');
        }
    }

}
