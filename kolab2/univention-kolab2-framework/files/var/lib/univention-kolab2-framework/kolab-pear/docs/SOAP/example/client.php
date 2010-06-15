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
// | Authors: Shane Caraveo <Shane@Caraveo.com>                           |
// +----------------------------------------------------------------------+
//
// $Id: client.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $
//
include("SOAP/Client.php");

/**
 * this client runs against the example server in SOAP/example/server.php
 * it does not use WSDL to run these requests, but that can be changed easily by simply
 * adding '?wsdl' to the end of the url.
 */
$soapclient = new SOAP_Client("http://localhost/SOAP/example/server.php");
// this namespace is the same as declared in server.php
$options = array('namespace' => 'urn:SOAP_Example_Server',
                 'trace' => 1);

$ret = $soapclient->call("echoStringSimple",
                         $params = array("inputStringSimple"=>"this is a test string"),
                         $options);
#print $soapclient->__get_wire();
print_r($ret);echo "<br>\n";

$ret = $soapclient->call("echoString",
                         $params = array("inputString"=>"this is a test string"),
                         $options);
print_r($ret);echo "<br>\n";

$ret = $soapclient->call("divide",
                         $params = array("dividend"=>22,"divisor"=>7),
                         $options);
# print $soapclient->__get_wire();
if (PEAR::isError($ret))
    print("Error: " . $ret->getMessage() . "<br>\n");
else
    print("Quotient is " . $ret . "<br>\n");

$ret = $soapclient->call("divide",
                         $params = array("dividend"=>22,"divisor"=>0),
                         $options);
if (PEAR::isError($ret))
    print("Error: " . $ret->getMessage() . "<br>\n");
else
    print("Quotient is " . $ret . "<br>\n");


// SOAPStruct is defined in the following file
require_once 'example_types.php';

$struct = new SOAPStruct('test string',123,123.123);

/* send an object, get an object back */
/* tell client to translate to classes we provide if possible */
$soapclient->_auto_translation = true;
/* or you can explicitly set the translation for
   a specific class.  auto_translation works for all cases,
   but opens ANY class in the script to be used as a data type,
   and may not be desireable.  both can be used on client or
   server */
$soapclient->__set_type_translation('{http://soapinterop.org/xsd}SOAPStruct','SOAPStruct');
$ret = $soapclient->call("echoStruct",
                         $p = array('inputStruct' => $struct->__to_soap()),
                         $options);
#print $soapclient->__get_wire();
print_r($ret);

/**
 * PHP doesn't support multiple OUT parameters in function calls, so we
 * must do a little work to make it happen here.  This requires knowledge on the
 * developers part to figure out how they want to deal with it.
 */
$ret = $soapclient->call("echoStructAsSimpleTypes",
                         $p = array('inputStruct' => $struct->__to_soap()),
                         $options);
if (PEAR::isError($ret)) {
    print("Error: " . $ret->getMessage() . "<br>\n");
} else {
    list($string, $int, $float) = array_values($ret);
}
echo "varString: $string<br>\nvarInt: $int<br>\nvarFloat: $float<br>\n";

?>