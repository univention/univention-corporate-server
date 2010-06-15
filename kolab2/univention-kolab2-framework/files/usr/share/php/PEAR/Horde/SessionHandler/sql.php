<?php
/**
 * SessionHandler implementation for PHP's PEAR database abstraction layer.
 *
 * Required values for $params:<pre>
 *     'phptype'   --  The database type (e.g. 'pgsql', 'mysql', etc.).
 *     'hostspec'  --  The hostname of the database server.
 *     'protocol'  --  The communication protocol ('tcp', 'unix', etc.).
 *     'username'  --  The username with which to connect to the database.
 *     'password'  --  The password associated with 'username'.
 *     'database'  --  The name of the database.
 *     'table'     --  The name of the sessiondata table in 'database'.</pre>
 *
 * Required by some database implementations:
 *     'options'  --   Additional options to pass to the database.
 *     'tty'      --   The TTY on which to connect to the database.
 *     'port'     --   The port on which to connect to the database.
 *
 * Optional parameters:
 *     'persistent'  --  Use persistent DB connections? (boolean)
 *
 * Ths table structure can be created by the scripts/db/sessionhandler.sql
 * script.
 *
 * $Horde: framework/SessionHandler/SessionHandler/sql.php,v 1.21 2004/04/07 14:43:13 chuck Exp $
 *
 * Copyright 2002-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_SessionHandler
 */
class SessionHandler_sql extends SessionHandler {

    /** Hash containing connection parameters. */
    var $_params = array();

    /** Handle for the current database connection.
        @var object DB $_db */
    var $_db;

    /**
     * Boolean indicating whether or not we're connected to the SQL
     * server. */
    var $_connected = false;

    /**
     * Constructs a new SQL SessionHandler object.
     *
     * @param array  $params    A hash containing connection parameters.
     */
    function SessionHandler_sql($params = array())
    {
        $this->_params = $params;
    }

    function open($save_path, $session_name)
    {
        /* Connect to database */
        $this->_connect();
    }

    function close()
    {
        /* Disconnect from Database */
        $this->_disconnect();
    }

    function read($id)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        require_once 'Horde/SQL.php';

        /* Execute the query. */
        $result = Horde_SQL::readBlob($this->_db, $this->_params['table'], 'session_data',
                                      array('session_id' => $id));

        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return '';
        }

        return $result;
    }

    function write($id, $session_data)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf('SELECT session_id FROM %s WHERE session_id = %s',
                         $this->_params['table'], $this->_db->quote($id));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_sql::write(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = $this->_db->getOne($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        require_once 'Horde/SQL.php';
        if ($result) {
            $result = Horde_SQL::updateBlob($this->_db, $this->_params['table'], 'session_data',
                                            $session_data, array('session_id' => $id),
                                            array('session_lastmodified' => time()));
        } else {
            $result = Horde_SQL::insertBlob($this->_db, $this->_params['table'], 'session_data',
                                            $session_data, array('session_id' => $id,
                                                                 'session_lastmodified' => time()));
        }

        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        return true;
    }

    function destroy($id)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf('DELETE FROM %s WHERE session_id = %s',
                         $this->_params['table'], $this->_db->quote($id));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_sql::destroy(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        return true;
    }

    function gc($maxlifetime = 300)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf('DELETE FROM %s WHERE session_lastmodified < %s',
                         $this->_params['table'], $this->_db->quote(time() - $maxlifetime));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_sql::gc(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        return true;
    }

    /**
     * Attempts to open a connection to the SQL server.
     *
     * @return boolean  True on success; exits (Horde::fatal()) on error.
     */
    function _connect()
    {
        if (!$this->_connected) {
            Horde::assertDriverConfig($this->_params, 'sessionhandler',
                array('phptype', 'hostspec', 'username', 'database', 'password'),
                'session handler SQL');

            if (empty($this->_params['table'])) {
                $this->_params['table'] = 'horde_sessionhandler';
            }

            /* Connect to the SQL server using the supplied
             * parameters. */
            include_once 'DB.php';
            $this->_db = &DB::connect($this->_params,
                                      array('persistent' => !empty($this->_params['persistent'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                Horde::fatal($this->_db, __FILE__, __LINE__);
            }

            /* Enable the "portability" option. */
            $this->_db->setOption('optimize', 'portability');

            $this->_connected = true;
        }

        return true;
    }

    /**
     * Disconnect from the SQL server and clean up the connection.
     *
     * @return boolean     true on success, false on failure.
     */
    function _disconnect()
    {
        if ($this->_connected) {
            $this->_connected = false;
            return $this->_db->disconnect();
        }

        return true;
    }

}
