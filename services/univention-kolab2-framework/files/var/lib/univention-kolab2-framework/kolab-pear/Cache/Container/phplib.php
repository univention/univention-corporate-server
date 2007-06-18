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
// $Id: phplib.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $

require_once 'Cache/Container.php';

/**
* Stores cache data into a database table using PHPLibs DB abstraction.
*
* WARNING: Other systems might or might not support certain datatypes of 
* the tables shown. As far as I know there's no large binary 
* type in SQL-92 or SQL-99. Postgres seems to lack any 
* BLOB or TEXT type, for MS-SQL you could use IMAGE, don't know 
* about other databases. Please add sugestions for other databases to 
* the inline docs.
*
* The field 'changed' is used by the garbage collection. Depending on 
* your databasesystem you might have to subclass fetch() and garbageCollection().
*
* For _MySQL_ you need this DB table:
*
* CREATE TABLE cache (
*   id          CHAR(32) NOT NULL DEFAULT '',
*   cachegroup  VARCHAR(127) NOT NULL DEFAULT '',
*   cachedata   BLOB NOT NULL DEFAULT '',
*   userdata    VARCHAR(255) NOT NULL DEFAUL '',
*   expires     INT(9) NOT NULL DEFAULT 0,
*  
*   changed     TIMESTAMP(14) NOT NULL,
*  
*   INDEX (expires),
*   PRIMARY KEY (id, cachegroup)
* )
*
* 
* @author   Ulf Wendel  <ulf.wendel@phpdoc.de>, Sebastian Bergmann <sb@sebastian-bergmann.de>
* @version  $Id: phplib.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $
* @package  Cache
* @see      save()
*/
class Cache_Container_phplib extends Cache_Container {
  
    /**
    * Name of the DB table to store caching data
    * 
    * @see  Cache_Container_file::$filename_prefix
    */  
    var $cache_table = 'cache';

    /**
    * PHPLib object
    * 
    * @var  object PEAR_DB
    */
    var $db;

    /**
    * Name of the PHPLib DB class to use
    * 
    * @var  string  
    * @see  $db_path, $local_path
    */
    var $db_class = '';

    /**
    * Filename of your local.inc
    * 
    * If empty, 'local.inc' is assumed.
    *
    * @var       string
    */
    var $local_file = '';

    /**
    * Include path for you local.inc
    *
    * HINT: If your're not using PHPLib's prepend.php you must 
    * take care that all classes (files) references by you 
    * local.inc are included automatically. So you might 
    * want to write a new local2.inc that only referrs to 
    * the database class (file) you're using and includes all required files.
    *
    * @var  string  path to your local.inc - make sure to add a trailing slash
    * @see  $local_file
    */
    var $local_path = '';

    /**
    * Creates an instance of a phplib db class to use it for storage.
    *
    * @param    mixed   If empty the object tries to used the 
    *                   preconfigured class variables. If given it 
    *                   must be an array with:
    *                     db_class => name of the DB class to use
    *                   optional:
    *                     db_file => filename of the DB class
    *                     db_path => path to the DB class
    *                     local_file => kind of local.inc
    *                     local_patk => path to the local.inc
    *                   see $local_path for some hints.s
    * @see  $local_path
    */
    function Cache_Container_phplib($options = '') {
        if (is_array($options))
            $this->setOptions($options,  array_merge($this->allowed_options, array('db_class', 'db_file', 'db_path', 'local_file', 'local_path')));

        if (!$this->db_class)
            return new Cache_Error('No database class specified.', __FILE__, __LINE__);

        // include the required files
        if ($this->db_file)
            include_once($this->db_path . $this->db_file);

        if ($this->local_file)
            include_once($this->local_path . $this->local_file);

        // create a db object 
        $this->db = new $this->db_class;
    } // end constructor

    function fetch($id, $group) {
        $query = sprintf("SELECT expires, cachedata, userdata FROM %s WHERE id = '%s' AND cachegroup = '%s'",
                            $this->cache_table, 
                            $id,
                            $group
                         );
        $this->db->query($query);
        if (!$this->db->Next_Record())
            return array(NULL, NULL, NULL);

        // last used required by the garbage collection   
        // WARNING: might be MySQL specific         
        $query = sprintf("UPDATE %s SET changed = (NOW() + 0) WHERE id = '%s' AND cachegroup = '%s'",
                            $this->cache_table,
                            $id,
                            $group
                          );
        $this->db->query($query);
        return array($this->db->f('expires'), $this->decode($this->db->f('cachedata')), $this->db->f('userdata'));
    } // end func fetch

    /**
    * Stores a dataset.
    * 
    * WARNING: we use the SQL command REPLACE INTO this might be 
    * MySQL specific. As MySQL is very popular the method should
    * work fine for 95% of you.
    */
    function save($id, $data, $expires, $group) {
        $this->flushPreload($id, $group);

        $query = sprintf("REPLACE INTO %s (cachedata, expires, id, cachegroup) VALUES ('%s', %d, '%s', '%s')",
                            $this->cache_table,
                            addslashes($this->encode($data)),
                            $this->getExpiresAbsolute($expires) ,
                            $id,
                            $group
                         );
        $this->db->query($query);

        return (boolean)$this->db->affected_rows(); 
    } // end func save

    function remove($id, $group) {
        $this->flushPreload($id, $group);
        $this->db->query(
                        sprintf("DELETE FROM %s WHERE id = '%s' AND cachegroup = '%s'",
                            $this->cache_table,
                            $id,
                            $group
                          )
                    );

        return (boolean)$this->db->affected_rows();
    } // end func remove

    function flush($group) {
        $this->flushPreload();

        if ($group) {
            $this->db->query(sprintf("DELETE FROM %s WHERE cachegroup = '%s'", $this->cache_table, $group));    
        } else {
            $this->db->query(sprintf("DELETE FROM %s", $this->cache_table));    
        }

        return $this->db->affected_rows();
    } // end func flush

    function idExists($id, $group) {
        $this->db->query(
                        sprintf("SELECT id FROM %s WHERE ID = '%s' AND cachegroup = '%s'", 
                            $this->cache_table,
                            $id, 
                            $group
                        )   
                    );

        return (boolean)$this->db->nf();                         
    } // end func isExists

    function garbageCollection($maxlifetime) {
        $this->flushPreload();

        $this->db->query( 
                        sprintf("DELETE FROM %s WHERE (expires <= %d AND expires > 0) OR changed <= (NOW() - %d)",
                            $this->cache_table, 
                            time(),
                            $maxlifetime
                        )
                    );

        //check for total size of cache
        $query = sprintf('select sum(length(cachedata)) as CacheSize from %s',
                         $this->cache_table
                       );

        $this->db->query($query);
        $this->db->Next_Record();
        $cachesize = $this->db->f('CacheSize');
        //if cache is to big.
        if ($cachesize > $this->highwater)
        {
            //find the lowwater mark.
            $query = sprintf('select length(cachedata) as size, changed from %s order by changed DESC',
                                     $this->cache_table
                       );
            $this->db->query($query);

            $keep_size=0;
            while ($keep_size < $this->lowwater && $this->db->Next_Record() )
            {
                $keep_size += $this->db->f('size');
            }
            //delete all entries, which were changed before the "lowwwater mark"
            $query = sprintf('delete from %s where changed <= '.$this->db->f('changed'),
                                     $this->cache_table
                                   );

            $this->db->query($query);
        }
    } // end func garbageCollection
}
?>