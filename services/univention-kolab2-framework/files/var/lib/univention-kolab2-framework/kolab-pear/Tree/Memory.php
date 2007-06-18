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
//  $Id: Memory.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once 'Tree/Common.php';
require_once 'Tree/Error.php';

/**
*   this class can be used to step through a tree using ['parent'], ['child'], etc.
*   the tree is saved as flat data in a db, where at least the parent
*   needs to be given if a previous member is given too then the order
*   on a level can be determined too
*   actually this class was used for a navigation tree
*   now it is extended to serve any kind of tree
*   you can unambigiously refer to any element by using the following
*   syntax
*   tree->data[currentId][<where>]...[<where>]
*   <where> can be either "parent", "child", "next" or "previous", this way
*   you can "walk" from any point to any other point in the tree
*   by using <where> in any order you want
*   example (in parentheses the id):
*   root
*    +---level 1_1 (1)
*    |      +----level 2_1 (2)
*    |      +----level 2_2 (3)
*    |              +-----level 3_1 (4)
*    +---level 1_2 (5)
*
*    the database table to this structure (without defined order)
*    id     parentId        name
*    1         0         level 1_1
*    2         1         level 2_1
*    3         1         level 2_1
*    4         3         level 3_1
*    5         0         level 1_2
*
*   now you can refer to elements for example like this (all examples assume you know the structure):
*   to go from "level 3_1" to "level 1_1": $tree->data[4]['parent']['parent']
*   to go from "level 3_1" to "level 1_2": $tree->data[4]['parent']['parent']['next']
*   to go from "level 2_1" to "level 3_1": $tree->data[2]['next']['child']
*   to go from "level 2_2" to "level 2_1": $tree->data[3]['previous']
*   to go from "level 1_2" to "level 3_1": $tree->data[5]['previous']['child']['next']['child']
*

on a pentium 1.9 GHz 512 MB RAM, Linux 2.4, Apache 1.3.19, PHP 4.0.6
performance statistics for version 1.26, using examples/Tree/Tree.php
    reading from DB and preparing took: 0.14958894252777
    building took: 0.074488043785095
    buildStructure took: 0.05151903629303
    setting up the tree time: 0.29579293727875
    number of elements: 1564
    deepest level: 17
so you can use it for tiny-big trees too :-)
but watch the db traffic, which might be considerable, depending on your setup

FIXXXME there is one really bad thing about the entire class, at some points there are references to
$this->data returned, or the programmer can even access this->data, which means he can change the
structure, since this->data can not be set to read-only, therefore this->data has to be handled with great care
!!! never do something like this: $x = &$tree->data[<some-id>]; $x = $y; this overwrites the element in the structure !!!

*
*
*   @access   public
*   @author   Wolfram Kriesing <wolfram@kriesing.de>
*   @version  2001/06/27
*   @package  Tree
*/
class Tree_Memory extends Tree_Common
{
    /**
    *   this array contains the pure data from the DB
    *   which are always kept, since all other structures will
    *   only make references on any element
    *   and those data are extended by the elements 'parent' 'children' etc...
    *   @var    array $data
    */
    var $data = array();

    /**
    *   this array contains references to this->data but it
    *   additionally represents the directory structure
    *   that means the array has as many dimensions as the
    *   tree structure has levels
    *   but this array is only used internally from outside you can do everything using
    *   the node-id's
    *
    *   @var    array $structure
    *   @access private
    */
    var $structure = array();

    /**
    *   it contains all the parents and their children, where the parentId is the
    *   key and all the children are the values, this is for speeding up the tree-building process
    *
    *   @var    array   $children
    */
    var $children = array();

    /**
    *   @access private
    *   @var    boolean saves if tree nodes shall be removed recursively
    *   @see    setRemoveRecursively()
    */
    var $removeRecursively = false;


    /**
    *   @access public
    *   @var    integer $debug  the debug mode, if > 0 then debug info are shown,
    *                           actually those messages only show performance times
    */
    var $debug = 0;

    /**
    *   @see    &getNode()
    *   @see    &_getNode()
    *   @access private
    *   @var    integer $_getNodeMaxLevel   variable only used in the method getNode and _getNode
    */
    var $_getNodeMaxLevel;

    /**
    *   @see    &getNode()
    *   @see    &_getNode()
    *   @access private
    *   @var    integer $_getNodeCurParent  variable only used in the method getNode and _getNode
    */
    var $_getNodeCurParent;

    /**
    *   the maximum depth of the tree
    *   @access private
    *   @var    int     the maximum depth of the tree
    */
    var $_treeDepth = 0;
    
