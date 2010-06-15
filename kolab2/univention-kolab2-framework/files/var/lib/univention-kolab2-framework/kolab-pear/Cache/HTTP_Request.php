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
// | Authors: Fabien MARTY <fabien.marty@free.fr> |
// +----------------------------------------------------------------------+
//
// $Id: HTTP_Request.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $

require_once 'Cache.php';
require_once 'HTTP/Request.php';

define('CACHE_HTTP_REQUEST_GROUP_NAME', 'cache_http_request');
define('CACHE_HTTP_REQUEST_SUCCESS_RESPONSE_CODE', 200);
define('CACHE_HTTP_REQUEST_KEEP_LOCAL_COPY', 1);
define('CACHE_HTTP_REQUEST_RETURN_FALSE', 2);
define('CACHE_HTTP_REQUEST_RETURN_PEAR_ERROR', 3);

/**
* HTTP_Request Cache
*
* The classical example is :
*
* You want to get news from another site through RSS remote files. But you
* don't want to access to to the remote site at every time you display
* its news on your site. Because, if the remote site is down or slow...
* So you you need a class which makes a local cache copy of the remote file.
* Every x hours, the cache is updated. But if the remote site is down, the
* local cache copy is keeped (you can also get error messages if you want).
*
* So you need this class!
*
* Cache_HTTP_Request inherits from Cache and use HTTP_Request to access to
* the remote file.
*
* Usage example :
*
* <?php
* require_once('Cache/HTTP_Request.php');
*
* $cache = &new Cache_HTTP_Request('http://www.php.net', NULL, 'file', NULL, 3600);
* $cache->sendRequest();
* $remoteFileBody = $cache->getResponseBody();
*
* (...)
* ?>
*
* @author   Fabien MARTY <fabien.marty@free.fr>
* @version  $Id: HTTP_Request.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $
* @package  Cache
*/

class Cache_HTTP_Request extends Cache
{

    // --- Private properties ---

    /**
    * Lifetime in seconds (0 endless)
    *
    * @var int $_expires
    */
    var $_expires;

    /**
    * HTTP Request
    *
    * @var object $_request
    */
    var $_request;

    /**
    * Cache id for the classic cache file
    *
    * @see sendRequest()
    * @var string $_id
    */
    var $_id;

    /**
    * Cache id for the endless cache file
    *
    * @see sendRequest()
    * @var string $_id
    */
    var $_id2;

    /**
    * Data to use
    *
    * @see getReponseBody(), getReponseHeader(), getReponseCode()
    * @var array $_data
    */
    var $_data ;

    // --- Public methods ---

    /**
    * Constructor
    *
    * @param $url The url to access
    * @param $params Associative array of parameters which can be:
    *                  method     - Method to use, GET, POST etc
    *                  http       - HTTP Version to use, 1.0 or 1.1
    *                  user       - Basic Auth username
    *                  pass       - Basic Auth password
    *                  proxy_host - Proxy server host
    *                  proxy_port - Proxy server port
    *                  proxy_user - Proxy auth username
    *                  proxy_pass - Proxy auth password
    * @param string $container Name of container class
    * @param array $containerOptions Array with container class options
    * @param int $mode What to do when the remote server is down :
    *                   CACHE_HTTP_REQUEST_KEEP_LOCAL_COPY or
    *                   CACHE_HTTP_REQUEST_RETURN_FALSE or
    *                   CACHE_HTTP_REQUEST_RETURN_PEAR_ERROR
    * @param int $expires lifetime of the cached data in seconds - 0 for endless
    * @see Cache, HTTP_Request
    * @access public
    */
    function Cache_HTTP_Request($url, $params = NULL, $container  = 'file',
                                $containerOptions = NULL, $expires = 3600,
                                $mode = CACHE_HTTP_REQUEST_KEEP_LOCAL_COPY)
    {
        if (!isset($params)) $params = array();
        if (!isset($containerOptions)) {
            $containerOptions = array (
                'cache_dir' => '/tmp/',
                'filename_prefix' => 'cache_'
            );
        }
        $this->Cache($container, $containerOptions);
        $this->_request = &new HTTP_Request($url, $params);
        $this->_id = md5($url.serialize($params));
        $this->_id2 = md5($this->id); // we need two keys
        $this->_mode = $mode;
        $this->_expires = $expires;
    }

