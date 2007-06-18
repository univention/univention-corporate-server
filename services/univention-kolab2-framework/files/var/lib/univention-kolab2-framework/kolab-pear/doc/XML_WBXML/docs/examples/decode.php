#!/usr/local/bin/php
<?php
/**
 * $Horde: framework/XML_WBXML/docs/examples/decode.php,v 1.8 2004/03/20 14:07:47 jan Exp $
 *
 * @package XML_WBXML
 */

error_reporting(E_ALL);

// Need to include only the Decoder class for decoding - everything
// else needed will be pulled in for you.
include_once 'XML/WBXML/Decoder.php';

// No options are needed for the decoder object - just instantiate it.
$decoder = &new XML_WBXML_Decoder();

// The decode() method expects a filehandle as input. Open up a wbxml
// file - the example here uses one of the test files included with
// the package. Make sure to open wbxml files in binary mode so that
// your code behaves properly on Windows.
$infile = isset($argv[1]) ? $argv[1] : 'syncml_client_packet_1.wbxml';
$input = fopen($infile, 'rb');
if (!$input) {
    die("Unable to open input file $infile.\n");
}

// Now we just pass the filehandle to the decode() method. It returns
// the decoded XML.
$xml = $decoder->decode($input);
 
// We can close the input handle now if desired.
fclose($input);

// Since this is an example, just print out the XML:
echo $xml;