    /**
    *   set up this object
    *
    *   @version    2001/06/27
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $dsn        this is a DSN for the PEAR::DB, can be either an object/string
    *   @param      array   $options    additional options you can set
    */
    function Tree_Memory( $type , $dsn='' , $options=array() )
    {
        $this->Tree_Options($options); // set the options for $this

        require_once("Tree/Memory/$type.php");

        $className = 'Tree_Memory_'.$type;
        $this->dataSourceClass =& new $className( $dsn , $options );
        // copy the options to be able to get them via getOption(s)
//FIXXME this is not really cool, maybe overwrite the *Option* methods!!!
        if( isset($this->dataSourceClass->options) )
            $this->options = $this->dataSourceClass->options;

    } // end of function

    /**
    *   use this to switch data sources on the run
    *   i.e. if you are reading the data from a db-tree and want to save it
    *   as xml data (which will work one day too)
    *   or reading the data from an xml file and writing it in the db
    *   which should already work
    *
    *   @version    2002/01/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      string  $dsn    this is a DSN of the for that PEAR::DB uses it
    *                               only that additionally you can add parameters like ...?table=test_table
    *                               to define the table it shall work on
    *   @param      array   $options  additional options you can set
    *   @return     boolean     true on success
    */
    function switchDataSource( $type , $dsn='' , $options=array() )
    {
        $data = $this->getNode();
        //$this->Tree( $dsn , $options );
        $this->Tree_Memory( $type , $GLOBALS['dummy'] , $options );

        // this method prepares data retreived using getNode to be used
        // in this type of tree
        $this->dataSourceClass->setData($data);
        $this->setup();
    }

    /**
    *
    *
    *   @version    2002/01/19
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return
    */
    function setupByRawData( $string )
    {
//  expects
//   for XML an XML-String,
//   for DB-a result set, may be or an array, dont know here - not implemented yet
        $res = $this->dataSourceClass->setupByRawData( $string );
        return $this->_setup( $res );
    }

    /**
    *
    *
    *   @version    2002/01/19
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array   the result of a query which retreives (all) the tree data from a source
    *   @return     true or Tree_Error
    */
    function setup($data=null)
    {
        if( $this->debug )
        {
            $startTime = split(" ",microtime());
            $startTime = $startTime[1]+$startTime[0];
        }

        if(PEAR::isError($res = $this->dataSourceClass->setup($data)) )
            return $res;

        if( $this->debug )
        {
            $endTime = split(" ",microtime());
            $endTime = $endTime[1]+$endTime[0];
            print( " reading and preparing tree data took: ".($endTime - $startTime)." <br>" );
        }

        return $this->_setup( $res );

    }

    /**
    *   retreive all the navigation data from the db and build the
    *   tree in the array data and structure
    *
    *   @version    2001/11/20
    *   @access     private
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     boolean     true on success
    */
    function _setup( $setupData )
    {
// TODO sort by prevId (parentId,prevId $addQuery) too if it exists in the table, or the root might be wrong
// TODO  since the prevId of the root should be 0
        if( !$setupData )
            return false;

//FIXXXXXME validate the structure. i.e. a problem occurs, if you give one node, which has a parentId=1 it screws up everything!!!
        // empty the data structures, since we are reading the data from the db (again)
        $this->structure = array();
        $this->data = array();
        $this->children = array();
        // build an array where all the parents have their children as a member
        // this i do to speed up the buildStructure
        foreach( $setupData as $values )
        {
            if( is_array($values) )
            {
                $this->data[$values['id']] = $values;
                $this->children[ $values['parentId'] ][] = $values['id'];
            }
        }

        // walk through all the children on each level and set the next/previous relations
        // of those children, since all children for "children[$id]" are on the same level we can do
        // this here :-)
        foreach( $this->children as $children )
        {
            $lastPrevId = 0;
            if(sizeof($children))
            foreach( $children as $key )
            {
                if( $lastPrevId )
                {
                    $this->data[$lastPrevId]['nextId'] = $key;  // remember the nextId too, so the build process can be sped up
                    $this->data[$lastPrevId]['next'] =   &$this->data[$key];

                    $this->data[$key]['prevId'] = $lastPrevId;
                    $this->data[$key]['previous'] = &$this->data[ $lastPrevId ];
                }
                $lastPrevId = $key;
            }
        }

//print_r($this->children);

        if( $this->debug )
        {
            $startTime = split(" ",microtime());
            $startTime = $startTime[1]+$startTime[0];
        }

        // when NO prevId is given, sort the entries in each level by the given sort order (to be defined)
        // and set the prevId so the build can work properly
        if( !isset($setupData[0]['prevId']) )   // does a prevId exist?
        {
            $lastPrevId = 0;
            $lastParentId = 0;
            $level = 0;
            // build the entire recursive relations, so you have 'parentId', 'childId', 'nextId', 'prevId'
            // and the references 'child', 'parent', 'next', 'previous' set in the property 'data'
            foreach( $this->data as $key=>$value )
            {
                // most if checks in this foreach are for the following reason, if not stated otherwise:
                // dont make an data[''] or data[0] since this was not read from the DB, because id is autoincrement and starts at 1
                // and also in an xml tree there can not be an element </> , i hope :-)
                if( $value['parentId'] )            // see comment above
                {
                    $this->data[$key]['parent']    = &$this->data[ $value['parentId'] ];
                    // the parent has an extra array which contains a reference to all it's children, set it here
                    $this->data[ $value['parentId'] ]['children'][] = &$this->data[$key];
                }

                // was a child saved (in the above 'if')
                if( isset($this->children[$key]) && sizeof( $this->children[$key] ) ) // see comment above
                {
                    // refer to the first child in the [child] and [childId] keys
                    $this->data[$key]['childId'] = $this->children[$key][0];
                    $this->data[$key]['child'] =   &$this->data[ $this->children[$key][0] ];
                }

                $lastParentId = $value['parentId'];
            }
        }

        if( $this->debug )
        {
            $endTime = split(" ",microtime());
            $endTime = $endTime[1]+$endTime[0];
            print( " building took: ".($endTime - $startTime)." <br>" );
        }

        // build the property 'structure'
        $this->structure = array(); // empty it, just to be sure everything will be set properly

        if( $this->debug )
        {
            $startTime = split(" ",microtime());
            $startTime = $startTime[1]+$startTime[0];
        }

        // build all the children that are on the root level, if we wouldnt do that
        // we would have to create a root element with an id 0, but since this is not
        // read from the db we dont add another element, the user wants to get what he had saved
        if( sizeof($this->children[0]) )
        foreach( $this->children[0] as $rootElement )
        {
            $this->buildStructure( $rootElement , $this->structure );
        }

        if( $this->debug )
        {
            $endTime = split(" ",microtime());
            $endTime = $endTime[1]+$endTime[0];
            print( " buildStructure took: ".($endTime - $startTime)." <br>" );
        }

        return true;
    }

