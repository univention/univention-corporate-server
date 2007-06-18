<?php
/**
 * The Auth_imsp class provides basic authentication against an IMSP server.
 * This will be most benificial if already using an IMSP based prefernece system or
 * IMSP based addressbook system
 *
 * $Horde: framework/Auth/Auth/imsp.php,v 1.2 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 2004 Michael Rubinsky <mike@theupstairsroom.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Rubinsky <mike@theupstairsroom.com>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Auth
 */
class Auth_imsp extends Auth{

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
     * Constructor function. Creates new Auth_imsp object.
     *
     * @access public
     * @param optional array $params A hash containing parameters.
     */
    function Auth_imsp($params = array())
    {
        $this->_setParams($params);
    }

    /**
     * Private authentication function.
     *
     * @access private
     * @param string $userID Username for IMSP server.
     * @param array $credentials Hash containing 'password' element.
     * @return boolean True on success / False on failure.
     */
    function _authenticate($userID, $credentials)
    {
        require_once 'Net/IMSP/Auth.php';

        $params = array();
        $params['username'] = $userID;
        $params['password'] = $credentials['password'];
        $params['server'] = $this->_params['server'];
        $params['port'] = $this->_params['port'];
        $imsp = &Net_IMSP_Auth::singleton($this->_params['auth_method']);
        if (is_a($imsp, 'PEAR_Error')){
            return $imsp;
        }

        $result = $imsp->authenticate($params, false);
        if (is_a($result, 'PEAR_Error')){
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
        if (empty($params['auth_method'])){
            $params['auth_method'] = 'plaintext';
        }

        $this->_params = $params;
    }

}
