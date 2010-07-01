<?php
/**
 * @package Horde_Prefs
 */

/**
 * PEAR DB layer.
 */
require_once 'DB.php';

/**
 * Horde_String class.
 */
require_once 'Horde/String.php';

/**
 * Preferences storage implementation for PHP's PEAR database
 * abstraction layer.
 *
 * Required parameters:<pre>
 *   'phptype'      The database type (ie. 'pgsql', 'mysql', etc.).
 *   'charset'      The database's internal charset.</pre>
 *
 * Optional parameters:<pre>
 *   'table'        The name of the preferences table in 'database'.
 *                  DEFAULT: 'horde_prefs'</pre>
 *
 * Required by some database implementations:<pre>
 *   'hostspec'     The hostname of the database server.
 *   'protocol'     The communication protocol ('tcp', 'unix', etc.).
 *   'database'     The name of the database.
 *   'username'     The username with which to connect to the database.
 *   'password'     The password associated with 'username'.
 *   'options'      Additional options to pass to the database.
 *   'port'         The port on which to connect to the database.
 *   'tty'          The TTY on which to connect to the database.</pre>
 *
 * Optional values when using separate reading and writing servers, for example
 * in replication settings:<pre>
 *   'splitread'   Boolean, whether to implement the separation or not.
 *   'read'        Array containing the parameters which are different for
 *                 the read database connection, currently supported
 *                 only 'hostspec' and 'port' parameters.</pre>
 *
 * The table structure for the Prefs system is in
 * scripts/sql/horde_prefs.sql.
 *
 * $Horde: framework/Prefs/Prefs/sql.php,v 1.91.10.26 2009-02-25 05:35:43 chuck Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @since   Horde 1.3
 * @package Horde_Prefs
 */
class Prefs_sql extends Prefs {

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Handle for the current database connection.
     *
     * @var DB
     */
    var $_db;

    /**
     * Handle for the current database connection, used for
     * writing. Defaults to the same handle as $_db if a separate
     * write database is not configured.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * Boolean indicating whether or not we're connected to the SQL server.
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * Constructs a new SQL preferences object.
     *
     * @param string $user      The user who owns these preferences.
     * @param string $password  The password associated with $user. (Unused)
     * @param string $scope     The current preferences scope.
     * @param array $params     A hash containing connection parameters.
     * @param boolean $caching  Should caching be used?
     */
    function Prefs_sql($user, $password = '', $scope = '',
                       $params = array(), $caching = false)
    {
        $this->_user = $user;
        $this->_scope = $scope;
        $this->_params = $params;
        $this->_caching = $caching;

        parent::Prefs();
    }

    /**
     * Returns the charset used by the concrete preference backend.
     *
     * @return string  The preference backend's charset.
     */
    function getCharset()
    {
        return $this->_params['charset'];
    }

