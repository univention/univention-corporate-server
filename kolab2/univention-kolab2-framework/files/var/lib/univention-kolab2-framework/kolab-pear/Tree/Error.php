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
//  $Id: Error.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

/**
*
*
*   @author     Wolfram Kriesing <wolfram@kriesing.de>
*   @package    Tree
*/
class Tree_Error extends PEAR_Error
{
    /**
    *   @var  string    prefix for error messages.
    */
    var $error_message_prefix = "Tree Error: ";

    /**
    *
    *
    *   @access     public
    *   @version    2002/03/03
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param
    *   @return
    */
    function Tree_Error( $msg , $line , $file , $mode=null , $userinfo='no userinfo' )
    {
        $this->PEAR_Error(  sprintf("%s <br/>in %s [%d].", $msg, $file, $line),
                            null , $mode , null, $userinfo );
    }

} // end of class
?>