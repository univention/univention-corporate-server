<?php

require_once dirname(__FILE__) . '/sql.php';

/**
 * The Auth_customsql class provides a sql implementation of the Horde
 * authentication system with the possibility to set custom-made queries.
 *
 * Required parameters:
 * ====================
 *   'database'  --  The name of the database.
 *   'hostspec'  --  The hostname of the database server.
 *   'password'  --  The password associated with 'username'.
 *   'phptype'   --  The database type (ie. 'pgsql', 'mysql, etc.).
 *   'protocol'  --  The communication protocol ('tcp', 'unix', etc.).
 *   'username'  --  The username with which to connect to the database.
 *
 * Required parameters: (Custom query)
 * ===================================
 * Some special tokens can be used in the sql query. They are replaced
 * at the query stage :
 *
 *   - "\L" will be replaced by the user's login
 *   - "\P" will be replaced by the user's password.
 *   - "\O" will be replaced by the old user's login (required for update)
 *
 *   Eg: "SELECT * FROM users WHERE uid = \L
 *                            AND passwd = \P
 *                            AND billing = 'paid'
 *
 *   'query_auth'    Authenticate the user.       "\L" & "\N"
 *   'query_add'     Add user.                    "\L" & "\N"
 *   'query_update'  Update user.                 "\O", "\L" & "\N"
 *   'query_resetpassword'  Reset password.       "\L", & "\P"
 *   'query_remove'  Remove user.                 "\L"
 *   'query_list'    List user.                   "\L"
 *
 * Optional parameters:
 * ====================
 *   'encryption'      --  The encryption to use to store the password in the
 *                         table (e.g. plain, crypt, md5-hex, md5-base64, smd5,
 *                         sha, ssha).
 *                         DEFAULT: 'md5-hex'
 *   'show_encryption' --  Whether or not to prepend the encryption in the
 *                         password field.
 *                         DEFAULT: 'false'
 *
 * Required by some database implementations:
 * ==========================================
 *   'options'  --  Additional options to pass to the database.
 *   'port'     --  The port on which to connect to the database.
 *   'tty'      --  The TTY on which to connect to the database.
 *
 *
 * $Horde: framework/Auth/Auth/customsql.php,v 1.14 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 2002 Ronnie Garcia <ronnie@mk2.net>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Ronnie Garcia <ronnie@mk2.net>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Joel Vandal <jvandal@infoteck.qc.ca>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_customsql extends Auth_sql {

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array $capabilities
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
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
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
        /* _connect() will die with Horde::fatal() upon failure. */
        $this->_connect();

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_auth'];
        $query = str_replace("\L", $this->_db->quote($userId), $query);
        $query = str_replace("\P", $this->_db->quote($this->getCryptedPassword($credentials['password'],
                                                                               '',
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
     * @access public
     *
     * @param string $userId      The userId to add.
     * @param array $credentials  The credentials to add.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        $this->_connect();

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_add'];
        $query = str_replace("\L", $this->_db->quote($userId), $query);
        $query = str_replace("\P", $this->_db->quote($this->getCryptedPassword($credentials['password'],
                                                                               '',
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
     * @access public
     *
     * @param string $oldID       The old userId.
     * @param string $newID       The new userId.
     * @param array $credentials  The new credentials
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function updateUser($oldID, $newID, $credentials)
    {
        /* _connect() will die with Horde::fatal() upon failure. */
        $this->_connect();

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_update'];
        $query = str_replace("\O", $this->_db->quote($oldId), $query);
        $query = str_replace("\L", $this->_db->quote($newId), $query);
        $query = str_replace("\P", $this->_db->quote($this->getCryptedPassword($credentials['password'],
                                                                               '',
                                                                               $this->_params['encryption'],
                                                                               $this->_params['show_encryption'])), $query);

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
    }

    /**
     * Reset a user's password. Used for example when the user does not
     * remember the existing password.
     *
     * @access public
     *
     * @param string $user_id  The user id for which to reset the password.
     *
     * @return mixed  The new passwrd on success or a PEAR_Error object on
     *                failure.
     */
    function resetPassword($user_id)
    {
        /* _connect() will die with Horde::fatal() upon failure. */
        $this->_connect();

        /* Get a new random password. */
        $password = Auth::genRandomPassword();

        /* Build the SQL query. */
        $query = $this->_params['query_resetpassword'];
        $query = str_replace("\L", $this->_db->quote($user_id), $query);
        $query = str_replace("\P", $this->_db->quote($this->getCryptedPassword($password,
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
     * @access public
     *
     * @param string $userId  The userId to delete.
     *
     * @return boolean        Success or failure.
     */
    function removeUser($userId)
    {
        /* _connect() will die with Horde::fatal() upon failure. */
        $this->_connect();

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_remove'];
        $query = str_replace("\L", $this->_db->quote($userId), $query);

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
    }

    /**
     * List all users in the system.
     *
     * @access public
     *
     * @return mixed  The array of userIds, or false on failure/unsupported.
     */
    function listUsers()
    {
        /* _connect() will die with Horde::fatal() upon failure. */
        $this->_connect();

        /* Build a custom query, based on the config file. */
        $query = $this->_params['query_list'];

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

}
