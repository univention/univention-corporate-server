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
// $Id: Email_Gateway.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
//

require_once 'SOAP/Server/Email.php';
require_once 'SOAP/Transport.php';

/**
*  SOAP_Server_Email
* SOAP Server Class
*
* implements Email SOAP Server
* http://www.pocketsoap.com/specs/smtpbinding/
*
* class overrides the default HTTP server, providing the ability
* to parse an email message and execute soap calls.
* this class DOES NOT pop the message, the message, complete
* with headers, must be passed in as a parameter to the service
* function call
*
* This class calls a provided HTTP SOAP server, forwarding
* the email request, then sending the HTTP response out as an
* email
*
* @access   public
* @version  $Id: Email_Gateway.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
* @package  SOAP::Server
* @author   Shane Caraveo <shane@php.net> 
*/
class SOAP_Server_Email_Gateway extends SOAP_Server_Email
{
    var $gateway = NULL;
    var $dump = FALSE;
    
    function SOAP_Server_Email_Gateway($gateway = '', $send_response = TRUE, $dump=FALSE)
    {
        parent::SOAP_Server();
        $this->send_response = $send_response;
        $this->gateway = $gateway;
        $this->dump = $dump;
    }
    
    function service(&$data, $gateway='', $endpoint = '', $send_response = TRUE, $dump = FALSE)
    {
        $this->endpoint = $endpoint;
        $response = '';
        $useEncoding='Mime';
        $options = array();
        if (!$gateway) $gateway = $this->gateway;
        
        // we have a full set of headers, need to find the first blank line
        $this->_parseEmail($data);
        if ($this->fault) {
            $response = $this->fault->message();
        }
        if ($this->headers['content-type']=='application/dime')
            $useEncoding='DIME';
        
        # call the HTTP Server
        if (!$response) {
            $soap_transport =& SOAP_Transport::getTransport($gateway, $this->xml_encoding);
            if ($soap_transport->fault) {
                $response = $soap_transport->fault->message();
            }
        }
        
        // send the message
        if (!$response) {
            $options['soapaction'] = $this->headers['soapaction'];
            $options['headers']['Content-Type'] = $this->headers['content-type'];
            
            $response = $soap_transport->send($data, $options);
            if (isset($this->headers['mime-version']))
                $options['headers']['MIME-Version'] = $this->headers['mime-version'];
            
            if ($soap_transport->fault) {
                $response = $soap_transport->fault->message();
            } else {
                foreach ($soap_transport->transport->attachments as $cid=>$body) {
                    $this->attachments[] = array('body' => $body, 'cid' => $cid, 'encoding' => 'base64');
                }
                if (count($this->__attachments)) {
                    if ($useEncoding == 'Mime') {
                        $soap_msg = $this->_makeMimeMessage($response);
                        $options['headers']['MIME-Version'] = '1.0';
                    } else {
                        // default is dime
                        $soap_msg = $this->_makeDIMEMessage($response);
                        $options['headers']['Content-Type'] = 'application/dime';
                    }
                    if (PEAR::isError($soap_msg)) {
                        return $this->_raiseSoapFault($soap_msg);
                    }
                    if (is_array($soap_msg)) {
                        $response = $soap_msg['body'];
                        if (count($soap_msg['headers'])) {
                            if (isset($options['headers'])) {
                                $options['headers'] = array_merge($options['headers'],$soap_msg['headers']);
                            } else {
                                $options['headers'] = $soap_msg['headers'];
                            }
                        }
                    }
                }
            }
        }
        
        if ($this->send_response) {        
            if ($this->dump || $dump) {
                print $response;
            } else {
                $from = array_key_exists('reply-to',$this->headers) ? $this->headers['reply-to']:$this->headers['from'];
                # XXX what if no from?????
                
                $soap_transport =& SOAP_Transport::getTransport('mailto:'.$from, $this->response_encoding);
                $from = $this->endpoint ? $this->endpoint : $this->headers['to'];
                $headers = array('In-Reply-To'=>$this->headers['message-id']);
                $options = array('from' => $from, 'subject'=> $this->headers['subject'], 'headers' => $headers);
                $soap_transport->send($response, $options);
            }
        }
    }    
}

?>