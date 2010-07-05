<?php
/**
 * The Auth_imsp class provides basic authentication against an IMSP server.
 * This will be most benificial if already using an IMSP based preference
 * system or IMSP based addressbook system
 *
 * $Horde: framework/Auth/Auth/imsp.php,v 1.2.10.14 2009-01-06 15:22:49 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @package Horde_Auth
 */
class Auth_imsp extends Auth{

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
                              'list'          => false,
                              'transparent'   => false);
    /**
     * Constructor function. Creates new Auth_imsp object.
     *
     * @param array $params A hash containing parameters.
     */
    function Auth_imsp($params = array())
    {
        $this->_setParams($params);
    }

    /**
     * Private authentication function.
     *
     * @access private
     *
     * @param string $userID Username for IMSP server.
     * @param array $credentials Hash containing 'password' element.
     *
     * @return boolean True on success / False on failure.
     */
    function _authenticate($userID, $credentials)
    {
        require_once 'Net/IMSP/Auth.php';

        $this->_params['username'] = $userID;
        $this->_params['password'] = $credentials['password'];
        $imsp = &Net_IMSP_Auth::singleton($this->_params['auth_method']);

        if (is_a($imsp, 'PEAR_Error')) {
            return $imsp;
        }

        $result = $imsp->authenticate($this->_params, false);
        if (is_a($result, 'PEAR_Error')) {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        } else {
            return true;
        }
    }

    /**
     * Checks the params array and sets default values.
     *
     * @access private
     * @param array $params Hash containing IMSP parameters.
     */
    function _setParams($params)
    {
        $this->_params['server'] = $params['server'];
        $this->_params['port'] = $params['port'];
        $this->_params['auth_method'] = $params['auth_method'];

        if (isset($params['auth_mechanism'])) {
            $this->_params['auth_mechanism'] = $params['auth_mechanism'];
            $this->_params['socket'] = $params['socket'];
            $this->_params['command'] = $params['command'];
        }
    }

}
