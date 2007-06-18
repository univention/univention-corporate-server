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
//  $Id: Array.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once('Tree/Error.php');

/**
*   EXPERIMENTAL
*
*   @access     public
*   @author     Wolfram Kriesing <wolfram@kriesing.de>
*   @version    2002/08/30
*   @package    Tree
*/
class Tree_Memory_Array
{

    var $data = array();
             
    /**
    *   this is the internal id that will be assigned if no id is given
    *   it simply counts from 1, so we can check if( $id ) i am lazy :-)
    */
    var $_id = 1;
    
    /**
    *   set up this object
    *
    *   @version    2002/08/30
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      string  $dsn    the path on the filesystem
    *   @param      array   $options  additional options you can set
    */
    function Tree_Memory_Array( &$array , $options=array() )
    {
        $this->_array = &$array;
        $this->_options = $options; // not in use currently
    } // end of function

    /**
    *
    *
    *   @version    2002/08/30
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     boolean     true on success
    */
    function setup()
    {
        unset($this->data);                         // unset the data to be sure to get the real data again, no old data
        if (is_array($this->_array)) {
            $this->data[0] = null;
            $theData = array(&$this->_array);
            $this->_setup($theData);
        }

/*foreach($this->data as $val){print "\r\n";
foreach ($val as $k=>$v)
    print "$k=>$v\r\n";
}*/
            return $this->data;
    }

    /**
    *   we modify the $this->_array in here, we also add the id
    *   so methods like 'add' etc can find the elements they are searching for,
    *   if you dont like your data to be modified dont pass them as reference!
    */
    function _setup( &$array , $parentId=0 )
    {
        foreach ($array as $nodeKey=>$aNode) {
            $newData = $aNode;
            if (!isset($newData['id']) || !$newData['id']) {    // if the current element has no id, we generate one
                $newData['id'] = $this->_id++;      // build a unique numeric id
                $array[$nodeKey]['id'] = $newData['id'];    // set the id
            } else {
                $idAsInt = (int)$newData['id'];
                if ($idAsInt > $this->_id) {
                    $this->_id = $idAsInt;
                }
            }
//print "a node name=".$aNode['name'].'<br>';
            $newData['parentId'] = $parentId;       // set the parent-id, since we only have a 'children' array
            $children = null;
            foreach ( $newData as $key=>$val ) {    // remove the 'children' array, since this is only info for this class
                if ($key=='children') {
                    unset($newData[$key]);
                }
            }

            $this->data[$newData['id']] = $newData;
            if (isset($aNode['children']) && $aNode['children']) {
                if (!isset($array[$nodeKey]['children'])) {
                    $array[$nodeKey]['children'] = array();
                }
                $this->_setup( $array[$nodeKey]['children'] , $newData['id'] );
            }
        }
    }


    /**
    *   this is mostly used by switchDataSource
    *   this method put data gotten from getNode() in the $this->_array
    *
    */
    function setData($data)
    {
/*
        $root = array_shift($data);
        unset($root['children']);
        $this->_array = array('children'=> array($root));
foreach ($this->_array['children'][0] as $key=>$val)
    print "$key=>$val<br>";
print "<br>";
*/
        $unsetKeys = array('childId','left','right');

        foreach ( $data as $aNode ) {
//print $aNode['id'].' : '.$aNode['name'].'  parentId='.$aNode['parentId'].' size='.sizeof($this->_array['children'][0]['children']).'<br>';
            foreach ($aNode as $key=>$val) {
                if (is_array($val) || in_array($key,$unsetKeys)) {
                    unset($aNode[$key]);
                }
            }
            $this->add($aNode,$aNode['parentId']);
        }
//foreach ($this->_array['children'][0]['children'] as $x){print "<br>";
//foreach ($x as $key=>$val)
//    print "$key=>$val<br>";}
        $this->_array = $this->_array['children'][0];
    }

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
    *   add a new item to the tree
    *   what is tricky here, we also need to add it to the source array
    *   
    *   @param  array   the data for the new node
    *   @param  int     the ID of the parent node
    *   @param  int     the ID of the previous node
    */
    function add( $data , $parentId , $previousId=null )
    {
        if (!isset($data['id'])) {
            $data['id'] = ++$this->_id;
        } elseif((int)$data['id'] > $this->_id) {
            // update the $this->_id if the data['id'] has a higher number, since
            // we dont want to overwrite anything. just in case
            $this->_id = (int)$data['id'];
        }
        $data['parentId'] = $parentId;
        $this->data[$data['id']] = $data;

        //$path = $this->getPathById($parentId);
        if (!isset($this->_array['children'])) {    // there might not be a root element yet
            $data['parentId'] = 0;
            $this->_array['children'][] = $data;
        } else {
            array_walk($this->_array['children'],array(&$this,'_add'),array($data,$parentId,$previousId));
        }

        //$this->_array
        return $data['id'];
    }

