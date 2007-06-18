<?php
/**
 * The Auth_login:: class provides a system login implementation of
 * the Horde authentication system.
 * This Auth driver is useful if you have a shadow password system
 * where the Auth_passwd driver doesn't work.
 *
 * Optional parameters:
 * ====================
 *   'location'  --  Location of the su binary
 *                   DEFAULT: /bin/su
 *
 *
 * $Horde: framework/Auth/Auth/login.php,v 1.3 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_login extends Auth {

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
     * su binary.
     *
     * @var string $_location
     */
    var $_location = '/bin/su';

    /**
     * List of users that should be excluded from being listed/handled
     * in any way by this driver.
     *
     * @var array $_exclude
     */
    var $_exclude = array('root', 'daemon', 'bin', 'sys', 'sync', 'games',
                          'man', 'lp', 'mail', 'news', 'uucp', 'proxy',
                          'postgres', 'www-data', 'backup', 'operator',
                          'list', 'irc', 'gnats', 'nobody', 'identd',
                          'sshd', 'gdm', 'postfix', 'mysql', 'cyrus', 'ftp');

    /**
     * Constructs a new Login authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
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
            Horde::fatal(PEAR::raiseError(_("No password provided for Login authentication.")), __FILE__, __LINE__);
        }

        $proc = popen($this->_location . ' ' . $userId, 'w');
        if (!is_resource($proc)) {
            return false;
        }
        fwrite($proc, $credentials['password']);
        fwrite($proc, 'exit');
 
        return pclose($proc) === 0;
    }

}