    /**
    * Deconstructor
    *
    * @access public
    */
    function _Cache_HTTP_Request()
    {
        $this->_Cache();
    }

    /**
    * Get and return the response body (NULL if no data available)
    *
    * @see sendRequest()
    * @return mixed response body
    * @access public
    */
    function getResponseBody()
    {
        return $this->_data['body'];
    }

    /**
    * Get and return the response code (NULL if no data available)
    *
    * @see sendRequest()
    * @return mixed response code
    * @access public
    */
    function getResponseCode()
    {
        return $this->_data['code'];
    }

    /**
    * Get and return the response header (NULL if no data available)
    *
    * @see sendRequest()
    * @return mixed response header
    * @access public
    */
    function getResponseHeader()
    {
        return $this->_data['header'];
    }


    /**
    * Set a new mode when the server is down
    *
    * @param int $newMode What to do when the remote server is down :
    *                      CACHE_HTTP_REQUEST_KEEP_LOCAL_COPY or
    *                      CACHE_HTTP_REQUEST_RETURN_FALSE or
    *                      CACHE_HTTP_REQUEST_RETURN_PEAR_ERROR
    * @access public
    */
    function setMode($newMode)
    {
        $this->_mode = $newMode;
    }

    /**
    * Send the HTTP request or use the cache system
    *
    * If there is a cache file for this HTTP request, the request is not re-sent.
    * Cached response is used. Yet, if the cache is expired, the HTTP request
    * is re-sent. Then, if the remote server is down, this method will return :
    * (depending on the selected mode)
    * - false or
    * - a PEAR_Error or (better)
    * - true and the local copy of the latest valid response will be used.
    *
    * (technical)
    * For the last choice, there is a technical tips.
    * Indeed, there are two cache files. The first one (id key) is a classical one
    * with the given lifetime. But it can be removed by automatic garbage collection
    * for example. So to be able to use the latest valid response (when the remote
    * server is dead), we make a second cache file with no lifetime (id2 key).
    *
    * @return mixed true or false or a PEAR_ERROR
    * @access public
    */
    function sendRequest()
    {
        if ($data = $this->get($this->_id, CACHE_HTTP_REQUEST_GROUP_NAME)) {
            // --- Cache hit ---
            $this->_data = $data;
            return true;
        } else {
            // --- Cache miss ---
            if ($this->_sendRequestAndGetResponse()) {
                // So the remote server is ok...
                $this->save($this->_id, $this->_data, $this->_expires, CACHE_HTTP_REQUEST_GROUP_NAME);
                $this->save($this->_id2, $this->_data, 0, CACHE_HTTP_REQUEST_GROUP_NAME);
                return true;
            } else {
                if ($data_sav = $this->get($this->_id2, CACHE_HTTP_REQUEST_GROUP_NAME)) {
                    // Ok, the "recover cache" is available...
                    switch ($this->_mode) {
                    case CACHE_HTTP_REQUEST_KEEP_LOCAL_COPY:
                        // We make a new local copy and keep it until it expires...
                        $this->save($this->_id, $data_sav, $this->_expires, CACHE_HTTP_REQUEST_GROUP_NAME);
                        $this->_data = $data_sav;
                        return true;
                        break;
                    case CACHE_HTTP_REQUEST_RETURN_FALSE:
                        // We return false
                        return false;
                        break;
                    case CACHE_HTTP_REQUEST_RETURN_PEAR_ERROR:
                        // We return a PEAR_Error!
                        return new Cache_Error('Remote file is not available!');
                        break;
                    }
                } else {
                    // It's terrible! The remote server is down and definitively no cache available!
                    return new Cache_Error('Remote server down and no cache available!');
                }
            }
        }
    }

    // --- Private Methods ---

    /**
    * Send HTTP request and get the response
    *
    * @return boolean success or not ?
    * @see HTTP_Request
    * @access private
    */
    function _sendRequestAndGetResponse()
    {
        $this->_request->sendRequest();
        $body = $this->_request->getResponseBody();
        $code = $this->_request->getResponseCode();
        $header = $this->_request->getResponseHeader();
        $this->_data = array(
            'body' => $body,
            'code' => $code,
            'header' => $header
        );
        return (($code==CACHE_HTTP_REQUEST_SUCCESS_RESPONSE_CODE) ? true : false);
    }

}
?>
