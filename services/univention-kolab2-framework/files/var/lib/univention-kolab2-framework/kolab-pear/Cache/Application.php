<?php
//
// +----------------------------------------------------------------------+
// | PEAR :: Cache                                                        |
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
// | Authors: Richard Heyes <richard@phpguru.org>                         |
// +----------------------------------------------------------------------+
//
// $Id: Application.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $

require_once 'Cache.php';

// Application level variables
//
// Purpose
// Variables that are persisent across all user sessions,
// not just a specific user ala normal sessions.
//
// Usage:
//
// Example 1:
//
// $app  =& new Cache_Application();
// $_APP =& $app->getData();
//
// In this case the $_APP variable is akin to the $_SESSION variable.
// If you add/remove stuff, it will be reflected in the next request
// (of any user).
//
// Example 2:
//
// $foo = 'Some data';
// $bar = 'Some other data';
//
// $app =& new Cache_Application();
// $app->register('foo');
// $app->register('bar', $bar); 
//
// $foo = 'Different data';
//
// In this case the variables are registered with the register() function.
// This is akin to session_register().
//
// As with session_register(), the contents of the variable at the *end* of the
// request is registered and not at the point of registration. Therefore in this
// example, for the $foo variable, the string 'Different data' is stored and not 
// 'Some data'. The exception to this rule is if you use the second argument to
// register() as in the second call to it above. This will cause the data supplied
// in the second argument to be stored and not the contents at the end of the request.
//
// Note: If you use this method with register_globals turned on, the variables will be
//       automatically globalled upon startup, (ie. when you create the object).
//
// Note: If you register a variable that is not set when the script finishes, it will
//       registered as NULL.
//
//
// *** You are strongly recommended to use only one method of the two above. ***
//
// (In fact if you use the register() function with register_globals Off, you have to
//  use the $_APP method to get at the data).

class Cache_Application extends Cache {

    var $data;
    var $id;
    var $group;
    var $registered_vars;

    /**
    * Constructor
    *
    * @param    string  Name of container class
    * @param    array   Array with container class options
    */
    function Cache_Application($container = 'file', $container_options = array('cache_dir' => '/tmp/', 'filename_prefix' => 'cache_'), $id = 'application_var', $group = 'application_cache')
    {
        $this->id    = $id;
        $this->group = $group;
        $this->registered_vars = array();

        $this->Cache($container, $container_options);
        $this->data = $this->isCached($this->id, $this->group) ? unserialize($this->get($this->id, $this->group)) : array();

        // If register_globals on, global all registered variables
        if (ini_get('register_globals') AND is_array($this->data)) {
            foreach ($this->data as $key => $value) {
                global $$key;
                $$key = $value;
            }
        }
    }

    /**
    * Destructor
    *
    * Gets values of all registered variables and stores them. Then calls save() to
    * write data away.
    */
    function _Cache_Application()
    {
        // Get contents of all registered variables
        if (is_array($this->registered_vars) AND !empty($this->registered_vars)) {
            foreach ($this->registered_vars as $varname) {
                global $$varname;
                $this->data[$varname] = $$varname;
            }
        }

        // Save the data
        $this->save($this->id, serialize($this->data), 0, $this->group);
    }

    /**
    * register()
    *
    * Registers a variable to be stored.
    *
    * @param    string  Name of variable to register
    * @param    mixed   Optional data to store
    */
    function register($varname, $data = null)
    {
        if (isset($data)) {
            $this->data[$varname] = $data;
        } else {
            $this->registered_vars[] = $varname;
        }
    }

    /**
    * unregister()
    *
    * Unregisters a variable from being stored.
    *
    * @param    string  Name of variable to unregister
    */
    function unregister($varname)
    {
        if (isset($this->data[$varname])) {
            unset($this->data[$varname]);
        }
    }

    /**
    * clear()
    *
    * Removes all stored data
    */
    function clear()
    {
        $this->data = array();
    }

    /**
    * getData()
    *
    * Use this to get a reference to the data to manipulate
    * in calling script. Eg. $_APP =& $obj->getData();
    *
    * @return mixed   A reference to the data
    */
    function &getData()
    {
        return $this->data;
    }
}
?>