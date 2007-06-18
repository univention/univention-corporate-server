#!/usr/local/bin/php
<?php
/**
 * $Horde: framework/XML_WBXML/tests/decode-encode.phpt,v 1.1 2003/12/07 21:16:59 chuck Exp $
 */

include_once 'XML/WBXML/Decoder.php';
include_once 'XML/WBXML/Encoder.php';

$test_input = '../docs/examples/syncml_client_packet_1.wbxml';
$test_wbxml = 'test-' . basename($test_input) . '.wbxml';
$test_xml   = 'test-' . basename($test_input) . '.xml';

$wbxml_in = fopen($test_input, 'rb');

$decoder = &new XML_WBXML_Decoder();
$decoder->decode($wbxml_in);

fclose($test_input);


$xml = file_get_contents($test_xml);
$wbxml_out = fopen($test_wbxml, 'wb');

$encoder = &new XML_WBXML_Encoder();
$encoder->setOutputStream($wbxml_out);
$encoder->encode($xml);

fclose($wbxml_out);
