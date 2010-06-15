<?php
/**
 * The Auth_smb class provides an SMB implementation of the Horde
 * authentication system.
 *
 * This module requires the smbauth extension for PHP:
 *   http://www.tekrat.com/smbauth.php
 *
 * At the time of this writing, the extension, and thus this module, only
 * supported authentication against a domain, and pdc and bdc must be
 * non-null and not equal to each other. In other words, to use this module
 * you must have a domain with at least one PDC and one BDC.
 *
 * Required parameters:
 * ====================
 *   'hostspec'  IP, DNS Name, or NetBios Name of the SMB server to
 *               authenticate with.
 *   'domain'    The domain name to authenticate with.
 *
 * Optional parameters:
 * ====================
 *   'group'     Optional group name that the user must be a member of.
 *               Will be ignored if the value passed is a zero length string.
 *
 *
 * $Horde: framework/Auth/Auth/smb.php,v 1.20 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 * Copyright 2002-2004 Marcus I. Ryan <marcus@riboflavin.net>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @author  Marcus I. Ryan <marcus@riboflavin.net>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_smb extends Auth {

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
     * Constructs a new SMB authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_smb($params = array())
    {
        if (!Util::extensionExists('smbauth')) {
            Horde::fatal(PEAR::raiseError(_("Auth_smbauth: Required smbauth extension not found."), __FILE__, __LINE__));
        }

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
            Horde::fatal(PEAR::raiseError(_("No password provided for SMB authentication.")), __FILE__, __LINE__);
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
