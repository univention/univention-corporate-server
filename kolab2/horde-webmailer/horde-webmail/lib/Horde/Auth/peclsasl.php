<?php
/**
 * The Auth_peclsasl:: class provides a SASL-based implementation of the Horde
 * authentication system.
 *
 * SASL is the Simple Authentication and Security Layer (as defined by RFC
 * 2222). It provides a system for adding plugable authenticating support to
 * connection-based protocols.
 *
 * This driver relies on the PECL sasl package:
 *
 *      http://pecl.php.net/package/sasl
 *
 * Optional parameters:<pre>
 *   'app'      The name of the authenticating application.
 *              DEFAULT: horde
 *   'service'  The name of the SASL service to use when authenticating.
 *              DEFAULT: php</pre>
 *
 *
 * $Horde: framework/Auth/Auth/peclsasl.php,v 1.1.2.5 2009-01-06 15:22:50 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Jan Parise <jon@horde.org>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_peclsasl extends Auth {

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
     * Constructs a new SASL authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_peclsasl($params = array())
    {
        $this->_params = $params;

        if (!extension_loaded('sasl')) {
            dl('sasl.so');
        }

        $app = (!empty($params['app'])) ? $params['app'] : 'horde';
        sasl_server_init($app);
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  An array of login credentials.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        if (empty($credentials['password'])) {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }

        if (!extension_loaded('sasl')) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, _("SASL authentication is not available."));
            return false;
        }

        $service = (!empty($params['service'])) ? $params['service'] : 'php';
        $conn = sasl_server_new($service);
        if (!is_resource($conn)) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, _("Failed to create new SASL connection."));
            return false;
        }

        if (!sasl_checkpass($conn, $userId, $credentials['password'])) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, sasl_errdetail($conn));
            return false;
        }

        return true;
    }

}
