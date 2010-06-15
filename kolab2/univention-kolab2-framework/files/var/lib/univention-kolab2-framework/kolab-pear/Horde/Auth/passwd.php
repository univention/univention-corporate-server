<?php
/**
 * The Auth_passwd:: class provides a passwd-file implementation of
 * the Horde authentication system.
 *
 * Optional parameters:
 * ====================
 *   'filename'  --  The passwd file to use.
 *                   DEFAULT: /etc/passwd
 *   'lock'      --  Should we lock the passwd file? (boolean)
 *                   DEFAULT: false
 *
 *
 * $Horde: framework/Auth/Auth/passwd.php,v 1.16 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 1997-2004 Rasmus Lerdorf <rasmus@php.net>
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Rasmus Lerdorf <rasmus@php.net>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_passwd extends Auth {

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
                              'list'          => true,
                              'transparent'   => false);

    /**
     * Passwd file.
     *
     * @var string $_filename
     */
    var $_filename = '/etc/passwd';

    /**
     * Hash list of users.
     *
     * @var array $_users
     */
    var $_users;

    /**
     * Filehandle for lockfile.
     *
     * @var integer $_fplock
     */
    var $_fplock;

    /**
     * Locking state.
     *
     * @var boolean $_locked
     */
    var $_locked;

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
     * Constructs a new Passwd authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_passwd($params = array())
    {
        $this->_params = $params;
        if (!empty($params['filename'])) {
            $this->_filename = $params['filename'];
        }
        
        $this->_fplock = fopen(Horde::getTempDir() . '/passwd.lock', 'w');
        if (!empty($params['lock'])) {
            flock($this->_fplock, LOCK_EX);
            $this->_locked = true;
        }

        $fp = fopen($this->_filename, 'r');
        if (!$fp) {
            return PEAR::raiseError("Couldn't open '" . $this->_filename . "'.");
        }
        while (!feof($fp)) {
            $line = fgets($fp, 128);
            if (!empty($line)) {
                list($user, $pass, $uid, $gid, $info, $home, $shell) = explode(':', $line);
                if (strlen($user) &&
                    !in_array($user, $this->_exclude)) {
                    $this->_users[$user]['password'] = $pass;
                    $this->_users[$user]['uid'] = $uid;
                    $this->_users[$user]['gid'] = $gid;
                    $this->_users[$user]['info'] = $info;
                    $this->_users[$user]['home'] = $home;
                    $this->_users[$user]['shell'] = $shell;
                }
            }
        }
        fclose($fp);
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  An array of login credentials. For MCAL,
     *                            this must contain a password entry.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        if (empty($credentials['password'])) {
            Horde::fatal(PEAR::raiseError(_("No password provided for PASSWD authentication.")), __FILE__, __LINE__);
        }
        if (isset($this->_users[$userId])) {
            if ($this->_users[$userId]['password'] == crypt($credentials['password'], substr($this->_users[$userId]['password'], 0, 2))) return true;
        }
        return false;
    }

    /**
     * List all users in the system.
     *
     * @access public
     *
     * @return mixed  The array of userIds, or a PEAR_Error object on failure.
     */
    function listUsers()
    {
        return array_keys($this->_users);
    }

    /**
     * Adds a user.
     *
     * @access public
     *
     * @param string $user          New user ID.
     * @param string $pass          Password for new user.
     * @param optional string $cvs  Cvs user id (needed for pserver passwd
     *                              files).
     *
     * @return boolean  Returns true or PEAR_Error if the user already
     *                  exists.
     */
    function addUser($user, $pass, $cvsuser = '')
    {
        if (!isset($this->_users[$user]) && $this->_locked) {
            $this->_users[$user] = crypt($pass);
            $this->_cvs[$user] = $cvsuser;
            return true;
        } else {
            return PEAR::raiseError("Couldn't add user '$user', because the user already exists.");
        }
    }

    /**
     * Modifies a user.
     *
     * @access public
     *
     * @param string $user          User ID.
     * @param string $pass          Password for new user.
     * @param optional string $cvs  Cvs user id (needed for pserver passwd
     *                              files).
     *
     * @return boolean  Returns true or PEAR_Error if the user doesn't
     *                  exists.
     */
    function modUser($user, $pass, $cvsuser = '')
    {
        if (isset($this->_users[$user]) && $this->_locked) {
            $this->_users[$user] = crypt($pass);
            $this->_cvs[$user] = $cvsuser;
            return true;
        } else {
            return PEAR::raiseError("Couldn't modify user '$user', because the user doesn't exist.");
        }
    }

    /**
     * Deletes a user.
     *
     * @access public
     *
     * @param string $user  User ID.
     *
     * @return boolean  Returs true or PEAR_Error if the user doesn't
     *                  exist.
     */
    function delUser($user)
    {
        if (isset($this->_users[$user]) && $this->_locked) {
            unset($this->_users[$user]);
            unset($this->_cvs[$user]);
        } else {
            return PEAR::raiseError("Couldn't delete user '$user', because the user doesn't exist.");
        }
    }

    /**
     * Writes changes to passwd file and unlocks it.
     *
     * @access public           
     */
    function close()
    {
        if ($this->_locked) {
            foreach($this->_users as $user => $pass) {
                if ($this->_users[$user]) {
                    fputs($this->_fplock, "$user:$pass:" . $this->_users[$user] . "\n");
                } else {
                    fputs($this->_fplock, "$user:$pass\n");
                }
            }
            rename($this->_lockfile, $this->_filename);
            flock($this->_fplock, LOCK_UN);
            $this->_locked = false;
            fclose($this->_fplock);
        }
    }

}
