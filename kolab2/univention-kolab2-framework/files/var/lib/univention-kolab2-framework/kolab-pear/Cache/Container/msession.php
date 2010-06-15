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
// +----------------------------------------------------------------------+
//
// $Id: msession.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $

require_once 'Cache/Container.php';

/**
* Stores cache contents in msessions.
*
* WARNING: experimental, untested
*
* @author   Ulf Wendel  <ulf.wendel@phpdoc.de>
* @version  $Id: msession.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $
*/
class Cache_Container_msession extends Cache_Container {


    /**
    * Length of the Cache-Identifier
    *
    * Note that the PEAR-Cache prefixes the ID with an md5() value
    * of the cache-group. A good value for the id_length
    * depends on the maximum number of entries per cache group.
    *
    * @var  int
    */
    var $id_length = 32;
    
    
    /**
    * Use msession_uniq to create a unique SID.
    * 
    * @var  boolean
    */
    var $uniq = true;
    
    
    /**
    * Establish a connection to a msession server?
    *
    * @var  boolean
    */
    var $connect = true;
   
   
    /**
    * msession host
    *
    * @var  string
    */  
    var $host = NULL;
    
   
    /**
    * msession port
    *
    * @var  string
    */
    var $port = NULL;
    
    
    /**
    * mesession server connection
    *
    * @var  resource msession
    */
    var $ms = NULL;

    
    function Cache_Container_msession($options = '') {
        if (is_array($options))
            $this->setOptions($options, array_merge($this->allowed_options, array('id_lenght', 'uniq', 'host', 'port', 'connect')));

        if ($connect) {            
            if (NULL == $this->host)
                new Cache_Error('No host specified.', __FILE__, __LINE__);
            if (NULL == $this->port)
                new Cache_Error('No port specified.', __FILE__, __LINE__);
        
            if (!($this->ms = msession_connect($this->host, $this->port)))
                new Cache_Error('Can not connect to the sever using host "' . $this->host . '" on port "' . $this->port . '"', __FILE__, __LINE__);
        }
        
    } // end func contructor

    function fetch($id, $group) {
    
        $id = strtoupper(md5($group)) . $id;
        $group = msession_get($id, '_pear_cache_data', NULL);
        
        if (NULL == $data)
            return array(NULL, NULL, NULL);
        
        return array($data['expires'], $data['cachedata'], $data['userdata']);
    } // end func fetch

    /**
    * Stores a dataset.
    *
    * WARNING: If you supply userdata it must not contain any linebreaks,
    * otherwise it will break the filestructure.
    */
    function save($id, $cachedata, $expires, $group, $userdata) {
        $this->flushPreload($id, $group);
        
        $cachedata      = $this->encode($cachedata);
        $expires_abs    = $this->getExpiresAbsolute($expires);

        $size = 1 + strlen($cachedata) + strlen($expires_abs) + strlen($userdata) + strlen($group);
        $size += strlen($size);
        
        $data = array(
                    'cachedata' => $cachedata, 
                    'expires'   => $expires_abs,
                    'userdata'  => $userdata
                  );
        $id = strtoupper(md5($group)) . $id;
                            
        msession_lock($id);
        
        if (!msession_set($id, '_pear_cache', true)) {
            msession_unlock($id);
            return new Cache_Error("Can't write cache data.", __FILE__, __LINE__);
        }
        
        if (!msession_set($id, '_pear_cache_data', $data)) {
            msession_unlock($id);
            return new Cache_Error("Can't write cache data.", __FILE__, __LINE__);
        }
        
        if (!msession_set($id, '_pear_cache_group', $group)) {
            msession_unlock($id);
            return new Cache_Error("Can't write cache data.", __FILE__, __LINE__);
        }
        
        if (!msession_set($id, '_pear_cache_size', $size)) {
            msession_unlock($id);
            return new Cache_Error("Can't write cache data.", __FILE__, __LINE__);
        }
        
        // let msession do some GC as well
        // note that msession works different from the PEAR Cache.
        // msession deletes an entry if it has not been used for n-seconds.
        // PEAR Cache deletes after n-seconds.
        if (0 != $expires)
            msession_timeout($id, $expires);
            
        msession_unlock($id);

        return true;
    } // end func save

    function remove($id, $group) {
        $this->flushPreload($id, $group);
    
        return msession_destroy(strtoupper(md5($group)) . $id);
    } // end func remove

    function flush($group) {
        $this->flushPreload();
      
        $sessions = msession_find('_pear_cache_group', $group);
        if (empty($sessions))
            return 0;
        
        foreach ($sessions as $k => $id)
            messsion_destroy($id);

        return count($sessions);
    } // end func flush

    function idExists($id, $group) {
        
        return (NULL == msession_get(strtoupper(md5($group)) . $id, '_pear_cache_group', NULL)) ? false : true;
    } // end func idExists

    /**
    * Deletes all expired files.
    *
    * Note: garbage collection should cause lot's of network traffic.
    *
    * @param    integer Maximum lifetime in seconds of an no longer used/touched entry
    * @throws   Cache_Error
    */
    function garbageCollection($maxlifetime) {
        $this->flushPreload();
        
        $sessions = msession_find('_pear_cache', true);
        if (empty($sessions))
            return true;
        
        $total = 0;
        $entries = array();
        
        foreach ($sessions as $k => $id) {
            $data = msession_get($id, '_pear_cache_data', NULL);
            if (NULL == $data)
                continue;
                
            if ($data['expires'] <= time()) {
                msession_destroy($id);
                continue;
            }
            
            $size = msession_get($id, '_pear_cache_size', NULL);
            $total += $size;
            $entries[$data['expires']] = array($id, $size);
        }
        
        if ($total > $this->highwater) {
            
            krsort($entries);
            reset($entries);
            
            while ($total > $this->lowwater && list($expires, $entry) = each($entries)) {
                msession_destroy($entry[0]);
                $total -= $entry[1];
            }
            
        }
        
        return true;
    } // end func garbageCollection
    
} // end class file
?>