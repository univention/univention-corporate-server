<?php
/**
 * The Auth_auto class transparently logs users in to Horde using ONE
 * username, either defined in the config or defaulting to
 * 'horde_user'. This is only for use in testing or behind a firewall;
 * it should NOT be used on a public, production machine.
 *
 * Optional parameters:<pre>
 *   'username'     The username to authenticate everyone as.
 *                  DEFAULT: 'horde_user'
 *   'password'     The password to record in the user's credentials.
 *                  DEFAULT: none
 *   'requestuser'  If true, allow username to be passed by GET, POST or
 *                  cookie.</pre>
 *
 *
 * $Horde: framework/Auth/Auth/auto.php,v 1.12.4.13 2009-01-06 15:22:49 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 2.2
 * @package Horde_Auth
 */
class Auth_auto extends Auth {

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
                              'transparent'   => true);

    /**
     * Constructs a new Automatic authentication object.
     *
     * @param array $params  A hash containing parameters.
     */
    function Auth_auto($params = array())
    {
        $this->_setParams($params);
    }

    /**
     * Set parameters for the Auth_auto object.
     *
     * @access private
     *
     * @param array $params  Parameters. None currently required;
     *                       'username', 'password', and 'requestuser' are optional.
     */
    function _setParams($params)
    {
        if (!isset($params['username'])) {
            $params['username'] = 'horde_user';
        }
        $this->_params = $params;
    }

    /**
     * Automatic authentication: Set the user allowed IP block.
     *
     * @return boolean  Whether or not the client is allowed.
     */
    function transparent()
    {
        $username = (!empty($this->_params['requestuser']) && isset($_REQUEST['username'])) ?
            $_REQUEST['username'] :
            $this->_params['username'];
        return $this->setAuth($username,
            array('transparent' => 1,
                  'password' => isset($this->_params['password']) ? $this->_params['password'] : null));
    }

}
