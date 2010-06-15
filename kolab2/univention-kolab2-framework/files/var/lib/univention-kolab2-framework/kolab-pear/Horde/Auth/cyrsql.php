<?php

require_once dirname(__FILE__) . '/sql.php';

/**
 * The Auth_cyrsql class provides a SQL implementation of the Horde
 * authentication system for the Cyrus IMAP server. Most of the
 * functionality is the same as for the SQL class; only what is
 * different overrides the parent class implementations.
 *
 * Required parameters:
 * ====================
 *   'cyradmin'  --  The username of the cyrus administrator.
 *   'cyrpass'   --  The password for the cyrus administrator.
 *   'database'  --  The name of the database.
 *   'hostspec'  --  The hostname of the database server.
 *   'imap_dsn'  --  The full IMAP DSN
 *                   (i.e. {localhost:993/imap/ssl/novalidate-cert}).
 *   'password'  --  The password associated with 'username'.
 *   'phptype'   --  The database type (ie. 'pgsql', 'mysql, etc.).
 *   'protocol'  --  The communication protocol ('tcp', 'unix', etc.).
 *   'username'  --  The username with which to connect to the database.
 *
 * Optional parameters:
 * ====================
 *   'domain_field'    --  If set to anything other than 'none' this is used as
 *                         field name where domain is stored.
 *                         DEFAULT: 'domain_name'
 *   'encryption'      --  The encryption to use to store the password in the
 *                         table (e.g. plain, crypt, md5-hex, md5-base64, smd5,
 *                         sha, ssha).
 *                         DEFAULT: 'md5-hex'
 *   'folders'         --  An array of folders to create under username.
 *                         DEFAULT: NONE
 *   'password_field'  --  The name of the password field in the auth table.
 *                         DEFAULT: 'password'
 *   'quota'           --  The quota (in kilobytes) to grant on the mailbox.
 *                         DEFAULT: NONE
 *   'table'           --  The name of the auth table in 'database'.
 *                         DEFAULT: 'accountuser'
 *   'unixhier'        --  The value of imapd.conf's unixhierarchysep setting.
 *                         Set this to true if the value is true in imapd.conf.
 *   'username_field'  --  The name of the username field in the auth table.
 *                         DEFAULT: 'username'
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
 *	       	   	     
 *
 * $Horde: framework/Auth/Auth/cyrsql.php,v 1.29 2004/04/14 15:49:04 eraserhd Exp $
 *
 * Copyright 2002-2004 Ilya <mail@krel.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Ilya <mail@krel.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_cyrsql extends Auth_sql {

    /**
     * Handle for the current IMAP connection.
     *
     * @var resource $_imapStream
     */
    var $_imapStream;

    /**
     * Hierarchy separator to use (e.g., is it user/mailbox or user.mailbox)
     *
     * @var string $_separator
     */
    var $_separator = '.';

    /**
     * Constructor.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_cyrsql($params = array())
    {
        if (!Util::extensionExists('imap')) {
            Horde::fatal(PEAR::raiseError(_("Auth_cyrsql: Required imap extension not found."), __FILE__, __LINE__));
        }
        parent::Auth_sql($params);
    }

    /**
     * Add a set of authentication credentials.
     *
     * @access public
     *
     * @param string $userId       The userId to add.
     * @param array  $credentials  The credentials to add.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        $this->_connect();

        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')){
            list($name,$domain)=explode('@',$userId);
            /* Build the SQL query. */
            $query = sprintf('INSERT INTO %s (%s, %s, %s) VALUES (%s, %s, %s)',
                             $this->_params['table'],
                             $this->_params['username_field'],
                             $this->_params['domain_field'],
                             $this->_params['password_field'],
                             $this->_db->quote($name),
                             $this->_db->quote($domain),
                             $this->_db->quote($this->getCryptedPassword($credentials['password'],
                                                                         '',
                                                                         $this->_params['encryption'],
                                                                         $this->_params['show_encryption'])));
            $dbresult = $this->_db->query($query);
            $query = sprintf('INSERT INTO virtual (alias, dest, username, status) VALUES (%s, %s, %s, 1)',
                             $this->_db->quote($userId),
                             $this->_db->quote($name),
                             $this->_db->quote($name));
            $dbresult2 = $this->_db->query($query);
        } else {
            $dbresult = parent::addUser($userId, $credentials);
        }
        if (is_a($dbresult, 'PEAR_Error')) {
            return $dbresult;
        }
        if (is_a($dbresult2, 'PEAR_Error')) {
            return $dbresult2;
        }
	
        $name = imap_utf7_encode($name);
        if (@imap_createmailbox($this->_imapStream,
                                imap_utf7_encode($this->_params['imap_dsn'] .
                                                 'user' . $this->_separator . $name))) {
            @array_walk($this->_params['folders'],
                        array($this, '_createSubFolders'), $name);
        } else {
            Horde::logMessage('IMAP mailbox creation for ' . $name . ' failed ',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return PEAR::raiseError(sprintf(_("IMAP mailbox creation failed: %s"), imap_last_error()));
        }

        if (isset($this->_params['quota']) && $this->_params['quota'] >= 0) {
            if (!@imap_set_quota($this->_imapStream,
                                 'user' . $this->_separator . $name,
                                 $this->_params['quota'])) {
                return PEAR::raiseError(sprintf(_("IMAP mailbox quota creation failed: %s"), imap_last_error()));
            }
        }


        return true;
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
        $this->_connect();

        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')){
            list($name,$domain)=explode('@',$userId);
            /* Build the SQL query. */
            $query = sprintf('DELETE FROM %s WHERE %s = %s and %s = %s',
                         $this->_params['table'],
                         $this->_params['username_field'],
                         $this->_db->quote($name),
                         $this->_params['domain_field'],
                         $this->_db->quote($domain));
            $dbresult = $this->_db->query($query);
            $query = sprintf('DELETE FROM virtual WHERE dest = %s',
                             $this->_db->quote($name));
            $dbresult2 = $this->_db->query($query); 
        } else {
            $dbresult = parent::removeUser($userId);
        }

        if (is_a($dbresult, 'PEAR_Error')) {
            return $dbresult;
        }

        if (is_a($dbresult2, 'PEAR_Error')) {
            return $dbresult2;
        }

        /* Set ACL for mailbox deletion. */
        list($admin)=explode('@',$this->_params['cyradmin']);
        @imap_setacl($this->_imapStream,
                     'user' . $this->_separator . $name,
                     $admin, 'lrswipcda');

        /* Delete IMAP mailbox. */
        $imapresult = @imap_deletemailbox($this->_imapStream,
                                          $this->_params['imap_dsn'] .
                                          'user' . $this->_separator . $name);

        if (!$imapresult) {
            return PEAR::raiseError(sprintf(_("IMAP mailbox deletion failed: %s"), imap_last_error()));
        }

        return true;
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
        if (!$this->_connected) {
            parent::_connect();

            // Reset the $_connected flag; we haven't yet successfully
            // opened everything.
            $this->_connected = false;

            $this->_imapStream = @imap_open($this->_params['imap_dsn'], $this->_params['cyradmin'], $this->_params['cyrpass'], OP_HALFOPEN);
            if (!$this->_imapStream) {
                Horde::fatal(PEAR::raiseError(sprintf(_("Can't connect to IMAP server: %s"), imap_last_error())), __FILE__, __LINE__);
            }

            if (!empty($this->_params['unixhier'])) {
                $this->_separator = '/';
            }
            $this->_connected = true;
        }

        return true;
    }

    /**
     * Disconnect from the SQL and IMAP servers and clean up the
     * connections.
     *
     * @access private
     *
     * @return boolean  True on success, false on failure.
     */
    function _disconnect()
    {
        if ($this->_connected) {
            parent::_disconnect();
            @imap_close($this->_imapStream);
        }

        return true;
    }

    /**
     * Creates all mailboxes supllied in configuration
     *
     * @access private
     */
    function _createSubFolders($value, $key, $userName)
    {
        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')){
            list($name,$domain)=explode('@',$userName);
            @imap_createmailbox($this->_imapStream,
                           	    imap_utf7_encode($this->_params['imap_dsn'] .
                                                 'user' . $this->_separator . $name .
                                                 $this->_separator . $value . '@' . $domain));
        } else {
            @imap_createmailbox($this->_imapStream,
                                imap_utf7_encode($this->_params['imap_dsn'] .
                                                 'user' . $this->_separator . $userName .
                                                 $this->_separator . $value));
        }
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

        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')){
            /* Build the SQL query with domain. */
            $query = sprintf('SELECT %s , %s FROM %s ORDER BY %s',
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

        $result = $this->_db->getAll($query, null, DB_FETCHMODE_ORDERED);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Loop through and build return array. */
        $users = array();
        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')){
            foreach ($result as $ar) {
                $users[] = $ar[0] . '@' . $ar[1];
            }
        } else {
            foreach ($result as $ar) {
                $users[] = $ar[0];
            }
        }

        return $users;
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

        if (!empty($this->_params['domain_field']) &&
            ($this->_params['domain_field'] != 'none')){
            list($name,$domain)=explode('@',$oldID);
            /* Build the SQL query with domain. */
            $query = sprintf('UPDATE %s SET %s = %s WHERE %s = %s and %s = %s',
                             $this->_params['table'],
                             $this->_params['password_field'],
                             $this->_db->quote($this->getCryptedPassword($credentials['password'],
                                                                         '',
                                                                         $this->_params['encryption'],
                                                                         $this->_params['show_encryption'])),
                             $this->_params['username_field'],
                             $this->_db->quote($name),
                             $this->_params['domain_field'],
                             $this->_db->quote($domain));
        } else {
            /* Build the SQL query. */
            $query = sprintf('UPDATE %s SET %s = %s WHERE %s = %s',
                             $this->_params['table'],
                             $this->_params['password_field'],
                             $this->_db->quote($this->getCryptedPassword($credentials['password'],
                                                                         '',
                                                                         $this->_params['encryption'],
                                                                         $this->_params['show_encryption'])),
                             $this->_params['username_field'],
                             $this->_db->quote($oldID));
        }

        return $this->_db->query($query);
    }

}
