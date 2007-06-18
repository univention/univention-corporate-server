<?php
// +----------------------------------------------------------------------+
// | PEAR :: Cache :: MDB Container                                       |
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
// | Note: This is a MDB-oriented rewrite of Cache/Container/db.php.      |
// | Thanks to Lukas Smith for his patience in answering my questions     |
// +----------------------------------------------------------------------+
// | Author: Lorenzo Alberton <l.alberton at quipo.it>                    |
// +----------------------------------------------------------------------+
//
// $Id: mdb.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $

require_once 'MDB.php';
require_once 'Cache/Container.php';

/**
* PEAR/MDB Cache Container.
*
* NB: The field 'changed' has no meaning for the Cache itself. It's just there
* because it's a good idea to have an automatically updated timestamp
* field for debugging in all of your tables.
*
* A XML MDB-compliant schema example for the table needed is provided.
* Look at the file "mdb_cache_schema.xml" for that.
*
* ------------------------------------------
* A basic usage example:
* ------------------------------------------
*
* $dbinfo = array(
*   'database'    => 'dbname',
*   'phptype'     => 'mysql',
*   'username'    => 'root',
*   'password'    => '',
*   'cache_table' => 'cache'
* );
*
*
* $cache = new Cache('mdb', $dbinfo);
* $id = $cache->generateID('testentry');
*
* if ($data = $cache->get($id)) {
*    echo 'Cache hit.<br />Data: '.$data;
*
* } else {
*   $data = 'data of any kind';
*   $cache->save($id, $data);
*   echo 'Cache miss.<br />';
* }
*
* ------------------------------------------
*
* @author   Lorenzo Alberton <l.alberton at quipo.it>
* @version  $Id: mdb.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $
* @package  Cache
*/
class Cache_Container_mdb extends Cache_Container {

    /**
     * Name of the MDB table to store caching data
     *
     * @see  Cache_Container_file::$filename_prefix
     */
    var $cache_table = '';

    /**
     * PEAR MDB object
     *
     * @var  object PEAR_MDB
     */
    var $db;

    /**
     * Constructor
     *
     * @param mixed Array with connection info or dsn string
     */
    function Cache_Container_mdb($options)
    {
        $this->db = &MDB::Connect($options);
        if(MDB::isError($this->db)) {
           return new Cache_Error('MDB::connect failed: '
                    . $this->db->getMessage(), __FILE__, __LINE__);
        } else {
            $this->db->setFetchMode(MDB_FETCHMODE_ASSOC);
        }
        $this->setOptions($options, array_merge($this->allowed_options,
                                         array('dsn', 'cache_table')));
    }

