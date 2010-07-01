<?php
/**
 * PostgreSQL Session Handler for PHP (native).
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * Required parameters:<pre>
 *   'database' - (string) The name of the database.
 *   'password' - (string) The password associated with 'username'.
 *   'protocol' - (string) The communication protocol ('tcp', 'unix').
 *   'username' - (string) The username with which to connect to the database.
 *
 * Required for some configurations (i.e. 'protocol' = 'tcp'):<pre>
 *   'hostspec' - (string) The hostname of the database server.
 *   'port'     - (integer) The port on which to connect to the database.
 * </pre>
 *
 * Optional parameters:<pre>
 *   'persistent' - (boolean) Use persistent DB connections?
 *                  Default: NO
 *   'table'      - (string) The name of the sessiondata table in 'database'.
 *                  Default: 'horde_sessionhandler'</pre>
 * </pre>

 * The table structure for the SessionHandler can be found in
 * horde/scripts/sql/horde_sessionhandler.pgsql.sql.
 *
 * Contributors:<pre>
 *  Jason Carlson           Return an empty string on failed reads
 *  pat@pcprogrammer.com    Perform update in a single transaction
 *  Jonathan Crompton       Lock row for life of session</pre>
 *
 * $Horde: framework/SessionHandler/SessionHandler/pgsql.php,v 1.12.10.22 2009-09-25 14:29:09 jan Exp $
 *
 * @author  Jon Parise <jon@csh.rit.edu>
 * @package Horde_SessionHandler
 */
class SessionHandler_pgsql extends SessionHandler {

    /**
     * Handle for the current database connection.
     *
     * @var resource
     */
    var $_db;

    /**
     * Attempts to open a connection to the SQL server.
     *
     * @access private
     *
     * @param string $save_path     The path to the session object.
     * @param string $session_name  The name of the session.
     *
     * @return boolean  True on success; PEAR_Error on failure.
     */
    function _open($save_path = null, $session_name = null)
    {
        Horde::assertDriverConfig($this->_params, 'sessionhandler',
                                  array('hostspec', 'username', 'database', 'password'),
                                  'session handler pgsql');

        if (empty($this->_params['table'])) {
            $this->_params['table'] = 'horde_sessionhandler';
        }

        $connect = empty($this->_params['persistent']) ?
            'pg_connect' :'pg_pconnect';

        $paramstr = '';
        if (isset($this->_params['protocol']) &&
            $this->_params['protocol'] == 'tcp') {
            $paramstr .= ' host=' . $this->_params['hostspec'];
            if (isset($this->_params['port'])) {
                $paramstr .= ' port=' . $this->_params['port'];
            }
        }
        $paramstr .= ' dbname=' . $this->_params['database'] .
            ' user=' . $this->_params['username'] .
            ' password=' . $this->_params['password'];

        if (!$this->_db = @$connect($paramstr)) {
            return PEAR::raiseError(sprintf('Could not connect to database %s for SQL SessionHandler.', $this->_params['database']));
        }

        return true;
    }

    /**
     * Close the SessionHandler backend.
     *
     * @access private
     *
     * @return boolean  True on success, false otherwise.
     */
    function _close()
    {
        /* Disconnect from database. */
        return @pg_close($this->_db);
    }

    /**
     * Read the data for a particular session identifier from the
     * SessionHandler backend.
     *
     * @access private
     *
     * @param string $id  The session identifier.
     *
     * @return string  The session data.
     */
    function _read($id)
    {
        @pg_query($this->_db, 'BEGIN;');

        $query = sprintf('SELECT session_data FROM %s WHERE session_id = %s ' .
                         'FOR UPDATE;',
                         $this->_params['table'],
                         $this->_quote($id));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_pgsql::' .
                                  '_read(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = @pg_query($this->_db, $query);
        $data = pg_fetch_result($result, 0, 'session_data');
        pg_free_result($result);

        return pack('H*', $data);
    }