    /**
    *   adds _one_ new element in the tree under the given parent
    *   the values' keys given have to match the db-columns, because the
    *   value gets inserted in the db directly
    *   to add an entire node containing children and so on see 'addNode()'
    *   @see        addNode()
    *   @version    2001/10/09
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array $newValues this array contains the values that shall be inserted in the db-table
    *   @param      int     the parent id
    *   @param      int     the prevId
    *   @return     mixed   either boolean false on failure or the id of the inserted row
    */
    function add( $newValues , $parentId=0 , $prevId=0 )
    {
        // see comments in 'move' and 'remove'

        if (method_exists($this->dataSourceClass,'add')) {
            return $this->dataSourceClass->add( $newValues , $parentId , $prevId );
        } else {
            return $this->_throwError( 'method not implemented yet.' , __LINE__ );
        }
    } // end of function


    /**
    *   removes the given node and all children if removeRecursively is on
    *
    *   @version    2002/01/24
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $id     the id of the node to be removed
    *   @return     boolean true on success
    */
    function remove( $id )
    {
        // if removing recursively is not allowed, which means every child should be removed
        // then check if this element has a child and return "sorry baby cant remove :-) "
        if ($this->removeRecursively != true) {
            if (isset( $this->data[$id]['child'] )) {
// TODO raise PEAR warning
                return $this->_throwError("Element with id=$id has children, cant be removed. Set 'setRemoveRecursively' to true to allow this.",__LINE__);
            }
        }

        // see comment in 'move'
        // if the prevId is in use we need to update the prevId of the element after the one that
        // is removed too, to have the prevId of the one that is removed!!!

        if (method_exists($this->dataSourceClass,'remove')) {
            return $this->dataSourceClass->remove( $id );
        } else {
            return $this->_throwError( 'method not implemented yet.' , __LINE__ );
        }
    }

    /**
    *   collects the ID's of the elements to be removed
    *
    *   @version    2001/10/09
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $id   the id of the node to be removed
    *   @return     boolean true on success
    */
    function _remove( $element )
    {
        return $element['id'];
    } // end of function

