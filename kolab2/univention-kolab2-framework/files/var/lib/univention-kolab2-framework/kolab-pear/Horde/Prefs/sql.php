<?php
/**
 * Preferences storage implementation for PHP's PEAR database abstraction
 * layer.
 *
 * Required parameters:
 * ====================
 *   'charset'   --  The database's internal charset.
 *   'database'  --  The name of the database.
 *   'hostspec'  --  The hostname of the database server.
 *   'password'  --  The password associated with 'username'.
 *   'phptype'   --  The database type (ie. 'pgsql', 'mysql, etc.).
 *   'protocol'  --  The communication protocol ('tcp', 'unix', etc.).
 *   'username'  --  The username with which to connect to the database.
 *
 * Optional preferences:
 * =====================
 *   'table'  --  The name of the preferences table in 'database'.
 *                DEFAULT: 'horde_prefs'
 *
 * Required by some database implementations:
 * ==========================================
 *   'options'  --  Additional options to pass to the database.
 *   'port'     --  The port on which to connect to the database.
 *   'tty'      --  The TTY on which to connect to the database.
 *
 *
 * The table structure for the preferences is as follows:
 *
 *  create table horde_prefs (
 *      pref_uid        varchar(255) not null,
 *      pref_scope      varchar(16) not null default '',
 *      pref_name       varchar(32) not null,
 *      pref_value      text null,
 *      primary key (pref_uid, pref_scope, pref_name)
 *  );
 *
 *
 * If setting up as the Horde preference handler in conf.php, simply configure
 * $conf['sql'] and don't enter anything for $conf['prefs']['params'].
 *
 *
 * $Horde: framework/Prefs/Prefs/sql.php,v 1.86 2004/05/24 21:55:00 mdjukic Exp $
 *
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Prefs
 */
class Prefs_sql extends Prefs {

    /**
     * Hash containing connection parameters.
     *
     * @var array $params
     */
    var $_params = array();

    /**
     * Handle for the current database connection.
     *
     * @var object DB $db
     */
    var $_db;

    /**
     * Boolean indicating whether or not we're connected to the SQL server.
     *
     * @var boolean $_connected
     */
    var $_connected = false;

    /**
     * Constructs a new SQL preferences object.
     *
     * @access public
     *
     * @param string $user               The user who owns these preferences.
     * @param string $password           The password associated with $user.
     *                                   (Unused)
     * @param string $scope              The current preferences scope.
     * @param array  $params             A hash containing connection
     *                                   parameters.
     * @param optional boolean $caching  Should caching be used?
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
     * @access public
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
     * @access public
     *
     * @param optional array $prefs  An array listing the preferences to
     *                               retrieve. If not specified, retrieve all
     *                               of the preferences listed in the $prefs
     *                               hash.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function retrieve($prefs = array())
    {
        /* Attempt to pull the values from the session cache first. */
        if ($this->cacheLookup()) {
            return true;
        }

        /* Load defaults to make sure we have all preferences. */
        parent::retrieve();

        /* Make sure we're connected. */
        $this->_connect();

        /* Build the SQL query. */
        $query = 'SELECT pref_scope, pref_name, pref_value FROM ';
        $query .= $this->_params['table'] . ' ';
        $query .= 'WHERE pref_uid = ' . $this->_db->quote($this->_user);
        $query .= ' AND (pref_scope = ' . $this->_db->quote($this->_scope);
        $query .= " OR pref_scope = 'horde') ORDER BY pref_scope";

        Horde::logMessage(sprintf('SQL Query by Prefs_sql::retrieve(): %s', $query), __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = $this->_db->query($query);

        if (isset($result) && !is_a($result, 'PEAR_Error')) {
            $row = $result->fetchRow(DB_FETCHMODE_ASSOC);
            if (is_a($row, 'PEAR_Error')) {
                Horde::logMessage($row, __FILE__, __LINE__, PEAR_LOG_ERR);
                return;
            }

            /* Set the requested values in the $this->_prefs hash
               based on the contents of the SQL result.

               Note that Prefs::setValue() can't be used here because
               of the check for the "changeable" bit. We want to
               override that check when populating the $this->_prefs
               hash from the SQL server.
            */
            while ($row && !is_a($row, 'PEAR_Error')) {
                $name = trim($row['pref_name']);
                if (isset($this->_prefs[$name])) {
                    $this->_setValue($name, $this->_convertFromDriver($row['pref_value']), false);
                    $this->setDirty($name, false);
                } else {
                    $this->add($name, $this->_convertFromDriver($row['pref_value']), $row['pref_scope'] == 'horde' ? _PREF_SHARED : 0);
                }
                $row = $result->fetchRow(DB_FETCHMODE_ASSOC);
            }

            /* Make sure we know that we've loaded these
             * preferences. */
            $_SESSION['prefs_cache']['_filled']['horde'] = true;
            $_SESSION['prefs_cache']['_filled'][$this->_scope] = true;

            /* Call hooks. */
            $this->_callHooks();
        } else {
            Horde::logMessage('No preferences were retrieved.', __FILE__, __LINE__, PEAR_LOG_DEBUG);
            return;
        }

        /* Update the session cache. */
        $this->cacheUpdate();

        return true;
    }

