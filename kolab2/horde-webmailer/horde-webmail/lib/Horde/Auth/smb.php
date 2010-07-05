<?php
/**
 * The Auth_smb class provides an SMB implementation of the Horde
 * authentication system.
 *
 * This module requires the smbauth extension for PHP:
 *   http://tekrat.com/wp/smbauth/
 *
 * At the time of this writing, the extension, and thus this module, only
 * supported authentication against a domain, and pdc and bdc must be non-null
 * and not equal to each other. In other words, to use this module you must
 * have a domain with at least one PDC and one BDC.
 *
 * Required parameters:<pre>
 *   'hostspec'  IP, DNS Name, or NetBios Name of the SMB server to
 *               authenticate with.
 *   'domain'    The domain name to authenticate with.</pre>
 *
 * Optional parameters:<pre>
 *   'group'     Group name that the user must be a member of. Will be
 *               ignored if the value passed is a zero length string.</pre>
 *
 *
 * $Horde: framework/Auth/Auth/smb.php,v 1.20.10.13 2009-01-06 15:22:50 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Jon Parise <jon@horde.org>
 * @author  Marcus I. Ryan <marcus@riboflavin.net>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_smb extends Auth {

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
     * Constructs a new SMB authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_smb($params = array())
    {
        /* Ensure we've been provided with all of the necessary parameters. */
        Horde::assertDriverConfig($params, 'auth',
            array('hostspec', 'domain'),
            'authentication Samba');

        $this->_params = $params;
    }

    /**
     * Find out if the given set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  An array of login credentials.
     *
     * @return boolean  True on success or a PEAR_Error object on failure.
     */
    function _authenticate($userId, $credentials)
    {
        if (empty($credentials['password'])) {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }

        if (!Util::extensionExists('smbauth')) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, _("Auth_smbauth: Required smbauth extension not found."));
            return false;
        }

        /* Authenticate. */
        $rval = validate($this->_params['hostspec'],
                         $this->_params['domain'],
                         empty($this->_params['group']) ? '' : $this->_params['group'],
                         $userId,
                         $credentials['password']);

        if ($rval === 0) {
            return true;
        } else {
            if ($rval === 1) {
                $this->_setAuthError(AUTH_REASON_MESSAGE, _("Failed to connect to SMB server."));
            } else {
                $this->_setAuthError(AUTH_REASON_MESSAGE, err2str());
            }
            return false;
        }
    }

}
