<?php
/**
 * The Auth_shibboleth class only provides transparent authentication based
 * on the headers set by a Shibboleth SP.  Note that this class does
 * not provide any actual SP functionality, it just takes the username
 * from the HTTP headers that should be set by the Shibboleth SP.
 *
 * Parameters:
 *   'username_header'     Name of the header holding the username of the logged in user
 *   'password_holder'     Where the hordeauth password is stored
 *   'password_header'     Name of the header holding the password of the logged in user
 *   'password_preference' Name of the Horde preference holding the password of the logged in user
 *
 * $Horde: framework/Auth/Auth/shibboleth.php,v 1.4.2.3 2009-10-26 11:58:59 jan Exp $
 *
 * Copyright 9Star Research, Inc. 2006 http://www.protectnetwork.org
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Cassio Nishiguchi <cassio@protectnetwork.org>
 * @since   Horde 3.2
 * @package Horde_Auth
 */
class Auth_shibboleth extends Auth {

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
     * Constructs a new Shibboleth SP authentication object.
     *
     * @param array $params  A hash containing parameters.
     */
    function Auth_shibboleth($params = array())
    {
        Horde::assertDriverConfig($params, 'auth', array('username_header'), 'authentication Shibboleth');

        if (!isset($params['password_holder'])) {
            $params['password_holder'] = false;
        }

        $this->_params = $params;
    }

    /**
     * Automatic authentication: Check if the username is set in the
     * configured header.
     *
     * @return boolean  Whether or not the client is allowed.
     */
    function transparent()
    {
        if (empty($_SERVER[$this->_params['username_header']])) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, _("Shibboleth authentication not available."));
            return false;
        }

        $username = $_SERVER[$this->_params['username_header']];
        // Remove scope from username, if present.
        $pos = strrpos($username, '@');
        if ($pos !== false) {
            $username = substr($username, 0, $pos);
        }

        if (!$this->setAuth($username, array('transparent' => 1))) {
            return false;
        }

        // Set password for hordeauth login.
        if ($this->_params['password_holder'] == 'header') {
            $this->setCredential('password', $_SERVER[$this->_params['password_header']]);
        } elseif ($this->_params['password_holder'] == 'preferences') {
            $this->setCredential('password', $GLOBALS['prefs']->getValue($this->_params['password_preference']));
        }
        return true;
    }

}
