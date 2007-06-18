<?php

include_once 'XML/WBXML.php';
include_once 'XML/WBXML/ContentHandler.php';
include_once 'XML/WBXML/DTDManager.php';
include_once 'Horde/String.php';

/**
 * $Horde: framework/XML_WBXML/WBXML/Encoder.php,v 1.22 2004/04/07 17:43:43 chuck Exp $
 *
 * Copyright 2003-2004 Anthony Mills <amills@pyramid6.com>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * From Binary XML Content Format Specification Version 1.3, 25 July
 * 2001 found at http://www.wapforum.org
 *
 * @package XML_WBXML
 */
class XML_WBXML_Encoder extends XML_WBXML_ContentHandler {

    var $_strings = array();

    var $_stringTable;

    var $_hasWrittenHeader = false;

    var $_dtd;

    var $_output;

    var $_uris = array();

    var $_uriNums = array();

    var $_currentURI;

    var $_subParser;
    var $_subParserStack;

    /**
     * These will store the startElement params to see if we should
     * call startElementImp or startEndElementImp.
     */
    var $_storeURI;
    var $_storeName;
    var $_storeAttributes;

    /**
     * The XML parser.
     * @var resource $_parser
     */
    var $_parser;

    /**
     * The DTD Manager.
     * @var object XML_WBXML_DTDManager $dtdManager
     */
    var $_dtdManager;

    var $_indent = 0;

    /**
     * Use wbxml2xml from libwbxml.
     * @var String
     */
    var $_xml2wbxml = '/usr/bin/xml2wbxml -n -v 1.2 -o ';

    /**
     * Constructor.
     */
    function XML_WBXML_Encoder()
    {
        $this->_stringTable = &new XML_WBXML_HashTable();
        $this->_dtdManager = &new XML_WBXML_DTDManager();
        $this->_hasWrittenHeader = false;

        $this->_subParser = null;
        $this->_subParserStack = 0;

        $this->_output = '';
    }

    /**
     * Take the input $xml and turn it into WBXML, which gets sent to
     * $this->_output.
     */
    function encode($xml)
    {
        if (isset($this->_xml2wbxml)) {
            $tmp_id = mt_rand();
            $tmp_file = '/tmp/wbxml_encoder_' . $tmp_id;

            $fp = fopen($tmp_file . '.xml', 'wb');
            fwrite($fp, $xml);
            fclose($fp);

            exec($this->_xml2wbxml . $tmp_file . '.wbxml ' . $tmp_file . '.xml');

            $ret = file_get_contents($tmp_file . '.wbxml');
            unlink($tmp_file . '.wbxml');
            unlink($tmp_file . '.xml');
            return $ret;
        } else {
            // Create the XML parser and set method references.
            $this->_parser = xml_parser_create_ns($this->_charset);
            xml_set_object($this->_parser, $this);
            xml_parser_set_option($this->_parser, XML_OPTION_CASE_FOLDING, false);
            xml_set_element_handler($this->_parser, '_startElement', '_endElement');
            xml_set_character_data_handler($this->_parser, '_characters');
            xml_set_default_handler($this->_parser, 'defaultHandler');
            xml_set_processing_instruction_handler($this->_parser, '');
            xml_set_external_entity_ref_handler($this->_parser, '');

            if (!xml_parse($this->_parser, $xml)) {
                return $this->raiseError(sprintf('XML error: %s at line %d',
                                                 xml_error_string(xml_get_error_code($this->_parser)),
                                                 xml_get_current_line_number($this->_parser)));
            }

            xml_parser_free($this->_parser);

            return $this->_output;
        }
    }

    /**
     * This will write the correct headers.
     */
    function writeHeader($uri)
    {
        $this->_dtd = &$this->_dtdManager->getInstanceURI($uri);

        $dpiString = $this->_dtd->getDPI();

        // Set Version Number from Section 5.4
        // version = u_int8
        // currently 1, 2 or 3
        $this->writeVersionNumber($this->_wbxmlVersion);

        // Set Document Public Idetifier from Section 5.5
        // publicid = mb_u_int32 | ( zero index )
        // zero = u_int8
        // containing the value zero (0)
        // The actual DPI is determined after the String Table is read.
        $this->writeDocumentPublicIdentifier($dpiString, $this->_strings);

        // Set Charset from 5.6
        // charset = mb_u_int32
        $this->writeCharset($this->_charset);

        // Set String Table from 5.7
        // strb1 = length *byte
        $this->writeStringTable($this->_strings, $this->_charset, $this->_stringTable);

        $this->_currentURI = $uri;

        $this->_hasWrittenHeader = true;
    }