    /**
    *   move an entry under a given parent or behind a given entry.
    *   !!! the 'move behind another element' is only implemented for nested trees now!!!
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
    *
    *   @version    2002/06/08
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer     the id(s) of the element(s) that shall be moved
    *   @param      integer     the id of the element which will be the new parent
    *   @param      integer     if prevId is given the element with the id idToMove
    *                           shall be moved _behind_ the element with id=prevId
    *                           if it is 0 it will be put at the beginning
    *   @return     boolean     true for success
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
// FIXXME return a Tree_Error, not an array !!!!!
        if( sizeof($errors) )
            return $errors;
        return true;
    }

    /**
    *   this method moves one tree element
    *
    *   @see        move()
    *   @version    2001/10/10
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer     the id of the element that shall be moved
    *   @param      integer     the id of the element which will be the new parent
    *   @param      integer     if prevId is given the element with the id idToMove
    *                           shall be moved _behind_ the element with id=prevId
    *                           if it is 0 it will be put at the beginning
    *   @return     mixed       true for success, Tree_Error on failure
    */
    function _move( $idToMove , $newParentId , $prevId=0 )
    {
        if( $idToMove == $newParentId )             // itself can not be a parent of itself
// TODO PEAR-ize error
            return TREE_ERROR_INVALID_PARENT;

        // check if $newParentId is a child (or a child-child ...) of $idToMove
        // if so prevent moving, because that is not possible
//        if( @$this->data[$idToMove]['children'] )     // does this element have children?
        if( $this->hasChildren($idToMove) )     // does this element have children?
        {
//            $allChildren = $this->data[$idToMove]['children'];
            $allChildren = $this->getChildren($idToMove);
// FIXXME what happens here we are changing $allChildren, doesnt this change the
// property data too??? since getChildren (might, not yet) return a reference
            while (list(, $aChild) = each ($allChildren))   // use while since foreach only works on a copy of the data to loop through, but we are changing $allChildren in the loop
            {
                array_shift( $allChildren );        // remove the first element because if array_merge is called the array pointer seems to be
                                                    // set to the beginning and this way the beginning is always the current element, simply work off and truncate in front
                if( @$aChild['children'] )
                {
                    $allChildren = array_merge( $allChildren , $aChild['children'] );
                }
                if( $newParentId == $aChild['id'] )
// TODO PEAR-ize error
                    return TREE_ERROR_INVALID_PARENT;
            }
        }

        // what happens if i am using the prevId too, then the db class also
        // needs to know where the element should be moved to
        // and it has to change the prevId of the element that will be after it
        // so we may be simply call some method like 'update' too?

        if( method_exists($this->dataSourceClass,'move') )
            return $this->dataSourceClass->move( $idToMove , $newParentId , $prevId );
        else
            return $this->_throwError( 'method not implemented yet.' , __LINE__ );
    } // end of function

    /**
    *   update data in a node
    *
    *   @version    2002/01/29
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array   $data   the data to update
    *   @return
    */
    function update( $id , $data )
    {
        if (method_exists($this->dataSourceClass,'update')) {
            return $this->dataSourceClass->update($id,$data);
        } else {
            return $this->_throwError( 'method not implemented yet.' , __LINE__ );
        }
    } // end of function






    //
    //
    //  from here all methods are not interacting on the  'dataSourceClass'
    //
    //

    /**
    *   builds the structure in the parameter $insertIn
    *   this function works recursively down into depth of the folder structure
    *   it builds an array which goes as deep as the structure goes
    *
    *   @access     public
    *   @version    2001/05/02
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer $parentId the parent for which it's structure shall be built
    *   @param      integer $insertIn the array where to build the structure in
    *                       given as a reference to be sure the substructure is built
    *                       in the same array as passed to the function
    *   @return     boolean returns always true
    *
    */
    function buildStructure( $parentId , &$insertIn )
    {
        // create the element, so it exists in the property "structure"
        // also if there are no children below
        $insertIn[$parentId] = array();

        // set the level, since we are walking through the structure here anyway we
        // can do this here, instead of up in the setup method :-)
        // always set the level to one higher than the parent's level, easy ha?
        if (isset($this->data[$parentId]['parent']['level'])) {  // this applies only to the root element(s)
            $this->data[$parentId]['level'] = $this->data[$parentId]['parent']['level']+1;
            
            if ($this->data[$parentId]['level']>$this->_treeDepth) {
                $this->_treeDepth = $this->data[$parentId]['level'];
            }
        } else {
            $this->data[$parentId]['level'] = 0;    // set first level number to 0
        }

        if (isset($this->children[$parentId]) && sizeof($this->children[$parentId])) {
            // go thru all the folders
            foreach ($this->children[$parentId] as $child) {
                // build the structure under this folder,
                // use the current folder as the new parent and call build recursively
                // to build all the children
                // by calling build with $insertIn[someindex] the array is filled
                // since the array was empty before
                $this->buildStructure( $child , $insertIn[$parentId] );
            }
        }

        return true;
    } // end of function

