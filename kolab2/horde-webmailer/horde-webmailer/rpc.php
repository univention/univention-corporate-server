<?php
/**
 * RPC processing script.
 *
 * Possible GET values:
 *
 *   'requestMissingAuthorization' -- Whether or not to request
 *   authentication credentials if they are not already present.
 *
 *   'wsdl' -- TODO
 *
 * $Horde: horde/rpc.php,v 1.30.10.12 2009-06-16 15:30:42 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

define('AUTH_HANDLER', true);
define('HORDE_BASE', dirname(__FILE__));
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/RPC.php';

$input = null;
$params = array();

/* Look at the Content-type of the request, if it is available, to try
 * and determine what kind of request this is. */
if (!empty($_SERVER['PATH_INFO']) ||
    in_array($_SERVER['REQUEST_METHOD'], array('DELETE', 'PROPFIND', 'PUT', 'OPTIONS'))) {
    $serverType = 'webdav';
} elseif (!empty($_SERVER['CONTENT_TYPE'])) {
    if (strpos($_SERVER['CONTENT_TYPE'], 'application/vnd.syncml+xml') !== false) {
        $serverType = 'syncml';
        /* Syncml does its own session handling. */
        $session_control = 'none';
        $no_compress = true;
    } elseif (strpos($_SERVER['CONTENT_TYPE'], 'application/vnd.syncml+wbxml') !== false) {
        $serverType = 'syncml_wbxml';
        /* Syncml does its own session handling. */
        $session_control = 'none';
        $no_compress = true;
    } elseif (strpos($_SERVER['CONTENT_TYPE'], 'text/xml') !== false) {
        $input = Horde_RPC::getInput();
        /* Check for SOAP namespace URI. */
        if (strpos($input, 'http://schemas.xmlsoap.org/soap/envelope/') !== false) {
            $serverType = 'soap';
        } else {
            $serverType = 'xmlrpc';
        }
    } elseif (strpos($_SERVER['CONTENT_TYPE'], 'application/json') !== false) {
        $serverType = 'jsonrpc';
    } else {
        header('HTTP/1.0 501 Not Implemented');
        exit;
    }
} elseif (!empty($_SERVER['QUERY_STRING']) && $_SERVER['QUERY_STRING'] == 'phpgw') {
    $serverType = 'phpgw';
} else {
    $serverType = 'soap';
}

if ($serverType == 'soap') {
    if (!isset($_SERVER['REQUEST_METHOD']) ||
        $_SERVER['REQUEST_METHOD'] != 'POST') {
        $session_control = 'none';
        $params['requireAuthorization'] = false;
        if (Util::getGet('wsdl') !== null) {
            $input = 'wsdl';
        } else {
            $input = 'disco';
        }
    } elseif (class_exists('SoapServer')) {
        $serverType = 'PhpSoap';
    }
}

/* Check to see if we want to exit if required credentials are not
 * present. */
if (($ra = Util::getGet('requestMissingAuthorization')) !== null) {
    $params['requestMissingAuthorization'] = $ra;
}

/* Load base libraries. */
require_once HORDE_BASE . '/lib/base.php';

/* Load the RPC backend based on $serverType. */
$server = Horde_RPC::factory($serverType, $params);

/* Let the backend check authentication. By default, we look for HTTP
 * basic authentication against Horde, but backends can override this
 * as needed. */
$server->authorize();

/* Get the server's response. We call $server->getInput() to allow
 * backends to handle input processing differently. */
if ($input === null) {
    $input = $server->getInput();
}

$out = $server->getResponse($input);
if (is_a($out, 'PEAR_Error')) {
    header('HTTP/1.0 500 Internal Server Error');
    echo $out->getMessage();
    exit;
}

/* Return the response to the client. */
header('Content-Type: ' . $server->getResponseContentType());
header('Content-length: ' . strlen($out));
header('Accept-Charset: UTF-8');
echo $out;
