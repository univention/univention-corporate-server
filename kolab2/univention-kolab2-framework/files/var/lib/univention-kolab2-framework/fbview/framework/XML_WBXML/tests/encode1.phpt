#!/usr/local/bin/php
<?php
/**
 * $Horde: framework/XML_WBXML/tests/encode1.phpt,v 1.1 2003/12/07 21:19:08 chuck Exp $
 */

include_once 'XML/WBXML/Encoder.php';

$test_file = 'syncml_client_packet_1.xml';

$encoder = &new XML_WBXML_Encoder();

$fp = fopen('test-' . $test_file . '.wbxml', 'wb');
$encoder->setOutputStream($fp);

$xml = file_get_contents($test_file);
$encoder->encode($xml);

fclose($fp);
