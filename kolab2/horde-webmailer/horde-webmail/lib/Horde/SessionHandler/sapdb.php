<?php

require_once dirname(__FILE__) . '/sql.php';

/**
 * SessionHandler implementation for PHP's PEAR database abstraction layer.
 *
 * If you access your database through ODBC, you will almost certainly need
 * to change PHP's default value for odbc.defaultlrl (this is a php.ini
 * setting). The default is 4096, which is too small (your session data will
 * be chopped off), and setting it to 0 DOES NOT work - that doesn't mean no
 * limit, for some reason. odbc.defaultlrl = 32768 seems to work pretty well
 * (using MSSQL-2000).
 *
 * Required parameters:<pre>
 *   'hostspec' - (string) The hostname of the database server.
 *   'username' - (string) The username with which to connect to the database.
 *   'password' - (string) The password associated with 'username'.
 *   'database' - (string) The name of the database.
 * </pre>
 *
 * Optional parameters:<pre>
 *   'table' - (string) The name of the sessiondata table in 'database'.
 *             DEFAULT: 'horde_sessionhandler'
 * </pre>
 *
 * The table structure for the SessionHandler can be found in
 * horde/scripts/sql/horde_sessionhandler.sapdb.sql.
 *
 * $Horde: framework/SessionHandler/SessionHandler/sapdb.php,v 1.13.12.12 2009-01-06 15:23:35 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Horde_SessionHandler
 */
class SessionHandler_sapdb extends SessionHandler_sql {

    /**
     * Constructs a new SQL SessionHandler object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function SessionHandler_sapdb($params = array())
    {
        $params['phptype'] = 'odbc';
        parent::SessionHandler_sql($params);
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
        /* Begin a transaction. */
        $result = $this->_db->autocommit(false);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return '';
        }

        /* Build the SQL query. */
        $query = sprintf('SELECT session_data FROM %s WHERE session_id = %s',
                         $this->_params['table'],
                         $this->_db->quote($id));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by SessionHandler_sapdb::_read(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query */
        $result = odbc_exec($this->_db->connection, $query);
        odbc_longreadlen($result, 1048576);

        /* Fetch the value */
        odbc_fetch_row($result, 0);
        $data = odbc_result($result, 'session_data');

        /* Clean up */
        odbc_free_result($result);

        return $data;
    }

}
