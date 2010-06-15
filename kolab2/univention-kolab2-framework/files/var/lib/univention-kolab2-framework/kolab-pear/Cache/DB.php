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
// | Authors: Sebastian Bergmann <sb@sebastian-bergmann.de>               |
// +----------------------------------------------------------------------+
//
// $Id: DB.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $

require_once 'Cache.php';
require_once 'DB.php';

/**
* Cache_DB
*
* @author       Sebastian Bergmann <sb@sebastian-bergmann.de>
* @module       Cache_DB
* @modulegroup  Cache_DB
* @package      Cache
* @version      $Revision: 1.1.2.1 $
* @access       public
*/
class Cache_DB extends Cache {
    /**
    * PEAR DB Object
    *
    * @var  object
    */
    var $db;

    /**
    * Lifetime of a cached result set (in seconds)
    *
    * @var  integer
    */
    var $expires = 3600;

    /**
    * PEAR DB DSN
    *
    * @var  string
    */
    var $dsn = '';

    /**
    * PEAR DB Options
    *
    * @var  mixed
    */
    var $options = false;

    /**
    * Fetchmode
    *
    * @var  integer
    */
    var $fetchmode = DB_FETCHMODE_ASSOC;

    /**
    * Fetchmode Object Class
    *
    * @var  string
    */
    var $fetchmode_object_class = 'DB_row';

    /**
    * Constructor
    *
    * @param    string  Name of container class
    * @param    array   Array with container class options
    * @param    integer Lifetime of a cached result set (in seconds)
    */
    function Cache_DB($container = 'file',
                      $container_options = array(
                        'cache_dir'       => '.',
                        'filename_prefix' => 'query_'
                      ),
                      $expires = 3600) {
        $this->Cache($container, $container_options);
        $this->expires = $expires;      
    }

    /**
    * PEAR-Deconstructor
    * Call deconstructor of parent,
    * close database connection if open
    */
    function _Cache_DB() {
        $this->_Cache();

        if (is_object($this->db)) {
            $this->db->disconnect();
        }
    }

    /**
    * Connect to a database.
    *
    * @param  string  PEAR DB DSN for the database connection
    * @param  mixed   options
    * @throws object  DB_Error
    */
    function connect($dsn, $options = false) {
        if (!isset($this->db)) {
            $this->db = DB::connect($dsn, $options);
        
            if (DB::isError($this->db)) {
                return $this->db;
            }
        }
    }

    /**
    * Register a database connection for connect on demand.
    *
    * @param  string  PEAR DB DSN for the database connection
    * @param  mixed   options
    */
    function setConnection($dsn, $options = false) {
      $this->dsn     = $dsn;
      $this->options = $options;
    }

    /**
    * Sets which fetch mode should be used by default on queries
    * on this connection.
    *
    * @param integer  DB_FETCHMODE_ASSOC, DB_FETCHMODE_OBJECT or
    *                 DB_FETCHMODE_ORDERED
    *
    * @param string   The class of the object to be returned by
    *                 the fetch methods when the DB_FETCHMODE_OBJECT
    *                 mode is selected.
    */
    function setFetchMode($fetchmode, $object_class = null) {
        switch ($fetchmode) {
            case DB_FETCHMODE_OBJECT: {
                if ($object_class) {
                    $this->fetchmode_object_class = $object_class;
                }
            }

            case DB_FETCHMODE_ORDERED:
            case DB_FETCHMODE_ASSOC: {
                $this->fetchmode = $fetchmode;
            }
            break;
        }
    }

    /**
    * Perform an SQL query.
    *
    * @param  string  SQL Query String
    * @return object  Cache_DB_Result
    * @throws object  Cache_Error
    */
    function &query($query) {
        if (stristr($query, 'SELECT')) {
            $cache_id = md5($query);

            $result = $this->get($cache_id, 'db_cache');

            if ($result == NULL) {
                if (!isset($this->db)) {
                    if (!empty($this->dsn)) {
                        $this->connect($this->dsn, $this->options);
                    } else {
                        return new Cache_Error(
                          'No database connection. Either open a connection ' .
                          'using connect() or register a connection with ' .
                          'setConnection($dsn, $options)',
                          __FILE__,
                          __LINE__
                        );
                    }
                }

                $_result = $this->db->query($query);

                if (!DB::isError($_result)) {
                    $rows = array();

                    while ($row = $_result->fetchRow(DB_FETCHMODE_ASSOC)) {
                        $rows[] = $row;
                    }

                    $result = new Cache_DB_Result(
                      $rows,
                      $this->fetchmode,
                      $this->fetchmode_object_class
                    );

                    $this->save($cache_id, $result, $this->expires, 'db_cache');
                } else {
                    return $_result;
                }
            }
        } else {
            if (!isset($this->db)) {
                if (!empty($this->dsn)) {
                    $this->connect($this->dsn, $this->options);
                    $result = $this->db->query($query);
                } else {
                    return new Cache_Error(
                      'No database connection. Either open a connection ' .
                      'using connect() or register a connection with ' .
                      'setConnection($dsn, $options)',
                      __FILE__,
                      __LINE__
                    );
                }
            }
        }

        return $result;
    }
}

