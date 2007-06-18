<?php
/**
 * The Auth_sasl:: class provides a SASL-based implementation of the
 * Horde authentication system.
 *
 * SASL is the Simple Authentication and Security Layer (as defined by
 * RFC 2222). It provides a system for adding plugable authenticating
 * support to connection-based protocols.
 *
 * This driver relies on the PECL sasl package:
 *
 *      http://pecl.php.net/package/sasl
 *
 * Optional parameters:
 * ====================
 *   'app'      --  The name of the authenticating application.
 *                  DEFAULT: horde
 *
 *   'service'  --  The name of the SASL service to use when authenticating.
 *                  DEFAULT: php
 *
 *
 * $Horde: framework/Auth/Auth/sasl.php,v 1.4 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Parise <jon@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_sasl extends Auth
{
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
     * Constructs a new SASL authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_sasl($params = array())
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
            Horde::fatal(PEAR::raiseError(_("No password provided for Login authentication.")), __FILE__, __LINE__);
        }

        if (!extension_loaded('sasl')) {
            Horde::fatal(PEAR::raiseError(_("SASL authentication is not available.")), __FILE__, __LINE__);
        }

        $service = (!empty($params['service'])) ? $params['service'] : 'php';
        $conn = sasl_server_new($service);
        if (!is_resource($conn)) {
            Horde::fatal(PEAR::raiseError(_("Failed to create new SASL connection.")), __FILE__, __LINE__);
        }

        if (!sasl_checkpass($conn, $userId, $credentials['password'])) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, sasl_errdetail($conn));
            return false;
        }

        return true;
    }

}