    function writeVersionNumber($version)
    {
        $this->_output.= chr($version);
    }

    function writeDocumentPublicIdentifier($dpiString, &$strings)
    {
        $i = XML_WBXML::getDPIInt($dpiString);

        if ($i == 0) {
            $strings[0] = $dpiString;
            $this->_output .= chr(0);
            $this->_output .= chr(0);
        } else {
            XML_WBXML::intToMBUInt32($this->_output, $i);
        }
    }

    function writeCharset($charset)
    {
        $cs = XML_WBXML::getCharsetInt($charset);

        if ($cs == 0) {
            return $this->raiseError('Unsupported Charset: ' . $charset);
        } else {
            XML_WBXML::intToMBUInt32($this->_output, $cs);
        }
    }

    function writeStringTable($strings, $charset, $stringTable)
    {
        $stringBytes = array();
        $count = 0;
        foreach ($strings as $str) {
            $bytes = $this->_getBytes($str, $charset);
            $stringBytes = array_merge($stringBytes, $bytes);
            $nullLength = $this->_addNullByte($bytes);
            $this->_stringTable->set($str, $count);
            $count += count($bytes) + $nullLength;
        }

        XML_WBXML::intToMBUInt32($this->_output, count($stringBytes));
        $this->_output.= implode('', $stringBytes);
    }

    function writeString($str, $cs)
    {
        $bytes = $this->_getBytes($str, $cs);
        $this->_output.= implode('', $bytes);
        $this->writeNull($cs);
    }

    function writeNull($charset)
    {
        $this->_output.= chr(0);
        return 1;
    }

    function _addNullByte(&$bytes)
    {
        $bytes[] = chr(0);
        return 1;
    }

    function _getBytes($string, $cs)
    {
        $string = String::convertCharset($string, $cs, 'utf-8');
        $nbytes = strlen($string);

        $bytes = array();
        for ($i = 0; $i < $nbytes; $i++) {
            $bytes[] = $string{$i};
        }

        return $bytes;
    }

    function _splitURI($tag)
    {
        $parts = explode(':', $tag);
        $name = array_pop($parts);
        $uri = implode(':', $parts);
        return array($uri, $name);
    }

    /**
     * Has no content, 64.
     */
    function startEndElementImp($uri, $name, $attributes)
    {
        if (!$this->_hasWrittenHeader) {
            $this->writeHeader($uri);
        }

        $this->writeTag($name, $attributes, false, $this->_charset);
    }

    function startElementImp($uri, $name, $attributes)
    {
        if (!$this->_hasWrittenHeader) {
            $this->writeHeader($uri);
        }

        if ($this->_currentURI != $uri) {
            $this->changecodepage($uri);

            $this->_currentURI != $uri;
        }

        $this->writeTag($name, $attributes, true, $this->_charset);
    }

    function writeStartElement($isEnd)
    {
        if ($this->_storeName != null) {
            if ($isEnd) {
                $this->startEndElementImp($this->_storeURI, $this->_storeName, $this->_storeAttributes);
            } else {
                $this->startElementImp($this->_storeURI, $this->_storeName, $this->_storeAttributes);
            }

            $this->_storeURI = null;
            $this->_storeName = null;
            $this->_storeAttributes = null;
        }
    }

    function startElement($uri, $name, $attributes)
    {
        if ($this->_subParser == null) {
            $this->writeStartElement(false);
            $this->_storeURI = $uri;
            $this->_storeName = $name;
            $this->_storeAttributes = $attributes;
        } else {
            $this->_subParserStack++;
        }
    }

    function _startElement($parser, $tag, $attributes)
    {
        list($uri, $name) = $this->_splitURI($tag);

        $this->startElement($uri, $name, $attributes);
    }

