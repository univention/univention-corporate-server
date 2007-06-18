<?php
/**
 * The Auth_ftp class provides an FTP implementation of the Horde
 * authentication system.
 *
 * Optional parameters:
 * ====================
 *   'hostspec'  --  The hostname or IP address of the FTP server.
 *                   DEFAULT: 'localhost'
 *   'port'          The server port to connect to.
 *                   DEFAULT: 21
 *
 *
 * $Horde: framework/Auth/Auth/ftp.php,v 1.23 2004/01/28 00:34:00 slusarz Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Max Kalika <max@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Max Kalika <max@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_ftp extends Auth {

    /**
     * Constructs a new FTP authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_ftp($params = array())
    {
        if (!Util::extensionExists('ftp')) {
            Horde::fatal(PEAR::raiseError(_("Auth_ftp: Required FTP extension not found. Compile PHP with the --enable-ftp switch.")), __FILE__, __LINE__);
        }

        $default_params = array(
            'hostspec' => 'localhost',
            'port' => 21
        );
        $this->_params = array_merge($default_params, $params);
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  An array of login credentials. For FTP,
     *                            this must contain a password entry.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        $ftp = @ftp_connect($this->_params['hostspec'], $this->_params['port']);

        if ($ftp && @ftp_login($ftp, $userId, $credentials['password'])) {
            @ftp_quit($ftp);
            return true;
        } else {
            @ftp_quit($ftp);
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }
    }

}
