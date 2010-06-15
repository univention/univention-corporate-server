<?php
/**
 * The Auth_sql class provides a SQL implementation of the Horde
 * authentication system.
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
 * Optional parameters:
 * ====================
 *   'encryption'      --  The encryption to use to store the password in the
 *                         table (e.g. plain, crypt, md5-hex, md5-base64, smd5,
 *                         sha, ssha, aprmd5).
 *                         DEFAULT: 'md5-hex'
 *   'show_encryption' --  Whether or not to prepend the encryption in the
 *                         password field.
 *                         DEFAULT: 'false'
 *   'password_field'  --  The name of the password field in the auth table.
 *                         DEFAULT: 'user_pass'
 *   'table'           --  The name of the SQL table to use in 'database'.
 *                         DEFAULT: 'horde_users'
 *   'username_field'  --  The name of the username field in the auth table.
 *                         DEFAULT: 'user_uid'
 *
 * Required by some database implementations:
 * ==========================================
 *   'options'  --  Additional options to pass to the database.
 *   'port'     --  The port on which to connect to the database.
 *   'tty'      --  The TTY on which to connect to the database.
 *
 *
 * The table structure for the auth system is as follows:
 *
 * CREATE TABLE horde_users (
 *     user_uid   VARCHAR(255) NOT NULL,
 *     user_pass  VARCHAR(255) NOT NULL,
 *     PRIMARY KEY (user_uid)
 * );
 *
 *
 * If setting up as the Horde auth handler in conf.php, simply configure
 * $conf['sql'].
 *
 *
 * $Horde: framework/Auth/Auth/sql.php,v 1.66 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_sql extends Auth {

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array $capabilities
     */
    var $capabilities = array('add'           => true,
                              'update'        => true,
                              'resetpassword' => false,
                              'remove'        => true,
                              'list'          => true,
                              'transparent'   => false);

    /**
     * Handle for the current database connection.
     *
     * @var object DB $_db
     */
    var $_db;

    /**
     * Boolean indicating whether or not we're connected to the SQL server.
     *
     * @var boolean $connected
     */
    var $_connected = false;

    /**
     * Constructs a new SQL authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_sql($params = array())
    {
        $this->_params = $params;
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

        /* Build the SQL query. */
        $query = sprintf('SELECT %s FROM %s WHERE %s = %s',
                         $this->_params['password_field'],
                         $this->_params['table'],
                         $this->_params['username_field'],
                         $this->_db->quote($userId));

        $result = $this->_db->query($query);
        if (!is_a($result, 'PEAR_Error')) {
            $row = $result->fetchRow(DB_GETMODE_ASSOC);
            if (is_array($row) && $this->_comparePasswords($row[$this->_params['password_field']], $credentials['password'])) {
                $result->free();
                return true;
            } else {
                if (is_array($row)) {
                    $result->free();
                }
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

        /* Build the SQL query. */
        $query = sprintf('INSERT INTO %s (%s, %s) VALUES (%s, %s)',
                         $this->_params['table'],
                         $this->_params['username_field'],
                         $this->_params['password_field'],
                         $this->_db->quote($userId),
                         $this->_db->quote($this->getCryptedPassword($credentials['password'],
                                                                     '',
                                                                     $this->_params['encryption'],
                                                                     $this->_params['show_encryption'])));

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
     * @param string $oldID        The old userId.
     * @param string $newID        The new userId.
     * @param array  $credentials  The new credentials
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function updateUser($oldID, $newID, $credentials)
    {
        /* _connect() will die with Horde::fatal() upon failure. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf('UPDATE %s SET %s = %s, %s = %s WHERE %s = %s',
                         $this->_params['table'],
                         $this->_params['username_field'],
                         $this->_db->quote($newID),
                         $this->_params['password_field'],
                         $this->_db->quote($this->getCryptedPassword($credentials['password'],
                                                                     '',
                                                                     $this->_params['encryption'],
                                                                     $this->_params['show_encryption'])),
                         $this->_params['username_field'],
                         $this->_db->quote($oldID));

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
        $query = sprintf('UPDATE %s SET %s = %s WHERE %s = %s',
                         $this->_params['table'],
                         $this->_params['password_field'],
                         $this->_db->quote($this->getCryptedPassword($password,
                                                                     '',
                                                                     $this->_params['encryption'],
                                                                     $this->_params['show_encryption'])),
                         $this->_params['username_field'],
                         $this->_db->quote($user_id));

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

        /* Build the SQL query. */
        $query = sprintf('DELETE FROM %s WHERE %s = %s',
                         $this->_params['table'],
                         $this->_params['username_field'],
                         $this->_db->quote($userId));

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

        /* Build the SQL query. */
        $query = sprintf('SELECT %s FROM %s ORDER BY %s',
                         $this->_params['username_field'],
                         $this->_params['table'],
                         $this->_params['username_field']);

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
     * Checks if a userId exists in the sistem.
     *
     * @access public
     *
     * @return boolean  Whether or not the userId already exists.
     */
    function exists($userId)
    {
        /* _connect() will die with Horde::fatal() upon failure. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf('SELECT %s FROM %s WHERE %s = %s',
                         $this->_params['username_field'],
                         $this->_params['table'],
                         $this->_params['username_field'],
                         $this->_db->quote($userId));

        return $this->_db->getOne($query);
    }

    /**
     * Compare an encrypted password to a plaintext string to see if
     * they match.
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

    /**
     * Attempts to open a connection to the SQL server.
     *
     * @access private
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _connect()
    {
        if (!$this->_connected) {
            Horde::assertDriverConfig($this->_params, 'auth',
                array('phptype', 'hostspec', 'username', 'database'),
                'authentication SQL');

            if (empty($this->_params['encryption'])) {
                $this->_params['encryption'] = 'md5-hex';
            }
            if (!isset($this->_params['show_encryption'])) {
                $this->_params['show_encryption'] = false;
            }
            if (empty($this->_params['table'])) {
                $this->_params['table'] = 'horde_users';
            }
            if (empty($this->_params['username_field'])) {
                $this->_params['username_field'] = 'user_uid';
            }
            if (empty($this->_params['password_field'])) {
                $this->_params['password_field'] = 'user_pass';
            }

            /* Connect to the SQL server using the supplied
             * parameters. */
            include_once 'DB.php';
            $this->_db = &DB::connect($this->_params,
                                      array('persistent' => !empty($this->_params['persistent'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                Horde::fatal(PEAR::raiseError(_("Unable to connect to SQL server.")), __FILE__, __LINE__);
            }

            /* Enable the "portability" option. */
            $this->_db->setOption('optimize', 'portability');

            $this->_connected = true;
        }

        return true;
    }

}
