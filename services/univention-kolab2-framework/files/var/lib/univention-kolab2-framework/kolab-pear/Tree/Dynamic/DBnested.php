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
// | Authors:                                                             |
// +----------------------------------------------------------------------+
//
//  $Id: DBnested.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once('Tree/Common.php');
require_once('Tree/Error.php');

/**
*   this class implements methods to work on a tree saved using the nested
*   tree model
*   explaination: http://research.calacademy.org/taf/proceedings/ballew/index.htm
*
*   @access     public
*   @package    Tree
*/
class Tree_Dynamic_DBnested extends Tree_Common
// FIXXME should actually extend Tree_Common, to use the methods provided in there... but we need to connect
// to the db here, so we extend optionsDB for now, may be use "aggregate" function to fix that
{

    var $debug = 0;

    var $options = array(
// FIXXME to be implemented
                            'whereAddOn'=>''    // add on for the where clause, this string is simply added behind the WHERE in the select
                                                // so you better make sure its correct SQL :-), i.e. 'uid=3'
                                                // this is needed i.e. when you are saving many trees in one db-table
                            ,'table'     =>''   //
                            // since the internal names are fixed, to be portable between different
                            // DB tables with different column namings, we map the internal name to the real column name
                            // using this array here, if it stays empty the internal names are used, which are:
                            // id, left, right
                            ,'columnNameMaps'=>array(
                                                //'id'            =>  'node_id',    // use "node_id" as "id"
                                                 'left'          =>  'l'            // since mysql at least doesnt support 'left' ...
                                                ,'right'         =>  'r'            // ...as a column name we set default to the first letter only
                                                //'name'          =>  'nodeName'  //
                                                ,'parentId'       =>  'parent'    // parent id
                                                )
                            ,'order'    => ''   // needed for sorting the tree, currently only used in Memory_DBnested
                            );

// the defined methods here are proposals for the implementation,
// they are named the same, as the methods in the "Memory" branch, if possible
// it would be cool to keep the same naming and if the same parameters would be possible too
// then it would be even better, so one could easily change from any kind of
// tree-implementation to another, without changing the source code, only the setupXXX would need to be changed

    /**
    *
    *
    *   @access     public
    *   @version    2002/03/02
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return
    */
    function __construct( $dsn , $options=array() )
    {
        Tree_Dynamic_DBnested( $dsn , $options );
    }

    /**
    *
    *
    *   @access     public
    *   @version    2002/03/02
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return
    */
    function Tree_Dynamic_DBnested( $dsn , $options=array() )
    {
        parent::Tree_OptionsDB( $dsn , $options ); // instanciate DB
        $this->table = $this->getOption('table');
    }

    /**
    *   add a new element to the tree
    *   there are three ways to use this method
    *   1.
    *   give only the $parentId and the $newValues will be inserted as the first child of this parent
    *   i.e.    // insert a new element under the parent with the ID=7
    *           $tree->add( array('name'=>'new element name') , 7 );
    *   2.
    *   give the $prevId ($parentId will be dismissed) and the new element
    *   will be inserted in the tree after the element with the ID=$prevId
    *   the parentId is not necessary because the prevId defines exactly where
    *   the new element has to be place in the tree, and the parent is the same as
    *   for the element with the ID=$prevId
    *   i.e.    // insert a new element after the element with the ID=5
    *           $tree->add( array('name'=>'new') , 0 , 5 );
    *   3.
    *   neither $parentId nor prevId is given, then the root element will be inserted
    *   this requires that programmer is responsible to confirm this
    *   this method does not (yet) check if there is already a root element saved !!!
    *
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array   $newValues  this array contains the values that shall be inserted in the db-table
    *   @param      integer $parentId   the id of the element which shall be the parent of the new element
    *   @param      integer $prevId     the id of the element which shall preceed the one to be inserted
    *                                   use either 'parentId' or 'prevId'
    *   @return     integer the ID of the element that had been inserted
    */
    function add( $newValues , $parentId=0 , $prevId=0 )
    {
        $lName = $this->_getColName('left');
        $rName = $this->_getColName('right');
        $prevVisited = 0;

        // check the DB-table if the columns which are given as keys
        // in the array $newValues do really exist, if not remove them from the array
// FIXXME do the above described

        if( $parentId || $prevId )                  // if no parent and no prevId is given the root shall be added
        {
            if( $prevId )
            {
                $element = $this->getElement( $prevId );
                $parentId = $element['parentId'];       // we also need the parent id of the element, to write it in the db
            }
            else
            {
                $element = $this->getElement( $parentId );
            }
            $newValues['parentId'] = $parentId;

            if( PEAR::isError($element) )
                return $element;

            // get the "visited"-value where to add the new element behind
            // if $prevId is given, we need to use the right-value
            // if only the $parentId is given we need to use the left-value
            // look at it graphically, that made me understand it :-)
            // i.e. at: http://research.calacademy.org/taf/proceedings/ballew/sld034.htm
            $prevVisited = $prevId ? $element['right'] : $element['left'];

// FIXXME start transaction here

            if( PEAR::isError($err=$this->_add( $prevVisited , 1 )) )
            {
    // FIXXME rollback
                //$this->dbh->rollback();
                return $err;
            }
        }

        // inserting _one_ new element in the tree
        $newData = array();
        foreach( $newValues as $key=>$value )       // quote the values, as needed for the insert
        {
            $newData[$this->_getColName($key)] = $this->dbh->quote($value);
        }

        // set the proper right and left values
        $newData[$lName] = $prevVisited+1;
        $newData[$rName] = $prevVisited+2;

        // use sequences to create a new id in the db-table
        $nextId = $this->dbh->nextId($this->table);
        $query = sprintf(   'INSERT INTO %s (%s,%s) VALUES (%s,%s)',
                            $this->table ,
                            $this->_getColName('id'),
                            implode( "," , array_keys($newData) ) ,
                            $nextId,
                            implode( "," , $newData )
                        );
        if( DB::isError( $res = $this->dbh->query($query) ) )
        {
// rollback
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
// commit here

        return $nextId;
    } // end of function

    /**
    *   this method only updates the left/right values of all the
    *   elements that are affected by the insertion
    *   be sure to set the parentId of the element(s) you insert
    *
    *   @param  int     this parameter is not the ID!!!
    *                   it is the previous visit number, that means
    *                   if you are inserting a child, you need to use the left-value
    *                   of the parent
    *                   if you are inserting a "next" element, on the same level
    *                   you need to give the right value !!
    *   @param  int     the number of elements you plan to insert
    *   @return mixed   either true on success or a Tree_Error on failure
    */
    function _add( $prevVisited , $numberOfElements=1 )
    {
        $lName = $this->_getColName('left');
        $rName = $this->_getColName('right');

        // update the elements which will be affected by the new insert
        $query = sprintf(   'UPDATE %s SET %s=%s+%s WHERE%s %s>%s',
                            $this->table,
                            $lName,$lName,
                            $numberOfElements*2,
                            $this->_getWhereAddOn(),
                            $lName,
                            $prevVisited );
        if( DB::isError( $res = $this->dbh->query($query) ) )
        {
// FIXXME rollback
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }

        $query = sprintf(   'UPDATE %s SET %s=%s+%s WHERE%s %s>%s',
                            $this->table,
                            $rName,$rName,
                            $numberOfElements*2,
                            $this->_getWhereAddOn(),
                            $rName,
                            $prevVisited );
        if( DB::isError( $res = $this->dbh->query($query) ) )
        {
// FIXXME rollback
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
        return true;
    }

    /**
    *   remove a tree element
    *   this automatically remove all children and their children
    *   if a node shall be removed that has children
    *
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer $id the id of the element to be removed
    *   @return     boolean returns either true or throws an error
    */
    function remove( $id )
    {
        $element = $this->getElement( $id );
        if( PEAR::isError($element) )
            return $element;

// FIXXME start transaction
        //$this->dbh->autoCommit(false);
        $query = sprintf(   'DELETE FROM %s WHERE%s %s BETWEEN %s AND %s',
                            $this->table,
                            $this->_getWhereAddOn(),
                            $this->_getColName('left'),
                            $element['left'],$element['right']);
        if( DB::isError( $res = $this->dbh->query($query) ) )
        {
// FIXXME rollback
            //$this->dbh->rollback();
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }

        if( PEAR::isError($err=$this->_remove( $element )) )
        {
// FIXXME rollback
            //$this->dbh->rollback();
            return $err;
        }
        return true;
    }

    /**
    *   removes a tree element, but only updates the left/right values
    *   to make it seem as if the given element would not exist anymore
    *   it doesnt remove the row(s) in the db itself!
    *
    *   @see        getElement()
    *   @access     private
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array   the entire element returned by "getElement"
    *   @return     boolean returns either true or throws an error
    */
    function _remove( $element )
    {
        $delta = $element['right'] - $element['left'] +1;
        $lName = $this->_getColName('left');
        $rName = $this->_getColName('right');

        // update the elements which will be affected by the remove
        $query = sprintf(   "UPDATE %s SET %s=%s-$delta, %s=%s-$delta WHERE%s %s>%s",
                            $this->table,
                            $lName,$lName,
                            $rName,$rName,
                            $this->_getWhereAddOn(),
                            $lName,$element['left'] );
        if( DB::isError( $res = $this->dbh->query($query) ) )
        {
            // the rollback shall be done by the method calling this one, since it is only private we can do that
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }

        $query = sprintf(   "UPDATE %s SET %s=%s-$delta WHERE%s %s<%s AND %s>%s",
                            $this->table,
                            $rName,$rName,
                            $this->_getWhereAddOn(),
                            $lName,$element['left'],
                            $rName,$element['right'] );
        if( DB::isError( $res = $this->dbh->query($query) ) )
        {
            // the rollback shall be done by the method calling this one, since it is only private
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
// FIXXME commit - should that not also be done in the method calling this one? like when an error occurs?
        //$this->dbh->commit();
        return true;
    } // end of function

    /**
    *   move an entry under a given parent or behind a given entry.
    *   If a newPrevId is given the newParentId is dismissed!
    *   call it either like this:
    *       $tree->move( x , y )
    *       to move the element (or entire tree) with the id x
    *       under the element with the id y
    *   or
    *       $tree->move( x , 0 , y );   // ommit the second parameter by setting it to 0
    *       to move the element (or entire tree) with the id x
    *       behind the element with the id y
    *   or
    *       $tree->move( array(x1,x2,x3) , ...
    *       the first parameter can also be an array of elements that shall be moved
    *       the second and third para can be as described above
    *   If you are using the Memory_DBnested then this method would be invain,
    *   since Memory.php already does the looping through multiple elements, but if
    *   Dynamic_DBnested is used we need to do the looping here
    *
    *   @version    2002/06/08
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer     the id(s) of the element(s) that shall be moved
    *   @param      integer     the id of the element which will be the new parent
    *   @param      integer     if prevId is given the element with the id idToMove
    *                           shall be moved _behind_ the element with id=prevId
    *                           if it is 0 it will be put at the beginning
    *   @return     mixed       true for success, Tree_Error on failure
    */
    function move( $idsToMove , $newParentId , $newPrevId=0 )
    {
        settype($idsToMove,'array');
        $errors = array();
        foreach( $idsToMove as $idToMove )
        {
            $ret = $this->_move( $idToMove , $newParentId , $newPrevId );
            if( PEAR::isError($ret) )
                $errors[] = $ret;
        }
// FIXXME the error in a nicer way, or even better let the throwError method do it!!!
        if( sizeof($errors) )
        {
            return $this->_throwError(serialize($errors),__LINE__);
        }
        return true;
    }

    /**
    *   this method moves one tree element
    *
    *   @see        move()
    *   @version    2002/04/29
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer     the id of the element that shall be moved
    *   @param      integer     the id of the element which will be the new parent
    *   @param      integer     if prevId is given the element with the id idToMove
    *                           shall be moved _behind_ the element with id=prevId
    *                           if it is 0 it will be put at the beginning
    *   @return     mixed       true for success, Tree_Error on failure
    */
    function _move( $idToMove , $newParentId , $newPrevId=0 )
    {
        // do some integrity checks first
        if ($newPrevId) {
            if ($newPrevId==$idToMove) {            // dont let people move an element behind itself, tell it succeeded, since it already is there :-)
                return true;
            }
            if (PEAR::isError($newPrevious=$this->getElement($newPrevId))) {
                return $newPrevious;
            }
            $newParentId = $newPrevious['parentId'];
        } else {
            if ($newParentId==0) {
                return $this->_throwError( 'no parent id given' , __LINE__ );
            }
            if ($this->isChildOf($idToMove,$newParentId)) { // if the element shall be moved under one of its children, return false
                return $this->_throwError( 'can not move an element under one of its children' , __LINE__ );
            }
            if ($newParentId==$idToMove) {          // dont do anything to let an element be moved under itself, which is bullshit
                return true;
            }
            if (PEAR::isError($newParent=$this->getElement($newParentId))) { // try to retreive the data of the parent element
                return $newParent;
            }
        }

        if (PEAR::isError($element=$this->getElement($idToMove))) { // get the data of the element itself
            return $element;
        }

        $numberOfElements = ($element['right'] - $element['left']+1)/2;
        $prevVisited = $newPrevId ? $newPrevious['right'] : $newParent['left'];

// FIXXME start transaction

        // add the left/right values in the new parent, to have the space to move the new values in
        if (PEAR::isError($err=$this->_add( $prevVisited , $numberOfElements ))) {
// FIXXME rollback
            //$this->dbh->rollback();
            return $err;
        }

        // update the parentId of the element with $idToMove
        if (PEAR::isError($err=$this->update($idToMove,array('parentId'=>$newParentId)))) {
// FIXXME rollback
            //$this->dbh->rollback();
            return $err;
        }

        // update the lefts and rights of those elements that shall be moved

        // first get the offset we need to add to the left/right values
        // if $newPrevId is given we need to get the right value, otherwise the left
        // since the left/right has changed, because we already updated it up there we need to
        // get them again, we have to do that anyway, to have the proper new left/right values
        if ($newPrevId) {
            if (PEAR::isError($temp = $this->getElement( $newPrevId ))) {
// FIXXME rollback
                //$this->dbh->rollback();
                return $temp;
            }
            $calcWith = $temp['right'];
        } else {
            if (PEAR::isError($temp=$this->getElement($newParentId))) {
// FIXXME rollback
                //$this->dbh->rollback();
                return $temp;
            }
            $calcWith = $temp['left'];
        }

        // get the element that shall be moved again, since the left and right might have changed by the add-call
        if (PEAR::isError($element=$this->getElement($idToMove))) {
            return $element;
        }

        $offset = $calcWith - $element['left'];     // calc the offset that the element to move has to the spot where it should go
        $offset++;                                  // correct the offset by one, since it needs to go inbetween!

        $lName = $this->_getColName('left');
        $rName = $this->_getColName('right');
        $query = sprintf(   "UPDATE %s SET %s=%s+$offset,%s=%s+$offset WHERE%s %s>%s AND %s<%s",
                            $this->table,
                            $rName,$rName,
                            $lName,$lName,
                            $this->_getWhereAddOn(),
                            $lName,$element['left']-1,
                            $rName,$element['right']+1 );
        if (DB::isError($res=$this->dbh->query($query))) {
// FIXXME rollback
            //$this->dbh->rollback();
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }

        // remove the part of the tree where the element(s) was/were before
        if (PEAR::isError($err=$this->_remove($element))) {
// FIXXME rollback
            //$this->dbh->rollback();
            return $err;
        }
// FIXXME commit all changes
        //$this->dbh->commit();

        return true;
    } // end of function

    /**
    *   update the tree element given by $id with the values in $newValues
    *
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      int     the id of the element to update
    *   @param      array   the new values, the index is the col name
    *   @return     mixed   either true or an Tree_Error
    */
    function update($id,$newValues)
    {
        // jsut to be sure nothing gets screwed up :-)
        unset($newValues[$this->_getColName('left')]);
        unset($newValues[$this->_getColName('right')]);
        unset($newValues[$this->_getColName('parentId')]);

        // updating _one_ element in the tree
        $values = array();
        foreach ($newValues as $key=>$value) {
            $values[] = $this->_getColName($key).'='.$this->dbh->quote($value);
        }
        $query = sprintf(   'UPDATE %s SET %s WHERE%s %s=%s',
                            $this->table,
                            implode(',',$values),
                            $this->_getWhereAddOn(),
                            $this->_getColName('id'),
                            $id);
        if (DB::isError( $res=$this->dbh->query($query))) {
// FIXXME raise PEAR error
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }

        return true;
    } // end of function

    /**
    *   copy a subtree/node/... under a new parent or/and behind a given element
    *
    *
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return
    */
    function copy( $id , $parentId=0 , $prevId=0 )
    {
        return $this->_throwError( 'copy-method is not implemented yet!' , __LINE__ );
        // get element tree
        // $this->addTree
    } // end of function


    /**
    *   get the root
    *
    *   @access     public
    *   @version    2002/03/02
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return     mixed   either the data of the root element or an Tree_Error
    */
    function getRoot()
    {
        $query = sprintf(   'SELECT * FROM %s WHERE%s %s=1',
                            $this->table,
                            $this->_getWhereAddOn(),
                            $this->_getColName('left'));
        if( DB::isError( $res = $this->dbh->getRow($query) ) )
        {
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
        return $this->_prepareResult( $res );
    } // end of function

    /**
    *
    *
    *   @access     public
    *   @version    2002/03/02
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return     mixed   either the data of the requested element or an Tree_Error
    */
    function getElement( $id )
    {
        $query = sprintf(   'SELECT * FROM %s WHERE%s %s=%s',
                            $this->table,
                            $this->_getWhereAddOn(),
                            $this->_getColName('id'),
                            $id);
        if( DB::isError( $res = $this->dbh->getRow($query) ) )
        {
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
        if( !$res )
            return $this->_throwError( "Element with id $id does not exist!" , __LINE__ );

        return $this->_prepareResult( $res );
    } // end of function

    /**
    *
    *
    *   @access     public
    *   @version    2002/03/02
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return     mixed   either the data of the requested element or an Tree_Error
    */
    function getChild($id)
    {
        // subqueries would be cool :-)
        $curElement = $this->getElement( $id );
        if (PEAR::isError($curElement)) {
            return $curElement;
        }

        $query = sprintf(   'SELECT * FROM %s WHERE%s %s=%s',
                            $this->table,
                            $this->_getWhereAddOn(),
                            $this->_getColName('left'),
                            $curElement['left']+1 );
        if (DB::isError( $res = $this->dbh->getRow($query))) {
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
        return $this->_prepareResult( $res );
    }

    /**
    *   gets the path from the element with the given id down
    *   to the root
    *   the returned array is sorted to start at root
    *   for simply walking through and retreiving the path
    *
    *   @access     public
    *   @version    2002/03/02
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return     mixed   either the data of the requested elements or an Tree_Error
    */
    function getPath( $id )
    {
        // subqueries would be cool :-)
        $curElement = $this->getElement( $id );

        $query = sprintf(   'SELECT * FROM %s WHERE%s %s<=%s AND %s>=%s ORDER BY %s',
                            $this->table,
                            $this->_getWhereAddOn(),
                            $this->_getColName('left'),
                            $curElement['left'],
                            $this->_getColName('right'),
                            $curElement['right'],
                            $this->_getColName('left') );
        if (DB::isError( $res = $this->dbh->getAll($query))) {
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
        return $this->_prepareResults( $res );
    }

    /**
    *   gets the element to the left, the left visit
    *
    *   @access     public
    *   @version    2002/03/07
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return     mixed   either the data of the requested element or an Tree_Error
    */
    function getLeft( $id )
    {
        $element = $this->getElement( $id );
        if( PEAR::isError($element) )
            return $element;

        $query = sprintf(   'SELECT * FROM %s WHERE%s (%s=%s OR %s=%s)',
                            $this->table,
                            $this->_getWhereAddOn(),
                            $this->_getColName('right'),$element['left']-1,
                            $this->_getColName('left'),$element['left']-1 );
        if( DB::isError( $res = $this->dbh->getRow($query) ) )
        {
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
        return $this->_prepareResult( $res );
    }

    /**
    *   gets the element to the right, the right visit
    *
    *   @access     public
    *   @version    2002/03/07
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return     mixed   either the data of the requested element or an Tree_Error
    */
    function getRight( $id )
    {
        $element = $this->getElement( $id );
        if( PEAR::isError($element) )
            return $element;

        $query = sprintf(   'SELECT * FROM %s WHERE%s (%s=%s OR %s=%s)',
                            $this->table,
                            $this->_getWhereAddOn(),
                            $this->_getColName('left'),$element['right']+1,
                            $this->_getColName('right'),$element['right']+1);
        if( DB::isError( $res = $this->dbh->getRow($query) ) )
        {
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
        return $this->_prepareResult( $res );
    }

    /**
    *   get the parent of the element with the given id
    *
    *   @access     public
    *   @version    2002/04/15
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return     mixed   the array with the data of the parent element
    *                       or false, if there is no parent, if the element is the root
    *                       or an Tree_Error
    */
    function getParent( $id )
    {
        $query = sprintf(   'SELECT p.* FROM %s p,%s e WHERE%s e.%s=p.%s AND e.%s=%s',
                            $this->table,$this->table,
                            $this->_getWhereAddOn( ' AND ' , 'p' ),
                            $this->_getColName('parentId'),
                            $this->_getColName('id'),
                            $this->_getColName('id'),
                            $id);
        if( DB::isError( $res = $this->dbh->getRow($query) ) )
        {
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
        return $this->_prepareResult( $res );
    }

    /**
    *   get the children of the given element
    *   or if the parameter is an array, it gets the children of all
    *   the elements given by their ids in the array
    *
    *   @access     public
    *   @version    2002/04/15
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   (1) int     the id of one element
    *                       (2) array   an array of ids for which
    *                                   the children will be returned
    *   @param      integer the children of how many levels shall be returned
    *   @return     mixed   the array with the data of all children
    *                       or false, if there are none
    */
    function getChildren($ids,$levels=1)
    {
        $res = array();
        for( $i=1 ; $i<$levels+1 ; $i++ )
        {
            // if $ids is an array implode the values
            $getIds = is_array($ids) ? implode(',',$ids) : $ids;

            $query = sprintf(   'SELECT c.* FROM %s c,%s e WHERE%s e.%s=c.%s AND e.%s IN (%s) '.
                                'ORDER BY c.%s',
                                $this->table,$this->table,
                                $this->_getWhereAddOn( ' AND ' , 'c' ),
                                $this->_getColName('id'),
                                $this->_getColName('parentId'),
                                $this->_getColName('id'),
                                $getIds,
                                // order by left, so we have it in the order as it is in the tree
                                // if no 'order'-option is given
                                $this->getOption('order') ? $this->getOption('order') : $this->_getColName('left')
                                );
            if (DB::isError($_res = $this->dbh->getAll($query))) {
                return $this->_throwError( $_res->getMessage() , __LINE__ );
            }
            $_res = $this->_prepareResults( $_res );

            // we use the id as the index, to make the use easier esp. for multiple return-values
            $tempRes = array();
            foreach ($_res as $aRes) {
                $tempRes[$aRes[$this->_getColName('id')]] = $aRes;
            }
            $_res = $tempRes;

            //
            if ($levels>1) {
                $ids = array();
                foreach( $_res as $aRes )
                    $ids[] = $aRes[$this->_getColName('id')];
            }
            $res = array_merge($res,$_res);

            // quit the for-loop if there are no children in the current level
            if (!sizeof($ids)) {
                break;
            }
        }
        return $res;
    }

    /**
    *   get the next element on the same level
    *   if there is none return false
    *
    *   @access     public
    *   @version    2002/04/15
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return     mixed   the array with the data of the next element
    *                       or false, if there is no next
    *                       or Tree_Error
    */
    function getNext( $id )
    {
        $query = sprintf(   'SELECT n.* FROM %s n,%s e WHERE%s e.%s=n.%s-1 AND e.%s=n.%s AND e.%s=%s',
                            $this->table,$this->table,
                            $this->_getWhereAddOn( ' AND ' , 'n' ),
                            $this->_getColName('right'),
                            $this->_getColName('left'),
                            $this->_getColName('parentId'),
                            $this->_getColName('parentId'),
                            $this->_getColName('id'),
                            $id);
        if( DB::isError( $res = $this->dbh->getRow($query) ) )
        {
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
        if( !$res )
            return false;
        return $this->_prepareResult( $res );
    }

    /**
    *   get the previous element on the same level
    *   if there is none return false
    *
    *   @access     public
    *   @version    2002/04/15
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return     mixed   the array with the data of the previous element
    *                       or false, if there is no previous
    *                       or a Tree_Error
    */
    function getPrevious( $id )
    {
        $query = sprintf(   'SELECT p.* FROM %s p,%s e WHERE%s e.%s=p.%s+1 AND e.%s=p.%s AND e.%s=%s',
                            $this->table,$this->table,
                            $this->_getWhereAddOn( ' AND ' , 'p' ),
                            $this->_getColName('left'),
                            $this->_getColName('right'),
                            $this->_getColName('parentId'),
                            $this->_getColName('parentId'),
                            $this->_getColName('id'),
                            $id);
        if( DB::isError( $res = $this->dbh->getRow($query) ) )
        {
            return $this->_throwError( $res->getMessage() , __LINE__ );
        }
        if( !$res )
            return false;
        return $this->_prepareResult( $res );
    }

    /**
    *   returns if $childId is a child of $id
    *
    *   @abstract
    *   @version    2002/04/29
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      int     id of the element
    *   @param      int     id of the element to check if it is a child
    *   @return     boolean true if it is a child
    */
    function isChildOf( $id , $childId )
    {
        // check simply if the left and right of the child are within the
        // left and right of the parent, if so it definitly is a child :-)
        $parent = $this->getElement($id);
        $child = $this->getElement($childId);

        if( $parent['left'] < $child['left'] &&
            $parent['right'] > $child['right'] )
        {
            return true;
        }

        return false;
    } // end of function

    /**
    *   return the maximum depth of the tree
    *
    *   @version    2003/02/25
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     int     the depth of the tree
    */
    function getDepth()
    {
// FIXXXME TODO!!!    
        return $this->_throwError( 'not implemented yet' , __LINE__ );
    }

    /**
    *   Tells if the node with the given ID has children.
    *
    *   @version    2003/03/04
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer the ID of a node
    *   @return     boolean if the node with the given id has children
    */
    function hasChildren($id)
    {
        $element = $this->getElement($id);
        return $element['right']-$element['left']>1;    // if the diff between left and right>1 then there are children
    }


    //
    //  PRIVATE METHODS
    //


    /**
    *
    *
    *   @access     private
    *   @version    2002/04/20
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      string  the current where clause
    *   @return
    */
    function _getWhereAddOn( $addAfter=' AND ' , $tableName='' )
    {
        if( $where=$this->getOption('whereAddOn') )
        {
            return ' '.($tableName?$tableName.'.':'')." $where$addAfter ";
        }
        return '';
    }




    // for compatibility to Memory methods
    function getFirstRoot()
    {
        return $this->getRoot();
    }
    /**
    *   gets the tree under the given element in one array, sorted
    *   so you can go through the elements from begin to end and list them
    *   as they are in the tree, where every child (until the deepest) is retreived
    *
    *   @see        &_getNode()
    *   @access     public
    *   @version    2001/12/17
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer $startId    the id where to start walking
    *   @param      integer $depth      this number says how deep into the structure the elements shall be retreived
    *   @return     array   sorted as listed in the tree
    */
    function &getNode( $startId=0 , $depth=0 )
    {
    }

}
?>
