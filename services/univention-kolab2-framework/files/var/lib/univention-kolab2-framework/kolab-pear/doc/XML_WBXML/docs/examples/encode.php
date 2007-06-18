#!/usr/local/bin/php
<?php
/**
 * $Horde: framework/XML_WBXML/docs/examples/encode.php,v 1.8 2004/03/20 14:07:47 jan Exp $
 *
 * @package XML_WBXML
 */

// Need to include only the Encoder class for encoding - everything
// else needed will be pulled in for you.
include_once 'XML/WBXML/Encoder.php';

// No options are needed for the encoder object - just instantiate it.
$encoder = &new XML_WBXML_Encoder();

$test_file = 'syncml_client_packet_1.xml';
$fp = fopen('test-' . $test_file . '.wbxml', 'wb');
$encoder->setOutputStream($fp);

$xml = file_get_contents($test_file);
$encoder->encode($xml);

fclose($fp);
