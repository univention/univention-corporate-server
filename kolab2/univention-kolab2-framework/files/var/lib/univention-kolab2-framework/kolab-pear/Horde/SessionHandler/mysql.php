<?php
/**
 * SessionHandler:: implementation for MySQL (native).
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
 * $Horde: framework/SessionHandler/SessionHandler/mysql.php,v 1.16 2004/01/01 15:14:28 jan Exp $
 *
 * Copyright 2002-2004 Mike Cochrane <mike@graftonhall.co.nz>
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrame <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_SessionHandler
 */
class SessionHandler_mysql extends SessionHandler {

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
     * Constructs a new MySQL SessionHandler object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     *                                See details above.
     */
    function SessionHandler_mysql($params = array())
    {
        $this->_params = $params;
    }

    /**
     * TODO
     */
    function open($save_path, $session_name)
    {
        /* Connect to database. */
        $this->_connect();
    }

    /**
     * TODO
     */
    function close()
    {
        /* Disconnect from database. */
        $this->_disconnect();
    }

    /**
     * TODO
     */
    function read($id)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Session timeout, don't rely on garbage collection */
        $timeout = time() - ini_get('session.gc_maxlifetime');

        $query = sprintf('SELECT session_data FROM %s WHERE session_id = %s' .
                         ' AND session_lastmodified > %s',
                         $this->_params['table'],
                         $this->_quote($id),
                         $timeout);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_mysql::read(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = @mysql_query($query, $this->_db);
        if (!$result){
            Horde::logMessage('Error retrieving session data (id = ' . $id . ')',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return '';
        }
            list($value) = mysql_fetch_row($result);
            return $value;
    }

    /**
     * TODO
     */
    function write($id, $session_data)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf('REPLACE INTO %s (session_id, session_data, session_lastmodified)' .
                         ' VALUES (%s, %s, %s)',
                         $this->_params['table'],
                         $this->_quote($id),
                         $this->_quote($session_data),
                         time());

        $result = mysql_query($query, $this->_db);
        if (!$result){
            Horde::logMessage('Error writing session data', __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        return true;
    }

    /**
     * TODO
     */
    function destroy($id)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf('DELETE FROM %s WHERE session_id = %s',
                         $this->_params['table'], $this->_quote($id));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_mysql::destroy(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = @mysql_query($query, $this->_db);
        if (!$result) {
            Horde::logMessage('Failed to delete session (id = ' . $id . ')', __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        return true;
    }

    /**
     * TODO
     */
    function gc($maxlifetime = 300)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf('DELETE FROM %s WHERE session_lastmodified < %s',
                         $this->_params['table'], (int)(time() - $maxlifetime));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_mysql::gc(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = @mysql_query($query, $this->_db);
        if (!$result) {
            Horde::logMessage('Error garbage collecting old sessions', __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        return @mysql_affected_rows($this->_db);
    }

    /**
     * Escape a mysql string.
     *
     * @access private
     *
     * @param string $value  The string to quote.
     *
     * @return string  The quoted string.
     */
    function _quote($value)
    {
        switch (strtolower(gettype($value))) {
        case 'null':
            return 'NULL';

        case 'integer':
            return $value;

        case 'string':
        default:
            return "'" . mysql_real_escape_string($value) . "'";
        }
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
            'session handler MySQL');

        if (empty($this->_params['table'])) {
            $this->_params['table'] = 'horde_sessionhandler';
        }

        if (empty($this->_params['persistent'])) {
            $connect = 'mysql_connect';
        } else {
            $connect = 'mysql_pconnect';
        }

        if (!$this->_db = @$connect($this->_params['hostspec'],
                                    $this->_params['username'],
                                    $this->_params['password'])) {
            Horde::fatal(PEAR::raiseError('Could not connect to database for SQL SessionHandler.'), __FILE__, __LINE__);
        }

        if (!@mysql_select_db($this->_params['database'], $this->_db)) {
            Horde::fatal(PEAR::raiseError(sprintf('Could not connect to table %s for SQL SessionHandler.', $this->_params['database']), __FILE__, __LINE__));
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
            return @mysql_close($this->_db);
        }
        $this->_connected = false;
    }

}