    /**
     * Retrieves the requested set of preferences from the user's database
     * entry.
     *
     * @param $scope Scope specifier.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _retrieve($scope)
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            if (empty($_SESSION['prefs_cache']['unavailable'])) {
                $_SESSION['prefs_cache']['unavailable'] = true;
                if (isset($GLOBALS['notification'])) {
                    $GLOBALS['notification']->push(_("The preferences backend is currently unavailable and your preferences have not been loaded. You may continue to use the system with default settings."));
                }
            }
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        $query = 'SELECT pref_scope, pref_name, pref_value FROM ' .
            $this->_params['table'] . ' ' .
            'WHERE pref_uid = ? AND pref_scope = ?';

        $values = array($this->_user, $scope);

        Horde::logMessage('SQL Query by Prefs_sql::retrieve(): ' . $query . ', values: ' . implode(', ', $values), __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage('No preferences were retrieved.', __FILE__, __LINE__, PEAR_LOG_DEBUG);
            return;
        }

        $row = $result->fetchRow(DB_FETCHMODE_ASSOC);
        if (is_a($row, 'PEAR_Error')) {
            Horde::logMessage($row, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        while ($row && !is_a($row, 'PEAR_Error')) {
            $name = trim($row['pref_name']);
            if (isset($this->_scopes[$scope][$name])) {
                $this->_scopes[$scope][$name]['v'] = $row['pref_value'];
                $this->_scopes[$scope][$name]['m'] &= ~_PREF_DEFAULT;
            } else {
                // This is a shared preference.
                $this->_scopes[$scope][$name] = array('v' => $row['pref_value'],
                                                      'm' => 0,
                                                      'd' => null);
            }

            $row = $result->fetchRow(DB_FETCHMODE_ASSOC);
        }
    }

    /**
     * Stores preferences to the SQL server.
     */
    function store()
    {
        // Get the list of preferences that have changed. If there are
        // none, no need to hit the backend.
        $dirty_prefs = $this->_dirtyPrefs();
        if (!$dirty_prefs) {
            return;
        }

        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        // For each preference, check for an existing table row and
        // update it if it's there, or create a new one if it's not.
        foreach ($dirty_prefs as $scope => $prefs) {
            foreach ($prefs as $name => $pref) {
                // Don't store locked preferences.
                if ($this->_scopes[$scope][$name]['m'] & _PREF_LOCKED) {
                    continue;
                }

                $values = array($this->_user, $name, $scope);

                // Does a row already exist for this preference?
                $query = 'SELECT 1 FROM ' . $this->_params['table'] .
                    ' WHERE pref_uid = ? AND pref_name = ?' .
                    ' AND pref_scope = ?';
                Horde::logMessage('SQL Query by Prefs_sql::store(): ' . $query . ', values: ' . implode(', ', $values), __FILE__, __LINE__, PEAR_LOG_DEBUG);

                $check = $this->_write_db->getOne($query, $values);
                if (is_a($check, 'PEAR_Error')) {
                    Horde::logMessage('Failed checking prefs for ' . $this->_user . ': ' . $check->getMessage(), __FILE__, __LINE__, PEAR_LOG_ERR);
                    return;
                }

                $value = isset($pref['v']) ? $pref['v'] : null;

                if (!empty($check)) {
                    // Update the existing row.
                    $query = 'UPDATE ' . $this->_params['table'] . ' ' .
                        'SET pref_value = ?' .
                        ' WHERE pref_uid = ?' .
                        ' AND pref_name = ?' .
                        ' AND pref_scope = ?';

                    $values = array((string)$value,
                                    $this->_user,
                                    $name,
                                    $scope);
                } else {
                    // Insert a new row.
                    $query  = 'INSERT INTO ' . $this->_params['table'] . ' ' .
                        '(pref_uid, pref_scope, pref_name, pref_value) VALUES' .
                        '(?, ?, ?, ?)';

                    $values = array($this->_user,
                                    $scope,
                                    $name,
                                    (string)$value);
                }

                Horde::logMessage('SQL Query by Prefs_sql::store(): ' . $query . ', values: ' . implode(', ', $values), __FILE__, __LINE__, PEAR_LOG_DEBUG);

                $result = $this->_write_db->query($query, $values);
                if (is_a($result, 'PEAR_Error')) {
                    Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                    return;
                }

                // Clean the pref since it was just saved.
                $this->_scopes[$scope][$name]['m'] &= ~_PREF_DIRTY;
            }

            // Update the cache for this scope.
            $this->_cacheUpdate($scope, array_keys($prefs));
        }
    }

    /**
     * Clears all preferences from the backend.
     */
    function clear()
    {
        if (is_a(($result = $this->_connect()), 'PEAR_Error')) {
            return $result;
        }

        // Build the SQL query.
        $query = 'DELETE FROM ' . $this->_params['table'] .
            ' WHERE pref_uid = ?';

        $values = array($this->_user);

        Horde::logMessage('SQL Query by Prefs_sql::clear():' . $query . ', values: ' . implode(', ', $values), __FILE__, __LINE__, PEAR_LOG_DEBUG);

        // Execute the query.
        $result = $this->_write_db->query($query, $values);

        // Cleanup.
        parent::clear();

        return $result;
    }

    /**
     * Converts a value from the driver's charset to the specified charset.
     *
     * @param mixed $value     A value to convert.
     * @param string $charset  The charset to convert to.
     *
     * @return mixed  The converted value.
     */
    function convertFromDriver($value, $charset)
    {
        static $converted = array();

        if (is_array($value)) {
            return String::convertCharset($value, $this->_params['charset'], $charset);
        }

        if (is_bool($value)) {
            return $value;
        }

        if (!isset($converted[$charset][$value])) {
            $converted[$charset][$value] = String::convertCharset($value, $this->_params['charset'], $charset);
        }

        return $converted[$charset][$value];
    }

    /**
     * Converts a value from the specified charset to the driver's charset.
     *
     * @param mixed $value  A value to convert.
     * @param string $charset  The charset to convert from.
     *
     * @return mixed  The converted value.
     */
    function convertToDriver($value, $charset)
    {
        return String::convertCharset($value, $charset, $this->_params['charset']);
    }

    /**
     * Attempts to open a persistent connection to the SQL server.
     *
     * @access private
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _connect()
    {
        if ($this->_connected) {
            return true;
        }

        Horde::assertDriverConfig($this->_params, 'prefs',
            array('phptype', 'charset'),
            'preferences SQL');

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
            $this->_params['table'] = 'horde_prefs';
        }

        // Connect to the SQL server using the supplied parameters.
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

        // Check if we need to set up the read DB connection
        // seperately.
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($this->_params, $this->_params['read']);
            $this->_db = &DB::connect($params,
                                      array('persistent' => !empty($params['persistent']),
                                            'ssl' => !empty($params['ssl'])));
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
            // Default to the same DB handle for reads.
            $this->_db = &$this->_write_db;
        }

        $this->_connected = true;
        return true;
    }

}
