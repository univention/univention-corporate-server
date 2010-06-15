<?php
# i think this class should go somewhere in a common PEAR-place,
# but since it is not very fancy to crowd the PEAR-namespace too much i dont know where to put it yet :-(

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
//  $Id: OptionsDB.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once('Tree/Options.php');

/**
*   this class additionally retreives a DB connection and saves it
*   in the property "dbh"
*
*   @package  Tree
*   @access   public
*   @author   Wolfram Kriesing <wolfram@kriesing.de>
*
*/
class Tree_OptionsDB extends Tree_Options
{
    /**
    *   @var    object
    */
    var $dbh;

    /**
    *   this constructor sets the options, since i normally need this and
    *   in case the constructor doesnt need to do anymore i already have it done :-)
    *
    *   @version    02/01/08
    *   @access     public
    *   @author     Wolfram Kriesing <wolfram@kriesing.de>
    *   @param      boolean true if loggedIn
    */
    function Tree_OptionsDB( $dsn , $options=array() )
    {
        $res = $this->_connectDB( $dsn );
        if( !PEAR::isError($res) )
        {
            $this->dbh->setFetchmode(DB_FETCHMODE_ASSOC);
        }
        else
        {
            return $res;
        }

        $this->Tree_Options( $options );          // do options afterwards since it overrules
    }

    /**
     * Connect to database by using the given DSN string
     *
     * @author  copied from PEAR::Auth, Martin Jansen, slightly modified
     * @access private
     * @param  string DSN string
     * @return mixed  Object on error, otherwise bool
     */
    function _connectDB( $dsn )
    {
        // only include the db if one really wants to connect
        require_once('DB.php');

        if (is_string($dsn) || is_array($dsn) )
        {
            // put the dsn parameters in an array
            // DB would be confused with an additional URL-queries, like ?table=...
            // so we do it before connecting to the DB
            if( is_string($dsn) )
                $dsn = DB::parseDSN( $dsn );

            $this->dbh = DB::Connect($dsn);
        }
        else
        {
            if(get_parent_class($dsn) == "db_common")
            {
                $this->dbh = $dsn;
            }
            else
            {
                if (is_object($dsn) && DB::isError($dsn))
                {
                    return new DB_Error($dsn->code, PEAR_ERROR_DIE);
                }
                else
                {
                    return new PEAR_Error("The given dsn was not valid in file " . __FILE__ . " at line " . __LINE__,
                                41,
                                PEAR_ERROR_RETURN,
                                null,
                                null
                                );

                }
            }
        }

        if (DB::isError($this->dbh))
            return new DB_Error($this->dbh->code, PEAR_ERROR_DIE);

        return true;
    }

} // end of class
?>