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
//  $Id: XML.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once "XML/Parser.php";

/**
*   the XML interface for the tree class
*
*   @package  Tree
*   @author
*   @version
*   @access  public
*/
class Tree_Memory_XML extends XML_Parser
{

    /**
    *   @var    array   $data   the first element has to be empty, so we can use the parentId=0 as "no parent"
    */
    var $data = array(0=>NULL);

    /**
    *   @var    integer $level
    */
    var $level = 0;

    /**
    *   @var    array   $parentIdOnLevel
    */
    var $parentIdOnLevel = array();

    /**
    *   @var    boolean $folding    set case folding for the XML_Parser to false
    */
    var $folding = false;   // turn off case folding

    /**
    *   @var    boolean     if true it converts all attributes and tag names etc to lower case
    *                       this is default, since i dont see no way of case insensitive comparison
    *                       in the tree class, since you can access the internal data directly
    *                       or you get them returned ... i know this is not 100% proper OOP but that's how it is right now
    */
    var $_toLower = true;

    /**
    *
    *
    *   @version    2002/01/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     boolean     true on success
    */
    function Tree_Memory_XML( $dsn , $options )
    {
        $handle = $dsn;

        $this->XML_Parser();

        if (@is_resource($handle)) {
            $this->setInput($handle);
        } elseif ($handle != "") {
            $this->setInputFile($handle);
        } else {
            return $this->raiseError("No filename passed.");
        }
    }

    /**
    *
    *
    *   @version    2002/01/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     boolean     true on success
    */
    function startHandler($parser, $element, $attribs)
    {
        $elementBeforeId = sizeof($this->data)-1;
        $curId = sizeof($this->data);

        $this->data[$curId]['id'] = $curId;
        $this->data[$curId]['name'] = $this->_toLower ? strtolower($element) : $element;
        $this->data[$curId]['level'] = $this->level;
        $this->data[$curId]['attributes'] = $attribs;
        if( $this->_toLower )
        {
            $this->data[$curId]['attributes'] = array();
            foreach( $attribs as $key=>$value )
                $this->data[$curId]['attributes'][strtolower($key)] = $value;
        }

        if( isset($this->data[$elementBeforeId]['level']) &&
            $this->level == $this->data[$elementBeforeId]['level'] )  // is that a new child, or just a 'next' of a child?
        {
            $this->data[$curId]['parentId'] = $this->data[$elementBeforeId]['parentId'];
        }
        else    // set stuff for the first child !!!
        {
            if( $this->level>0 )    // the root has no parent
            {
                $parentId = $this->parentIdOnLevel[$this->level-1];
                $this->data[$curId]['parentId'] = $parentId;
            }
            else
            {
                $this->data[$curId]['parentId'] = 0;
            }
        }
        $this->parentIdOnLevel[$this->level] = $curId;

#print "$curId $element ".$this->data[$curId]['parentId'].'<br>';
        $this->level++;
    }

    /**
    *
    *
    *   @version    2002/01/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     boolean     true on success
    */
    function endHandler($parser, $element)
    {
        $this->level--;
    }

    /**
    *
    *
    *   @version    2002/01/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     boolean     true on success
    */
    function cdataHandler($parser, $cdata)
    {
# QUESTION: why is this method called multiple times for one element?
# is every space a cdata ???
# ANSWER: if you call xml_parse($parser, "foo ", false) and then
#         xml_parse($parser, "bar", true), callbacks are done once
#         for each xml_parse() call.
        if( !isset($this->data[ sizeof($this->data)-1 ]['cdata']) )
            $this->data[ sizeof($this->data)-1 ]['cdata'] = '';
#print "cdata = '$cdata'\r\n";
        $this->data[ sizeof($this->data)-1 ]['cdata'].= $cdata;
    }

    /**
    *
    *
    *   @version    2002/01/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     boolean     true on success
    */
    function defaultHandler($parser, $cdata)
    {
#        $this->data[ sizeof($this->data)-1 ]['cdata'] = $cdata;
# not in use yet :-( is that ok??
    }




    /**
    *   read the data from the xml file and prepare them so the tree
    *   class can work with it, the preparation is mainly done in startHandler
    *
    *   @version    2002/01/17
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     boolean     true on success
    */
    function setup()
    {
        $this->parse();

        return $this->data;
    } // end of function

    /**
    *   read the data from an xml string and prepare them so the tree
    *   class can work with it, the preparation is mainly done in startHandler
    *
    *   @version    2002/02/05
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @return     boolean     true on success
    */
    function setupByRawData( $xmlString )
    {
        $this->parseString( $xmlString , true );

        return $this->data;
    }

    /**
    *   TO BE IMPLEMNTED
    *   adds _one_ new element in the tree under the given parent
    *   the values' keys given have to match the db-columns, because the
    *   value gets inserted in the db directly
    *   to add an entire node containing children and so on see 'addNode()'
    *
    *   @see        addNode()
    *   @version    2001/10/09
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array $newValues this array contains the values that shall be inserted in the db-table
    *   @return     mixed   either boolean false on failure or the id of the inserted row
    */
/*    function add( $newValues )
    {
        // add the data in the internal structure $this->data
        $this->data[sizeof($this->data)] = $newValues;

# i am thinking if it might be a good solution to walk the data-array
# and write each line singlely until the one to add comes, write it and
# keep on writing the data-array
# but that means writing the entire file every time any method that
# changes the xml-file's structure the entire file is written,
# can that not be done somehow better ???

#        // and regenerate the xml file
#        $this->_writeFile();

    } // end of function
*/
    /**
    *   TO BE IMPLEMNTED
    *   removes the given node
    *
    *   @version  2001/10/09
    *   @access     public
    *   @author   Wolfram Kriesing <wolfram@kriesing.de>
    *   @param    mixed   $id   the id of the node to be removed
    *   @return   boolean true on success
    */
/*    function remove( $id )
    {
        // remove the data from this->data
        unset($this->data[$id]);

# see comment in "add"-method
    } // end of function
*/
    /**
    *   TO BE IMPLEMNTED
    *   move an entry under a given parent or behind a given entry
    *
    *   @version    2001/10/10
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @param
    *   @param      integer if prevId is given the element with the id idToMove shall be moved _behind_ element with id=prevId
    *                       before would be easier, but then no element could be inserted at the end :-/
    *   @return     boolean     true for success
    */
/*    function move( $idToMove , $newParentId , $prevId=0 )
    {
        $this->data[$idToMove]['parentId'] = $newParentId;
        $this->data[$idToMove]['prevId'] = $prevId;

# see comment in "add"-method
    } // end of function
*/

}
?>