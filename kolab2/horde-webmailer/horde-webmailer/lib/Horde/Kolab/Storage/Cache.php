<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage/Cache.php,v 1.2.2.4 2009-01-06 15:23:18 jan Exp $
 */

/** We need the Horde Cache system for caching */
require_once 'Horde/Cache.php';

/**
 * The Kolab_Cache class provides a cache for the Kolab
 * storage for groupware objects
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage/Cache.php,v 1.2.2.4 2009-01-06 15:23:18 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @package Kolab_Storage
 */
class Kolab_Cache {

    /**
     * The version of the cache we loaded.
     *
     * @var int
     */
    var $_version;

    /**
     * The internal version of the cache format represented by the
     * code.
     *
     * @var int
     */
    var $_base_version = 1;

    /**
     * The version of the data format provided by the storage handler.
     *
     * @var int
     */
    var $_data_version;

    /**
     * The version of the cache format that includes the data version.
     *
     * @var int
     */
    var $_cache_version = -1;

    /**
     * A validity marker for a share in the cache. This allows the
     * storage handler to invalidate the cache for this share.
     *
     * @var int
     */
    var $validity;

    /**
     * A nextid marker for a share in the cache. This allows the
     * storage handler to invalidate the cache for this share.
     *
     * @var int
     */
    var $nextid;

    /**
     * The objects of the current share.
     *
     *   | objects: key is uid (GUID)
     *   | ----------- hashed object data
     *                 |----------- uid: object id (GUID)
     *   |             |----------- all fields from kolab specification
     *
     * @var array
     */
    var $objects;

    /**
     * The uid<->object mapping of the current share.
     *
     *   | uids   Mapping between imap uid and object uids: imap uid -> object uid
     *            Special: A value of "false" means we've seen the uid
     *                     but we deciced to ignore it in the future
     *
     * @var array
     */
    var $uids;

    /**
     * The unique key for the currently loaded data.
     *
     * @var string
     */
    var $_key;

    /**
     * The link to the horde cache.
     *
     * @var Horde_Cache
     */
    var $_horde_cache;

    /**
     * Constructor.
     */
    function Kolab_Cache()
    {
        /**
         * We explicitly select the file based cache to ensure
         * that different users have access to the same cache
         * data. I am not certain this is guaranteed for the other
         * possible cache drivers.
         */
        $this->_horde_cache = &Horde_Cache::singleton('file',
                                                      array('prefix' => 'kolab_cache',
                                                            'dir' => Horde::getTempDir()));
    }

    /**
     * Attempts to return a reference to a concrete
     * Kolab_Cache instance.  It will only create a new
     * instance if no Kolab_Cache instance currently exists.
     *
     * This method must be invoked as: $var = &Kolab_Cache::singleton()
     *
     * @return Kolab_Cache The concrete Kolab_Cache
     *                     reference, or false on error.
     */
    function &singleton()
    {
        static $kolab_cache;

        if (!isset($kolab_cache)) {
            $kolab_cache = new Kolab_Cache();
        }

        return $kolab_cache;
    }

    /**
     * Load the cached share data identified by $key.
     *
     * @param string $key          Access key to the cached data.
     * @param int    $data_version A version identifier provided by
     *                             the storage manager.
     * @param bool   $force        Force loading the cache.
     */
    function load($key, $data_version, $force = false)
    {
        if (!$force && $this->_key == $key
            && $this->_data_version == $data_version) {
            return;
        }

        $this->_key = $key;
        $this->_data_version = $data_version;
        $this->_cache_version = ($data_version << 8) | $this->_base_version;

        $this->reset();

        $cache = $this->_horde_cache->get($this->_key, 0);

        if (!$cache) {
            return;
        }

        $data = unserialize($cache);

        // Delete disc cache if it's from an old version
        if ($data['version'] != $this->_cache_version) {
            $this->_horde_cache->expire($this->_key);
            $this->reset();
        } else {
            $this->_version = $data['version'];
            $this->validity = $data['uidvalidity'];
            $this->nextid = $data['uidnext'];
            $this->objects = $data['objects'];
            $this->uids = $data['uids'];
        }
    }

    /**
     * Load a cached attachment.
     *
     * @param string $key          Access key to the cached data.
     *
     * @return mixed The data of the object.
     */
    function loadAttachment($key)
    {
        return $this->_horde_cache->get($key, 0);
    }

    /**
     * Cache an attachment.
     *
     * @param string $key  Access key to the cached data.
     * @param string $data The data to be cached.
     *
     * @return boolean True if successfull.
     */
    function storeAttachment($key, $data)
    {
        return $this->_horde_cache->set($key, $data);
    }

    /**
     * Initialize the cache structure.
     */
    function reset()
    {
        $this->_version = $this->_cache_version;
        $this->validity = -1;
        $this->nextid = -1;
        $this->objects = array();
        $this->uids = array();
    }

    /**
     * Save the share data in the cache.
     *
     * @return boolean True on success.
     */
    function save()
    {
        if (!isset($this->_key)) {
            return PEAR::raiseError('The cache has not been loaded yet!');
        }

        $data = array('version' => $this->_version,
                      'uidvalidity' =>  $this->validity,
                      'uidnext' =>  $this->nextid,
                      'objects' =>  $this->objects,
                      'uids' =>  $this->uids);

        return $this->_horde_cache->set($this->_key,
                                        serialize($data));
    }

    /**
     * Store an object in the cache.
     *
     * @param int     $id             The storage ID.
     * @param string  $object_id      The object ID.
     * @param array   $object         The object data.
     */
    function store($id, $object_id, &$object)
    {
        $this->uids[$id] = $object_id;
        $this->objects[$object_id] = $object;
    }

    /**
     * Mark the ID as invalid (cannot be correctly parsed).
     *
     * @param int     $id       The ID of the storage item to ignore.
     */
    function ignore($id)
    {
        $this->uids[$id] = false;
    }

    /**
     * Deliberately expire a cache.
     */
    function expire()
    {
        if (!isset($this->_key)) {
            return PEAR::raiseError('The cache has not been loaded yet!');
        }

        $this->_version = -1;
        $this->save();
        $this->load($this->_key, $this->_data_version, true);
    }

}


