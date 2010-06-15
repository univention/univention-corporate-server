<?php
// +----------------------------------------------------------------------+
// | PEAR :: Cache                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.0 of the PHP license,       |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Sebastian Bergmann <sb@sebastian-bergmann.de>               |
// +----------------------------------------------------------------------+
//
// $Id: Function.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $

require_once 'Cache.php';

/**
* Function_Cache
*
* Purpose:
*
*   Caching the result and output of functions.
*
* Example:
*
*   require_once 'Cache/Function.php';
*
*   class foo {
*     function bar($test) {
*       echo "foo::bar($test)<br>";
*     }
*   }
*
*   class bar {
*     function foobar($object) {
*       echo '$'.$object.'->foobar('.$object.')<br>';
*     }
*   }
*
*   $bar = new bar;
*
*   function foobar() {
*     echo 'foobar()';
*   }
*
*   $cache = new Cache_Function();
*
*   $cache->call('foo::bar', 'test');
*   $cache->call('bar->foobar', 'bar');
*   $cache->call('foobar');
*
* Note:
* 
*   You cannot cache every function. You should only cache 
*   functions that only depend on their arguments and don't use
*   global or static variables, don't rely on database queries or 
*   files, and so on.
* 
* @author       Sebastian Bergmann <sb@sebastian-bergmann.de>
* @module       Function_Cache
* @modulegroup  Function_Cache
* @package      Cache
* @version      $Revision: 1.1.2.1 $
* @access       public
*/
class Cache_Function extends Cache {
    var $expires;

    /**
    * Constructor
    *
    * @param    string  Name of container class
    * @param    array   Array with container class options
    * @param    integer Number of seconds for which to cache
    */
    function Cache_Function($container  = 'file',
                            $container_options = array('cache_dir'       => '.',
                                                       'filename_prefix' => 'cache_'
                                                      ),
                            $expires = 3600
                           )
    {
      $this->Cache($container, $container_options);
      $this->expires = $expires;      
    }

    /**
    * PEAR-Deconstructor
    * Call deconstructor of parent
    */
    function _Cache_Function() {
        $this->_Cache();
    }

    /**
    * Calls a cacheable function or method.
    *
    * @return mixed $result
    * @access public
    */
    function call() {
        // get arguments
        $arguments = func_get_args();

        // generate cache id
        $id = md5(serialize($arguments));

        // query cache
        $cached_object = $this->get($id, 'function_cache');

        if ($cached_object != NULL) {
            // cache hit: return cached output and result

            $output = $cached_object[0];
            $result = $cached_object[1];

        } else {
            // cache miss: call function, store output and result in cache

            ob_start();
            $target = array_shift($arguments);

            // classname::staticMethod
            if (strstr($target, '::')) {
                list($class, $method) = explode('::', $target);

                $result = call_user_func_array(array($class, $method), $arguments);
            }

            // object->method
            elseif (strstr($target, '->')) {
                list($object, $method) = explode('->', $target);
                global $$object;

                $result = call_user_func_array(array($$object, $method), $arguments);
            }

            // function
            else {
                $result = call_user_func_array($target, $arguments);
            }

            $output = ob_get_contents();
            ob_end_clean();

            $this->save($id, array($output, $result), $this->expires, 'function_cache');
        }

        echo $output;
        return $result;
    }
}
?>
