<?php
/**
 * The Auth_pam:: class provides a PAM-based implementation of the Horde
 * authentication system.
 *
 * PAM (Pluggable Authentication Modules) is a flexible mechanism for
 * authenticating users. It has become the standard authentication system for
 * Linux, Solaris and FreeBSD.
 *
 * This driver relies on the PECL PAM package:
 *
 *      http://pecl.php.net/package/PAM
 *
 * Optional parameters:<pre>
 *   'service'  The name of the PAM service to use when authenticating.
 *              DEFAULT: php</pre>
 *
 *
 * $Horde: framework/Auth/Auth/pam.php,v 1.3.10.16 2009-01-06 15:22:50 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @deprecated This driver will be removed for Horde 4.0 unless there is a
 *             maintained PAM extension at that time.
 * @author     Jan Parise <jon@horde.org>
 * @since      Horde 3.0
 * @package    Horde_Auth
 */
class Auth_pam extends Auth {

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
     * Constructs a new PAM authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_pam($params = array())
    {
        $this->_params = $params;

        if (!empty($params['service'])) {
            ini_set('pam.servicename', $params['service']);
        }

        Util::loadExtension('pam') || Util::loadExtension('pam_auth');
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

        if (!function_exists('pam_auth')) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, _("PAM authentication is not available."));
            return false;
        }

        $error = null;
        if (!pam_auth($userId, $credentials['password'], &$error)) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, $error);
            return false;
        }

        return true;
    }

}
