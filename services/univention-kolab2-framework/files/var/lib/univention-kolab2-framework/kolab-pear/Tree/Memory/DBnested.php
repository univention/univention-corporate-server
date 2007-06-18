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

require_once 'Tree/Dynamic/DBnested.php';

/**
*
*
*   @access     public
*   @author
*   @package    Tree
*/
class Tree_Memory_DBnested extends Tree_Dynamic_DBnested
{

    /**
    *   retreive all the data from the db and prepare the data so the structure can
    *   be built in the parent class
    *
    *   @version    2002/04/20
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      array   the result of a query which retreives (all) the tree data from a DB
    *   @return     array   the result
    */
    function setup($res=null)
    {
        if ($res==null) {
            //
            $whereAddOn = '';
            if ($this->options['whereAddOn']) {
                $whereAddOn = 'WHERE '.$this->getOption('whereAddOn');
            }

            //
            $orderBy = 'left';
            if ($order=$this->getOption('order')) {
                $orderBy = $order;
            }

            // build the query this way, that the root, which has no parent (parentId=0) is first
            $query = sprintf(   'SELECT * FROM %s %s ORDER BY %s',
                                $this->table,
                                $whereAddOn,
                                $this->_getColName($orderBy)  // sort by the left-column, so we have the data sorted as it is supposed to be :-)
                                );
            if (DB::isError( $res = $this->dbh->getAll($query))) {
                return $this->_throwError($res->getMessage(),__LINE__);
            }
        }

        return $this->_prepareResults( $res );
    }

}

?>
