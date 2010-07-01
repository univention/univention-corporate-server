<?php
/**
 * Kronolith_Storage:: defines an API for storing free/busy
 * information.
 *
 * $Horde: kronolith/lib/Storage/sql.php,v 1.7.10.7 2009-02-17 18:52:00 chuck Exp $
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Kronolith
 */
class Kronolith_Storage_sql extends Kronolith_Storage {

    /**
     * Handle for the current database connection, used for reading.
     *
     * @var DB
     */
    var $_db;

    /**
     * Handle for the current database connection, used for writing. Defaults
     * to the same handle as $_db if a separate write database is not required.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Constructs a new Kronolith_Storage SQL instance.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Kronolith_Storage_sql($user, $params = array())
    {
        $this->_user = $user;

        /* Use defaults where needed. */
        $this->_params = $params;
        $this->_params['table'] = isset($params['table']) ? $params['table'] : 'kronolith_storage';
    }

    /**
     * Connect to the database
     *
     * @return boolean  True on success or PEAR_Error on failure.
     */
    function initialize()
    {
        Horde::assertDriverConfig($this->_params, 'storage',
            array('phptype'),
            'kronolith storage SQL');

        if (!isset($this->_params['database'])) {
            $this->_params['database'] = '';
        }
        if (!isset($this->_params['username'])) {
            $this->_params['username'] = '';
        }
        if (!isset($this->_params['hostspec'])) {
            $this->_params['hostspec'] = '';
        }

        /* Connect to the SQL server using the supplied parameters. */
        include_once 'DB.php';
        $this->_write_db = &DB::connect($this->_params,
                                        array('persistent' => !empty($this->_params['persistent']),
                                              'ssl' => !empty($this->_params['ssl'])));
        if (is_a($this->_write_db, 'PEAR_Error')) {
            return PEAR::raiseError(_("Unable to connect to SQL server."));
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
            /* Default to the same DB handle for the writer too. */
            $this->_db =& $this->_write_db;
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
        /* Build the SQL query. */
        $query = sprintf('SELECT vfb_serialized FROM %s WHERE vfb_email=? AND (vfb_owner=?',
                         $this->_params['table']);
        $values = array($email, $this->_user);

        if ($private_only) {
            $query .= ')';
        } else {
            $query .= " OR vfb_owner='')";
        }

        /* Log the query at debug level. */
        Horde::logMessage(sprintf('SQL search by %s: query = "%s"',
                                  Auth::getAuth(), $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = $this->_db->query($query, $values);
        if (!is_a($result, 'PEAR_Error')) {
            $row = $result->fetchRow(DB_GETMODE_ASSOC);
            $result->free();
            if (is_array($row)) {
                /* Retrieve Freebusy object.  TODO: check for multiple
                 * results and merge them into one and return. */
                require_once 'Horde/Serialize.php';
                $vfb = Horde_Serialize::unserialize($row['vfb_serialized'], SERIALIZE_BASIC);
                return $vfb;
            }
        }
        return PEAR::raiseError(_("Not found"), KRONOLITH_ERROR_FB_NOT_FOUND);
    }

    /**
     * Store the freebusy information for a given email address.
     *
     * @param string                     $email        The email address to store fb info for.
     * @param Horde_iCalendar_vFreebusy  $vfb          TODO
     * @param boolean                    $private_only (optional) TODO
     *
     * @return boolean              True on success
     *                              PEAR_Error on error or not found
     */
    function store($email, $vfb, $public = false)
    {
        $owner = (!$public) ? $this->_user : '';

        /* Build the SQL query. */
        require_once 'Horde/Serialize.php';
        $query = sprintf('INSERT INTO %s (vfb_owner, vfb_email, vfb_serialized) VALUES (?, ?, ?)',
                         $this->_params['table']);
        $values = array($owner, $email, Horde_Serialize::serialize($vfb, SERIALIZE_BASIC));

        /* Log the query at debug level. */
        Horde::logMessage(sprintf('SQL insert by %s: query = "%s"',
                                  Auth::getAuth(), $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        return $this->_write_db->query($query, $values);
    }

}
