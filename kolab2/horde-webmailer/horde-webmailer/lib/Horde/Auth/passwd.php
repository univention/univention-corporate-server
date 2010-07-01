<?php
/**
 * The Auth_passwd:: class provides a passwd-file implementation of
 * the Horde authentication system.
 *
 * Required parameters:<pre>
 *   'filename'  The passwd file to use.</pre>
 *
 * Optional parameters:<pre>
 *   'encryption'       The encryption to use to store the password in
 *                      the table (e.g. plain, crypt, md5-hex,
 *                      md5-base64, smd5, sha, ssha, aprmd5).
 *                      DEFAULT: 'crypt-des'
 *   'show_encryption'  Whether or not to prepend the encryption in the
 *                      password field.
 *                      DEFAULT: 'false'
 *   'lock'             Should we lock the passwd file? (boolean) The password
 *                      file cannot be changed (add, edit, or delete users)
 *                      unless this is true.
 *                      DEFAULT: false</pre>
 *
 *
 * $Horde: framework/Auth/Auth/passwd.php,v 1.16.10.20 2009-01-06 15:22:50 jan Exp $
 *
 * Copyright 1997-2007 Rasmus Lerdorf <rasmus@php.net>
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Rasmus Lerdorf <rasmus@php.net>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_passwd extends Auth {

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
                              'list'          => true,
                              'transparent'   => false);

    /**
     * Hash list of users.
     *
     * @var array
     */
    var $_users = null;

    /**
     * Array of groups and members.
     *
     * @var array
     */
    var $_groups = array();

    /**
     * Filehandle for lockfile.
     *
     * @var integer
     */
    var $_fplock;

    /**
     * Locking state.
     *
     * @var boolean
     */
    var $_locked;

    /**
     * List of users that should be excluded from being listed/handled
     * in any way by this driver.
     *
     * @var array
     */
    var $_exclude = array(
        'root',
        'daemon',
        'bin',
        'sys',
        'sync',
        'games',
        'man',
        'lp',
        'mail',
        'news',
        'uucp',
        'proxy',
        'postgres',
        'www-data',
        'backup',
        'operator',
        'list',
        'irc',
        'gnats',
        'nobody',
        'identd',
        'sshd',
        'gdm',
        'postfix',
        'mysql',
        'cyrus',
        'ftp',
    );

    /**
     * Constructs a new Passwd authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_passwd($params = array())
    {
        $this->_params = $params;

        if (empty($this->_params['lock'])) {
            $this->_params['lock'] = false;
        }

        // Default to DES passwords.
        if (empty($this->_params['encryption'])) {
            $this->_params['encryption'] = 'crypt-des';
        }

        if (empty($this->_params['show_encryption'])) {
            $this->_params['show_encryption'] = false;
        }

        if ($this->_params['lock']) {
            register_shutdown_function(array(&$this, '_commit'));
        }
    }

    /**
     * Read and, if requested, lock the password file.
     */
    function _read()
    {
        if (is_array($this->_users)) {
            return true;
        }

        if (empty($this->_params['filename'])) {
            return PEAR::raiseError('No password file set.');
        }

        if ($this->_params['lock']) {
            $this->_fplock = fopen(Horde::getTempDir() . '/passwd.lock', 'w');
            flock($this->_fplock, LOCK_EX);
            $this->_locked = true;
        }

        $fp = fopen($this->_params['filename'], 'r');
        if (!$fp) {
            return PEAR::raiseError("Couldn't open '" . $this->_params['filename'] . "'.");
        }

        $this->_users = array();
        while (!feof($fp)) {
            $line = trim(fgets($fp, 128));
            if (empty($line)) {
                continue;
            }

            $parts = explode(':', $line);
            if (!count($parts)) {
                continue;
            }

            $user = $parts[0];
            $userinfo = array();
            if (strlen($user) && !in_array($user, $this->_exclude)) {
                if (isset($parts[1])) {
                    $userinfo['password'] = $parts[1];
                }
                if (isset($parts[2])) {
                    $userinfo['uid'] = $parts[2];
                }
                if (isset($parts[3])) {
                    $userinfo['gid'] = $parts[3];
                }
                if (isset($parts[4])) {
                    $userinfo['info'] = $parts[4];
                }
                if (isset($parts[5])) {
                    $userinfo['home'] = $parts[5];
                }
                if (isset($parts[6])) {
                    $userinfo['shell'] = $parts[6];
                }

                $this->_users[$user] = $userinfo;
            }
        }

        fclose($fp);

        if (!empty($this->_params['group_filename'])) {
            $fp = fopen($this->_params['group_filename'], 'r');
            if (!$fp) {
                return PEAR::raiseError("Couldn't open '" . $this->_params['group_filename'] . "'.");
            }

            $this->_groups = array();
            while (!feof($fp)) {
                $line = trim(fgets($fp));
                if (empty($line)) {
                    continue;
                }

                $parts = explode(':', $line);
                $group = array_shift($parts);
                $users = array_pop($parts);
                $this->_groups[$group] = array_flip(preg_split('/\s*[,\s]\s*/', trim($users), -1, PREG_SPLIT_NO_EMPTY));
            }

            fclose($fp);
        }

        return true;
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
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }

        $result = $this->_read();
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            $this->_setAuthError(AUTH_REASON_FAILED);
            return false;
        }

        if (!isset($this->_users[$userId])) {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }

        if (!$this->_comparePasswords($this->_users[$userId]['password'],
                                      $credentials['password'])) {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }

        if (!empty($this->_params['required_groups'])) {
            $allowed = false;
            foreach ($this->_params['required_groups'] as $group) {
                if (isset($this->_groups[$group][$userId])) {
                    $allowed = true;
                    break;
                }
            }

            if (!$allowed) {
                $this->_setAuthError(AUTH_REASON_BADLOGIN);
                return false;
            }
        }

        return true;
    }

    /**
     * List all users in the system.
     *
     * @return mixed  The array of userIds, or a PEAR_Error object on failure.
     */
    function listUsers()
    {
        $result = $this->_read();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $users = array_keys($this->_users);
        if (empty($this->_params['required_groups'])) {
            return $users;
        } else {
            $groupUsers = array();
            foreach ($this->_params['required_groups'] as $group) {
                $groupUsers = array_merge($groupUsers, array_intersect($users, array_keys($this->_groups[$group])));
            }
            return $groupUsers;
        }
    }

    /**
     * Add a set of authentication credentials.
     *
     * @param string $userId      The userId to add.
     * @param array $credentials  The credentials to add.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        $result = $this->_read();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!isset($this->_users[$userId]) && $this->_locked) {
            $this->_users[$userId] = crypt($pass);
            return true;
        } else {
            return PEAR::raiseError("Couldn't add user '$user', because the user already exists.");
        }
    }

    /**
     * Update a set of authentication credentials.
     *
     * @param string $oldID        The old userId.
     * @param string $newID        The new userId.
     * @param array  $credentials  The new credentials
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function updateUser($oldID, $newID, $credentials)
    {
        $result = $this->_read();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (isset($this->_users[$oldID]) && $this->_locked) {
            $this->_users[$newID] = array(
                'password' => $this->getCryptedPassword($credentials['password'],
                                                        '',
                                                        $this->_params['encryption'],
                                                        $this->_params['show_encryption']),
            );
            return true;
        } else {
            return PEAR::raiseError("Couldn't modify user '$oldID', because the user doesn't exist.");
        }
    }

    /**
     * Reset a user's password. Used for example when the user does not
     * remember the existing password.
     *
     * @param string $userId  The user id for which to reset the password.
     *
     * @return mixed  The new password on success or a PEAR_Error object on
     *                failure.
     */
    function resetPassword($userId)
    {
        /* Get a new random password. */
        $password = Auth::genRandomPassword();
        $result = $this->updateUser($userId, $userId, array('password' => $password));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $password;
    }

    /**
     * Delete a set of authentication credentials.
     *
     * @param string $userId  The userId to delete.
     *
     * @return boolean        Success or failure.
     */
    function removeUser($userId)
    {
        $result = $this->_read();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!isset($this->_users[$userId]) || !$this->_locked) {
            return PEAR::raiseError("Couldn't delete user '$userId', because the user doesn't exist.");
        }

        unset($this->_users[$userId]);

        return $this->removeUserData($userId);
    }

    /**
     * Writes changes to passwd file and unlocks it.  Takes no arguments and
     * has no return value. Called on script shutdown.
     */
    function _commit()
    {
        if ($this->_locked) {
            foreach ($this->_users as $user => $pass) {
                if ($this->_users[$user]) {
                    fputs($this->_fplock, "$user:$pass:" . $this->_users[$user] . "\n");
                } else {
                    fputs($this->_fplock, "$user:$pass\n");
                }
            }
            rename($this->_lockfile, $this->_params['filename']);
            flock($this->_fplock, LOCK_UN);
            $this->_locked = false;
            fclose($this->_fplock);
        }
    }

    /**
     * Compare an encrypted password to a plaintext string to see if
     * they match.
     *
     * @access private
     *
     * @param string $encrypted  The crypted password to compare against.
     * @param string $plaintext  The plaintext password to verify.
     *
     * @return boolean  True if matched, false otherwise.
     */
    function _comparePasswords($encrypted, $plaintext)
    {
        return $encrypted == $this->getCryptedPassword($plaintext,
                                                       $encrypted,
                                                       $this->_params['encryption'],
                                                       $this->_params['show_encryption']);
    }

}
