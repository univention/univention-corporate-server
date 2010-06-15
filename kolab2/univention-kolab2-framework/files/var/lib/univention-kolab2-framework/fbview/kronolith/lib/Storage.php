<?php

/**
 * Kronolith_Storage:: defines an API for storing free/busy information
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Kronolith
 */
class Kronolith_Storage {

    /**
     * String containing the current username.
     * @var string $_user
     */
    var $_user = '';

    /**
     * Attempts to return a concrete Kronolith_Storage instance based on $driver.
     *
     * @param string    $driver     The type of concrete Kronolith_Storage subclass
     *                              to return.  The is based on the storage
     *                              driver ($driver).  The code is dynamically
     *                              included.
     *
     * @param string    $user       The name of the user who owns the free/busy
     *                              information
     *
     * @param array     $params     (optional) A hash containing any additional
     *                              configuration or connection parameters a
     *                              subclass might need.
     *
     * @return mixed    The newly created concrete Kronolith_Storage instance, or
     *                  false on an error.
     */
    function &factory($user = null, $driver = null, $params = null)
    {
        if (is_null($user)) {
            $user = Auth::getAuth();
        }

        if (is_null($driver)) {
            $driver = $GLOBALS['conf']['storage']['driver'];
        }

        $driver = basename($driver);

        if (is_null($params)) {
            $params = Horde::getDriverConfig('storage', $driver);
        }

        require_once dirname(__FILE__) . '/Storage/' . $driver . '.php';
        $class = 'Kronolith_Storage_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($user, $params);
        } else {
            return false;
        }
    }

    /**
     * Attempts to return a reference to a concrete Kronolith_Storage instance
     * based on $driver.  It will only create a new instance if no
     * Kronolith_Storage instance with the same parameters currently exists.
     *
     * This should be used if multiple storage sources are required.
     *
     * This method must be invoked as: $var = &Kronolith_Storage::singleton()
     *
     * @param string    $driver     The type of concrete Kronolith_Storage subclass
     *                              to return.  The is based on the storage
     *                              driver ($driver).  The code is dynamically
     *                              included.
     *
     * @param string    $user       The name of the user who owns the free/busy
     *                              information
     *
     * @param array     $params     (optional) A hash containing any additional
     *                              configuration or connection parameters a
     *                              subclass might need.
     *
     * @return mixed    The created concrete Kronolith_Storage instance, or false
     *                  on error.
     */
    function &singleton($user = null, $driver = null, $params = null)
    {
        static $instances;

        if (is_null($user)) {
            $user = Auth::getAuth();
        }

        if (is_null($driver)) {
            $driver = $GLOBALS['conf']['storage']['driver'];
        }

        if (is_null($params)) {
            $params = Horde::getDriverConfig('storage', $driver);
        }

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($user, $driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Kronolith_Storage::factory($user, $driver, $params);
        }

        return $instances[$signature];
    }
}