    /**
     * Fetch in the db the data that matches input parameters
     *
     * @param    string  dataset ID
     * @param    string  cache group
     * @return   mixed   dataset value or NULL/Cache_Error on failure
     * @access   public
     */
    function fetch($id, $group)
    {
        $query = 'SELECT cachedata FROM ' . $this->cache_table
                .' WHERE id='       . $this->db->getTextValue($id)
                .' AND cachegroup=' . $this->db->getTextValue($group);
        if($res = $this->db->query($query)) {
            if($this->db->endOfResult($res)) {
                //no rows returned
                $data = array(NULL, NULL, NULL);
            } else {
                $clob = $this->db->fetchClob($res,0,'cachedata');
                if(!MDB::isError($clob)) {
                    $cached_data = '';
                    while(!$this->db->endOfLOB($clob)) {
                        if(MDB::isError($error =
                                    $this->db->readLob($clob,$data,8000)<0)) {
                            return new Cache_Error('MDB::query failed: '
                                    . $error->getMessage(), __FILE__, __LINE__);
                        }
                        $cached_data .= $data;
                    }
                    unset($data);
                    $this->db->destroyLob($clob);
                    $this->db->freeResult($res);

                    //finished fetching LOB, now fetch other fields...
                    $query = 'SELECT userdata, expires FROM ' . $this->cache_table
                            .' WHERE id='       . $this->db->getTextValue($id)
                            .' AND cachegroup=' . $this->db->getTextValue($group);
                    if($res = $this->db->query($query)) {
                        $row = $this->db->fetchInto($res);
                        if (is_array($row)) {
                            $data = array(
                                        $row['expires'],
                                        $this->decode($cached_data),
                                        $row['userdata']
                                    );
                        } else {
                            $data = array(NULL, NULL, NULL);
                        }
                    } else {
                        $data = array(NULL, NULL, NULL);
                    }
                } else {
                    return new Cache_Error('MDB::query failed: '
                             . $clob->getMessage(), __FILE__, __LINE__);
                }
            }
            $this->db->freeResult($res);
        } else {
            //return new Cache_Error('MDB::query failed: '
            //          . $result->getMessage(), __FILE__, __LINE__);
            $data = array(NULL, NULL, NULL);
        }

        // last used required by the garbage collection
        $query = 'UPDATE '          . $this->cache_table
                .' SET changed='    . time()
                .' WHERE id='       . $this->db->getTextValue($id)
                .' AND cachegroup=' . $this->db->getTextValue($group);

        $res = $this->db->query($query);
        if (MDB::isError($res)) {
            return new Cache_Error('MDB::query failed: '
                . $this->db->errorMessage($res), __FILE__, __LINE__);
        }
        return $data;
    }

   /**
     * Stores a dataset in the database
     *
     * If dataset_ID already exists, overwrite it with new data,
     * else insert data in a new record.
     *
     * @param    string  dataset ID
     * @param    mixed   data to be cached
     * @param    integer expiration time
     * @param    string  cache group
     * @param    string  userdata
     * @access   public
     */
    function save($id, $data, $expires, $group, $userdata)
    {
        global $db;
        $this->flushPreload($id, $group);

        $fields = array(
            'id'        => array(
                            'Type'   => 'text',
                            'Value'  => $id,
                            'Key'    => true
                        ),
            'userdata'  => array(
                            'Type'   => 'integer',
                            'Value'  => $userdata,
                            'Null'   => ($userdata ? false : true)
                        ),
            'expires'   => array(
                            'Type'   => 'integer',
                            'Value'  => $this->getExpiresAbsolute($expires)
                        ),
            'cachegroup' => array(
                            'Type'   => 'text',
                            'Value'  => $group
                        )
            );

        $result = $this->db->replace($this->cache_table, $fields);

        if(MDB::isError($result)) {
            //Var_Dump::display($result);
            return new Cache_Error('MDB::query failed: '
                    . $this->db->errorMessage($result), __FILE__, __LINE__);
        }
        unset($fields); //end first part of query
        $query2 = 'UPDATE '   . $this->cache_table
                 .' SET cachedata=?'
                 .' WHERE id='. $this->db->getTextValue($id);

        if(($prepared_query = $this->db->prepareQuery($query2))) {
            $char_lob = array(
                            'Error' => '',
                            'Type' => 'data',
                            'Data' => $this->encode($data)
                        );
            if(!MDB::isError($clob = $this->db->createLob($char_lob))) {
                $this->db->setParamClob($prepared_query,1,$clob,'cachedata');
                if(MDB::isError($error=$this->db->executeQuery($prepared_query))) {
                    return new Cache_Error('MDB::query failed: '
                            . $error->getMessage() , __FILE__, __LINE__);
                }
                $this->db->destroyLob($clob);
            } else {
                // creation of the handler object failed
                return new Cache_Error('MDB::query failed: '
                        . $clob->getMessage() , __FILE__, __LINE__);
            }
            $this->db->freePreparedQuery($prepared_query);
        } else {
            //prepared query failed
            return new Cache_Error('MDB::query failed: '
                    . $prepared_query->getMessage() , __FILE__, __LINE__);
        }
    }

