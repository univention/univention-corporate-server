<?php

include_once 'HTTP/WebDAV/Server.php';

/**
 * The Horde_RPC_webdav class provides a WebDAV implementation of the
 * Horde RPC system.
 *
 * $Horde: framework/RPC/RPC/webdav.php,v 1.1 2004/01/24 23:21:08 chuck Exp $
 *
 * Copyright 2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_RPC
 */
class Horde_RPC_webdav extends Horde_RPC {

    /**
     * Resource handler for the WebDAV server.
     * @var object HTTP_WebDAV_Server_Horde $_server
     */
    var $_server;

    /**
     * WebDav server constructor.
     *
     * @access private
     * @return object   An RPC server instance
     */
    function Horde_RPC_xmlrpc()
    {
        parent::Horde_RPC();

        $this->_server = &new HTTP_WebDAV_Server_Horde();
    }

    /**
     * Sends an RPC request to the server and returns the result.
     *
     * @param string    The raw request string.
     *
     * @return string   The XML encoded response from the server.
     */
    function getResponse($request)
    {
        $this->_server->ServeRequest();
        exit;
    }

    /**
     * WebDAV handles authentication internally, so bypass the
     * system-level auth check by just returning true here.
     */
    function authorize()
    {
        return true;
    }

}

/**
 * Horde extension of the base HTTP_WebDAV_Server class.
 *
 * @package Horde_RPC
 */
class HTTP_WebDAV_Server_Horde extends HTTP_WebDAV_Server {

    /**
     * GET implementation.
     *
     * @param array &$params  Array of input and output parameters.
     * <br><b>input</b><ul>
     * <li> path - 
     * </ul>
     * <br><b>output</b><ul>
     * <li> size - 
     * </ul>
     *
     * @return integer  HTTP-Statuscode.
     */
    function GET(&$params)
    {
        return true;
    }

    /**
     * Check authentication. We always return true here since we
     * handle permissions based on the resource that's requested, but
     * we do record the authenticated user for later use.
     *
     * @param string $type      Authentication type, e.g. "basic" or "digest"
     * @param string $username  Transmitted username.
     * @param string $password  Transmitted password.
     *
     * @return boolean  Authentication status. Always true.
     */
    function check_auth($type, $username, $password)
    {
        $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
        $auth->authenticate($username, array('password' => $password));

        return true;
    }

}
