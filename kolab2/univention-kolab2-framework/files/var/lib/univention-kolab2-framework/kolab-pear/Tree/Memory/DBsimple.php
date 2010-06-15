<?php
//
// +----------------------------------------------------------------------+
// | PHP Version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.02 of the PHP license,      |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Wolfram Kriesing <wolfram@kriesing.de>                      |
// +----------------------------------------------------------------------+
//
//  $Id: DBsimple.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once('Tree/OptionsDB.php');
require_once('Tree/Error.php');

/**
*   the DB interface to the tree class
*
*   @access     public
*   @author     Wolfram Kriesing <wolfram@kriesing.de>
*   @version    2001/06/27
*   @package    Tree
*/
class Tree_Memory_DBsimple extends Tree_OptionsDB
// FIXXME should actually extend Tree_Common, to use the methods provided in there... but we need to connect
// to the db here, so we extend optionsDB for now, may be use "aggregate" function to fix that
{

    /**
    *   @access public
    *   @var    array   saves the options passed to the constructor
    */
    var $options =  array(  'order'     =>'',   // which column to order by when reading the data from the DB, this sorts the data even inside every level
                            'whereAddOn'=>'',   // add on for the where clause, this string is simply added behind the WHERE in the select
                                                // so you better make sure its correct SQL :-), i.e. 'uid=3'
                                                // this is needed i.e. when you are saving many trees for different user
                                                // in one table where each entry has a uid (user id)
                            'table'     =>'',   //
                            // the column-name maps are used for the "as" in the select queries
                            // so you can use any column name in the table and "map" it to the name that shall be used in the
                            // internal array, that is built, see the examples (in comments)
                            'columnNameMaps'=>array(
                                   /*           'id'            =>  'tree_id',   // use "tree_id" as "id"
                                                'parentId'      =>  'parent_id',
                                                'prevId'        =>  'previous_id',
                                                'name'          =>  'nodeName'
                                   */
                                                ),
                            );

    /**
    *   @access public
    *   @var    string  the table where to read the tree data from
    *                   can also be set using the DSN in the constructor
    */
    var $table;

    /**
    *   @access private
    *   @var    object  $dbh    the handle to the DB-object
    */
//    var $dbh;

    /**
    *   set up this object
    *
    *   @version    2001/06/27
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      string  $dsn    this is a DSN of the for that PEAR::DB uses it
    *                               only that additionally you can add parameters like ...?table=test_table
    *                               to define the table it shall work on
    *   @param      array   $options  additional options you can set
    */
    function Tree_Memory_DBsimple( $dsn , $options=array() )
    {
        $this->Tree_OptionsDB( $dsn , $options ); // instanciate DB
        if( is_string($options) )                  // just to be backward compatible, or to make the second paramter shorter
        {
            $this->setOption( 'order' , $options );
        }

        $this->table = $this->getOption('table');

    } // end of function

    /**
    *   retreive all the navigation data from the db and call build to build the
    *   tree in the array data and structure
    *
    *   @version    2001/11/20
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     boolean     true on success
    */
    function setup()
    {
// TODO sort by prevId (parentId,prevId $addQuery) too if it exists in the table, or the root might be wrong
// TODO  since the prevId of the root should be 0

        //
        $whereAddOn = '';
        if( $this->options['whereAddOn'] )
        {
            $whereAddOn = 'WHERE '.$this->getOption('whereAddOn');
        }

        //
        $orderBy = '';
        if( $this->options['order'] )
        {
            $orderBy = ",".$this->options['order'];
        }

        $map = $this->getOption('columnNameMaps');
        if( isset($map['parentId']) )
        {
            $orderBy = $map['parentId'].$orderBy;
        }
        else
        {
            $orderBy = 'parentId'.$orderBy;
        }

        // build the query this way, that the root, which has no parent (parentId=0)
        // and no previous (prevId=0) is in first place (in case prevId is given)
        $query = sprintf(   "SELECT * FROM %s %s ORDER BY %s",
                            $this->table,
                            $whereAddOn,
                            $orderBy); //,prevId !!!!
        if( DB::isError( $res = $this->dbh->getAll( $query ) ) )
        {
// FIXXME remove print use debug mode instead
            printf("ERROR - Tree::setup - %s - %s<br>",DB::errormessage($res),$query);
            return $this->_throwError($res->getMessage(),__LINE__);
        }

        // if the db-column names need to be mapped to different names
// FIXXME somehow we should be able to do this in the query, but i dont know how to select
// only those columns, use "as" on them and select the rest, without getting those columns again :-(
        if( $map )
        foreach( $res as $id=>$aResult )    // map each result
        {
            foreach( $map as $key=>$columnName )
            {
                $res[$id][$key] = $res[$id][$columnName];
                unset($res[$id][$columnName]);
            }
        }

        return $res;
    }

    /**
    *   adds _one_ new element in the tree under the given parent
    *   the values' keys given have to match the db-columns, because the
    *   value gets inserted in the db directly
    *   to add an entire node containing children and so on see 'addNode()'
    *
    *   to ba compatible, to the DBnested u can also give the parent and previd as the second and third parameter
    *
    *   @see        addNode()
    *   @version    2001/10/09
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array   $newValues  this array contains the values that shall be inserted in the db-table
    *                                   the key for each element is the name of the column
    *   @return     mixed   either boolean false on failure or the id of the inserted row
    */
    function add( $newValues , $parentId=0 )
    {
// FIXXME use $this->dbh->tableInfo to check which columns exist
// so only data for which a column exist is inserted
        if( $parentId )
            $newValues['parentId'] = $parentId;

        $newData = array();
        foreach( $newValues as $key=>$value )       // quote the values, as needed for the insert
        {
            $newData[$this->_getColName($key)] = $this->dbh->quote($value);
        }

        // use sequences to create a new id in the db-table
        $nextId = $this->dbh->nextId($this->table);
        $query = sprintf("INSERT INTO %s (%s,%s) VALUES (%s,%s)",
                            $this->table ,
                            $this->_getColName('id'),
                            implode( ',' , array_keys($newData) ) ,
                            $nextId,
                            implode( ',' , $newData ) );
        if( DB::isError( $res = $this->dbh->query( $query ) ) )
        {
            // TODO raise PEAR error
            printf("ERROR - Tree::add - %s - %s<br>",DB::errormessage($res),$query);
            return false;
        }

        return $nextId;
    } // end of function

    /**
    *   removes the given node
    *
    *   @version  2001/10/09
    *   @access     public
    *   @author   Wolfram Kriesing <wolfram@kriesing.de>
    *   @param    mixed   $id   the id of the node to be removed, or an array of id's to be removed
    *   @return   boolean true on success
    */
    function remove( $id )
    {
        // if the one to remove has children, get their id's to remove them too
        if( $this->hasChildren($id) )
            $id = $this->walk( array('_remove',$this) , $id , 'array' );

        $idColumnName = 'id';
        $map = $this->getOption('columnNameMaps');
        if( isset($map['id']) )                     // if there are maps given
        {
            $idColumnName = $map['id'];
        }

        $whereClause = "WHERE $idColumnName=$id";
        if( is_array($id) )
        {
            $whereClause = "WHERE $idColumnName in (".implode( ',' , $id ).')';
        }

        $query = "DELETE FROM {$this->table} $whereClause";
//print("<br>".$query);
        if( DB::isError( $res = $this->dbh->query( $query ) ) )
        {
// TODO raise PEAR error
            printf("ERROR - Tree::remove - %s - %s<br>",DB::errormessage($res),$query);
            return false;
        }
// TODO if remove succeeded set prevId of the following element properly

        return true;
    } // end of function

    /**
    *   move an entry under a given parent or behind a given entry
    *
    *   @version    2001/10/10
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer $idToMove   the id of the element that shall be moved
    *   @param      integer $newParentId    the id of the element which will be the new parent
    *   @param      integer $newPrevId      if prevId is given the element with the id idToMove
    *                                       shall be moved _behind_ the element with id=prevId
    *                                       if it is 0 it will be put at the beginning
    *                                       if no prevId is in the DB it can be 0 too and won't bother
    *                                       since it is not written in the DB anyway
    *   @return     boolean     true for success
    */
    function move( $idToMove , $newParentId , $newPrevId=0 )
    {

        $idColumnName = 'id';
        $parentIdColumnName = 'parentId';
        $map = $this->getOption('columnNameMaps');
        if( isset($map['id']) )
            $idColumnName = $map['id'];
        if( isset($map['parentId']) )
            $parentIdColumnName = $map['parentId'];
// FIXXME todo: previous stuff

        // set the parent in the DB
        $query = "UPDATE $this->table SET $parentIdColumnName=$newParentId WHERE $idColumnName=$idToMove";
//print($query);
        if( DB::isError( $res = $this->dbh->query( $query ) ) )
        {
// TODO raise PEAR error
            printf("ERROR - Tree::move - %s - %s<br>",DB::errormessage($res),$query);
            return false;
        }
// FIXXME update the prevId's of the elements where the element was moved away from and moved in

        return true;
    } // end of function

    /**
    *   update an element in the DB
    *
    *   @version    2002/01/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array   $newData    all the new data, the key 'id' is used to
    *                                   build the 'WHERE id=' clause and all the other
    *                                   elements are the data to fill in the DB
    *   @return     boolean true for success
    */
    function update( $id , $newData )
    {

// FIXXME check $this->dbh->tableInfo to see if all the columns that shall be updated
// really exist, this will also extract nextId etc. if given before writing it in the DB
// in case they dont exist in the DB
        $setData = array();
        foreach( $newData as $key=>$value )       // quote the values, as needed for the insert
        {
            $setData[] = $this->_getColName($key).'='.$this->dbh->quote($value);
        }

        $query = sprintf(   'UPDATE %s SET %s WHERE %s=%s',
                            $this->table,
                            implode( ',' , $setData ),
                            $this->_getColName('id'),
                            $id
                        );
        if( DB::isError( $res=$this->dbh->query($query) ) )
        {
// FIXXME raise PEAR error
            printf("ERROR - Tree::update - %s - %s<br>",DB::errormessage($res),$query);
            return false;
        }

        return true;
    } // end of function

    /**
    *
    *
    *   @access     private
    *   @version    2002/03/02
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return
    */
    function _throwError( $msg , $line , $mode=null )
    {
        return new Tree_Error( $msg , $line , __FILE__ , $mode , $this->db->last_query );
    }



    /**
    *   prepare multiple results
    *
    *   @see        _prepareResult()
    *   @access     private
    *   @version    2002/03/03
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return
    */
    function _prepareResults( $results )
    {
        $newResults = array();
        foreach( $results as $aResult )
            $newResults[] = $this->_prepareResult($aResult);
        return $newResults;
    }

    /**
    *   map back the index names to get what is expected
    *
    *   @access     private
    *   @version    2002/03/03
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return
    */
    function _prepareResult( $result )
    {
        $map = $this->getOption('columnNameMaps');

        if( $map )
        foreach( $map as $key=>$columnName )
        {
            $result[$key] = $result[$columnName];
            unset($result[$columnName]);
        }
        return $result;
    }

    /**
    *   this method retreives the real column name, as used in the DB
    *   since the internal names are fixed, to be portable between different
    *   DB-column namings, we map the internal name to the real column name here
    *
    *   @access     private
    *   @version    2002/03/02
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return
    */
    function _getColName( $internalName )
    {
        if( $map = $this->getOption( 'columnNameMaps' ) )
        {
            if( isset($map[$internalName]) )
                return $map[$internalName];
        }
        return $internalName;
    }


} // end of class
?>
