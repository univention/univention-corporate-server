#!/usr/local/bin/php
<?php
/**
 * $Horde: framework/XML_WBXML/tests/encode-decode.phpt,v 1.4 2004/01/31 08:34:39 amills Exp $
 */

include_once 'XML/WBXML/Decoder.php';
include_once 'XML/WBXML/Encoder.php';

//$test_input = '../docs/examples/syncml_client_packet_2.xml';
$test_input = './syncml_client_packet_1.xml';
$test_wbxml = 'test-' . basename($test_input) . '.wbxml';
$test_xml   = 'test-' . basename($test_input) . '.xml';

$xml_in = file_get_contents($test_input);

$encoder = &new XML_WBXML_Encoder();
//$encoder->setVersion($decoder->getVersion());
//$encoder->setCharset($decoder->getCharsetStr());
$wbxml_out = $encoder->encode($xml_in);

$f = fopen($test_wbxml, 'wb');
fwrite($f, $wbxml_out);
fclose($f);

$wbxml_in = $wbxml_out;

$decoder = &new XML_WBXML_Decoder();
$xml_out = $decoder->decode($wbxml_in);

$f = fopen($test_xml, 'wb');
fwrite($f, $xml_out);
fclose($f);