    /**
    *   this method only serves to call the _walk method and reset $this->walkReturn
    *   that will be returned by all the walk-steps
    *
    *   @version    2001/11/25
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $walkFunction   the name of the function to call for each walk step,
    *                                       or an array for a method, where
    *                                       [0] is the method name and [1] the object
    *   @param      array   $id     the id to start walking through the tree, everything below is walked through
    *   @param      string  $returnType the return of all the walk data will be of the given type (values: string, array)
    *   @return     mixed   this is all the return data collected from all the walk-steps
    *
    */
    function walk( $walkFunction , $id=0 , $returnType='string')
    {
        $useNode = $this->structure;                // by default all of structure is used
        if ($id == 0) {
            $keys = array_keys($this->structure);
            $id = $keys[0];
        } else {
            $path = $this->getPath($id);            // get the path, to be able to go to the element in this->structure
            array_pop($path);                       // pop off the last element, since it is the one requested
            $curNode = $this->structure;            // start at the root of structure
            foreach ($path as $node) {
                $curNode = $curNode[$node['id']];   // go as deep into structure as path defines
            }
            $useNode = array();                     // empty it first, so we dont have the other stuff in there from before
            $useNode[$id] = $curNode[$id];          // copy only the branch of the tree that the parameter $id requested
        }

        unset($this->walkReturn);                   // a new walk starts, unset the return value
        return $this->_walk( $walkFunction , $useNode , $returnType );
    }

    /**
    *   walks through the entire tree and returns the current element and the level
    *   so a user can use this to build a treemap or whatever
    *
    *   @version    2001/06/xx
    *   @access     private
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $walkFunction   the name of the function to call for each walk step,
    *                                       or an array for a method, where
    *                                       [0] is the method name and [1] the object
    *   @param      array   $curLevel      the reference in the this->structure, to walk everything below
    *   @param      string  $returnType the return of all the walk data will be of the given type (values: string, array, ifArray)
    *   @return     mixed   this is all the return data collected from all the walk-steps
    *
    */
    function _walk( $walkFunction , &$curLevel , $returnType )
    {
        if (sizeof($curLevel)) {
            foreach ($curLevel as $key=>$value) {
                $ret = call_user_func( $walkFunction , $this->data[$key] );
                switch ($returnType) {
                    case 'array':   $this->walkReturn[] = $ret;
                                    break;
                    case 'ifArray': // this only adds the element if the $ret is an array and contains data
                                    if (is_array($ret)) {
                                        $this->walkReturn[] = $ret;
                                    }
                                    break;
                    default:        $this->walkReturn.= $ret;
                                    break;
                }
                $this->_walk( $walkFunction , $value , $returnType );
            }
        }
        return $this->walkReturn;
    } // end of function

    /**
    *   adds multiple elements
    *   you have to pass those elements in a multidimensional array which represents the
    *   tree structure as it shall be added (this array can of course also simply contain one element)
    *   the following array $x passed as the parameter
    *        $x[0] = array(  'name'=>'bla','parentId'=>'30',
    *                        array(  'name'=>'bla1','comment'=>'foo',
    *                                array('name'=>'bla2'),
    *                                array('name'=>'bla2_1')
    *                        ),
    *                        array(  'name'=>'bla1_1'),
    *                        )
    *                      );
    *        $x[1] = array(  'name'=>'fooBla','parentId'=>'30');
    *
    *   would add the following tree (or subtree, or node whatever you want to call it)
    *   under the parent with the id 30 (since 'parentId'=30 in $x[0] and in $x[1])
    *    +--bla
    *    |   +--bla1
    *    |   |    +--bla2
    *    |   |    +--bla2_1
    *    |   +--bla1_1
    *    +--fooBla
    *
    *   @see        add()
    *   @version    2001/12/19
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array   $node   the tree to be inserted, represents the tree structure,
    *                               see add() for the exact member of each node
    *   @return     mixed   either boolean false on failure or the id of the inserted row
    */
    function addNode( $node )
    {
        if( sizeof($node) )
        foreach( $node as $aNode )
        {
            $newNode = array();
            foreach( $aNode as $name=>$value )      // this should always have data, if not the passed structure has an error
            {
                if( !is_array($value) )             // collect the data that need to go in the DB
                    $newEntry[$name] = $value;
                else                                // collect the children
                    $newNode[] = $value;
            }
            $insertedId = $this->add( $newEntry );  // add the element and get the id, that it got, to have the parentId for the children

            if( $insertedId!= false )               // if inserting suceeded, we have received the id under which we can insert the children
            {
                if( sizeof($newNode) )              // if there are children, set their parentId, so they kknow where they belong in the tree
                foreach( $newNode as $key=>$aNewNode )
                {
                    $newNode[$key]['parentId'] = $insertedId;
                }
                $this->addNode( $newNode );         // call yourself recursively to insert the children, and its children and ...
            }
        }
    } // end of function