    /**
     * Write session data to the SessionHandler backend.
     *
     * @access private
     *
     * @param string $id            The session identifier.
     * @param string $session_data  The session data.
     *
     * @return boolean  True on success, false otherwise.
     */
    function _write($id, $session_data)
    {
        $query = sprintf('SELECT session_data FROM %s WHERE session_id = %s ' .
                         'FOR UPDATE',
                         $this->_params['table'],
                         $this->_quote($id));
        $result = @pg_query($this->_db, $query);
        $rows = pg_num_rows($result);
        pg_free_result($result);

        if ($rows == 0) {
            $query = sprintf('INSERT INTO %s (session_id, ' .
                             'session_lastmodified, session_data) ' .
                             'VALUES (%s, %s, %s);',
                             $this->_params['table'],
                             $this->_quote($id),
                             time(),
                             $this->_quote(bin2hex($session_data)));
        } else {
            $query = sprintf('UPDATE %s SET session_lastmodified = %s, ' .
                             'session_data = %s WHERE session_id = %s;',
                             $this->_params['table'],
                             time(),
                             $this->_quote(bin2hex($session_data)),
                             $this->_quote($id));
        }

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_pgsql::' .
                                  '_write(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = @pg_query($this->_db, $query);
        $rows = pg_affected_rows($result);
        pg_free_result($result);

        @pg_query($this->_db, 'COMMIT;');

        if ($rows != 1) {
            Horde::logMessage('Error writing session data',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        return true;
    }

    /**
     * Destroy the data for a particular session identifier in the
     * SessionHandler backend.
     *
     * @param string $id  The session identifier.
     *
     * @return boolean  True on success, false otherwise.
     */
    function destroy($id)
    {
        /* Build the SQL query. */
        $query = sprintf('DELETE FROM %s WHERE session_id = %s;',
                         $this->_params['table'], $this->_quote($id));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_pgsql::' .
                                  'destroy(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = @pg_query($this->_db, $query);

        @pg_query($this->_db, 'COMMIT;');

        if (!$result) {
            pg_free_result($result);
            Horde::logMessage('Failed to delete session (id = ' . $id . ')',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        pg_free_result($result);
        return true;
    }

    /**
     * Garbage collect stale sessions from the SessionHandler backend.
     *
     * @param integer $maxlifetime  The maximum age of a session.
     *
     * @return boolean  True on success, false otherwise.
     */
    function gc($maxlifetime = 300)
    {
        /* Build the SQL query. */
        $query = sprintf('DELETE FROM %s WHERE session_lastmodified < %s',
                         $this->_params['table'],
                         $this->_quote(time() - $maxlifetime));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_pgsql::' .
                                  'gc(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = @pg_query($this->_db, $query);
        if (!$result) {
            Horde::logMessage('Error garbage collecting old sessions',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        pg_free_result($result);
        return $result;
    }

    /**
     * Get a list of the valid session identifiers.
     *
     * @return array  A list of valid session identifiers.
     */
    function getSessionIDs()
    {
        /* Make sure we have a valid database connection. */
        if (!$this->open()) {
            return false;
        }

        /* Build the SQL query. */
        $query = sprintf('SELECT session_id FROM %s ' .
                         'WHERE session_lastmodified >= %s',
                         $this->_params['table'],
                         time() - ini_get('session.gc_maxlifetime'));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_pgsql::' .
                                  'getSessionIDs(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = @pg_query($this->_db, $query);
        if (!$result) {
            pg_free_result($result);
            Horde::logMessage('Error getting session IDs',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        $sessions = array();
        while ($row = pg_fetch_row($result)) {
            $sessions[] = $row[0];
        }

        pg_free_result($result);

        return $sessions;
    }

    /**
     * Escape a string for insertion into the database.
     *
     * @access private
     *
     * @param string $value  The string to quote.
     *
     * @return string  The quoted string.
     */
    function _quote($value)
    {
        return "'" . addslashes($value) . "'";
    }

}
