<?php
/**
 * The Auth_auto class transparently logs users in to Horde using ONE
 * username, either defined in the config or defaulting to
 * 'horde_user'. This is only for use in testing or behind a firewall;
 * it should NOT be used on a public, production machine.
 *
 * Optional parameters:
 * ====================
 *   'username'     --  The username to authenticate everyone as.
 *                      DEFAULT: 'horde_user'
 *   'requestuser'  --  If true, allow username to be passed by GET, POST
 *                      or cookie.
 *
 *
 * $Horde: framework/Auth/Auth/auto.php,v 1.11 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package Horde_Auth
 */
class Auth_auto extends Auth {

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
                              'transparent'   => true);

    /**
     * Constructs a new Automatic authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing parameters.
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
     * @param array $params  Parameters. None currently required,
     *                       'username' is optional.
     */
    function _setParams($params)
    {
        if (!isset($params['username'])) {
            $params['username'] = 'horde_user';
        }
        $this->_params = $params;
    }

    /**
     * Automatic authentication: Set the user
     * allowed IP block.
     *
     * @access public
     *
     * @return boolean  Whether or not the client is allowed.
     */
    function transparent()
    {
        $username = (!empty($this->_params['requestuser']) && isset($_REQUEST['username'])) ? 
                     $_REQUEST['username'] : 
                     $this->_params['username'];
        $this->setAuth($username,
                       array('transparent' => 1));
        return true;
    }

}