    /**
    *   gets the path to the element given by its id
    *   !!! ATTENTION watch out that you never change any of the data returned,
    *   since they are references to the internal property $data
    *
    *   @access     public
    *   @version    2001/10/10
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $id     the id of the node to get the path for
    *   @return     array   this array contains all elements from the root to the element given by the id
    *
    */
    function getPath( $id )
    {
        $path = array();                            // empty the path, to be clean

// FIXXME may its better to use a for(level) to count down,
// since a while is always a little risky
        while( @$this->data[$id]['parent'] )        // until there are no more parents
        {
            $path[] = &$this->data[$id];            // curElement is already a reference, so save it in path
            $id = $this->data[$id]['parent']['id']; // get the next parent id, for the while to retreive the parent's parent
        }
        $path[] = &$this->data[$id];                // dont forget the last one

        return array_reverse($path);
    } // end of function

    /**
    *   sets the remove-recursively mode, either true or false
    *
    *   @version    2001/10/09
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      boolean $newValues set to true if removing a tree level shall remove all it's children and theit children ...
    *
    */
    function setRemoveRecursively( $case=true )
    {
        $this->removeRecursively = $case;
    } // end of function

    /**
    *
    *
    *   @version    2002/01/21
    *   @access     private
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *
    */
    function &_getElement( $id , $what='' )
    {
        if( $what=='' )
        {
            return $this->data[$id];
        }

        $elementId = $this->_getElementId( $id , $what );
        if( $elementId !== NULL )
            return $this->data[$elementId];

        return NULL;    // we should not return false, since that might be a value of the element that is requested
    } // end of function

    /**
    *
    *
    *   @version    2002/01/21
    *   @access     private
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *
    */
    function _getElementId( $id , $what )
    {
        if( @$this->data[$id][$what] )          // use @ since the key $what might not exist
            return $this->data[$id][$what]['id'];

        return NULL;
    } // end of function

    /**
    *   gets an element as a reference
    *
    *   @version    2002/01/21
    *   @access     private
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *
    */
    function &getElement( $id )
    {
        return $this->_getElement( $id );
    }

    /**
    *
    *
    *   @version    2002/02/06
    *   @access     private
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   either the id of an element or the path to the element
    *
    */
    function getElementContent( $idOrPath , $fieldName )
    {
        if( is_string($idOrPath) )
        {
            $id = $this->getIdByPath($idOrPath);
        }

        return $this->data[$id][$fieldName];
    }

    /**
    *
    *
    *   @version    2002/02/06
    *   @access     private
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *
    */
    function getElementsContent( $ids , $fieldName )
    {
// i dont know if this method is not just overloading the file, since it only serves my lazyness
// is this effective here? i can also loop in the calling code!?
        $fields = array();
        if(is_array($ids) && sizeof($ids))
        foreach( $ids as $aId )
            $fields[] = $this->getElementContent( $aId , $fieldName );

        return $fields;
    }

    /**
    *   gets an element given by it's path as a reference
    *
    *   @version    2002/01/21
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      string  $path       the path to search for
    *   @param      integer $startId    the id where to search for the path
    *   @param      string  $nodeName   the name of the key that contains the node name
    *   @param      string  $seperator  the path seperator
    *   @return     integer the id of the searched element
    *
    */
    function &getElementByPath( $path , $startId=0 , $nodeName='name' , $seperator='/' )
    {
        $id = $this->getIdByPath( $path , $startId );
        if( $id )
            return $this->getElement( $id );
        return NULL;                                // return NULL since false might be interpreted as id 0
    }

    /**
    *   gets an element ID
    *
    *   @version    2002/01/21
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *
    */
/* we already have a method getIdByPath, which one should we use ????
    function &getElementIdByPath( $id )
    {
        return $this->_getElement( $id );
    }
*/

    /**
    *   get the level, which is how far below the root are we?
    *
    *   @version    2001/11/25
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $id     the id of the node to get the level for
    *
    */
    function getLevel( $id )
    {
        return $this->data[$id]['level'];
    } // end of function

    /**
    *   returns the child if the node given has one
    *   !!! ATTENTION watch out that you never change any of the data returned,
    *   since they are references to the internal property $data
    *
    *   @version    2001/11/27
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $id     the id of the node to get the child for
    *
    */
    function &getChild( $id )
    {
        return $this->_getElement( $id , 'child' );
    } // end of function

    /**
    *   returns the child if the node given has one
    *   !!! ATTENTION watch out that you never change any of the data returned,
    *   since they are references to the internal property $data
    *
    *   @version    2001/11/27
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $id     the id of the node to get the child for
    *
    */
    function &getParent( $id )
    {
        return $this->_getElement( $id , 'parent' );
    } // end of function