    /**
    *   we need to add the node to the source array
    *   for this we have this private method which loops through 
    *   the source array and adds it in the right place
    *   
    *   @param  mixed   the value of the array, as a reference, so we work right on the source
    *   @param  mixed   the key of the node
    *   @param  array   an array which contains the following
    *                       new data, 
    *                       parent ID under which to add the node, 
    *                       the prvious ID
    */
    function _add( &$val , $key , $data )
    {
        if ($val['id']==$data[1]) { // is the id of the current elment ($val) == to the parentId ($data[1])
            if (isset($data[2]) && $data[2]===0 ) {  
                // if the previousId is 0 means, add it as the first member
                $val['children'] = array_merge(array($data[0]),$val['children']);
            } else {
                $val['children'][] = $data[0];
            }
        } else {        // if we havent found the new element go on searching
            if (isset($val['children'])) {
                array_walk($val['children'],array(&$this,'_add'),$data);
            }
        }
    }

    /**
    *   update an entry with the given id and set the data as given in the array $data
    *
    *   @param  int     the id of the element that shall be updated
    *   @param  array   the data, [key]=>[value]
    *   @return void
    */
    function update($id,$data)
    {
        if ($this->_array['id']==$id) {
            foreach ($data as $key=>$newVal) {
                $this->_array[$key] = $newVal;
            }
        } else {
            array_walk($this->_array['children'],array(&$this,'_update'),array($id,$data));
        }
    }

    /**
    *   update the element with the given id
    *
    *   @param  array   a reference to an element inside $this->_array
    *                   has to be a reference, so we can really modify the actual data
    *   @param  int     not in use, but array_walk passes this param
    *   @param  array   [0] is the id we are searching for
    *                   [1] are the new data we shall set
    *   @return void
    */
    function _update( &$val , $key , $data )
    {
//print $val['id'].'=='.$data[0].'<br>';
        if ($val['id']==$data[0]) { // is the id of the current elment ($val) == to the parentId ($data[1])
            foreach ($data[1] as $key=>$newVal) {
//print "set ".$val['name']."  $key = $newVal<br>";
                $val[$key] = $newVal;
            }
        } else {        // if we havent found the new element go on searching in the children
            if (isset($val['children'])) {
                array_walk($val['children'],array(&$this,'_update'),$data);
            }
        }
    }

    /**
    *   remove an element from the tree
    *   this removes all the children too
    *
    *   @param  int the id of the element to be removed
    */
    function remove($id)
    {
        if ($this->data[$id]) {                     // we only need to search for element that do exist :-) otherwise we save some processing time
            $this->_remove($this->_array,$id);
        }
    }

    /**
    *   remove the element with the given id
    *   this will definitely remove all the children too
    *
    *   @param  array   a reference to an element inside $this->_array
    *                   has to be a reference, so we can really modify the actual data
    *   @param  int     the id of the element to be removed
    *   @return void
    */
    function _remove( &$val , $id )
    {
        if (isset($val['children'])) {
            foreach ($val['children'] as $key=>$aVal) {
//print $aVal['id'].'=='.$id."\r\n";
                if ($aVal['id']==$id) {
//print "remove ".$aVal['name']."\r\n";
                    if (sizeof($val['children'])<2) {
                        unset($val['children']);
                    } else {
                        unset($val['children'][$key]);
                    }
                } else {
                    $this->_remove($val['children'][$key],$id);
                }
            }
        }
    }

} // end of class
?>