    /**
     * Stores preferences to SQL server.
     *
     * @access public
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function store()
    {
        /* Check for any "dirty" preferences. If no "dirty"
           preferences are found, there's no need to update the SQL
           server. Exit successfully. */
        $dirty_prefs = $this->_dirtyPrefs();
        if (!count($dirty_prefs)) {
            return true;
        }

        /* Make sure we're connected. */
        $this->_connect();

        /* Loop through the "dirty" preferences.  If a row already exists for
           this preference, attempt to update it.  Otherwise, insert a new
           row. */
        foreach ($dirty_prefs as $name) {
            // Don't store locked preferences.
            if ($this->isLocked($name)) {
                continue;
            }

            $scope = $this->getScope($name);

            /* Does an entry already exist for this preference? */
            $query = 'SELECT 1 FROM ';
            $query .= $this->_params['table'] . ' ';
            $query .= 'WHERE pref_uid = ' . $this->_db->quote($this->_user);
            $query .= ' AND pref_name = ' . $this->_db->quote($name);
            $query .= ' AND (pref_scope = ' . $this->_db->quote($scope);
            $query .= " OR pref_scope = 'horde')";

            /* Execute the query. */
            $check = $this->_db->getOne($query);

            /* Return an error if the query fails. */
            if (is_a($check, 'PEAR_Error')) {
                Horde::logMessage('Failed retrieving prefs for ' . $this->_user, __FILE__, __LINE__, PEAR_LOG_ERR);
                return PEAR::raiseError(_("Failed retrieving preferences."));
            }

            /* Is there an existing row for this preference? */
            if (!empty($check)) {
                /* Update the existing row. */
                $query = 'UPDATE ' . $this->_params['table'] . ' ';
                $query .= 'SET pref_value = ' . $this->_db->quote($this->_convertToDriver((string)$this->getValue($name)));
                $query .= ' WHERE pref_uid = ' . $this->_db->quote($this->_user);
                $query .= ' AND pref_name = ' . $this->_db->quote($name);
                $query .= ' AND pref_scope = ' . $this->_db->quote($scope);
                $result = $this->_db->query($query);

                /* Return an error if the update fails. */
                if (is_a($result, 'PEAR_Error')) {
                    Horde::fatal($result, __FILE__, __LINE__);
                }
            } else {
                /* Insert a new row. */
                $query  = 'INSERT INTO ' . $this->_params['table'] . ' ';
                $query .= '(pref_uid, pref_scope, pref_name, pref_value) VALUES';
                $query .= '(' . $this->_db->quote($this->_user) . ', ';
                $query .= $this->_db->quote($scope) . ', ' . $this->_db->quote($name) . ', ';
                $query .= $this->_db->quote($this->_convertToDriver((string)$this->getValue($name))) . ')';
                $result = $this->_db->query($query);

                /* Return an error if the insert fails. */
                if (is_a($result, 'PEAR_Error')) {
                    Horde::fatal($result, __FILE__, __LINE__);
                }
            }

            /* Mark this preference as "clean" now. */
            $this->setDirty($name, false);
        }

        /* Update the session cache. */
        $this->cacheUpdate();

        return true;
    }

    /**
     * Perform cleanup operations.
     *
     * @access public
     *
     * @param optional boolean $all  Cleanup all Horde preferences.
     */
    function cleanup($all = false)
    {
        /* Close the database connection. */
        $this->_disconnect();

        parent::cleanup($all);
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
        /* Check to see if we are already connected. */
        if ($this->_connected) {
            return true;
        }

        Horde::assertDriverConfig($this->_params, 'prefs',
            array('phptype', 'hostspec', 'username', 'database', 'charset'),
            'preferences SQL');

        if (!isset($this->_params['table'])) {
            $this->_params['table'] = 'horde_prefs';
        }

        if (!isset($this->_params['password'])) {
            $this->_params['password'] = '';
        }

        /* Connect to the SQL server using the supplied parameters. */
        require_once 'DB.php';
        $this->_db = &DB::connect($this->_params,
                                  array('persistent' => !empty($this->_params['persistent'])));
        if (is_a($this->_db, 'PEAR_Error')) {
            Horde::fatal($this->_db, __FILE__, __LINE__);
        }

        /* Enable the "portability" option. */
        $this->_db->setOption('optimize', 'portability');

        $this->_connected = true;

        return true;
    }

    /**
     * Disconnect from the SQL server and clean up the connection.
     *
     * @access private
     *
     * @return boolean  True on success, false on failure.
     */
    function _disconnect()
    {
        if ($this->_connected) {
            $this->_connected = false;
            return $this->_db->disconnect();
        } else {
            return true;
        }
    }

    /**
     * Converts a value from the driver's charset to the default charset.
     *
     * @param mixed $value  A value to convert.
     * @return mixed        The converted value.
     */
    function _convertFromDriver($value)
    {
        return String::convertCharset($value, $this->_params['charset'], NLS::getCharset());
    }

    /**
     * Converts a value from the default charset to the driver's charset.
     *
     * @param mixed $value  A value to convert.
     * @return mixed        The converted value.
     */
    function _convertToDriver($value)
    {
        return String::convertCharset($value, NLS::getCharset(), $this->_params['charset']);
    }

}
