<?php

require_once 'MDB2.php';

/**
 * Auth_Signup:: This class provides an interface to sign up or have
 * new users sign themselves up into the horde installation, depending
 * on how the admin has configured Horde.
 *
 * $Horde: framework/Auth/Auth/Signup/sql.php,v 1.3.2.5 2009-06-15 15:23:29 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.2.2
 * @package Horde_Auth
 */
class Auth_Signup_sql extends Auth_Signup {

    /**
     * Handle for the current database connection.
     *
     * @var DB
     */
    var $_db;

    /**
     * Handle for the current database connection, used for writing. Defaults
     * to the same handle as $db if a separate write database is not required.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * SQL connection parameters
     */
    var $_params = array();

    /**
     * Connect to DB
     */
    function Auth_Signup_sql($params)
    {
        $this->_params = $params;
        $this->_connect();
    }

    /**
     * Stores the signup data in the backend.
     *
     * @params SQLObject_Signup $signup  Signup data.
     */
    function _queueSignup($signup)
    {
        $query = 'INSERT INTO ' . $this->_params['table']
            . ' (user_name, signup_date, signup_host, signup_data) VALUES (?, ?, ?, ?) ';
        $values = array($signup->name,
                        time(),
                        $_SERVER['REMOTE_ADDR'],
                        serialize($signup->data));
        Horde::logMessage('SQL query by Auth_Signup_sql::_queueSignup(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $stmt = $this->_write_db->prepare($query, null, MDB2_PREPARE_MANIP);
        if (is_a($stmt, 'PEAR_Error')) {
            Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $stmt;
        }
        $result = $stmt->execute($values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }
        $stmt->free();
    }

    /**
     * Checks if a user exists in the system.
     *
     * @param string $user  The user to check.
     *
     * @return boolean  True if the user exists.
     */
    function exists($user)
    {
        $stmt = $this->_db->prepare('SELECT 1 FROM ' . $this->_params['table']
                                    . ' WHERE user_name = ?');

        if (is_a($stmt, 'PEAR_Error')) {
            Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $stmt;
        }
        $result = $stmt->execute(array($user));
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        $exists = (bool)$result->fetchOne();
        $stmt->free();
        $result->free();

        return $exists;
    }

    /**
     * Get a user's queued signup information.
     *
     * @param string $username  The username to retrieve the queued info for.
     *
     * @return SQLObject_Signup  The SQLObject for the requested
     *                                signup.
     */
    function getQueuedSignup($username)
    {
        $stmt = $this->_db->prepare('SELECT * FROM ' . $this->_params['table'] . ' WHERE user_name = ?');
        if (is_a($stmt, 'PEAR_Error')) {
            Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $stmt;
        }
        $results = $stmt->execute(array($username));
        if (is_a($results, 'PEAR_Error')) {
            Horde::logMessage($results, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $results;
        }
        $data = $results->fetchRow(MDB2_FETCHMODE_ASSOC);
        if (is_a($data, 'PEAR_Error')) {
            Horde::logMessage($data, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $data;
        } elseif (empty($data)) {
            return PEAR::RaiseError(sprintf(_("User \"%s\" does not exist."), $name));
        }
        $stmt->free();
        $results->free();

        $object = new SQLObject_Signup($data['user_name']);
        $object->setData($data);

        return $object;
    }

    /**
     * Get the queued information for all pending signups.
     *
     * @return array  An array of SQLObject_Signup objects, one for
     *                each signup in the queue.
     */
    function getQueuedSignups()
    {
        $query = 'SELECT * FROM ' . $this->_params['table'] . '  ORDER BY signup_date';
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        } elseif (empty($result)) {
            return array();
        }

        $signups = array();
        while ($signup = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
            $object = new SQLObject_Signup($signup['user_name']);
            $object->setData($signup);
            $signups[] = $object;
        }

        $result->free();

        return $signups;
    }

    /**
     * Remove a queued signup.
     *
     * @param string $username  The user to remove from the signup queue.
     */
    function removeQueuedSignup($username)
    {
        $stmt = $this->_write_db->prepare('DELETE FROM ' . $this->_params['table'] . ' WHERE user_name = ?', null, MDB2_PREPARE_MANIP);
        if (is_a($stmt, 'PEAR_Error')) {
            Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $stmt;
        }
        $result = $stmt->execute(array($username));
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }
        $stmt->free();

        return true;
    }

    /**
     * Return a new signup object.
     *
     * @param string $name  The signups's name.
     *
     * @return SQLObject_Signup  A new signup object.
     */
    function newSignup($name)
    {
        if (empty($name)) {
            return PEAR::raiseError('Signup names must be non-empty');
        }
        return new SQLObject_Signup($name);
    }

    /**
     * Attempts to open a connection to the sql server.
     *
     * @return boolean  True on success; exits (Horde::fatal()) on error.
     */
    function _connect()
    {
        if (!isset($this->_params['database'])) {
            $this->_params['database'] = '';
        }
        if (!isset($this->_params['username'])) {
            $this->_params['username'] = '';
        }
        if (!isset($this->_params['hostspec'])) {
            $this->_params['hostspec'] = '';
        }
        if (!isset($this->_params['table'])) {
            $this->_params['table'] = 'horde_signups';
        }

        /* Connect to the sql server using the supplied parameters. */
        require_once 'MDB2.php';
        $params = $this->_params;
        unset($params['charset']);
        $this->_write_db = MDB2::factory($params);
        if (is_a($this->_write_db, 'PEAR_Error')) {
            Horde::fatal($this->_write_db, __FILE__, __LINE__);
        }

        /* Set DB portability options. */
        switch ($this->_write_db->phptype) {
        case 'mssql':
            $this->_write_db->setOption('field_case', CASE_LOWER);
            $this->_write_db->setOption('portability', MDB2_PORTABILITY_FIX_CASE | MDB2_PORTABILITY_ERRORS | MDB2_PORTABILITY_RTRIM | MDB2_PORTABILITY_FIX_ASSOC_FIELD_NAMES);
            break;
        default:
            $this->_write_db->setOption('field_case', CASE_LOWER);
            $this->_write_db->setOption('portability', MDB2_PORTABILITY_FIX_CASE | MDB2_PORTABILITY_ERRORS | MDB2_PORTABILITY_FIX_ASSOC_FIELD_NAMES);
        }

        /* Check if we need to set up the read DB connection seperately. */
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($params, $this->_params['read']);
            $this->_db = MDB2::factory($params);
            if (is_a($this->_db, 'PEAR_Error')) {
                Horde::fatal($this->_db, __FILE__, __LINE__);
            }

            /* Set DB portability options. */
            switch ($this->_db->phptype) {
            case 'mssql':
                $this->_db->setOption('field_case', CASE_LOWER);
                $this->_db->setOption('portability', MDB2_PORTABILITY_FIX_CASE | MDB2_PORTABILITY_ERRORS | MDB2_PORTABILITY_RTRIM | MDB2_PORTABILITY_FIX_ASSOC_FIELD_NAMES);
                break;
            default:
                $this->_db->setOption('portability', MDB2_PORTABILITY_FIX_CASE | MDB2_PORTABILITY_ERRORS | MDB2_PORTABILITY_FIX_ASSOC_FIELD_NAMES);
            }
        } else {
            /* Default to the same DB handle as the writer for reading too */
            $this->_db = $this->_write_db;
        }

        return true;
    }

}

