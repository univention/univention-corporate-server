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
// | Authors: Ulf Wendel <ulf.wendel@phpdoc.de>                           |
// |          Christian Stocker <chregu@phant.ch>                         |
// |          Vinai Kopp <kopp@netzarbeiter.de>                           |
// +----------------------------------------------------------------------+
//
// $Id: Output.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $

require_once 'Cache.php';

/**
* Class to cache the output of a script using the output buffering functions
*
* Simple output cache. Some pages require lots of time to compute. Caching the
* output can increase the overall speed dramatically, especially if you use
* a Shared Memory storage container.
*
* As you can see in the example the usage is extemely simple. To cache a script
* simple put some few lines of code in front of your script and some at the end.
* A preferrable place for this are the auto_prepend and auto_append files (=> php.ini).
*
* Usage example:
*
*  // place this somewhere in a central config file
*  define(CACHE_STORAGE_CLASS, 'file');
*  // file storage needs a dir to put the cache files
*  define(CACHE_DIR, '/var/tmp/');
*
*  // get a cache object
*  $cache = new Cache_Output(CACHE_STORAGE_CLASS, array('cache_dir' => CACHE_DIR));
*
*  // compute the unique handle.
*  // if your script depends on Cookie and HTTP Post data as well
*  // you should use:
*  // $cache_handle = array(
*  //                       'file' => $REQUEST_URI,
*  //                       'post' => $HTTP_POST_VARS,
*  //                       'cookie'  => $HTTP_COOKIE_VARS
*  //                    );
*  // But be warned, using all GET or POST Variables as a seed
*  // can be used for a DOS attack. Calling http://www.example.com/example.php?whatever
*  // where whatever is a random text might be used to flood your cache.
*  $cache_handle = $cache->generateID($REQUEST_URI);
*
*  // now the magic happens: if cached call die()
*  // to end the time consumptiong script script execution and use the cached value!
*  if ($content = $cache->start($cache_handle)) {
*     print $content;
*     print '<p>Cache hit</p>';
*     die();
*  }
*
*  // time consumption script goes here.
*
*  // store the output of the cache into the cache and print the output.
*  print $cache->end();
*  print "<p>Cache miss, stored using the ID '$id'.</p>";
*
*  If you do not want to cache a whole page - no problem:
*
*  if (!($content = $cache->start($cache_handle))) {
*     // do the computation here
*     print $cache->end()
*  } else {
*     print $content;
*  }
*
*  If you need an example script check the (auto_)prepend and (auto_)append
*  files of my homepage:
*
*    http://www.ulf-wendel.de/php/show_source.php?file=prepend
*    http://www.ulf-wendel.de/php/show_source.php?file=append
*
*  Don't know how to use it or you need profiling informations?`
*  Ask Christian he was patient with me and he'll be so with your questions ;).
*
*  Have fun!
*
* @authors  Ulf Wendel <ulf.wendel@phpdoc.de>
* @version  $ID: $
* @package  Cache
* @access   public
*/
class Cache_Output extends Cache {

    /**
    * ID passed to start()
    *
    * @var  string
    * @see  start(), end()
    */
    var $output_id = '';

    /**
    * Group passed to start()
    *
    * @var  string
    * @see  start(), end()
    */
    var $output_group = '';

    /**
    * PEAR-Deconstructor
    * Call deconstructor of parent
    */
    function _Cache_Output()
    {
                $this->_Cache();
    }

    /**
    * starts the output buffering and returns an empty string or returns the cached output from the cache.
    *
    * @param    string  dataset ID
    * @param    string  cache group
    * @return   string
    * @access   public
    */
    function start($id, $group = 'default') {
        if (!$this->caching)
            return '';

        // this is already cached return it from the cache so that the user
        // can use the cache content and stop script execution
        if ($content = $this->get($id, $group))
            return $content;

        // remember some data to be able to fill the cache on calling end()
        $this->output_id = $id;
        $this->output_group = $group;

        // WARNING: we need the output buffer - possible clashes
        ob_start();
        ob_implicit_flush(false);

        return '';
    } // end func start

    /*
    * Stores the content of the output buffer into the cache and returns the content.
    *
    * @param    mixed   lifetime of the cached data in seconds - 0 for endless. More formats available. see Container::getExpiresAbsolute()
    * @param    string  additional userdefined data
    * @return   string  cached output
    * @access   public
    * @see      endPrint(), endGet(), Container::getExpiresAbsolute()
    */
    function end($expire = 0, $userdata = '') {
        $content = ob_get_contents();
        ob_end_clean();

        // store in the cache
        if ($this->caching)
            $this->container->save($this->output_id, $content, $expire, $this->output_group, $userdata);

        return $content;
    } // end func end()

    /**
    * Stores the content of the output buffer into the cache and prints the content.
    *
    * @brother  end()
    */
    function endPrint($expire = 0, $userdata = '') {
        $this->printContent($this->end($expire, $userdata));
    } // end func endPrint

    /**
    * Sends the data to the user.
    * This is for compatibility with OutputCompression
    * 
    * @param    string
    * @access   public
    */    
    function printContent($content = '') {
        if ('' == $content)
            $content = &$this->container->cachedata;
            
        print $content;
    }
    /**
    * Returns the content of the output buffer but does not store it into the cache.
    *
    * Use this method if the content of your script is markup (XML)
    * that has to be parsed/converted (XSLT) before you can output
    * and store it into the cache using save().
    *
    * @return   string
    * @access   public
    * @see      endPrint(), end()
    */
    function endGet() {
        $content = ob_get_contents();
        ob_end_clean();

        $this->output_id = '';
        $this->output_group = '';

        return $content;
    } // end func endGet
} // end class output
?>
