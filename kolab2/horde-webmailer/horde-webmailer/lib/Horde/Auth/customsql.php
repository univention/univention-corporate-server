<?php

require_once dirname(__FILE__) . '/sql.php';

/**
 * The Auth_customsql class provides a sql implementation of the Horde
 * authentication system with the possibility to set custom-made queries.
 *
 * Required parameters:<pre>
 *   'phptype'  The database type (ie. 'pgsql', 'mysql', etc.).</pre>
 *
 * Required parameters: (Custom query)<pre>
 * Some special tokens can be used in the sql query. They are replaced
 * at the query stage:
 *
 *   - '\L' will be replaced by the user's login
 *   - '\P' will be replaced by the user's password.
 *   - '\O' will be replaced by the old user's login (required for update)
 *
 *   Eg: "SELECT * FROM users WHERE uid = \L
 *                            AND passwd = \P
 *                            AND billing = 'paid'
 *
 *   'query_auth'    Authenticate the user.       '\L' & '\P'
 *   'query_add'     Add user.                    '\L' & '\P'
 *   'query_getpw'   Get one user's password.     '\L'
 *   'query_update'  Update user.                 '\O', '\L' & '\P'
 *   'query_resetpassword'  Reset password.       '\L', & '\P'
 *   'query_remove'  Remove user.                 '\L'
 *   'query_list'    List user.
 *   'query_exists'  Check for existance of user. '\L'</pre>
 *
 * Optional parameters:<pre>
 *   'encryption'       The encryption to use to store the password in the
 *                      table (e.g. plain, crypt, md5-hex, md5-base64, smd5,
 *                      sha, ssha).
 *                      DEFAULT: 'md5-hex'
 *   'show_encryption'  Whether or not to prepend the encryption in the
 *                      password field.
 *                      DEFAULT: 'false'</pre>
 *
 * Required by some database implementations:<pre>
 *   'hostspec'  The hostname of the database server.
 *   'protocol'  The communication protocol ('tcp', 'unix', etc.).
 *   'database'  The name of the database.
 *   'username'  The username with which to connect to the database.
 *   'password'  The password associated with 'username'.
 *   'options'   Additional options to pass to the database.
 *   'port'      The port on which to connect to the database.
 *   'tty'       The TTY on which to connect to the database.</pre>
 *
 *
 * $Horde: framework/Auth/Auth/customsql.php,v 1.16.10.12 2008-06-30 17:04:36 jan Exp $
 *
 * Copyright 2002 Ronnie Garcia <ronnie@mk2.net>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Ronnie Garcia <ronnie@mk2.net>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Joel Vandal <joel@scopserv.com>
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_customsql extends Auth_sql {

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array
     */
    var $capabilities = array('add'           => true,
                              'update'        => true,
                              'resetpassword' => true,
                              'remove'        => true,
                              'list'          => true,
                              'transparent'   => false);

    /**
     * Constructs a new SQL authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_customsql($params = array())
    {
        $this->_params = $params;

        Horde::assertDriverConfig($params, 'auth',
            array('query_auth'),
            'authentication custom SQL');
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  The credentials to use.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            $this->_setAuthError(AUTH_REASON_FAILED, $result->getMessage());
            return false;
        }

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_auth'];
        $query = str_replace('\L', $this->_db->quote($userId), $query);
        $query = str_replace('\P', $this->_db->quote($this->getCryptedPassword(
                                                         $credentials['password'],
                                                         $this->_getPassword($userId),
                                                         $this->_params['encryption'],
                                                         $this->_params['show_encryption'])), $query);

        $result = $this->_db->query($query);
        if (!is_a($result, 'PEAR_Error')) {
            $row = $result->fetchRow(DB_GETMODE_ASSOC);
            /* If we have at least one returned row, then the user is
             * valid. */
            if (is_array($row)) {
                $result->free();
                return true;
            } else {
                $result->free();
                $this->_setAuthError(AUTH_REASON_BADLOGIN);
                return false;
            }
        } else {
            $this->_setAuthError(AUTH_REASON_FAILED);
            return false;
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
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_add'];
        $query = str_replace('\L', $this->_db->quote($userId), $query);
        $query = str_replace('\P', $this->_db->quote($this->getCryptedPassword(
                                                         $credentials['password'], '',
                                                         $this->_params['encryption'],
                                                         $this->_params['show_encryption'])), $query);

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
    }

    /**
     * Update a set of authentication credentials.
     *
     * @param string $oldId       The old userId.
     * @param string $newId       The new userId.
     * @param array $credentials  The new credentials
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function updateUser($oldId, $newId, $credentials)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_update'];
        $query = str_replace('\O', $this->_db->quote($oldId), $query);
        $query = str_replace('\L', $this->_db->quote($newId), $query);
        $query = str_replace('\P', $this->_db->quote($this->getCryptedPassword(
                                                         $credentials['password'],
                                                         $this->_getPassword($oldId),
                                                         $this->_params['encryption'],
                                                         $this->_params['show_encryption'])), $query);

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
    }

    /**
     * Resets a user's password. Used for example when the user does not
     * remember the existing password.
     *
     * @param string $userId  The user id for which to reset the password.
     *
     * @return mixed  The new password on success or a PEAR_Error object on
     *                failure.
     */
    function resetPassword($userId)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        /* Get a new random password. */
        $password = Auth::genRandomPassword();

        /* Build the SQL query. */
        $query = $this->_params['query_resetpassword'];
        $query = str_replace('\L', $this->_db->quote($userId), $query);
        $query = str_replace('\P', $this->_db->quote($this->getCryptedPassword($password,
                                                                               '',
                                                                               $this->_params['encryption'],
                                                                               $this->_params['show_encryption'])), $query);

        $result = $this->_db->query($query);
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
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_remove'];
        $query = str_replace('\L', $this->_db->quote($userId), $query);

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $this->removeUserData($userId);
    }

    /**
     * List all users in the system.
     *
     * @return mixed  The array of userIds, or false on failure/unsupported.
     */
    function listUsers()
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_list'];
        $query = str_replace('\L', $this->_db->quote(Auth::getAuth()), $query);

        $result = $this->_db->getAll($query, null, DB_FETCHMODE_ORDERED);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Loop through and build return array. */
        $users = array();
        foreach ($result as $ar) {
            $users[] = $ar[0];
        }

        return $users;
    }

    /**
     * Checks if a userId exists in the system.
     *
     * @return boolean  Whether or not the userId already exists.
     */
    function exists($userId)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_exists'];
        $query = str_replace('\L', $this->_db->quote($userId), $query);

        $result = $this->_db->getOne($query);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return (bool)$result;
    }

    /**
     * Fetch $userId's current password - needed for the salt with some
     * encryption schemes when doing authentication or updates.
     *
     * @param string $userId
     *
     * @return string $userId's current password.
     */
    function _getPassword($userId)
    {
        /* Retrieve the old password in case we need the salt. */
        $query = $this->_params['query_getpw'];
        $query = str_replace('\L', $this->_db->quote($userId), $query);
        $pw = $this->_db->getOne($query);
        if (is_a($pw, 'PEAR_Error')) {
            Horde::logMessage($pw, __FILE__, __LINE__, PEAR_LOG_ERR);
            return '';
        }

        return $pw;
    }

}
