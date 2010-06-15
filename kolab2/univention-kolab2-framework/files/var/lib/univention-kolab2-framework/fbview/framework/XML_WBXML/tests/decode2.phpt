#!/usr/local/bin/php
<?php
/**
 * $Horde: framework/XML_WBXML/tests/decode2.phpt,v 1.1 2003/12/07 21:19:08 chuck Exp $
 */

include_once 'XML/WBXML/Decoder.php';

$decoder = &new XML_WBXML_Decoder();

$input = fopen('syncml_client_packet_1.wbxml', 'rb');

$decoder->decode($input);

fclose($input);