/**
* Cache_DB_Result
*
* @author       Sebastian Bergmann <sb@sebastian-bergmann.de>
* @module       Cache_DB
* @modulegroup  Cache_DB
* @package      Cache
* @version      $Revision: 1.1.2.1 $
* @access       public
*/
class Cache_DB_Result {
    /**
    * Names of the result set's columns
    *
    * @var  array
    */
    var $column_names = array();

    /**
    * Cursor
    *
    * @var  integer
    */
    var $cursor = 0;

    /**
    * Fetchmode
    *
    * @var  integer
    */
    var $fetchmode = DB_FETCHMODE_ASSOC;

    /**
    * Fetchmode Object Class
    *
    * @var  string
    */
    var $fetchmode_object_class = 'DB_row';

    /**
    * Number of columns in the result set
    *
    * @var  integer
    */
    var $num_columns = 0;

    /**
    * Number of rows in the result set
    *
    * @var  integer
    */
    var $num_rows = 0;

    /**
    * Rows of the result set
    *
    * @var  array
    */
    var $rows = array();

    /**
    * Constructor
    *
    * @param  array   rows
    * @param  integer fetchmode
    * @param  string  fetchmode_object_class
    */
    function Cache_DB_Result(&$rows, $fetchmode, $fetchmode_object_class) {
        $this->rows                   = $rows;
        $this->fetchmode              = $fetchmode;
        $this->fetchmode_object_class = $fetchmode_object_class;

        $this->column_names = array_keys($this->rows[0]);
        $this->cursor       = 0;
        $this->num_columns  = sizeof($this->column_names);
        $this->num_rows     = sizeof($this->rows);
    }

    /**
     * Fetch and return a row of data.
     * @param   integer format of fetched row
     * @param   mixed   row to fetch
     * @return  mixed   a row of data, NULL on no more rows
     * @throws  object  DB_Error
     */
    function fetchRow($fetchmode = DB_FETCHMODE_DEFAULT, $rownum = null) {
        if ($fetchmode === DB_FETCHMODE_DEFAULT) {
            $fetchmode = $this->fetchmode;
        }

        if ($fetchmode === DB_FETCHMODE_OBJECT) {
            $fetchmode = DB_FETCHMODE_ASSOC;
            $return_object = true;
        }
  
        if ($rownum === null) {
            $this->cursor++;
        } else {
            $this->cursor = $rownum;
        }

        if ($rownum < sizeof($this->rows)) {
            $row = $this->rows[$this->cursor];
        } else {
            return false;
        }

        switch ($fetchmode) {
            case DB_FETCHMODE_ASSOC: {
                if (isset($return_object)) {
                    $class  =  $this->fetchmode_object_class;
                    $object =& new $class($row);

                    return $object;
                } else {
                    return $row;
                }
            }
            break;

            case DB_FETCHMODE_ORDERED: {
                $_row = array();

                foreach ($this->column_names as $column_name) {
                    $_row[] = $row[$column_name];
                }

                return $_row;
            }
            break;

            default: {
               return false;
            }
        }
    }

    /**
     * Fetch a row of data into an existing variable.
     *
     * @param   array   reference to data containing the row
     * @param   integer format of fetched row
     * @param   integer row number to fetch
     * @return  mixed   DB_OK on success, NULL on no more rows
     */
    function fetchInto(&$row, $fetchmode = DB_FETCHMODE_DEFAULT, $rownum = null) {
        if ($row = $this->fetchRow($fetchmode, $rownum)) {
            return DB_OK;
        } else {
            return NULL;
        }
    }

    /**
     * Get the the number of columns in a result set.
     *
     * @return integer  number of columns
     */
    function numCols() {
        return $this->num_columns;
    }

    /**
     * Get the number of rows in a result set.
     *
     * @return integer  number of rows
     */
    function numRows() {
        return $this->num_rows;
    }

    /**
     * Frees the resources allocated for this result set.
     */
    function free() {
        $this->column_names = array();
        $this->rows         = array();
        $this->num_columns  = 0;
        $this->num_rows     = 0;
    }

    /**
     * tableInfo() is not implemented in the PEAR Cache DB module.
     * @param   mixed   $mode
     * @throws  object  Cache_Error
     */
    function tableInfo($mode = null) {
        return new Cache_Error(
          'tableInfo() is not implemented in the ' .
          'PEAR Cache DB module.',
          __FILE__,
          __LINE__
        );
    }
}
?>
