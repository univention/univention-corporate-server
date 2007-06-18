<?php
/**
 * SessionHandler:: implementation for Oracle 8i (native).
 *
 * Required values for $params:<pre>
 *     'hostspec'  --  The hostname of the database server.
 *     'protocol'  --  The communication protocol ('tcp', 'unix', etc.).
 *     'username'  --  The username with which to connect to the database.
 *     'password'  --  The password associated with 'username'.
 *     'database'  --  The name of the database.
 *     'table'     --  The name of the sessiondata table in 'database'.</pre>
 *
 * Required for some configurations:
 *     'port'  --  The port on which to connect to the database.
 *
 * Optional parameters:
 *     'persistent'  --  Use persistent DB connections? (boolean)
 *
 * The table structure can be created by the scripts/db/sessionhandler.sql
 * script.
 *
 * $Horde: framework/SessionHandler/SessionHandler/oci8.php,v 1.7 2004/01/01 15:14:28 jan Exp $
 *
 * Copyright 2003-2004 Liam Hoekenga <liamr@umich.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Liam Hoekenga <liamr@umich.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package Horde_SessionHandler
 */
class SessionHandler_oci8 extends SessionHandler {

    /**
     * Hash containing connection parameters.
     *
     * @var array $_params
     */
    var $_params = array();

    /**
     * Handle for the current database connection.
     *
     * @var resource $_db
     */
    var $_db;

    /**
     * Are we connected to the SQL server.
     *
     * @var boolean $_connected
     */
    var $_connected = false;

    /**
     * The quote function to use.
     *
     * @var string $_quote
     */
    var $_quote = null;

    /**
     * Constructs a new Oracle8 SessionHandler object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     *                                See details above.
     */
    function SessionHandler_oci8($params = array())
    {
        $this->_params = $params;
    }

    function open($save_path, $session_name)
    {
        /* Connect to database. */
        $this->_connect();
    }

    function close()
    {
        /* Disconnect from database. */
        $this->_disconnect();
    }

    function read($id)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        $select_query = sprintf('SELECT session_data FROM %s WHERE session_id = %s',
                $this->_params['table'], $this->_quote($id));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_oci8::read(): query = "%s"', $select_query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute query */
        $select_statement = OCIParse($this->_db, $select_query);
        OCIExecute($select_statement);
        if (!OCIFetchInto($select_statement, $result)) {
            $insert_query = sprintf('INSERT INTO %s (session_id, session_lastmodified, session_data) VALUES (%s, %s, EMPTY_BLOB()) RETURNING session_data INTO :blob',
                    $this->_params['table'],
                    $this->_quote($id),
                    $this->_quote(time()));
            $insert_statement = OCIParse($this->_db, $insert_query);
            $lob = OCINewDescriptor($this->_db);
            OCIBindByName($insert_statement, ':blob', $lob, -1, SQLT_BLOB);
            OCIExecute($insert_statement, OCI_DEFAULT);
            if ($session_data) {
                $lob->save($session_data);
            }
            $result = OCICommit($this->_db);
            OCIFreeStatement($insert_statement);
            OCIExecute($select_statement);
            OCIFetchInto($select_statement, $result);
        }
        $value = $result[0]->load();
        OCIFreeStatement($select_statement);
        return($value);
    }

    function write($id, $session_data)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Build the SQL query. */
        /* there has to be a better way to to do this... */
        $query = sprintf('UPDATE %s SET session_lastmodified = %s, session_data = EMPTY_BLOB() WHERE session_id = %s RETURNING session_data INTO :blob',
                $this->_params['table'],
                $this->_quote(time()),
                $this->_quote($id));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_oci8::write(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute query */
        $statement = OCIParse($this->_db, $query);
        $lob = OCINewDescriptor($this->_db);
        OCIBindByName($statement, ':blob', $lob, -1, SQLT_BLOB);
        OCIExecute($statement, OCI_DEFAULT);
        if ($session_data) {
            $lob->save($session_data);
        }
        $result = OCICommit($this->_db);
        if (!$result){
            Horde::logMessage('Error writing session data', __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        return true;
    }

    function destroy($id)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf( 'DELETE FROM %s WHERE session_id = %s',
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

    function gc($maxlifetime = 1)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

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
     * Escape a string for insertion.   stolen from PEAR::DB
     * @access private
     *
     * @param string $value  The string to quote.
     *
     * @return string  The quoted string.
     */
    function _quote($value)
    {
        return ($value === null) ? 'NULL' : "'" . str_replace("'", "''", $value) . "'";
    }

    /**
     * Attempts to open a connection to the SQL server.
     *
     * @access private
     */
    function _connect()
    {
        if ($this->_connected) {
            return;
        }

        Horde::assertDriverConfig($this->_params, 'sessionhandler',
            array('hostspec', 'username', 'database', 'password'),
            'session handler Oracle');

        if (!array_key_exists('table', $this->_params)) {
            $this->_params['table'] = 'horde_sessionhandler';
        }

        if (empty($this->_params['persistent'])) {
            $connect = 'OCILogon';
        } else {
            $connect = 'OCIPLogon';
        }

        if (!$this->_db = @$connect($this->_params['username'],
                                    $this->_params['password'],
                                    $this->_params['hostspec'])) {
            Horde::fatal(PEAR::raiseError('Could not connect to database for SQL SessionHandler.'), __FILE__, __LINE__);
        }

        $this->_connected = true;
    }

    /**
     * Disconnect from the SQL server and clean up the connection.
     *
     * @access private
     */
    function _disconnect()
    {
        if ($this->_connected) {
            return OCILogOff($this->_db);
        }
        $this->_connected = false;
    }

}