    /**
     * Removes a dataset from the database
     *
     * @param    string  dataset ID
     * @param    string  cache group
     */
    function remove($id, $group)
    {
        $this->flushPreload($id, $group);

        $query = 'DELETE FROM '     . $this->cache_table
                .' WHERE id='       . $this->db->getTextValue($id)
                .' AND cachegroup=' . $this->db->getTextValue($group);

        $res = $this->db->query($query);
        if (MDB::isError($res)) {
            return new Cache_Error('MDB::query failed: '
                    . $this->db->errorMessage($res), __FILE__, __LINE__);
        }
    }

    /**
     * Remove all cached data for a certain group, or empty
     * the cache table if no group is specified.
     *
     * @param    string  cache group
     */
    function flush($group = '')
    {
        $this->flushPreload();

        if ($group) {
            $query = 'DELETE FROM '       . $this->cache_table
                    .' WHERE cachegroup=' . $this->db->getTextValue($group);
        } else {
            $query = 'DELETE FROM ' . $this->cache_table;
        }

        $res = $this->db->query($query);
        if (MDB::isError($res)) {
            return new Cache_Error('MDB::query failed: '
                . $this->db->errorMessage($res), __FILE__, __LINE__);
        }
    }

    /**
     * Check if a dataset ID/group exists.
     *
     * @param    string  dataset ID
     * @param    string  cache group
     * @return   boolean
     */
    function idExists($id, $group)
    {
        $query = 'SELECT id FROM '  . $this->cache_table
                .' WHERE id='       . $this->db->getTextValue($id)
                .' AND cachegroup=' . $this->db->getTextValue($group);
        echo $query;
        $res = $this->db->query($query);
        if (MDB::isError($res)) {
            return new Cache_Error('MDB::query failed: '
                    . $this->db->errorMessage($res), __FILE__, __LINE__);
        }
        $row = $this->db->fetchInto($res);

        if (is_array($row)) {
            return true;
        } else {
            return false;
        }
    }

    /**
     * Garbage collector.
     *
     * @param    int maxlifetime
     */
    function garbageCollection($maxlifetime)
    {
        $this->flushPreload();
        $query = 'DELETE FROM '        . $this->cache_table
                .' WHERE (expires <= ' . time()
                .' AND expires > 0) OR changed <= '. time() - $maxlifetime;

        $res = $this->db->query($query);

        $query = 'SELECT sum(length(cachedata)) as CacheSize FROM '
                . $this->cache_table;

        $cachesize = $this->db->getOne($query);
        if (MDB::isError($cachesize)) {
            return new Cache_Error('MDB::query failed: '
                   . $this->db->errorMessage($cachesize), __FILE__, __LINE__);
        }
        //if cache is to big.
        if ($cachesize > $this->highwater)
        {
            //find the lowwater mark.
            $query = 'SELECT length(cachedata) as size, changed FROM '
                    . $this->cache_table .' ORDER BY changed DESC';

            $res = $this->db->query($query);
            if (MDB::isError($res)) {
               return new Cache_Error('MDB::query failed: '
                    . $this->db->errorMessage($res), __FILE__, __LINE__);
            }
            $numrows = $this->db->numRows($res);
            $keep_size = 0;
            while ($keep_size < $this->lowwater && $numrows--) {
                $entry = $this->db->fetchInto($res,MDB_FETCHMODE_ASSOC);
                $keep_size += $entry['size'];
            }

            //delete all entries, which were changed before the "lowwater mark"
            $query = 'DELETE FROM ' . $this->cache_table
                    .' WHERE changed<='.($entry['changed'] ? $entry['changed'] : 0);

            $res = $this->db->query($query);
            if (MDB::isError($res)) {
               return new Cache_Error('MDB::query failed: '
                    . $this->db->errorMessage($res), __FILE__, __LINE__);
            }
        }
    }

}
?>