<?php
/**
 * The Horde_Cache:: class provides a common abstracted interface into
 * the various caching backends. It also provides functions for
 * checking in, retrieving, and flushing a cache.
 *
 * $Horde: framework/Cache/Cache.php,v 1.30 2004/01/01 15:14:06 jan Exp $
 *
 * Copyright 1999-2004 Anil Madhavapeddy <anil@recoil.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Cache
 */
class Horde_Cache {

    /**
     * Returns the result of a cacheable function or method that
     * returns its results, only actually calling it if there isn't a
     * cached version or the cache has expired.
     *
     * @param string  $oid       The cache key.
     * @param string  $code      The code to execute if the value isn't cached.
     * @param integer $lifetime  The lifetime of the object in the cache.
     *
     * Example:
     *
     * $foo = $cache->getData('myContent', 'function($arg1, $arg2)', $date);
     *
     * @return mixed  The return value of the function or method.
     * @access public
     */
    function getData($oid, $code, $lifetime)
    {
        if ($data = $this->_fetch($oid, $lifetime)) {
            return $data;
        } else {
            $data = $this->_call($code, 'result');
            if (!is_a($data, 'PEAR_Error')) {
                $this->_store($oid, $data);
            }
            return $data;
        }
    }

    /**
     * Outputs the result of a function that returns its results, only
     * actually calling it if there isn't a cached version or the
     * cache has expired.
     *
     * @param string  $oid       The cache key.
     * @param string  $code      The code to execute if the value isn't cached.
     * @param integer $lifetime  The lifetime of the object in the cache.
     *
     * Example:
     *
     * $cache->printData('myContent', 'function($arg1, $arg2)', $date);
     *
     * @return mixed  The return value of the function or method.
     * @access public
     */
    function printData($oid, $code, $lifetime)
    {
        if ($this->_output($oid, $lifetime)) {
            return true;
        } else {
            $data = $this->_call($code, 'result');
            if (is_a($data, 'PEAR_Error')) {
                return $data;
            }

            $this->_store($oid, $data);
            echo $data;
            return true;
        }
    }

    /**
     * Returns the result of a cacheable function or method that
     * prints its results, only actually calling it if there isn't a
     * cached version or the cache has expired.
     *
     * @param string  $oid       The cache key.
     * @param string  $code      The code to execute if the value isn't cached.
     * @param integer $lifetime  The lifetime of the object in the cache.
     *
     * Example:
     *
     * $foo = $cache->getOutput('myContent', 'function($arg1, $arg2)', $date);
     *
     * @return mixed  Any return status.
     * @access public
     */
    function getOutput($oid, $code, $lifetime)
    {
        if ($data = $this->_fetch($oid, $lifetime)) {
            return $data;
        } else {
            $data = $this->_call($code, 'output');
            if (!is_a($data, 'PEAR_Error')) {
                $this->_store($oid, $data);
            }
            return $data;
        }
    }

    /**
     * Outputs the result of a cacheable function or method that
     * prints its results, only actually calling it if there isn't a
     * cached version or the cache has expired.
     *
     * @param string  $oid       The cache key.
     * @param string  $code      The code to execute if the value isn't cached.
     * @param integer $lifetime  The lifetime of the object in the cache.
     *
     * Example:
     *
     * $cache->printOutput('myContent', 'function($arg1, $arg2)', $date);
     *
     * @return mixed  Any return status.
     * @access public
     */
    function printOutput($oid, $code, $lifetime)
    {
        if ($this->_output($oid, $lifetime)) {
            return true;
        } else {
            $data = $this->_call($code, 'output');
            if (is_a($data, 'PEAR_Error')) {
                return $data;
            }

            $this->_store($oid, $data);
            echo $data;
            return true;
        }
    }

    /**
     * Static utility method for caching the results of object calls.
     * When called with $object and $function set, they are stored as
     * the current object/function to call. When called with no
     * arguments, $object->$function() is executed.
     *
     * Example:
     *   Horde_Cache::cacheObject($this, 'getCacheable');
     *   $ob = $cache->getData($cid, 'Horde_Cache::cacheObject()', $conf['cache']['default_lifetime']);
     */
    function setCacheObject(&$object, $function)
    {
        $GLOBALS['_horde_cache_object'] = &$object;
        $GLOBALS['_horde_cache_function'] = $function;
    }

