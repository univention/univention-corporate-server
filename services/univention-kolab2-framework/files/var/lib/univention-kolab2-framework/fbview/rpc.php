<?php
/**
 * $Horde: horde/rpc.php,v 1.27 2004/04/07 14:43:00 chuck Exp $
 *
 * Copyright 2002-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__));
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/RPC.php';

/* Look at the Content-type of the request, if it is available, to try
 * and determine what kind of request this is. */
$input = null;
$params = null;

if (!empty($_SERVER['CONTENT_TYPE'])) {
    if (strstr($_SERVER['CONTENT_TYPE'], 'application/vnd.syncml+xml')) {
        $serverType = 'syncml';
    } elseif (strstr($_SERVER['CONTENT_TYPE'], 'application/vnd.syncml+wbxml')) {
        $serverType = 'syncml_wbxml';
    } elseif (strstr($_SERVER['CONTENT_TYPE'], 'text/xml')) {
        $input = Horde_RPC::getInput();
        /* Check for SOAP namespace URI. */
        if (strstr($input, 'http://schemas.xmlsoap.org/soap/envelope/')) {
            $serverType = 'soap';
        } else {
            $serverType = 'xmlrpc';
        }
    } else {
        header('HTTP/1.0 501 Not Implemented');
        exit;
    }
} else {
    $serverType = 'soap';
}

if ($serverType == 'soap' &&
    (!isset($_SERVER['REQUEST_METHOD']) ||
     $_SERVER['REQUEST_METHOD'] != 'POST')) {
    if (isset($_GET['wsdl'])) {
        $params = 'wsdl';
    } else {
        $params = 'disco';
    }
}

/* Load the RPC backend based on $serverType. */
$server = &Horde_RPC::singleton($serverType);

/* Let the backend check authentication. By default, we look for HTTP
 * basic authentication against Horde, but backends can override this
 * as needed. */
$server->authorize();

/* Get the server's response. We call $server->getInput() to allow
 * backends to handle input processing differently. */
if ($input === null) {
    $input = $server->getInput();
}
$out = $server->getResponse($input, $params);

/* Return the response to the client. */
header('Content-Type: ' . $server->getResponseContentType());
header('Content-length: ' . strlen($out));
header('Accept-Charset: UTF-8');
echo $out;