    /**
    *   returns the next element if the node given has one
    *   !!! ATTENTION watch out that you never change any of the data returned,
    *   since they are references to the internal property $data
    *
    *   @version    2002/01/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $id     the id of the node to get the child for
    *   @return     mixed   reference to the next element or false if there is none
    */
    function &getNext( $id )
    {
        return $this->_getElement( $id , 'next' );
    } // end of function

    /**
    *   returns the previous element if the node given has one
    *   !!! ATTENTION watch out that you never change any of the data returned,
    *   since they are references to the internal property $data
    *
    *   @version    2002/02/05
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $id     the id of the node to get the child for
    *   @return     mixed   reference to the next element or false if there is none
    */
    function &getPrevious( $id )
    {
        return $this->_getElement( $id , 'previous' );
    } // end of function

    /**
    *   returns the node for the given id
    *   !!! ATTENTION watch out that you never change any of the data returned,
    *   since they are references to the internal property $data
    *
    *   @version    2001/11/28
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      mixed   $id     the id of the node to get
    *
    */
/* this should be getElement, i think it was a bit weird that i made this method like this
    function &getNode( $id )
    {
        return $this->_getElement( $id );
    } // end of function
*/

    /**
    *   return the id of the element which is referenced by $path
    *   this is useful for xml-structures, like: getIdByPath( '/root/sub1/sub2' )
    *   this requires the structure to use each name uniquely
    *   if this is not given it will return the first proper path found
    *   i.e. there should only be one path /x/y/z
    *
    *   @version    2001/11/28
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      string  $path       the path to search for
    *   @param      integer $startId    the id where to search for the path
    *   @param      string  $nodeName   the name of the key that contains the node name
    *   @param      string  $seperator  the path seperator
    *   @return     integer the id of the searched element
    *
    */
    function getIdByPath( $path , $startId=0 , $nodeName='name' , $seperator='/' )
// should this method be called getElementIdByPath ????
    {
        // if no start ID is given get the root
        if( $startId==0 )
            $startId = $this->getFirstRootId();
        else    // if a start id is given, get its first child to start searching there
        {
            $startId = $this->getChildId($startId);
            if( $startId == false )                 // is there a child to this element?
                return false;
        }

        if( strpos( $path , $seperator )===0 )  // if a seperator is at the beginning strip it off
            $path = substr( $path , strlen($seperator) );

        $nodes = explode( $seperator , $path );

        $curId = $startId;
        foreach( $nodes as $key=>$aNodeName )
        {
            $nodeFound = false;
            do
            {
//print "search $aNodeName, in ".$this->data[$curId][$nodeName]."<br>";
                if( $this->data[$curId][$nodeName] == $aNodeName )
                {
                    $nodeFound = true;
                    // do only save the child if we are not already at the end of path
                    // because then we need curId to return it
                    if( $key < (sizeof($nodes)-1) )
                        $curId = $this->getChildId($curId);
                    break;
                }
                $curId = $this->getNextId($curId);
//print "curId = $curId<br>";
            }
            while( $curId );

            if( $nodeFound==false )
            {
//print 'NOT FOUND<br><br>';
                return false;
            }
        }
//print '<br>';

        return $curId;
// FIXXME to be implemented
    } // end of function

    /**
    *   this gets the first element that is in the root node
    *   i think that there can't be a "getRoot" method since there might
    *   be multiple number of elements in the root node, at least the
    *   way it works now
    *
    *   @access     public
    *   @version    2001/12/10
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     returns the first root element
    */
    function &getFirstRoot()
    {
        // could also be reset($this->data) i think, since php keeps the order ... but i didnt try
        reset($this->structure);
        return $this->data[key($this->structure)];
    } // end of function

