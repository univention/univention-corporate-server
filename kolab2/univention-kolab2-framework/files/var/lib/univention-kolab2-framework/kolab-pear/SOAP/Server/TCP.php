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
// | Authors: Shane Caraveo <Shane@Caraveo.com>   Port to PEAR and more   |
// +----------------------------------------------------------------------+
//
// $Id: TCP.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
//

require_once 'SOAP/Server.php';
/**
*  SOAP_Server_TCP
* SOAP Server Class
*
* implements TCP SOAP Server
* http://www.pocketsoap.com/specs/smtpbinding/
*
* class overrides the default HTTP server, providing the ability
* to accept socket connections and execute soap calls.
*
* TODO:
*   use Net_Socket
*   implement some security scheme
*   implement support for attachments
*
* @access   public
* @version  $Id: TCP.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
* @package  SOAP::Server
* @author   Shane Caraveo <shane@php.net> 
*/
class SOAP_Server_TCP extends SOAP_Server {
    var $headers = array();
    var $localaddr;
    var $port;
    var $listen;
    var $reuse;
    
    function SOAP_Server_TCP($localaddr="127.0.0.1", $port=10000, $listen=5, $reuse=TRUE)
    {
        parent::SOAP_Server();
        $this->localaddr = $localaddr;
        $this->port = $port;
        $this->listen = $listen;
        $this->reuse = $reuse;
    }

    function run()
    {
        if (($sock = socket_create (AF_INET, SOCK_STREAM, 0)) < 0) {
            return $this->_raiseSoapFault("socket_create() failed: reason: " . socket_strerror ($sock));
        }
        if ($this->reuse &&
            !@socket_setopt($sock,SOL_SOCKET,SO_REUSEADDR,1)) {
            return $this->_raiseSoapFault("socket_setopt() failed: reason: ".socket_strerror(socket_last_error($sock)));
        }        
        if (($ret = socket_bind ($sock, $this->localaddr, $this->port)) < 0) {
            return $this->_raiseSoapFault("socket_bind() failed: reason: " . socket_strerror ($ret));
        }
        # print "LISTENING on {$this->localaddr}:{$this->port}\n";
        if (($ret = socket_listen ($sock, $this->listen)) < 0) {
            return $this->_raiseSoapFault("socket_listen() failed: reason: " . socket_strerror ($ret));
        }
        
        do {
            $data = NULL;
            if (($msgsock = socket_accept($sock)) < 0) {
                $this->_raiseSoapFault("socket_accept() failed: reason: " . socket_strerror ($msgsock));
                break;
            }
            # print "Accepted connection\n";
            while ($buf = socket_read ($msgsock, 8192)) {
                if (!$buf = trim($buf)) {
                    continue;
                }
                $data .= $buf;
            }
            
            if ($data) {
                $response = $this->service($data);
                # write to the socket
                if (!socket_write($msgsock, $response, strlen($response))) {
                    return $this->_raiseSoapFault('Error sending response data reason '.socket_strerror());
                }
            }
            
            socket_close ($msgsock);
        } while (true);
        
        socket_close ($sock);
    }
    
    function service(&$data)
    {
        # XXX we need to handle attachments somehow
        return $this->parseRequest($data,$attachments);
    }    
}

?>