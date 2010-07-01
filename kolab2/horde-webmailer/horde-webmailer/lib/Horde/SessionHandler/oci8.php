<?php
/**
 * SessionHandler:: implementation for Oracle 8i (native).
 *
 * Required parameters:<pre>
 *   'hostspec' - (string) The hostname of the database server.
 *   'username' - (string) The username with which to connect to the database.
 *   'password' - (string) The password associated with 'username'.
 *   'database' - (string) The name of the database.
 *   'table'    - (string) The name of the sessiondata table in 'database'.
 * </pre>
 *
 * Required for some configurations:<pre>
 *   'port' - (integer) The port on which to connect to the database.
 * </pre>
 *
 * Optional parameters:<pre>
 *   'persistent' - (boolean) Use persistent DB connections?
 * </pre>

 * The table structure for the SessionHandler can be found in
 * horde/scripts/sql/horde_sessionhandler.oci8.sql.
 *
 * $Horde: framework/SessionHandler/SessionHandler/oci8.php,v 1.8.4.16 2008-09-02 21:36:43 slusarz Exp $
 *
 * Copyright 2003-2007 Liam Hoekenga <liamr@umich.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Liam Hoekenga <liamr@umich.edu>
 * @package Horde_SessionHandler
 */
class SessionHandler_oci8 extends SessionHandler {

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
     * @return boolean  True on success, false on error.
     */
    function _open($save_path = false, $session_name = false)
    {
        Horde::assertDriverConfig($this->_params, 'sessionhandler',
            array('hostspec', 'username', 'password'),
            'session handler Oracle');

        if (!isset($this->_params['table'])) {
            $this->_params['table'] = 'horde_sessionhandler';
        }

        if (function_exists('oci_connect')) {
            if (empty($this->_params['persistent'])) {
                $connect = 'oci_connect';
            } else {
                $connect = 'oci_pconnect';
            }
        } else {
            if (empty($this->_params['persistent'])) {
                $connect = 'OCILogon';
            } else {
                $connect = 'OCIPLogon';
            }
        }

        if (!is_resource($this->_db = @$connect($this->_params['username'],
                                                $this->_params['password'],
                                                $this->_params['hostspec']))) {
            return PEAR::raiseError('Could not connect to database for SQL SessionHandler.');
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
        return OCILogOff($this->_db);
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
        $select_query = sprintf('SELECT session_data FROM %s WHERE session_id = %s FOR UPDATE',
                                $this->_params['table'], $this->_quote($id));

        Horde::logMessage(sprintf('SQL Query by SessionHandler_oci8::_read(): query = "%s"', $select_query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $select_statement = OCIParse($this->_db, $select_query);
        OCIExecute($select_statement, OCI_DEFAULT);
        if (OCIFetchInto($select_statement, $result)) {
            $value = $result[0]->load();
        } else {
            $value = '';
        }

        OCIFreeStatement($select_statement);
        return $value;
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
        $select_query = sprintf('SELECT session_data FROM %s WHERE session_id = %s FOR UPDATE',
                                $this->_params['table'], $this->_quote($id));

        Horde::logMessage(sprintf('SQL Query by SessionHandler_oci8::_write(): query = "%s"', $select_query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $select_statement = OCIParse($this->_db, $select_query);
        OCIExecute($select_statement, OCI_DEFAULT);
        if (OCIFetchInto($select_statement, $result)) {
            /* Discard the existing LOB contents. */
            if (!$result[0]->truncate()) {
                OCIRollback($this->_db);
                return false;
            }

            /* Save the session data. */
            if ($result[0]->save($session_data)) {
                OCICommit($this->_db);
                OCIFreeStatement($select_statement);
            } else {
                OCIRollback($this->_db);
                return false;
            }
        } else {
            $insert_query = sprintf('INSERT INTO %s (session_id, session_lastmodified, session_data) VALUES (%s, %s, EMPTY_BLOB()) RETURNING session_data INTO :blob',
                                    $this->_params['table'],
                                    $this->_quote($id),
                                    $this->_quote(time()));

            Horde::logMessage(sprintf('SQL Query by SessionHandler_oci8::_read(): query = "%s"', $insert_query),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $insert_statement = OCIParse($this->_db, $insert_query);
            $lob = OCINewDescriptor($this->_db);
            OCIBindByName($insert_statement, ':blob', $lob, -1, SQLT_BLOB);
            OCIExecute($insert_statement, OCI_DEFAULT);
            if (!$lob->save($session_data)) {
                OCIRollback($this->_db);
                return false;
            }
            OCICommit($this->_db);
            OCIFreeStatement($insert_statement);
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
        $query = sprintf('DELETE FROM %s WHERE session_id = %s',
                         $this->_params['table'], $this->_quote($id));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_oci8::destroy(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $statement = OCIParse($this->_db, $query);
        $result = OCIExecute($statement);
        if (!$result) {
            OCIFreeStatement($statement);
            Horde::logMessage('Failed to delete session (id = ' . $id . ')', __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        OCIFreeStatement($statement);
        return true;
    }

    /**
     * Garbage collect stale sessions from the SessionHandler backend.
     *
     * @param integer $maxlifetime  The maximum age of a session.
     *
     * @return boolean  True on success, false otherwise.
     */
    function gc($maxlifetime = 1)
    {
        /* Build the SQL query. */
        $query = sprintf('DELETE FROM %s WHERE session_lastmodified < %s',
                         $this->_params['table'], $this->_quote(time() - $maxlifetime));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_oci8::gc(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $statement = OCIParse($this->_db, $query);
        $result = OCIExecute($statement);
        if (!$result) {
            OCIFreeStatement($statement);
            Horde::logMessage('Error garbage collecting old sessions', __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        OCIFreeStatement($statement);
        return true;
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

        /* Session timeout, don't rely on garbage collection */

        $query = sprintf('SELECT session_id FROM %s ' .
                         'WHERE session_lastmodified >= %s',
                         $this->_params['table'],
                         time() - ini_get('session.gc_maxlifetime'));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_oci8::getSessionIDs(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute query */
        $statement = OCIParse($this->_db, $query);
        OCIExecute($statement);

        $sessions = array();
        while (OCIFetchInto($statement, $row)) {
            $sessions[] = $row[0];
        }

        OCIFreeStatement($statement);
        return $sessions;
    }

    /**
     * Escape a string for insertion. Stolen from PEAR::DB.
     *
     * @access private
     *
     * @param string $value  The string to quote.
     *
     * @return string  The quoted string.
     */
    function _quote($value)
    {
        return (is_null($value)) ? 'NULL' : "'" . str_replace("'", "''", $value) . "'";
    }

}
