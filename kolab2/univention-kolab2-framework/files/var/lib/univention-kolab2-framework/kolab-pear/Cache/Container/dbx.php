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
// | Authors: Christian Stocker <chregu@phant.ch>                         |
// +----------------------------------------------------------------------+
//
// $Id: dbx.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $


require_once 'Cache/Container.php';

/**
* ext/dbx Cache Container.
*
* WARNING: Other systems might or might not support certain datatypes of 
* the tables shown. As far as I know there's no large binary 
* type in SQL-92 or SQL-99. Postgres seems to lack any 
* BLOB or TEXT type, for MS-SQL you could use IMAGE, don't know 
* about other databases. Please add sugestions for other databases to 
* the inline docs.
*
* The field 'changed' has no meaning for the Cache itself. It's just there 
* because it's a good idea to have an automatically updated timestamp
* field for debugging in all of your tables.
*
* For _MySQL_ you need this DB table:
*
* CREATE TABLE cache (
*   id          CHAR(32) NOT NULL DEFAULT '',
*   cachegroup  VARCHAR(127) NOT NULL DEFAULT '',
*   cachedata   BLOB NOT NULL DEFAULT '',
*   userdata    VARCHAR(255) NOT NULL DEFAULT '',
*   expires     INT(9) NOT NULL DEFAULT 0,
*  
*   changed     TIMESTAMP(14) NOT NULL,
*  
*   INDEX (expires),
*   PRIMARY KEY (id, cachegroup)
* )
*
* @author   Christian Stocker <chregu@phant.ch>
* @version  $Id: dbx.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $
* @package  Cache
*/
class Cache_Container_dbx extends Cache_Container {

    /**
    * Name of the DB table to store caching data
    * 
    * @see  Cache_Container_file::$filename_prefix
    */  
    var $cache_table = '';

    /**
    * DBx module to use
    *
    *  at the moment only mysql or odbc
    * 
    * @var  string
    */
    var $module = '';

    /**
    * DB host to use
    * 
    * @var  string
    */
    var $host = '';

    /**
    * DB database to use
    * 
    * @var  string
    */
    var $db = '';

    /**
    * DB username to use
    * 
    * @var  string
    */
    var $username = '';

    /**
    * DB password to use
    * 
    * @var  string
    */
    var $password = '';

    /**
    * DBx handle object
    * 
    * @var  object DBx handle
    */
    var $db;
    
    
    /**
    * Establish a persistent connection?
    * 
    * @var  boolean 
    */
    var $persistent = true;
    

    function Cache_Container_dbx($options)
    {
        if (!is_array($options) ) {
            return new Cache_Error('No options specified!', __FILE__, __LINE__);
        }

        $this->setOptions($options,  array_merge($this->allowed_options, array('module','host','db','username','password', 'cache_table', 'persistent')));

        if (!$this->module)
            return new Cache_Error('No module specified!', __FILE__, __LINE__);

        $this->db = dbx_connect($this->module, $this->host, $this->db, $this->username, $this->password, $this->persistent);

        if (dbx_error($this->db)) {
            return new Cache_Error('DBx connect failed: ' . dbx_error($this->db), __FILE__, __LINE__);
        } else {
            //not implemented yet in dbx
            //$this->db->setFetchMode(DB_FETCHMODE_ASSOC);
        }
    }

    function fetch($id, $group)
    {
        $query = sprintf("SELECT cachedata, userdata, expires FROM %s WHERE id = '%s' AND cachegroup = '%s'",
                         $this->cache_table,
                         addslashes($id),
                         addslashes($group)
                        );

        $res = dbx_query($this->db, $query);
        if (dbx_error($this->db))
            return new Cache_Error('DBx query failed: ' . dbx_error($this->db), __FILE__, __LINE__);

        $row = $res->data[0];

        if (is_array($row))
            $data = array($row['expires'], $this->decode($row['cachedata']), $row['userdata']);
        else 
            $data = array(NULL, NULL, NULL);

        // last used required by the garbage collection   
        // WARNING: might be MySQL specific         
        $query = sprintf("UPDATE %s SET changed = (NOW() + 0) WHERE id = '%s' AND cachegroup = '%s'",
                            $this->cache_table,
                            addslashes($id),
                            addslashes($group)
                          );
        
        $res = dbx_query($this->db, $query);
        if (dbx_error($this->db))
            return new Cache_Error('DBx query failed: ' . dbx_error($this->db), __FILE__, __LINE__);                             
            
        return $data;            
    }

