<?php
/**
 * PostgreSQL Session Handler for PHP (native).
 *
 * Copyright 2000-2004 Jon Parise <jon@csh.rit.edu>.  All rights reserved.
 *
 *  Redistribution and use in source and binary forms, with or without
 *  modification, are permitted provided that the following conditions
 *  are met:
 *  1. Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *  2. Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
 *  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 *  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 *  ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
 *  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 *  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 *  OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 *  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 *  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 *  OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 *  SUCH DAMAGE.
 *
 * <pre>
 * Required values for $params:
 *     'database'  --  The name of the database.
 *     'password'  --  The password associated with 'username'.
 *     'protocol'  --  The communication protocol ('tcp', 'unix').
 *     'username'  --  The username with which to connect to the database.
 *
 * Required for some configurations (i.e. 'protocol' = 'tcp'):
 *     'hostspec'  --  The hostname of the database server.
 *     'port'      --  The port on which to connect to the database.
 *
 * Optional parameters:
 *     'persistent'  --  Use persistent DB connections? (boolean)
 *                       Default: NO
 *     'table'       --  The name of the sessiondata table in 'database'.
 *                       Default: 'horde_sessionhandler'
 * </pre>
 *  
 * The table structure can be created by the
 * scripts/db/pgsql_sessionhandler.sql script.
 *
 * Contributors:
 *  Jason Carlson           Return an empty string on failed reads
 *  pat@pcprogrammer.com    Perform update in a single transaction
 *  Jonathan Crompton       Lock row for life of session
 *
 * $Horde: framework/SessionHandler/SessionHandler/pgsql.php,v 1.11 2004/01/01 15:14:28 jan Exp $
 *
 * @author  Jon Parise <jon@csh.rit.edu>
 * @version 1.10, 9/11/02
 * @since   Horde 3.0
 * @package Horde_SessionHandler
 */
class SessionHandler_pgsql extends SessionHandler {

    /** Hash containing connection parameters. */
    var $_params = array();

    /** Handle for the current database connection.
        @var resource $_db */
    var $_db;

    /**
     * Boolean indicating whether or not we're connected to the SQL
     * server. */
    var $_connected = false;

    /**
     * Constructs a new PostgreSQL SessionHandler object.
     *
     * @param array  $params    A hash containing connection parameters.
     */
    function SessionHandler_pgsql($params = array())
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

        $expired = time() - ini_get('session.gc_maxlifetime');
        $squery = sprintf('BEGIN; SELECT session_data FROM %s WHERE session_id = %s AND session_lastmodified >= %s FOR UPDATE;',
                         $this->_params['table'], $this->quote($id), $expired);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_pgsql::read(): query = "%s"', $squery),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = @pg_exec($this->_db, $squery);
        if (pg_numrows($result) < 1) {
            pg_freeresult($result);

            $iquery = sprintf('INSERT INTO %s VALUES (%s, %s, \'\')',
                             $this->_params['table'], $this->quote($id), time());
            $result = @pg_exec($this->_db, $iquery);

            $result = @pg_exec($this->_db, $squery);
        }

        $data = pg_result($result, 0, 'session_data');
        pg_freeresult($result);

        return $data;
    }

    function write($id, $session_data)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf('UPDATE %s SET session_lastmodified = %s, session_data = %s WHERE session_id = %s; commit;',
                         $this->_params['table'],
                         time(),
                         $this->quote($session_data),
                         $this->quote($id));

        $result = @pg_exec($this->_db, $query);
        $success = (pg_cmdtuples($result) == 0);
        pg_freeresult($result);

        if (!$success){
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
        $query = sprintf('DELETE FROM %s WHERE session_id = %s; commit;',
                         $this->_params['table'], $this->quote($id));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_pgsql::destroy(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = @pg_exec($this->_db, $query);
        if (!$result) {
            pg_freeresult($result);
            Horde::logMessage('Failed to delete session (id = ' . $id . ')', __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        pg_freeresult($result);
        return true;
    }

    function gc($maxlifetime = 300)
    {
        /* Make sure we have a valid database connection. */
        $this->_connect();

        /* Build the SQL query. */
        $query = sprintf('DELETE FROM %s WHERE session_lastmodified < %s',
                         $this->_params['table'], $this->quote(time() - $maxlifetime));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_pgsql::gc(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = @pg_exec($this->_db, $query);
        if (!$result) {
            pg_freeresult($result);
            Horde::logMessage('Error garbage collecting old sessions', __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        pg_freeresult($result);
        return $result;
    }

    function quote($value)
    {
        return "'" . addslashes($value) . "'";
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
                array('hostspec', 'username', 'database', 'password'),
                'session handler pgsql');

            if (!array_key_exists('table', $this->_params)) {
                $this->_params['table'] = 'horde_sessionhandler';
            }

            $connect = (empty($this->_params['persistent'])) ? 'pg_connect' :'pg_pconnect';

            $paramstr = '';
            if ($tcp_protocol) {
                $paramstr .= ' host=' . $this->_params['hostspec'];
                $paramstr .= ' port=' . $this->_params['port'];
            }
            $paramstr .= ' dbname=' . $this->_params['database'];
            $paramstr .= ' user=' . $this->_params['username'];
            $paramstr .= ' password=' . $this->_params['password'];

            if (!$this->_db = @$connect($paramstr)) {
                return false;
            }

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
            return @pg_close($this->_db);
        }

        return true;
    }

}