    /**
    *   since in a nested tree there can only be one root
    *   which i think (now) is correct, we also need an alias for this method
    *   this also makes all the methods in Tree_Common, which access the
    *   root element work properly!
    *
    *   @access     public
    *   @version    2002/07/26
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     returns the first root element
    */
    function &getRoot()
    {
        return $this->getFirstRoot();
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
    *   @param      integer $depth      this number says how deep into
    *                                   the structure the elements shall be retreived
    *   @return     array   sorted as listed in the tree
    */
    function &getNode( $startId=0 , $depth=0 )
    {
        if ($startId == 0) {
            $level = 0;
        } else {
            $level = $this->getLevel($startId);
        }

        $this->_getNodeMaxLevel = $depth ? ($depth + $level) : 0 ;
//!!!        $this->_getNodeCurParent = $this->data['parent']['id'];

        // if the tree is empty dont walk through it
        if (!sizeof($this->data)) {
            return;
        }

        $ret = $this->walk( array(&$this,'_getNode') , $startId , 'ifArray' );
        return $ret;
    } // end of function

    /**
    *   this is used for walking through the tree structure
    *   until a given level, this method should only be used by getNode
    *
    *   @see        &getNode()
    *   @see        walk()
    *   @see        _walk()
    *   @access     private
    *   @version    2001/12/17
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array   $node   the node passed by _walk
    *   @return     mixed   either returns the node, or nothing if the level _getNodeMaxLevel is reached
    */
    function &_getNode( &$node )
    {
        if ($this->_getNodeMaxLevel) {
            if ($this->getLevel($node['id']) < $this->_getNodeMaxLevel) {
                return $node;
            }
            return;
        }
        return $node;
    } // end of function

    /**
    *   returns if the given element has any children
    *
    *   @version    2001/12/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer $id the id of the node to check for children
    *   @return     boolean true if the node has children
    */
    function hasChildren( $id=0 )
    {
        if( isset($this->data[$id]['children']) && sizeof($this->data[$id]['children']) > 0 )
            return true;
        return false;
    } // end of function

    /**
    *   returns the children of the given ids
    *
    *   @version    2001/12/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer $id the id of the node to check for children
    *   @param      integer the children of how many levels shall be returned
    *   @return     boolean true if the node has children
    */
    function getChildren( $ids , $levels=1 )
    {
//FIXXME $levels to be implemented
        $ret = array();
        if (is_array($ids)) {
            foreach ($ids as $aId) {
                if ($this->hasChildren( $aId )) {
                    $ret[$aId] = $this->data[$aId]['children'];
                }
            }

        } else {
            if ($this->hasChildren( $ids )) {
                $ret = $this->data[$ids]['children'];
            }
        }
        return $ret;
    } // end of function

    /**
    *   returns if the given element is a valid node
    *
    *   @version    2001/12/21
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      integer $id the id of the node to check for children
    *   @return     boolean true if the node has children
    */
    function isNode( $id=0 )
    {
        return isset($this->data[$id]);
    } // end of function

    /**
    *   this is for debugging, dumps the entire data-array
    *   an extra method is needed, since this array contains recursive
    *   elements which make a normal print_f or var_dump not show all the data
    *
    *   @version    2002/01/21
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @params     mixed   $node   either the id of the node to dump, this will dump everything below the given node
    *                               or an array of nodes, to dump, this only dumps the elements passed as an array
    *                               or 0 or no parameter if the entire tree shall be dumped
    *                               if you want to dump only a single element pass it as an array using
    *                               array($element)
    */
    function varDump( $node=0 )
    {
        $dontDump = array('parent','child','children','next','previous');

        // if $node is an array, we assume it is a collection of elements
        if( !is_array($node) )
            $nodes = $this->getNode($node);  // if $node==0 then the entire tree is retreived
            
        if (sizeof($node)) {
            print '<table border="1"><tr><th>name</th>';
            $keys = array();
            foreach ($this->getRoot() as $key=>$x) {
                if (!is_array($x)) {
                    print "<th>$key</th>";
                    $keys[] = $key;
                }
            }
            print "</tr>";
            
            foreach ($nodes as $aNode) {
                print '<tr><td nowrap="nowrap">';
                $prefix = '';
                for($i=0;$i<$aNode['level'];$i++) $prefix .= '- ';
                print "$prefix {$aNode['name']}</td>";
                foreach ($keys as $aKey) {
                    if (!is_array($key)) {
                        $val = $aNode[$aKey] ? $aNode[$aKey] : '&nbsp;';
                        print "<td>$val</td>";
                    }
                }
                print "</tr>";
            }  
            print "</table>";          
        }            
    } // end of function







    //### TODO's ###

    /**
    *   NOT IMPLEMENTED YET
    *   copies a part of the tree under a given parent
    *
    *   @version    2001/12/19
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      $srcId      the id of the element which is copied, all its children are copied too
    *   @param      $destId     the id that shall be the new parent
    *   @return     boolean     true on success
    *
    */
    function copy( $srcId , $destId )
    {
        if( method_exists($this->dataSourceClass,'copy') )
            return $this->dataSourceClass->copy( $srcId , $destId );
        else
            return $this->_throwError( 'method not implemented yet.' , __LINE__ );
/*
    remove all array elements after 'parent' since those had been created
    and remove id and set parentId and that should be it, build the tree and pass it to addNode

    those are the fields in one data-entry
id=>41
parentId=>39
name=>Java
parent=>Array
prevId=>58
previous=>Array
childId=>77
child=>Array
nextId=>104
next=>Array
children=>Array
level=>2

        $this->getNode
        foreach( $this->data[$srcId] as $key=>$value )
            print("$key=>$value<br>");
*/
    } // end of function



} // end of class
?>
