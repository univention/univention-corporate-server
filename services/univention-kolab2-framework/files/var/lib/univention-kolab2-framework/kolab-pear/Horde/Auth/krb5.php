<?php
/**
 * The Auth_krb5 class provides an kerberos implementation of the Horde
 * authentication system.
 *
 * This driver requires the 'krb5' PHP extension to be loaded.
 * The module can be downloaded here:
 *   http://www.horde.org/download/php/phpkrb5.tar.gz
 *
 * Required parameters:
 * ====================
 *   NONE. Instead, Kerberos must be correctly configured on your system (e.g.
 *   /etc/krb5.conf) for this class to work correctly.
 *
 *
 * $Horde: framework/Auth/Auth/krb5.php,v 1.21 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package Horde_Auth
 */
class Auth_krb5 extends Auth {

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
     * Constructs a new Kerberos authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_krb5($params = array())
    {
        if (!Util::extensionExists('krb5')) {
            Horde::fatal(PEAR::raiseError(_("Auth_krb5: Required krb5 extension not found."), __FILE__, __LINE__));
        }

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
            Horde::fatal(PEAR::raiseError(_("No password provided for Kerberos authentication.")), __FILE__, __LINE__);
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
