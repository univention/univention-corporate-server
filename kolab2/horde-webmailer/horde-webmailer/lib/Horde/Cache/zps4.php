<?php
/**
 * The Horde_Cache_zps4:: class provides a Zend Performance Suite
 * (version 4.0+) implementation of the Horde caching system.
 *
 * $Horde: framework/Cache/Cache/zps4.php,v 1.1.10.9 2009-01-06 15:22:56 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_Cache
 */
class Horde_Cache_zps4 extends Horde_Cache {

    /**
     * Attempts to retrieve a piece of cached data and return it to the caller.
     *
     * @param string  $key       Cache key to fetch.
     * @param integer $lifetime  Lifetime of the key in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function get($key, $lifetime = 1)
    {
        return output_cache_get($key, $lifetime);
    }

    /**
     * Attempts to store an object to the cache.
     *
     * @param string $key        Cache key (identifier).
     * @param mixed  $data       Data to store in the cache.
     * @param integer $lifetime  Data lifetime. @since Horde 3.2 [Not used]
     *
     * @return boolean  True on success, false on failure.
     */
    function set($key, $data, $lifetime = null)
    {
        output_cache_put($key, $data);
        return true;
    }

    /**
     * Checks if a given key exists in the cache, valid for the given lifetime.
     *
     * @param string  $key       Cache key to check.
     * @param integer $lifetime  Lifetime of the key in seconds.
     *
     * @return boolean  Existance.
     */
    function exists($key, $lifetime = 1)
    {
        $exists = output_cache_exists($key, $lifetime);
        output_cache_stop();
        return $exists;
    }

    /**
     * Expire any existing data for the given key.
     *
     * @param string $key  Cache key to expire.
     *
     * @return boolean  Success or failure.
     */
    function expire($key)
    {
        return output_cache_remove_key($key);
    }

}
