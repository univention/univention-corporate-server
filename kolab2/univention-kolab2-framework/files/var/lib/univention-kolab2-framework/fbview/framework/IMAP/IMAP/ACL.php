<?php
/**
 * Contains functions related to managing
 * Access Control Lists.
 *
 * $Horde: framework/IMAP/IMAP/ACL.php,v 1.2 2004/02/19 00:11:20 jan Exp $
 *
 * Copyright 2003-2004 Chris Hastie <imp@oak-wood.co.uk>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chris Hastie <imp@oak-wood.co.uk>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_ACL {

    /**
     * Hash containing connection parameters.
     *
     * @var array $_params
     */
    var $_params = array();

    /**
     * Boolean indicating if the driver is supported by the server
     *
     * @var boolean $_supported
     */
    var $_supported = false;

    /**
     * Any PEAR_Error that occured but couldn't be returned directly.
     *
     * @var object PEAR_Error $_error
     */
    var $_error = null;

    /**
     * Hash containing the list of possible rights and a human
     * readable description of each
     * 
     * Array (
     *     right-id => right-description   
     * )
     *
     * @var array $_rightsList
     */
    var $_rightsList = array();

    /**
     * Array containing user names that can not have their access
     * rights changed.
     *
     * @var boolean $_protected
     */
    var $_protected;

    /**
     * Constructor.
     *
     * @access public
     *
     * @param optional array $params  Hash containing connection parameters.
     */
    function IMAP_ACL($params = array())
    {
        $this->_params = $params;
    }    

    /**
     * Attempts to retrieve the existing ACL for a folder from 
     * the current IMAP server. If protocol is imap/ssl, will
     * only attempt ssl connection with PHP >= 4.3
     *
     * @access public
     *
     * @param string folder  The folder to get the ACL for
     *
     * @return array  A hash containing information on the ACL
     *                Array (
     *                    user => Array (
     *                                right => 1
     *                            )
     *                )
     */
    function getACL($folder)
    {
        return false;
    }

    /**
     * Sets the ACL on an IMAP server
     *
     * @access public
     *
     * @param string $folder  The folder on which to edit the ACL
     *                           
     * @param string $share_user  The user to grant rights to
     *
     * @param array $acl  An array, the keys of which are the 
     *                    rights to be granted (see RFC 2086)
     *
     * @return mixed  True on success, false on failure unless
     *                server doesn't support ACLs, returns 'no_support'
     */
    function createACL($folder, $share_user, $acl)
    {
        return false;
    }

    /**
     * Edits an ACL on an IMAP server
     *
     * @access public
     *
     * @param string $folder  The folder on which to edit the ACL
     *                           
     * @param string $share_user  The user to grant rights to
     *
     * @param array $acl  An array, the keys of which are the 
     *                    rights to be granted (see RFC 2086)
     *
     * @return mixed  True on success, false on failure unless
     *                server doesn't support ACLs, returns 'no_support'
     */
    function editACL($folder, $share_user, $acl)
    {
        return false;
    }    

    /**
     * Can a user edit the ACL for this folder? Returns true if $user   
     * permission to edit the ACL on $folder
     *
     * @param string $folder  The folder name
     *
     * @param string $user  A user name
     *
     * @returns boolean  True if $user has 'a' right
     */
    function canEdit($folder, $user)
    {
        return true;
    }

    function getRights()
    {
        return $this->_rightsList;
    }

    function getProtected()
    {
        return $this->_protected;
    }

    function isSupported()
    {
        return $this->_supported;
    }

    function getError()
    {
        $error = $this->_error;
        $this->_error = null;
        return $error;
    }

    /**
     * Attempts to return an ACL instance based on $driver.
     *
     * @access public
     *
     * @param string $driver          The type of concrete ACL subclass
     *                                to return.  The is based on the acl
     *                                source ($driver).  The code is
     *                                dynamically included.
     *
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters
     *                                a subclass might need.
     *
     * @return mixed  The newly created concrete ACL instance, or false
     *                on error.
     */
    function &factory($driver, $params = array())
    {
        $driver = basename($driver);
        require_once dirname(__FILE__) . '/ACL/' . $driver . '.php';
        $class = 'IMAP_ACL_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return false;
        }
    }

    /**
     * Attempts to return a reference to a concrete ACL instance
     * based on $driver.  It will only create a new instance if no
     * ACL instance with the same parameters currently exists.
     *
     * This method must be invoked as: $var = &IMAP_ACL::singleton()
     *
     * @access public
     *
     * @param string $driver          The type of concrete ACL subclass
     *                                to return.  The is based on the acl
     *                                source ($driver).  The code is
     *                                dynamically included.
     *
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters
     *                                a subclass might need.
     *
     * @return mixed  The created concrete ACL instance, or false on error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &IMAP_ACL::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
