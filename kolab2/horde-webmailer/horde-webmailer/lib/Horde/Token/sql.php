<?php
/**
 * Token tracking implementation for PHP's PEAR database abstraction layer.
 *
 * Required parameters:<pre>
 *   'phptype'      The database type (ie. 'pgsql', 'mysql', etc.).</pre>
 *
 * Required by some database implementations:<pre>
 *   'database'     The name of the database.
 *   'hostspec'     The hostname of the database server.
 *   'username'     The username with which to connect to the database.
 *   'password'     The password associated with 'username'.
 *   'options'      Additional options to pass to the database.
 *   'tty'          The TTY on which to connect to the database.
 *   'port'         The port on which to connect to the database.</pre>
 *
 * Optional parameters:<pre>
 *   'table'        The name of the tokens table in 'database'.
 *                  Defaults to 'horde_tokens'.
 *   'timeout'      The period (in seconds) after which an id is purged.
 *                  Defaults to 86400 (i.e. 24 hours).</pre>
 *
 * Optional values when using separate reading and writing servers, for example
 * in replication settings:<pre>
 *   'splitread'   Boolean, whether to implement the separation or not.
 *   'read'        Array containing the parameters which are different for
 *                 the read database connection, currently supported
 *                 only 'hostspec' and 'port' parameters.</pre>
 *
 * The table structure for the tokens is as follows:
 *
 * <pre>
 * CREATE TABLE horde_tokens (
 *     token_address    VARCHAR(100) NOT NULL,
 *     token_id         VARCHAR(32) NOT NULL,
 *     token_timestamp  BIGINT NOT NULL,
 *
 *     PRIMARY KEY (token_address, token_id)
 * );
 * </pre>
 *
 * $Horde: framework/Token/Token/sql.php,v 1.23.6.17 2009-02-13 05:45:19 chuck Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Max Kalika <max@horde.org>
 * @since   Horde 1.3
 * @package Horde_Token
 */
class Horde_Token_sql extends Horde_Token {

    /**
     * Handle for the current database connection.
     *
     * @var DB
     */
    var $_db = '';

    /**
     * Handle for the current database connection, used for writing. Defaults
     * to the same handle as $_db if a separate write database is not required.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * Boolean indicating whether or not we're connected to the SQL
     * server.
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * Constructs a new SQL connection object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Horde_Token_sql($params = array())
    {
        $this->_params = $params;

        /* Set timeout to 24 hours if not specified. */
        if (!isset($this->_params['timeout'])) {
            $this->_params['timeout'] = 86400;
        }
    }

    /**
     * Deletes all expired connection id's from the SQL server.
     *
     * @return boolean  True on success, a PEAR_Error object on failure.
     */
    function purge()
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        /* Build SQL query. */
        $query = 'DELETE FROM ' . $this->_params['table']
            . ' WHERE token_timestamp < ?';

        $values = array(time() - $this->_params['timeout']);

        /* Return an error if the update fails. */
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        return true;
    }

    function exists($tokenID)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return false;
        }

        /* Build SQL query. */
        $query = 'SELECT token_id FROM ' . $this->_params['table']
            . ' WHERE token_address = ? AND token_id = ?';

        $values = array($this->encodeRemoteAddress(), $tokenID);

        $result = $this->_db->getOne($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        } else {
            return !empty($result);
        }
    }

    function add($tokenID)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        /* Build SQL query. */
        $query = 'INSERT INTO ' . $this->_params['table']
            . ' (token_address, token_id, token_timestamp)'
            . ' VALUES (?, ?, ?)';

        $values = array($this->encodeRemoteAddress(), $tokenID, time());

        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        return true;
    }

    /**
     * Opens a connection to the SQL server.
     *
     * @return boolean  True on success, a PEAR_Error object on failure.
     */
    function _connect()
    {
        if ($this->_connected) {
            return true;
        }

        $result = Util::assertDriverConfig($this->_params, array('phptype'),
                                           'token SQL', array('driver' => 'token'));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!isset($this->_params['database'])) {
            $this->_params['database'] = '';
        }
        if (!isset($this->_params['username'])) {
            $this->_params['username'] = '';
        }
        if (!isset($this->_params['password'])) {
            $this->_params['password'] = '';
        }
        if (!isset($this->_params['hostspec'])) {
            $this->_params['hostspec'] = '';
        }
        if (!isset($this->_params['table'])) {
            $this->_params['table'] = 'horde_tokens';
        }

        /* Connect to the SQL server using the supplied parameters. */
        require_once 'DB.php';
        $this->_write_db = &DB::connect($this->_params,
                                  array('persistent' => !empty($this->_params['persistent']),
                                        'ssl' => !empty($this->_params['ssl'])));
        if (is_a($this->_write_db, 'PEAR_Error')) {
            return $this->_write_db;
        }

        // Set DB portability options.
        switch ($this->_write_db->phptype) {
        case 'mssql':
            $this->_write_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
            break;
        default:
            $this->_write_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
        }

        /* Check if we need to set up the read DB connection
         * seperately. */
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($this->_params, $this->_params['read']);
            $this->_db = &DB::connect($params,
                                      array('persistent' => !empty($params['persistent']),
                                            'ssl' => !empty($this->_params['ssl'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                return $this->_db;
            }

            // Set DB portability options.
            switch ($this->_db->phptype) {
            case 'mssql':
                $this->_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
                break;
            default:
                $this->_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
            }

        } else {
            /* Default to the same DB handle for read. */
            $this->_db = $this->_write_db;
        }

        $this->_connected = true;
        return true;
    }

}
