<?php

require_once 'Horde/Serialize.php';

/**
 * Kronolith_Storage:: defines an API for storing free/busy information
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Kronolith
 */
class Kronolith_Storage_sql extends Kronolith_Storage {

    /** Pointer to the sql connection. */
    var $_db;

    /** Boolean which contains state of sql connection */
    var $_connected = false;

    /** Hash containing connection parameters. */
    var $_params = array();

    /**
     * Constructs a new sql Passwd_Driver object.
     *
     * @param array  $params    A hash containing connection parameters.
     */
    function Kronolith_Storage_sql($user, $params = array())
    {
        $this->_user = $user;

        /* Use defaults from Horde where needed */
        $this->_params = $params;
        $this->_params['table'] = array_key_exists('table', $params) ? $params['table'] : 'Kronolith_Storage';
    }

    /**
     * Connect to the database
     *
     * @return   boolean   True on success or PEAR_Error on failure.
     *
     */
    function _connect()
    {
        if (!$this->_connected) {
            Horde::assertDriverConfig($this->_params, 'storage',
                array('phptype', 'hostspec', 'username', 'database'),
                'kronolith storage SQL');

            // Connect to the SQL server using the supplied parameters.
            include_once 'DB.php';
            $this->_db = &DB::connect($this->_params,
                                      array('persistent' => !empty($this->_params['persistent'])));
            if (DB::isError($this->_db)) {
                return PEAR::raiseError(_("Unable to connect to SQL server."));
            }

            // Enable the "portability" option.
            $this->_db->setOption('optimize', 'portability');
            $this->_connected = true;
        }

        return true;
    }

    /**
     * Disconnect from the SQL server and clean up the connection.
     *
     * @return boolean true on success, false on failure.
     */
    function _disconnect()
    {
        if ($this->_connected) {
            $this->_connected = false;
            return $this->_db->disconnect();
        }
       return true;

    }

    /**
     * Search for a user's free/busy information.
     *
     * @param string  $email        The email address to lookup
     * @param boolean $private_only (optional) Only return free/busy
     *                              information owned by this used.
     *
     * @return object               Horde_iCalendar_vFreebusy on success
     *                              PEAR_Error on error or not found
     */
    function search($email, $private_only = false)
    {
        // Connect to the database
        $res = $this->_connect();
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }

        // Build the SQL query.
        $query = sprintf('SELECT vfb_serialized FROM %s WHERE vfb_email=%s AND (vfb_owner=%s',
                         $this->_params['table'],
                          $this->_db->quote($email),
                          $this->_db->quote($this->_user));

        if ($private_only) {
            $query .= ')';
        } else {
            $query .= " OR vfb_owner='')";
        }

        // Log the query at debug level
        Horde::logMessage(sprintf('SQL search by %s: query = "%s"',
                                  Auth::getAuth(), $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        // Execute the query.
        $result = $this->_db->query($query);
        if (!DB::isError($result)) {
            $row = $result->fetchRow(DB_GETMODE_ASSOC);
            $result->free();
            if (is_array($row)) {
                // Retrieve Freebusy object.
                // TODO: check for multiple results and merge them
                // into one and return.
                $vfb = Horde_Serialize::unserialize($row['vfb_serialized'], SERIALIZE_BASIC);
                return $vfb;
            }
        }
        return PEAR::raiseError(_("Not found"), KRONOLITH_ERROR_FB_NOT_FOUND);
    }

    /**
     * Store the freebusy information for a given email address.
     *
     * @param string                     $email        The email address to store for
     * @param Horde_iCalendar_vFreebusy  $vfb          TODO
     * @param boolean                    $private_only (optional) TODO
     *
     * @return boolean              True on success
     *                              PEAR_Error on error or not found
     */
    function store($email, $vfb, $public = false)
    {
        // Connect to the database
        $res = $this->_connect();
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }

        $owner = (!$public) ? $this->_user : '';

        // Build the SQL query.
        $query = sprintf('INSERT INTO %s (vfb_owner, vfb_email, vfb_serialized) VALUES (%s, %s, %s)',
                         $this->_params['table'],
                         $this->_db->quote($owner),
                         $this->_db->quote($email),
                         $this->_db->quote(Horde_Serialize::serialize($vfb, SERIALIZE_BASIC)));

        // Log the query at debug level.
        Horde::logMessage(sprintf('SQL insert by %s: query = "%s"',
                                  Auth::getAuth(), $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        // Execute the query.
        $result = $this->_db->query($query);
        if (DB::isError($result)) {
            return $result;
        } else {
            return true;
        }
    }

}
