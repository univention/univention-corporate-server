<?php
/**
 * The Auth_krb5 class provides an kerberos implementation of the Horde
 * authentication system.
 *
 * This driver requires the 'krb5' PHP extension to be loaded.
 * The module can be downloaded here:
 *   http://www.horde.org/download/php/phpkrb5.tar.gz
 *
 * Required parameters:<pre>
 *   None.</pre>
 *
 * Instead, Kerberos must be correctly configured on your system (e.g.
 *   /etc/krb5.conf) for this class to work correctly.
 *
 *
 * $Horde: framework/Auth/Auth/krb5.php,v 1.21.10.12 2009-01-06 15:22:49 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 2.2
 * @package Horde_Auth
 */
class Auth_krb5 extends Auth {

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
     * Constructs a new Kerberos authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_krb5($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  An array of login credentials.
     *                            For kerberos, this must contain a password
     *                            entry.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        if (empty($credentials['password'])) {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }

        if (!Util::extensionExists('krb5')) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, _("Auth_krb5: Required krb5 extension not found."));
            return false;
        }

        $result = krb5_login($userId, $credentials['password']);
        if ($result === KRB5_OK) {
            return true;
        } else {
            if ($result === KRB5_BAD_PASSWORD) {
                $this->_setAuthError(AUTH_REASON_MESSAGE, _("Bad kerberos password."));
            } elseif ($result === KRB5_BAD_USER) {
                $this->_setAuthError(AUTH_REASON_MESSAGE, _("Bad kerberos username."));
            } else {
                $this->_setAuthError(AUTH_REASON_MESSAGE, _("Kerberos server rejected authentication."));
            }
            return false;
        }
    }

}
