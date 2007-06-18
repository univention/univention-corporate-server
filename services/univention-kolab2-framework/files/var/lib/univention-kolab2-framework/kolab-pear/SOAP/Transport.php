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
// | Authors: Dietrich Ayala <dietrich@ganx4.com> Original Author         |
// +----------------------------------------------------------------------+
//
// $Id: Transport.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
//

require_once 'SOAP/Base.php';

/**
* SOAP Transport Layer
*
* This layer can use different protocols dependant on the endpoint url provided
* no knowlege of the SOAP protocol is available at this level
* no knowlege of the transport protocols is available at this level
*
* @access   public
* @version  $Id: Transport.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
* @package  SOAP::Transport
* @author   Shane Caraveo <shane@php.net>
*/
class SOAP_Transport
{
    function &getTransport($url, $encoding = SOAP_DEFAULT_ENCODING)
    {
        $urlparts = @parse_url($url);
        
        if (!$urlparts['scheme']) {
            return SOAP_Base_Object::_raiseSoapFault("Invalid transport URI: $url");
        }
        
        if (strcasecmp($urlparts['scheme'], 'mailto') == 0) {
            $transport_type = 'SMTP';
        } else if (strcasecmp($urlparts['scheme'], 'https') == 0) {
            $transport_type = 'HTTP';
        } else {
            /* handle other transport types */
            $transport_type = strtoupper($urlparts['scheme']);
        }
        $transport_include = 'SOAP/Transport/'.$transport_type.'.php';
        $res = @include_once($transport_include);
        if(!$res && !in_array($transport_include, get_included_files())) {
            return SOAP_Base_Object::_raiseSoapFault("No Transport for {$urlparts['scheme']}");
        }
        $transport_class = "SOAP_Transport_$transport_type";
        if (!class_exists($transport_class)) {
            return SOAP_Base_Object::_raiseSoapFault("No Transport class $transport_class");
        }
        return new $transport_class($url, $encoding);
    }
} // end SOAP_Transport
?>