<?php
/**
 * The Cache_zps:: class provides a Zps Performance Suite
 * implementation of the Horde caching system.
 *
 * $Horde: framework/Cache/Cache/zps.php,v 1.4 2004/01/01 15:14:08 jan Exp $
 *
 * Copyright 2003-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Cache
 */
class Horde_Cache_zps extends Horde_Cache {

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
        return output_cache_fetch($oid, $code, $lifetime);
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
        echo output_cache_fetch($oid, $code, $lifetime);
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
        ob_start();
        output_cache_output($oid, $code, $lifetime);
        $output = ob_get_contents();
        ob_end_clean();
        return $output;
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
        return output_cache_output($oid, $code, $lifetime);
    }

}
