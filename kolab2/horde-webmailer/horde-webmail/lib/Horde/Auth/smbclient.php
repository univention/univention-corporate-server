<?php
/**
 * The Auth_smbclient class provides an smbclient implementation of
 * the Horde authentication system.
 *
 * Required parameters:<pre>
 *   'hostspec'        IP, DNS Name, or NetBios Name of the SMB server to
 *                     authenticate with.
 *   'domain'          The domain name to authenticate with.</pre>
 *   'smbclient_path'  The location of the smbclient(1) utility.
 *
 * Optional parameters:<pre>
 *   'group'     Group name that the user must be a member of. Will be
 *               ignored if the value passed is a zero length string.</pre>
 *
 *
 * $Horde: framework/Auth/Auth/smbclient.php,v 1.1.2.5 2009-01-06 15:22:50 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Jon Parise <jon@horde.org>
 * @author  Marcus I. Ryan <marcus@riboflavin.net>
 * @since   Horde 3.1.4
 * @package Horde_Auth
 */
class Auth_smbclient extends Auth {

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
    function Auth_smbclient($params = array())
    {
        /* Ensure we've been provided with all of the necessary parameters. */
        Horde::assertDriverConfig($params, 'auth',
            array('hostspec', 'domain', 'smbclient_path'),
            'authentication smbclient');

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

        /* Authenticate. */
        $cmdline = implode(' ', array($this->_params['smbclient_path'],
                                      '-L',
                                      $this->_params['hostspec'],
                                      '-W',
                                      $this->_params['domain'],
                                      '-U',
                                      $userId));

        $sc = popen($cmdline, 'w');
        if ($sc === false) {
            $this->_setAuthError(AUTH_REASON_MESSAGE,
                                 _("Unable to execute smbclient."));
            return false;
        }

        fwrite($sc, $credentials['password']);
        $rc = pclose($sc);
        if ((int)($rc & 0xff) == 0) {
            return true;
        }

        $this->_setAuthError(AUTH_REASON_BADLOGIN);
        return false;
    }

}