/**
 * Extension of the SQLObject class for storing Signup
 * information in the SQL driver. If you want to store
 * specialized Signup information, you should extend this class
 * instead of extending SQLObject directly.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class SQLObject_Signup {

    /**
     * Key-value hash that will be serialized.
     *
     * @see getData()
     * @var array
     */
    var $data = array();

    /**
     * The unique name of this object.
     * These names have the same requirements as other object names - they must
     * be unique, etc.
     *
     * @var string
     */
    var $name;

    /**
     * The SQLObject_Signup constructor. Just makes sure to call
     * the parent constructor so that the signup's is is set
     * properly.
     *
     * @param string $id  The id of the signup.
     */
    function SQLObject_Signup($id)
    {
        if (is_null($this->data)) {
            $this->data = array();
        }

        $this->name = $id;
    }

    /**
     * Gets the data array.
     *
     * @return array  The internal data array.
     */
    function getData()
    {
        return $this->data;
    }

    /**
     * Sets the data array.
     *
     * @param array  The data array to store internally.
     */
    function setData($data)
    {
        $part = unserialize($data['signup_data']);
        if (!empty($part) && is_array($part)) {
            if (!empty($part['extra'])) {
                $extra = $part['extra'];
                unset($part['extra']);
                $part = array_merge($part, $extra);
            }
            $this->data = array_merge($data, $part);
        } else {
            $this->data = $data;
        }

        unset($this->data['signup_data']);
        $this->data['dateReceived'] = $data['signup_date'];
    }

    /**
     * Gets the name of this object.
     *
     * @return string The object name.
     */
    function getName()
    {
        return $this->name;
    }

}
