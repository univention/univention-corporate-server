<?php

require_once 'Horde/Auth/sql.php';
require_once 'Horde/IMAP/Admin.php';

/**
 * The Auth_cyrsql class provides a SQL implementation of the Horde
 * authentication system for the Cyrus IMAP server. Most of the functionality
 * is the same as for the SQL class; only what is different overrides the
 * parent class implementations.
 *
 * Required parameters:<pre>
 *   'cyradmin'  The username of the cyrus administrator.
 *   'cyrpass'   The password for the cyrus administrator.
 *   'imap_dsn'  The full IMAP DSN
 *               (i.e. {localhost:993/imap/ssl/novalidate-cert}).
 *   'phptype'   The database type (ie. 'pgsql', 'mysql', etc.).</pre>
 *
 * Optional parameters:<pre>
 *   'domain_field'    If set to anything other than 'none' this is used as
 *                     field name where domain is stored.
 *                     DEFAULT: 'domain_name'
 *   'encryption'      The encryption to use to store the password in the
 *                     table (e.g. plain, crypt, md5-hex, md5-base64, smd5,
 *                     sha, ssha).
 *                     DEFAULT: 'md5-hex'
 *   'folders'         An array of folders to create under username.
 *                     DEFAULT: NONE
 *   'password_field'  The name of the password field in the auth table.
 *                     DEFAULT: 'password'
 *   'quota'           The quota (in kilobytes) to grant on the mailbox.
 *                     DEFAULT: NONE
 *   'table'           The name of the auth table in 'database'.
 *                     DEFAULT: 'accountuser'
 *   'unixhier'        The value of imapd.conf's unixhierarchysep setting.
 *                     Set this to true if the value is true in imapd.conf.
 *   'username_field'  The name of the username field in the auth table.
 *                     DEFAULT: 'username'</pre>
 *   'hidden_accounts' An array of system accounts to hide from the user interface.
 *
 * Required by some database implementations:<pre>
 *   'database'  The name of the database.
 *   'hostspec'  The hostname of the database server.
 *   'protocol'  The communication protocol ('tcp', 'unix', etc.).
 *   'username'  The username with which to connect to the database.
 *   'password'  The password associated with 'username'.
 *   'options'   Additional options to pass to the database.
 *   'port'      The port on which to connect to the database.
 *   'tty'       The TTY on which to connect to the database.</pre>
 *
 *
 * The table structure for the auth system is as follows:
 *
 * <pre>
 * CREATE TABLE accountuser (
 *     username    VARCHAR(255) BINARY NOT NULL DEFAULT '',
 *     password    VARCHAR(32) BINARY NOT NULL DEFAULT '',
 *     prefix      VARCHAR(50) NOT NULL DEFAULT '',
 *     domain_name VARCHAR(255) NOT NULL DEFAULT '',
 *     UNIQUE KEY username (username)
 * );
 *
 * CREATE TABLE adminuser (
 *     username    VARCHAR(50) BINARY NOT NULL DEFAULT '',
 *     password    VARCHAR(50) BINARY NOT NULL DEFAULT '',
 *     type        INT(11) NOT NULL DEFAULT '0',
 *     SID         VARCHAR(255) NOT NULL DEFAULT '',
 *     home        VARCHAR(255) NOT NULL DEFAULT '',
 *     PRIMARY KEY (username)
 * );
 *
 * CREATE TABLE alias (
 *     alias       VARCHAR(255) NOT NULL DEFAULT '',
 *     dest        LONGTEXT,
 *     username    VARCHAR(50) NOT NULL DEFAULT '',
 *     status      INT(11) NOT NULL DEFAULT '1',
 *     PRIMARY KEY (alias)
 * );
 *
 * CREATE TABLE domain (
 *     domain_name VARCHAR(255) NOT NULL DEFAULT '',
 *     prefix      VARCHAR(50) NOT NULL DEFAULT '',
 *     maxaccounts INT(11) NOT NULL DEFAULT '20',
 *     quota       INT(10) NOT NULL DEFAULT '20000',
 *     transport   VARCHAR(255) NOT NULL DEFAULT 'cyrus',
 *     freenames   ENUM('YES','NO') NOT NULL DEFAULT 'NO',
 *     freeaddress ENUM('YES','NO') NOT NULL DEFAULT 'NO',
 *     PRIMARY KEY (domain_name),
 *     UNIQUE KEY prefix (prefix)
 * );
 *
 * CREATE TABLE domainadmin (
 *     domain_name VARCHAR(255) NOT NULL DEFAULT '',
 *     adminuser   VARCHAR(255) NOT NULL DEFAULT ''
 * );
 *
 * CREATE TABLE search (
 *     search_id   VARCHAR(255) NOT NULL DEFAULT '',
 *     search_sql  TEXT NOT NULL,
 *     perpage     INT(11) NOT NULL DEFAULT '0',
 *     timestamp   TIMESTAMP(14) NOT NULL,
 *     PRIMARY KEY (search_id),
 *     KEY search_id (search_id)
 * );
 *
 * CREATE TABLE virtual (
 *     alias       VARCHAR(255) NOT NULL DEFAULT '',
 *     dest        LONGTEXT,
 *     username    VARCHAR(50) NOT NULL DEFAULT '',
 *     status      INT(11) NOT NULL DEFAULT '1',
 *     KEY alias (alias)
 * );
 *
 * CREATE TABLE log (
 *     id          INT(11) NOT NULL AUTO_INCREMENT,
 *     msg         TEXT NOT NULL,
 *     user        VARCHAR(255) NOT NULL DEFAULT '',
 *     host        VARCHAR(255) NOT NULL DEFAULT '',
 *     time        DATETIME NOT NULL DEFAULT '2000-00-00 00:00:00',
 *     pid         VARCHAR(255) NOT NULL DEFAULT '',
 *     PRIMARY KEY (id)
 * );
 * </pre>
 *
 * $Horde: framework/Auth/Auth/cyrsql.php,v 1.33.10.19 2009-01-06 15:22:49 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Ilya Krel <mail@krel.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_cyrsql extends Auth_sql {

    /**
     * Handle for the current IMAP connection.
     *
     * @var resource
     */
    var $_imapStream;

    /**
     * Handle for an IMAP_Admin object.
     *
     * @var IMAP_Admin
     */
    var $_admin;

    /**
     * Hierarchy separator to use (e.g., is it user/mailbox or user.mailbox)
     *
     * @var string
     */
    var $_separator = '.';

    /**
     * Constructor.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_cyrsql($params = array())
    {
        parent::Auth_sql($params);

        $admin_params = array('admin_user' => $params['cyradmin'],
                              'admin_password' => $params['cyrpass'],
                              'dsn' => $params['imap_dsn']);
        if (!empty($this->_params['unixhier'])) {
            $admin_params['userhierarchy'] = 'user/';
        }
        $this->_admin = new IMAP_Admin($admin_params);
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
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            $this->_setAuthError(AUTH_REASON_FAILED);
            return false;
        }

        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')) {
            /* Build the SQL query with domain. */
            $query = sprintf('SELECT * FROM %s WHERE %s = ? AND %s = ?',
                             $this->_params['table'],
                             $this->_params['username_field'],
                             $this->_params['domain_field']);
            $values = explode('@', $userId);
        } else {
            /* Build the SQL query without domain. */
            $query = sprintf('SELECT * FROM %s WHERE %s = ?',
                             $this->_params['table'],
                             $this->_params['username_field']);
            $values = array($userId);
        }

        Horde::logMessage('SQL Query by Auth_cyrsql::_authenticate(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            $this->_setAuthError(AUTH_REASON_FAILED);
            return false;
        }

        $row = $result->fetchRow(DB_GETMODE_ASSOC);
        if (is_array($row)) {
            $result->free();
        } else {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }

        if (!$this->_comparePasswords($row[$this->_params['password_field']],
                                      $credentials['password'])) {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }

        $now = time();
        if (!empty($this->_params['hard_expiration_field']) &&
            !empty($row[$this->_params['hard_expiration_field']]) &&
            ($now > $row[$this->_params['hard_expiration_field']])) {
            $this->_setAuthError(AUTH_REASON_EXPIRED);
            return false;
        }

        if (!empty($this->_params['soft_expiration_field']) &&
            !empty($row[$this->_params['soft_expiration_field']]) &&
            ($now > $row[$this->_params['soft_expiration_field']])) {
            $this->_authCredentials['changeRequested'] = true;
        }

        return true;
    }

    /**
     * Add a set of authentication credentials.
     *
     * @param string $userId       The userId to add.
     * @param array  $credentials  The credentials to add.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')) {
            list($name, $domain) = explode('@', $userId);
            /* Build the SQL query. */
            $query = sprintf('INSERT INTO %s (%s, %s, %s) VALUES (?, ?, ?)',
                             $this->_params['table'],
                             $this->_params['username_field'],
                             $this->_params['domain_field'],
                             $this->_params['password_field']);
            $values = array($name,
                            $domain,
                            $this->getCryptedPassword($credentials['password'],
                                                      '',
                                                      $this->_params['encryption'],
                                                      $this->_params['show_encryption']));

            Horde::logMessage('SQL Query by Auth_cyrsql::addUser(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $dbresult = $this->_db->query($query, $values);
            $query = 'INSERT INTO virtual (alias, dest, username, status) VALUES (?, ?, ?, 1)';
            $values = array($userId, $userId, $name);

            Horde::logMessage('SQL Query by Auth_cyrsql::addUser(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $dbresult2 = $this->_db->query($query, $values);
            if (is_a($dbresult2, 'PEAR_Error')) {
                return $dbresult2;
            }
        } else {
            $dbresult = parent::addUser($userId, $credentials);
        }
        if (is_a($dbresult, 'PEAR_Error')) {
            return $dbresult;
        }

        if (!is_a($result = $this->_admin->addMailbox($userId), 'PEAR_Error')) {
            @array_walk($this->_params['folders'],
                        array($this, '_createSubFolders'), $userId);
        } else {
            Horde::logMessage('IMAP mailbox creation for ' . $userId . ' failed: ' . $result->getMessage(),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return PEAR::raiseError(sprintf(_("IMAP mailbox creation failed: %s"), $result->getMessage()));
        }

        if (isset($this->_params['quota']) && $this->_params['quota'] >= 0) {
            if (!@imap_set_quota($this->_imapStream,
                                 'user' . $this->_separator . $userId,
                                 $this->_params['quota'])) {
                return PEAR::raiseError(sprintf(_("IMAP mailbox quota creation failed: %s"), imap_last_error()));
            }
        }

        return true;
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

        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')) {
            list($name, $domain) = explode('@', $userId);
            /* Build the SQL query. */
            $query = sprintf('DELETE FROM %s WHERE %s = ? and %s = ?',
                             $this->_params['table'],
                             $this->_params['username_field'],
                             $this->_params['domain_field']);
            $values = array($name, $domain);

            Horde::logMessage('SQL Query by Auth_cyrsql::removeUser(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $dbresult = $this->_db->query($query, $values);
            $query = 'DELETE FROM virtual WHERE dest = ?';
            $values = array($userId);

            Horde::logMessage('SQL Query by Auth_cyrsql::removeUser(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $dbresult2 = $this->_db->query($query, $values);
            if (is_a($dbresult2, 'PEAR_Error')) {
                return $dbresult2;
            }
        } else {
            $dbresult = parent::removeUser($userId);
        }

        if (is_a($dbresult, 'PEAR_Error')) {
            return $dbresult;
        }

        /* Delete IMAP mailbox. */
        $imapresult = $this->_admin->removeMailbox($userId);

        if (is_a($imapresult, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("IMAP mailbox deletion failed: %s"), $imapresult->getMessage()));
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

        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')) {
            /* Build the SQL query with domain. */
            $query = sprintf('SELECT %s, %s FROM %s ORDER BY %s',
                             $this->_params['username_field'],
                             $this->_params['domain_field'],
                             $this->_params['table'],
                             $this->_params['username_field']);
        } else {
            /* Build the SQL query without domain. */
            $query = sprintf('SELECT %s FROM %s ORDER BY %s',
                             $this->_params['username_field'],
                             $this->_params['table'],
                             $this->_params['username_field']);
        }

        Horde::logMessage('SQL Query by Auth_cyrsql::listUsers(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_db->getAll($query, null, DB_FETCHMODE_ORDERED);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Loop through and build return array. */
        $users = array();
        if (!empty($this->_params['domain_field'])
            && ($this->_params['domain_field'] != 'none')) {
            foreach ($result as $ar) {
                if (!in_array($ar[0], $this->_params['hidden_accounts'])) {
                    $users[] = $ar[0] . '@' . $ar[1];
                }
            }
        } else {
            foreach ($result as $ar) {
                if (!in_array($ar[0], $this->_params['hidden_accounts'])) {
                    $users[] = $ar[0];
                }
            }
        }

        return $users;
    }

    /**
     * Update a set of authentication credentials.
     *
     * @param string $oldID       The old userId.
     * @param string $newID       The new userId.
     * @param array $credentials  The new credentials
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function updateUser($oldID, $newID, $credentials)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')) {
            list($name, $domain) = explode('@', $oldID);
            /* Build the SQL query with domain. */
            $query = sprintf('UPDATE %s SET %s = ? WHERE %s = ? and %s = ?',
                             $this->_params['table'],
                             $this->_params['password_field'],
                             $this->_params['username_field'],
                             $this->_params['domain_field']);
            $values = array($this->getCryptedPassword($credentials['password'],
                                                      '',
                                                      $this->_params['encryption'],
                                                      $this->_params['show_encryption']),
                            $name, $domain);
        } else {
            /* Build the SQL query. */
            $query = sprintf('UPDATE %s SET %s = ? WHERE %s = ?',
                             $this->_params['table'],
                             $this->_params['password_field'],
                             $this->_params['username_field']);
            $values = array($this->getCryptedPassword($credentials['password'],
                                                      '',
                                                      $this->_params['encryption'],
                                                      $this->_params['show_encryption']),
                            $oldID);
        }

        Horde::logMessage('SQL Query by Auth_cyrsql::updateUser(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $this->_db->query($query, $values);
    }

    /**
     * Attempts to open connections to the SQL and IMAP servers.
     *
     * @access private
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _connect()
    {
        if ($this->_connected) {
            return true;
        }

        if (!Util::extensionExists('imap')) {
            return PEAR::raiseError(_("Auth_cyrsql: Required imap extension not found."));
        }

        $result = parent::_connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!isset($this->_params['hidden_accounts'])) {
            $this->_params['hidden_accounts'] = array('cyrus');
        }

        // Reset the $_connected flag; we haven't yet successfully
        // opened everything.
        $this->_connected = false;

        $this->_imapStream = @imap_open($this->_params['imap_dsn'], $this->_params['cyradmin'], $this->_params['cyrpass'], OP_HALFOPEN);
        if (!$this->_imapStream) {
            return PEAR::raiseError(sprintf(_("Can't connect to IMAP server: %s"), imap_last_error()));
        }

        if (!empty($this->_params['unixhier'])) {
            $this->_separator = '/';
        }

        $this->_connected = true;
        return true;
    }

    /**
     * Creates all mailboxes supplied in configuration
     *
     * @access private
     *
     * @param string $value
     * @param string $key      Unused by this driver
     * @param string userName
     */
    function _createSubFolders($value, $key, $userName)
    {
        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')) {
            list($userName, $domain) = explode('@', $userName);
            $this->_admin->addMailbox($userName . $this->_separator . $value . '@' . $domain);
        } else {
            $this->_admin->addMailbox($userName . $this->_separator . $value);
        }
    }

}
