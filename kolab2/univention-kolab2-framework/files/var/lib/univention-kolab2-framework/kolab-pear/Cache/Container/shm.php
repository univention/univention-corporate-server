<?php
// +----------------------------------------------------------------------+
// | PEAR :: Cache                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.0 of the PHP license,       |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Ulf Wendel <ulf.wendel@phpdoc.de>                           |
// |          Sebastian Bergmann <sb@sebastian-bergmann.de>               |
// +----------------------------------------------------------------------+
//
// $Id: shm.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $

require_once 'Cache/Container.php';

/**
* Stores cache data into shared memory.
*
* Well, this is not a very efficient implementation. Indeed it's much 
* slower than the file container as far as my tests showed. Files are 
* cached by most operating systems and it will be hard to write a faster 
* caching algorithm using PHP.
*
* @author   Ulf Wendel <ulf.wendel@phpdoc.de>
* @version  $Id: shm.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $
* @package  Cache
*/
class Cache_Container_shm extends Cache_Container {
    /**
    * Key of the semaphore used to sync the SHM access
    * 
    * @var  int
    */
    var $sem_key = NULL;

    /**
    * Permissions of the semaphore used to sync the SHM access
    * 
    * @var  int
    */
    var $sem_perm = 0644;

    /**
    * Semaphore handler
    * 
    * @var  resource
    */
    var $sem_id = NULL;

    /**
    * Key of the shared memory block used to store cache data
    *
    * @var  int
    */
    var $shm_key = NULL;

    /**
    * Size of the shared memory block used
    * 
    * Note: the container does only use _one_ shm block no more!
    * 
    * @var  int
    */        
    var $shm_size = 131072;

    /**
    * Permissions of the shared memory block
    * 
    * @var  int
    */
    var $shm_perm = 0644;

    /**
    * Shared memory handler
    * 
    * @var resource
    */
    var $shm_id = NULL;

    /**
    * Hash of cache entries
    * 
    * Used by the garbage collection to find old entries.
    *
    * @var  array
    */
    var $entries = array();

    /**
    * Number of bytes consumed by the cache
    * 
    * @var  int
    */
    var $total_size = 0;

    /**
    * Creates a shared memory container
    *
    * @param array    shm_key, sem_key, shm_size, sem_perm, shm_perm
    */    
    function Cache_Container_shm($options = '') {
        if (is_array($options))
            $this->setOptions($options, array_merge($this->allowed_options, 
                                                    array('shm_key',  'sem_key', 
                                                          'shm_size', 'sem_perm',
                                                          'shm_perm'
                                                         )
                                        )
                               );

        // Cache::Container high- and lowwater defaults should be overridden if
        // not already done by the user
        if (!isset($options['highwater'])) 
            $this->highwater = round(0.75 * 131072);
        if (!isset($options['lowwater']))
            $this->lowwater = round(0.5 * 131072);

        if (!isset($options['shm_size']))
            $this->shm_size = 131072;

        //get SHM and Semaphore handles
        if (!($this->shm_id = shmop_open($this->shm_key, 'c', $this->shm_perm, $this->shm_size)))
            new Cache_Error("Can't open SHM segment '{$this->shm_key}', size '{$this->shm_size}'.",
                            __FILE__,
                            __LINE__
                           );

        if (!($this->sem_id = sem_get($this->sem_key, 1, $this->sem_perm)))
            new Cache_Error("Can't get semaphore '{$this->sem_key}' using perms '{$this->sem_perm}'.",
                            __FILE__,
                            __LINE__
                           );

    } // end constructor

    function fetch($id, $group) {
        sem_acquire($this->sem_id);

        $cachedata = shmop_read($this->shm_id, 0, $this->shm_size);

        sem_release($this->sem_id);

        $cachedata = $this->decode($cachedata);

        if (!isset($cachedata[$group][$id]))
            return array(NULL, NULL, NULL);
        else 
            $cachedata = $cachedata[$group][$id];

        return array($cachedata['expire'],
                     $cachedata['cachedata'],
                     $cachedata['userdata']
                    );
    } // end func fetch

    function save($id, $data, $expire, $group, $userdata) {
        $this->flushPreload($id, $group);

        sem_acquire($this->sem_id);

        $cachedata = $this->decode(shmop_read($this->shm_id, 0, $this->shm_size));
        $cachedata[$group][$id] = array('expire'    => $this->getExpiresAbsolute($expire),
                                        'cachedata' => $data,
                                        'userdata'  => $userdata,
                                        'changed'   => time()
                                       );

        if (strlen($newdata = $this->encode($cachedata)) > $this->shm_size)
            $cachedata = $this->garbageCollection(time(), $cachedata);

        shmop_write($this->shm_id, $newdata, 0);

        sem_release($this->sem_id);

        return true;
    } // end func save

    function remove($id, $group) {
        $this->flushPreload($id, $group);

        sem_acquire($this->sem_id);

        $cachedata = $this->decode(shmop_read($this->shm_id, 0, $this->shm_size));
        unset($cachedata[$group][$id]);
        shmop_write($this->shm_id, $this->encode($cachedata), 0);

        sem_release($this->sem_id);
    } // end func remove

    function flush($group = '') {
        $this->flushPreload();

        sem_acquire($this->sem_id);

        shmop_write($this->shm_id, $this->encode(array()), 0);

        sem_release($this->sem_id);
    } // end func flush

    function idExists($id, $group) {
        sem_acquire($this->sem_id);

        $cachedata = shm_read($this->shm_id, 0, $this->shm_size);

        sem_release($this->sem_id);

        $cachedata = $this->decode($cachedata);

        return isset($cachedata[$group][$id]);
    } // end func isExists

    function garbageCollection($maxlifetime, $cachedata = array()) {
        if ($lock = empty($cachedata)) {
            sem_acquire($this->sem_id);
            $cachedata = $this->decode(shmop_read($this->shm_id, 0, $this->shm_size));
        }

        $this->doGarbageCollection($maxlifetime, &$cachedata);
        if ($this->total_size > $this->highwater) {
            krsort($this->entries);
            reset($this->entries);

            while ($this->total_size > $this->lowwater && list($size, $entries) = each($this->entries)) {
                reset($entries);

                while (list($k, $entry) = each($entries)) {
                    unset($cachedata[$entry['group']][$entry['id']]);
                    $this->total_size -= $size;
                }
            }
        }

        if ($lock)
            sem_release($this->sem_id);

        $this->entries = array();
        $this->total_size = 0;

        return $cachedata;           
    } // end func garbageCollection

    function doGarbageCollection($maxlifetime, &$cachedata) {
        $changed = time() - $maxlifetime;
        $removed = 0;

        reset($cachedata);

        while (list($group, $groupdata) = each($cachedata)) {
            reset($groupdata);

            while (list($id, $data) = each($groupdata)) {
                if ($data['expire'] < time() || $data['changed'] < $changed) {
                    unset($cachedata[$group][$id]);
                }
            }

            // ugly but simple to implement :/
            $size = strlen($this->encode($data));
            $this->entries[$size][] = array('group' => $group,
                                            'id'    => $id
                                           );

            $this->total_size += $size;
        }

        return $removed;
    }  // end func doGarbageCollection
} // end class Cache_Container_shm
?>
