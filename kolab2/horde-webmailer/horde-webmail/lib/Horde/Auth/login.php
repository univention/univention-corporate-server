<?php
/**
 * The Auth_login:: class provides a system login implementation of
 * the Horde authentication system.
 * This Auth driver is useful if you have a shadow password system
 * where the Auth_passwd driver doesn't work.
 *
 * Optional parameters:<pre>
 *   'location'  Location of the su binary.
 *               DEFAULT: /bin/su</pre>
 *
 *
 * $Horde: framework/Auth/Auth/login.php,v 1.3.10.13 2009-01-06 15:22:49 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_login extends Auth {

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
     * su binary.
     *
     * @var string
     */
    var $_location = '/bin/su';

    /**
     * List of users that should be excluded from being listed/handled
     * in any way by this driver.
     *
     * @var array
     */
    var $_exclude = array('root', 'daemon', 'bin', 'sys', 'sync', 'games',
                          'man', 'lp', 'mail', 'news', 'uucp', 'proxy',
                          'postgres', 'www-data', 'backup', 'operator',
                          'list', 'irc', 'gnats', 'nobody', 'identd',
                          'sshd', 'gdm', 'postfix', 'mysql', 'cyrus', 'ftp');

    /**
     * Constructs a new Login authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_login($params = array())
    {
        $this->_params = $params;
        if (!empty($params['location'])) {
            $this->_location = $params['location'];
        }
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

        $proc = @popen($this->_location . ' -c /bin/true ' . $userId, 'w');
        if (!is_resource($proc)) {
            $this->_setAuthError(AUTH_REASON_FAILED);
            return false;
        }

        fwrite($proc, $credentials['password']);
        return @pclose($proc) === 0;
    }

}