    function opaque($bytes)
    {
        if ($this->_subParser == null) {
            $this->writeStartElement(false);

            $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_OPAQUE);
            XML_WBXML::intToMBUInt32($this->_output, count($bytes));
            $this->_output .= $bytes;
        }
    }

    function characters($chars)
    {
        $chars = trim($chars);

        if (strlen($chars)) {
            /* We definitely don't want any whitespace. */
            if ($this->_subParser == null) {
                $this->writeStartElement(false);

                $i = $this->_stringTable->get($chars);
                if ($i != null) {
                    $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_STR_T);
                    XML_WBXML::intToMBUInt32($this->_output, $i);
                } else {
                    $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_STR_I);
                    $this->writeString($chars, $this->_charset);
                }
            }
        }
    }

    function _characters($parser, $chars)
    {
        $this->characters($chars);
    }

    function defaultHandler($parser, $data)
    {
    }

    function writeTag($name, $attrs, $hasContent, $cs)
    {
        if ($attrs != null && !count($attrs)) {
            $attrs = null;
        }

        $t = $this->_dtd->toTagInt($name);
        if ($t == -1) {
            $i = $this->_stringTable->get($name);
            if ($i == null) {
                return $this->raiseError($name . ' is not found in String Table or DTD');
            } else {
                if ($attrs == null && !$hasContent) {
                    $this->_output.= chr(XML_WBXML_GLOBAL_TOKEN_LITERAL);
                } elseif ($attrs == null && $hasContent) {
                    $this->_output.= chr(XML_WBXML_GLOBAL_TOKEN_LITERAL_A);
                } elseif ($attrs != null && $hasContent) {
                    $this->_output.= chr(XML_WBXML_GLOBAL_TOKEN_LITERAL_C);
                } elseif ($attrs != null && !$hasContent) {
                    $this->_output.= chr(XML_WBXML_GLOBAL_TOKEN_LITERAL_AC);
                }

                XML_WBXML::intToMBUInt32($this->_output, $i);
            }
        } else {
            if ($attrs == null && !$hasContent) {
                $this->_output.= chr($t);
            } elseif ($attrs == null && $hasContent) {
                $this->_output.= chr($t | 64);
            } elseif ($attrs != null && $hasContent) {
                $this->_output.= chr($t | 128);
            } elseif ($attrs != null && !$hasContent) {
                $this->_output.= chr($t | 192);
            }
        }

        if ($attrs != null) {
            $this->writeAttributes($attrs, $cs);
        }
    }

    function writeAttributes($attrs, $cs)
    {
        foreach ($attrs as $name => $value) {
            $this->writeAttribute($name, $value, $cs);
        }

        $this->_output.= chr(XML_WBXML_GLOBAL_TOKEN_END);
    }

    function writeAttribute($name, $value, $cs)
    {
        $a = $this->_dtd->toAttribute($name);
        if ($a == -1) {
            $i = $this->_stringTable->get($name);
            if ($i == null) {
                return $this->raiseError($name . ' is not found in String Table or DTD');
            } else {
                $this->_output.= chr(XML_WBXML_GLOBAL_TOKEN_LITERAL);
                XML_WBXML::intToMBUInt32($this->_output, $i);
            }
        } else {
            $this->_output.= $a;
        }

        $i = $this->_stringTable->get($name);
        if ($i != null) {
            $this->_output.= chr(XML_WBXML_GLOBAL_TOKEN_STR_T);
            XML_WBXML::intToMBUInt32($this->_output, $i);
        } else {
            $this->_output.= chr(XML_WBXML_GLOBAL_TOKEN_STR_I);
            $this->writeString($value, $cs);
        }
    }

    function endElement($uri, $name)
    {
        if ($this->_subParser == null) {
            $this->writeStartElement(false);
            $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_END);
        } else {
            $this->_subParserStack--;
            if ($this->_subParserStack == 0) {
                unset($this->_subParser);
            }
        }
    }

    function _endElement($parser, $tag)
    {
        list($uri, $name) = $this->_splitURI($tag);
        $this->endElement($uri, $name);
    }

    function changecodepage($uri)
    {
        $cp = $this->_dtd->toCodePageURI($uri);

        if (strlen($cp)) {
            $this->_dtd = &$this->_dtdManager->getInstanceURI($uri);

            $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_SWITCH_PAGE);
            $this->_output .= chr($cp);
        } else {
            $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_OPAQUE);

            $this->_subParser = &new XML_WBXML_Encoder($this->_output);
            $this->startElement($this->_storeURI, $this->_storeName, $this->_storeAttributes);

            $this->_subParserStack = 2;

            $this->_storeURI = null;
            $this->_storeName = null;
            $this->_storeAttributes = null;
        }
    }

    /**
     * Getter for property output.
     */
    function getOutput($output)
    {
        return $this->_output;
    }

}
