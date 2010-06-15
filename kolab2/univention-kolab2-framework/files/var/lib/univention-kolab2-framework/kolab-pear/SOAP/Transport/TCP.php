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
// | Authors: Shane Hanna <iordy_at_iordy_dot_com>                        |
// +----------------------------------------------------------------------+
//
// $Id: TCP.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
//

require_once 'SOAP/Base.php';

/**
*  TCP Transport for SOAP
*
* TODO:
*   use Net_Socket
*   implement some security scheme
*   implement support for attachments
*
*
* @access public
* @package SOAP::Transport::TCP
* @author Shane Hanna <iordy_at_iordy_dot_com>
*/
class SOAP_Transport_TCP extends SOAP_Base_Object
{

    var $headers = array();
    var $urlparts = NULL;
    var $url = '';
    var $incoming_payload = '';
    var $_userAgent = SOAP_LIBRARY_NAME;
    var $encoding = SOAP_DEFAULT_ENCODING;
    var $result_encoding = 'UTF-8';
    var $result_content_type;

    # socket
    var $socket = '';

    /**
    * SOAP_Transport_TCP Constructor
    *
    * @param string $URL    http url to soap endpoint
    *
    * @access public
    */
    function SOAP_Transport_TCP($URL, $encoding = SOAP_DEFAULT_ENCODING)
    {
        parent::SOAP_Base_Object('TCP');
        $this->urlparts = @parse_url($URL);
        $this->url = $URL;
        $this->encoding = $encoding;
    }

    function _socket_ping () {
        // XXX how do we restart after socket_shutdown?
        //if (!$this->socket) {
            # create socket resource
            $this->socket = @socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
            if ($this->socket < 0) return 0;

            # connect
            $result = socket_connect($this->socket, $this->urlparts['host'], $this->urlparts['port']);
            if ($result < 0) return 0;
        //}
        return 1;
    }

    /**
    * send and receive soap data
    *
    * @param string &$msg       outgoing post data
    * @param string $action      SOAP Action header data
    *
    * @return string|fault response
    * @access public
    */
    function &send(&$msg, $options = NULL)
    {
        $this->incoming_payload = '';
        $this->outgoing_payload = &$msg;
        if (!$this->_validateUrl()) return $this->fault;

        # check for TCP scheme
        if (strcasecmp($this->urlparts['scheme'], 'TCP') == 0) {
            # check connection
            if (!$this->_socket_ping())
                return $this->_raiseSoapFault('error on '.$this->url.' reason '.socket_strerror(socket_last_error($this->socket)));

            # write to the socket
            if (!@socket_write($this->socket, $this->outgoing_payload, strlen($this->outgoing_payload))) {
                return $this->_raiseSoapFault('Error sending data to '.$this->url.' reason '.socket_strerror(socket_last_error($this->socket)));
            }

            # shutdown writing
            if(!socket_shutdown($this->socket, 1))
                return $this->_raiseSoapFault("can't change socket mode to read.");

            # read everything we can.
            while($buf = @socket_read($this->socket, 1024, PHP_BINARY_READ)) {
                $this->incoming_payload .= $buf;
            }

            # return payload or die
            if ($this->incoming_payload)
                return $this->incoming_payload;
            
            return $this->_raiseSoapFault("Error reveiving data from ".$this->url);
        }
        return $this->_raiseSoapFault('Invalid url scheme '.$this->url);
    }

    // private members

    /**
    * validate url data passed to constructor
    *
    * @return boolean
    * @access private
    */
    function _validateUrl()
    {
        if ( ! is_array($this->urlparts) ) {
            $this->_raiseSoapFault("Unable to parse URL $url");
            return FALSE;
        }
        if (!isset($this->urlparts['host'])) {
            $this->_raiseSoapFault("No host in URL $url");
            return FALSE;
        }
        if (!isset($this->urlparts['path']) || !$this->urlparts['path'])
            $this->urlparts['path'] = '/';
        return TRUE;
    }

}
?>