    /**
    * Stores a dataset.
    * 
    * WARNING: we use the SQL command REPLACE INTO this might be 
    * MySQL specific. As MySQL is very popular the method should
    * work fine for 95% of you.
    */
    function save($id, $data, $expires, $group, $userdata)
    {
        $this->flushPreload($id, $group);

        $query = sprintf("REPLACE INTO %s (userdata, cachedata, expires, id, cachegroup) VALUES ('%s', '%s', %d, '%s', '%s')",
                         $this->cache_table,
                         addslashes($userdata),
                         addslashes($this->encode($data)),
                         $this->getExpiresAbsolute($expires) ,
                         addslashes($id),
                         addslashes($group)
                        );

        $res = dbx_query($this->db, $query);

        if (dbx_error($this->db)) {
            return new Cache_Error('DBx query failed: ' . dbx_error($this->db) , __FILE__, __LINE__);
        }
    }

    function remove($id, $group)
    {
        $this->flushPreload($id, $group);

        $query = sprintf("DELETE FROM %s WHERE id = '%s' and cachegroup = '%s'",
                         $this->cache_table,
                         addslashes($id),
                         addslashes($group)
                        );

        $res = dbx_query($this->db, $query);

        if (dbx_error($this->db))
            return new Cache_Error('DBx query failed: ' . dbx_error($this->db), __FILE__, __LINE__);
    }

    function flush($group = '')
    {
        $this->flushPreload();

        if ($group) {
            $query = sprintf("DELETE FROM %s WHERE cachegroup = '%s'", $this->cache_table, addslashes($group));
        } else {
            $query = sprintf("DELETE FROM %s", $this->cache_table);
        }

        $res = dbx_query($this->db,$query);

        if (dbx_error($this->db))
            return new Cache_Error('DBx query failed: ' . dbx_error($this->db), __FILE__, __LINE__);
    }

    function idExists($id, $group)
    {
        $query = sprintf("SELECT id FROM %s WHERE ID = '%s' AND cachegroup = '%s'",
                         $this->cache_table,
                         addslashes($id),
                         addslashes($group)
                        );

        $res = dbx_query($this->db, $query);

        if (dbx_error($this->db))
            return new Cache_Error('DBx query failed: ' . dbx_error($this->db), __FILE__, __LINE__);


        $row = $res[0];

        if (is_array($row)) {
            return true;
        } else {
            return false;
        }
    }

    function garbageCollection($maxlifetime)
    {
        $this->flushPreload();
        
        $query = sprintf('DELETE FROM %s WHERE (expires <= %d AND expires > 0) OR changed <= (NOW() - %d)',
                         $this->cache_table,
                         time(),
                         $maxlifetime
                       );


        $res = dbx_query($this->db, $query);

        if (dbx_error($this->db))
            return new Cache_Error('DBx query failed: ' . dbx_error($this->db), __FILE__, __LINE__);

        $query = sprintf('select sum(length(cachedata)) as CacheSize from %s',
                         $this->cache_table
                       );

        $res = dbx_query($this->db, $query);
        //if cache is to big.
        if ($res->data[0][CacheSize] > $this->highwater)
        {
            //find the lowwater mark.
            $query = sprintf('select length(cachedata) as size, changed from %s order by changed DESC',
                                     $this->cache_table
                       );

            $res = dbx_query($this->db, $query);
            $keep_size=0;
            $i=0;
            while ($keep_size < $this->lowwater && $i < $res->rows )
            {

                $keep_size += $res->data[$i][size];
                $i++;
    }
    
            //delete all entries, which were changed before the "lowwwater mark"
            $query = sprintf('delete from %s where changed <= %s',
                                     $this->cache_table,
                                     $res->data[$i][changed]
                                   );
            $res = dbx_query($this->db, $query);
        }
    }
}
?>