<?php
/**
 * The Horde_Cache_apc:: class provides an Alternative PHP Cache implementation
 * of the Horde caching system.
 *
 * $Horde: framework/Cache/Cache/apc.php,v 1.9.2.1 2007-12-20 13:48:51 jan Exp $
 *
 * Copyright 2006-2007 Duck <duck@obala.net>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.2
 * @package Horde_Cache
 */
class Horde_Cache_apc extends Horde_Cache {

    /**
     * Attempts to retrieve a piece of cached data and return it to
     * the caller.
     *
     * @param string  $key       Cache key to fetch.
     * @param integer $lifetime  Lifetime of the key in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function get($key, $lifetime = 1)
    {
        $this->_setExpire($key, $lifetime);
        return apc_fetch($key);
    }

    /**
     * Attempts to store an object to the cache.
     *
     * @param string $key        Cache key (identifier).
     * @param mixed  $data       Data to store in the cache.
     * @param integer $lifetime  Data lifetime. @since Horde 3.2
     *
     * @return boolean  True on success, false on failure.
     */
    function set($key, $data, $lifetime = null)
    {
        $lifetime = $this->_getLifetime($lifetime);
        apc_store($key . '_expire', time(), $lifetime);
        return apc_store($key, $data, $lifetime);
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
        $this->_setExpire($key, $lifetime);
        return apc_fetch($key) === false ? false : true;
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
        apc_delete($key . '_expire');
        return apc_delete($key);
    }

    /**
     * Set expire time on each call since APC sets it on cache
     * creation.
     *
     * @access private
     *
     * @param string  $key   Cache key to expire.
     * @param integer $lifetime  Lifetime of the data in seconds.
     */
    function _setExpire($key, $lifetime)
    {
        if ($lifetime == 0) {
            // Don't expire.
            return true;
        }

        $expire = apc_fetch($key . '_expire');

        // Set prune period.
        if ($expire + $lifetime < time()) {
            // Expired
            apc_delete($key);
            apc_delete($key . '_expire');
            $lifetime = 0;
        } else {
            // Not Expired
            $lifetime = ($expire + $lifetime) - time();
        }

        return $lifetime;
    }

}
