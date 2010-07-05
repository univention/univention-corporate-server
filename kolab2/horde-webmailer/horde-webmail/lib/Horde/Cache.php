<?php
/**
 * The Horde_Cache:: class provides a common abstracted interface into
 * the various caching backends.  It also provides functions for
 * checking in, retrieving, and flushing a cache.
 *
 * $Horde: framework/Cache/Cache.php,v 1.31.10.17 2009-01-06 15:22:55 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 1.3
 * @package Horde_Cache
 */
class Horde_Cache {

    /**
     * Cache parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Construct a new Horde_Cache object.
     *
     * @param array $params  Parameter array.
     */
    function Horde_Cache($params = array())
    {
        if (!isset($params['lifetime'])) {
            $params['lifetime'] = isset($GLOBALS['conf']['cache']['default_lifetime'])
                ? $GLOBALS['conf']['cache']['default_lifetime'] : 86400;
        }

        $this->_params = $params;
    }

    /**
     * Attempts to retrieve a cached object and return it to the
     * caller.
     *
     * @abstract
     *
     * @param string  $key       Object ID to query.
     * @param integer $lifetime  Lifetime of the object in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function get($key, $lifetime = 1)
    {
        return false;
    }

    /**
     * Attempts to store an object in the cache.
     *
     * @abstract
     *
     * @param string $key        Object ID used as the caching key.
     * @param mixed  $data       Data to store in the cache.
     * @param integer $lifetime  Object lifetime - i.e. the time before the
     *                           data becomes available for garbage
     *                           collection.  If null use the default Horde GC
     *                           time.  If 0 will not be GC'd.
     *                           @since Horde 3.2
     *
     * @return boolean  True on success, false on failure.
     */
    function set($key, $data, $lifetime = null)
    {
        return true;
    }

    /**
     * Attempts to directly output a cached object.
     *
     * @abstract
     *
     * @param string  $key       Object ID to query.
     * @param integer $lifetime  Lifetime of the object in seconds.
     *
     * @return boolean  True if output or false if no object was found.
     */
    function output($key, $lifetime = 1)
    {
        $data = $this->get($key, $lifetime);
        if ($data === false) {
            return false;
        } else {
            echo $data;
            return true;
        }
    }

    /**
     * Checks if a given key exists in the cache, valid for the given
     * lifetime.
     *
     * @abstract
     *
     * @param string  $key       Cache key to check.
     * @param integer $lifetime  Lifetime of the key in seconds.
     *
     * @return boolean  Existance.
     */
    function exists($key, $lifetime = 1)
    {
        return false;
    }

    /**
     * Expire any existing data for the given key.
     *
     * @abstract
     *
     * @param string $key  Cache key to expire.
     *
     * @return boolean  Success or failure.
     */
    function expire($key)
    {
        return true;
    }

    /**
     * Determine the default lifetime for data.
     *
     * @private
     * @since Horde 3.2
     *
     * @param mixed $lifetime  The lifetime to use or null for default.
     */
    function _getLifetime($lifetime)
    {
        return is_null($lifetime) ? $this->_params['lifetime'] : $lifetime;
    }

    /**
     * Attempts to return a concrete Horde_Cache instance based on $driver.
     *
     * @param mixed $driver  The type of concrete Horde_Cache subclass to
     *                       return. If $driver is an array, then we will look
     *                       in $driver[0]/lib/Cache/ for the subclass
     *                       implementation named $driver[1].php.
     * @param array $params  A hash containing any additional
     *                       configuration or connection parameters a subclass
     *                       might need.
     *
     * @return Horde_Cache  The newly created concrete Horde_Cache instance, or
     *                      false on error.
     */
    function factory($driver, $params = array())
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);
        if (empty($driver) || $driver == 'none') {
            return new Horde_Cache($params);
        }

        if (!empty($app)) {
            include_once $app . '/lib/Cache/' . $driver . '.php';
        } elseif (file_exists(dirname(__FILE__) . '/Cache/' . $driver . '.php')) {
            include_once dirname(__FILE__) . '/Cache/' . $driver . '.php';
        } else {
            include_once 'Horde/Cache/' . $driver . '.php';
        }

        $class = 'Horde_Cache_' . $driver;
        if (class_exists($class)) {
            $cache = new $class($params);
        } else {
            $cache = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $cache;
    }

    /**
     * Attempts to return a reference to a concrete Horde_Cache
     * instance based on $driver. It will only create a new instance
     * if no Horde_Cache instance with the same parameters currently
     * exists.
     *
     * This should be used if multiple cache backends (and, thus,
     * multiple Horde_Cache instances) are required.
     *
     * This method must be invoked as:
     * $var = &Horde_Cache::singleton()
     *
     * @param mixed $driver  The type of concrete Horde_Cache subclass to
     *                       return. If $driver is an array, then we will look
     *                       in $driver[0]/lib/Cache/ for the subclass
     *                       implementation named $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Horde_Cache  The concrete Horde_Cache reference, or PEAR_Error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances = array();

        $signature = serialize(array($driver, $params));
        if (empty($instances[$signature])) {
            $instances[$signature] = Horde_Cache::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