    /**
     * Static utility method for caching the results of object
     * calls. Executes the cached object function.
     *
     * Example:
     *   Horde_Cache::setCacheObject($this, 'getCacheable');
     *   $ob = $cache->getData($cid, 'Horde_Cache::getCacheObject()', $conf['cache']['default_lifetime']);
     */
    function getCacheObject()
    {
        if (is_null($GLOBALS['_horde_cache_object']) || is_null($GLOBALS['_horde_cache_function'])) {
            return '';
        } else {
            return $GLOBALS['_horde_cache_object']->$GLOBALS['_horde_cache_function']();
        }
    }

    /**
     * Execute $code. $code is expected to EITHER return its results
     * or to output them. If it does both, only the output will be
     * returned.
     *
     * @access private
     *
     * @param string $code  The PHP code to execute.
     * @param string $mode  (optional) Return 'result' or 'output'?
     *                      Defaults to an array of both.
     *
     * @return string  The results or output of $code.
     */
    function _call($code, $mode = null)
    {
        // Make sure we have a trailing ;.
        if (substr($code, -1) != ';') {
            $code .= ';';
        }

        // Store the result in $result.
        $code = '$result = ' . $code;

        // Initialize $result so we always have something to return.
        $result = null;

        // Start the output buffer so that we can catch if $code
        // outputs results instead of returning them.
        ob_start();

        @eval($code);

        // Check output/results.
        $output = ob_get_contents();
        ob_end_clean();

        switch ($mode) {
        case 'result':
            return $result;

        case 'output':
            return $output;

        default:
            return array('result' => $result,
                         'output' => $output);
        }
    }

    /**
     * Attempts to store an object in the cache.
     *
     * @access abstract
     *
     * @param string $oid  Object ID used as the caching key.
     * @param mixed $data  Data to store in the cache.
     *
     * @return boolean  True on success, false on failure.
     */
    function _store($oid, $data)
    {
        return true;
    }

    /**
     * Attempts to retrieve a cached object and return it to the
     * caller.
     *
     * @access abstract
     *
     * @param string  $oid        Object ID to query.
     * @param integer $lifetime   Lifetime of the object in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function _fetch($oid, $lifetime = 1)
    {
        return false;
    }

    /**
     * Attempts to directly output a cached object.
     *
     * @access abstract
     *
     * @param string $oid             Object ID to query.
     * @param integer $lifetime   Lifetime of the object in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function _output($oid, $lifetime = 1)
    {
        return false;
    }

    /**
     * Attempts to return a concrete Horde_Cache instance based on
     * $driver.
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Horde_Cache subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is
     *                                dynamically included. If $driver is an
     *                                array, then we will look in
     *                                $driver[0]/lib/Cache/ for the subclass
     *                                implementation named $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object Horde_Cache  The newly created concrete Horde_Cache instance,
     *                             or false on error.
     */
    function &factory($driver, $params = array())
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);
        if (empty($driver) || $driver == 'none') {
            return $ret = &new Horde_Cache($params);
        }

        if (!empty($app)) {
            require_once $app . '/lib/Cache/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/Cache/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Cache/' . $driver . '.php';
        } else {
            @include_once 'Horde/Cache/' . $driver . '.php';
        }
        $class = 'Horde_Cache_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
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
     * @access public
     *
     * @param mixed $driver           The type of concrete Horde_Cache subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is
     *                                dynamically included. If $driver is an
     *                                array, then we will look in
     *                                $driver[0]/lib/Cache/ for the subclass
     *                                implementation named $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @since Horde 2.2
     *
     * @return object Horde_Cache  The concrete Horde_Cache reference,
     *                             or false on error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!array_key_exists($signature, $instances)) {
            $instances[$signature] = &Horde_Cache::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
