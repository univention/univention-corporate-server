<?php
/**
 * Token tracking implementation for PHP's PEAR database abstraction
 * layer.
 *
 * Required values for $params:
 *      'phptype'       The database type (ie. 'pgsql', 'mysql, etc.).
 *      'hostspec'      The hostname of the database server.
 *      'username'      The username with which to connect to the database.
 *      'password'      The password associated with 'username'.
 *      'database'      The name of the database.
 *
 * Required by some database implementations:
 *      'options'       Additional options to pass to the database.
 *      'tty'           The TTY on which to connect to the database.
 *      'port'          The port on which to connect to the database.
 *
 * Optional value for $params:
 *      'table'         The name of the connections table in 'database'.
 *                      Defaults to horde_tokens.
 *      'timeout'       The period (in seconds) after which an id is purged.
 *
 * The table structure for the connections is as follows:
 *
 * CREATE TABLE horde_tokens (
 *     token_address    VARCHAR(8) NOT NULL,
 *     token_id         VARCHAR(32) NOT NULL,
 *     token_timestamp  BIGINT NOT NULL,
 *
 *     PRIMARY KEY (token_address, token_id)
 * );
 *
 * $Horde: framework/Token/Token/sql.php,v 1.21 2004/03/30 20:54:02 chuck Exp $
 *
 * Copyright 1999-2004 Max Kalika <max@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Max Kalika <max@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Token
 */
class Horde_Token_sql extends Horde_Token {

    /**
     * Handle for the current database connection.
     * @var object DB $_db
     */
    var $_db = '';

    /**
     * Boolean indicating whether or not we're connected to the SQL
     * server.
     * @var boolean $_connected
     */
    var $_connected = false;

    /**
     * Constructs a new SQL connection object.
     *
     * @param optional array $params   A hash containing connection parameters.
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
        $query = 'DELETE FROM ' . $this->_params['table'] . ' WHERE ';
        $query .= 'token_timestamp < ' . (time() - $this->_params['timeout']);

        $result = $this->_db->query($query, $this->_db);

        /* Return an error if the update fails, too. */
        if (is_a($result, 'PEAR_Error')) {
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
        $query  = 'SELECT token_id FROM ' . $this->_params['table'];
        $query .= ' WHERE token_address = ' . $this->_db->quote($this->hexRemoteAddr());
        $query .= ' AND token_id = ' . $this->_db->quote($tokenID);

        $result = $this->_db->getOne($query);
        if (is_a($result, 'PEAR_Error')) {
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
        $query = sprintf('INSERT INTO %s (token_address, token_id, token_timestamp)' .
                         ' VALUES (%s, %s, %s)',
                         $this->_params['table'],
                         $this->_db->quote($this->hexRemoteAddr()),
                         $this->_db->quote($tokenID),
                         time());

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
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

        $result = Util::assertDriverConfig($this->_params,
            array('phptype', 'hostspec', 'username', 'database'),
            'token SQL', array('driver' => 'token'));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!array_key_exists('table', $this->_params)) {
            $this->_params['table'] = 'horde_tokens';
        }

        /* Connect to the SQL server using the supplied parameters. */
        require_once 'DB.php';
        $this->_db = &DB::connect($this->_params,
                                  array('persistent' => !empty($this->_params['persistent'])));
        if (is_a($this->_db, 'PEAR_Error')) {
            return $this->_db;
        }

        /* Enable the "portability" option. */
        $this->_db->setOption('optimize', 'portability');

        $this->_connected = true;
        return true;
    }

    /**
     * Disconnect from the SQL server and clean up the connection.
     *
     * @return boolean  True on success, a PEAR_Error object on failure.
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
