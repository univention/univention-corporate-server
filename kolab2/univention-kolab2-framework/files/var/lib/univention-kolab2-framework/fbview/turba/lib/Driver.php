<?php

require_once TURBA_BASE . '/lib/Turba.php';

/**
 * The Turba_Driver:: class provides a common abstracted interface to the
 * various directory search drivers.  It includes functions for searching,
 * adding, removing, and modifying directory entries.
 *
 * $Horde: turba/lib/Driver.php,v 1.43 2004/02/24 19:31:00 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Turba 0.0.1
 * @package Turba
 */
class Turba_Driver {

    /**
     * Hash holding the driver's additional parameters.
     * @var array $_params
     */
    var $_params = array();

    /**
     * Constructs a new Turba_Driver object.
     *
     * @param array $params  Hash containing additional configuration parameters.
     */
    function Turba_Driver($params)
    {
        $this->_params = $params;
    }

    /**
     * Returns the current driver's additional parameters.
     *
     * @return          Hash containing the driver's additional parameters.
     */
    function getParams()
    {
        return $this->_params;
    }

    /**
     * Searches the backend with the given criteria and returns a
     * filtered list of results. If no criteria are specified, all
     * records are returned.
     *
     * @abstract
     *
     * @param $criteria      Array containing the search criteria.
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function search($criteria, $fields)
    {
        return PEAR::raiseError('Not supported');
    }

    /**
     * Initialize any connections, etc. for this driver that might
     * return an error.
     *
     * @abstract
     */
    function init()
    {
    }

    /**
     * Read the given data from the backend and returns
     * the result's fields.
     *
     * @abstract
     *
     * @param $criteria      Search criteria.
     * @param $id      	     Data identifier.
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function read($criteria, $id, $fields)
    {
        return PEAR::raiseError('Not supported');
    }

    /**
     * Adds the specified object to the backend.
     *
     * @abstract
     */
    function addObject($attributes)
    {
        return PEAR::raiseError('Not supported');
    }

    /**
     * Deletes the specified object from the backend.
     *
     * @abstract
     */
    function removeObject($object_key, $object_id)
    {
        return PEAR::raiseError('Not supported');
    }

    /**
     * Saves the specified object to the backend.
     *
     * @abstract
     */
    function setObject($object_key, $object_id, $attributes)
    {
        return PEAR::raiseError('Not supported');
    }

    /**
     * Create an object key for a new object.
     *
     * @abstract
     * @param array $attributes  The attributes (in driver keys) of the
     *                           object being added.
     *
     * @return string  A unique ID for the new object.
     */
    function makeKey($attributes)
    {
    }

    /**
     * Attempts to return a concrete Turba_Driver instance based on $driver.
     *
     * @param $driver   The type of Turba_Driver subclass to return.  The
     *                  code is dynamically included.
     * @param $params   Hash containing additional paramters to be passed to
     *                  the subclass's constructor.
     *
     * @return          The newly created concrete Turba_Driver instance, or
     *                  false on an error.
     */
    function &factory($driver, $params = array())
    {
        $driver = basename($driver);
        include_once dirname(__FILE__) . '/Driver/' . $driver . '.php';
        $class = 'Turba_Driver_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            Horde::fatal(PEAR::raiseError(sprintf(_("Unable to load the definition of %s."), $class)), __FILE__, __LINE__);
        }
    }

    /**
     * Attempts to return a reference to a concrete Turba_Driver instance
     * based on $driver. It will only create a new instance if no
     * Turba_Driver instance with the same parameters currently exists.
     *
     * This method must be invoked as: $var = &Turba_Driver::singleton()
     *
     * @param $driver   The type of concrete Turba_Driver subclass to return.
     *                  This is based on the storage driver ($driver). The
     *                  code is dynamically included.
     * @param $params   A hash containing additional parameters for the
     *                  subclass.
     *
     * @return          The concrete Turba_Driver reference, or false on an
     *                  error.
     */
    function &singleton($driver, $params)
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Turba_Driver::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
