<?php

include_once 'XML/WBXML.php';
include_once 'XML/WBXML/ContentHandler.php';
include_once 'XML/WBXML/DTDManager.php';

/**
 * From Binary XML Content Format Specification Version 1.3, 25 July 2001
 * found at http://www.wapforum.org
 *
 * $Horde: framework/XML_WBXML/WBXML/Encoder.php,v 1.25.10.18 2009-01-06 15:23:50 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anthony Mills <amills@pyramid6.com>
 * @package XML_WBXML
 */
class XML_WBXML_Encoder extends XML_WBXML_ContentHandler {

    var $_strings = array();

    var $_stringTable;

    var $_hasWrittenHeader = false;

    var $_dtd;

    var $_output = '';

    var $_uris = array();

    var $_uriNums = array();

    var $_currentURI;

    var $_subParser = null;
    var $_subParserStack = 0;

    /**
     * The XML parser.
     *
     * @var resource
     */
    var $_parser;

    /**
     * The DTD Manager.
     *
     * @var XML_WBXML_DTDManager
     */
    var $_dtdManager;

    /**
     * Constructor.
     */
    function XML_WBXML_Encoder()
    {
        $this->_dtdManager = &new XML_WBXML_DTDManager();
        $this->_stringTable = &new XML_WBXML_HashTable();
    }

    /**
     * Take the input $xml and turn it into WBXML. This is _not_ the
     * intended way of using this class. It is derived from
     * Contenthandler and one should use it as a ContentHandler and
     * produce the XML-structure with startElement(), endElement(),
     * and characters().
     */
    function encode($xml)
    {
        // Create the XML parser and set method references.
        $this->_parser = xml_parser_create_ns($this->_charset);
        xml_set_object($this->_parser, $this);
        xml_parser_set_option($this->_parser, XML_OPTION_CASE_FOLDING, false);
        xml_set_element_handler($this->_parser, '_startElement', '_endElement');
        xml_set_character_data_handler($this->_parser, '_characters');
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

    /**
     * This will write the correct headers.
     */
    function writeHeader($uri)
    {
        $this->_dtd = &$this->_dtdManager->getInstanceURI($uri);
        if (!$this->_dtd) {
            // TODO: proper error handling
            die('Unable to find dtd for ' . $uri);
        }
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
        $this->_output .= chr($version);
    }

    function writeDocumentPublicIdentifier($dpiString, &$strings)
    {
        $i = 0;

        // The OMA test suite doesn't like DPI as integer code.
        // So don't try lookup and always send full DPI string.
        // $i = XML_WBXML::getDPIInt($dpiString);

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
        $this->_output .= implode('', $stringBytes);
    }

    function writeString($str, $cs)
    {
        $bytes = $this->_getBytes($str, $cs);
        $this->_output .= implode('', $bytes);
        $this->writeNull($cs);
    }

    function writeNull($charset)
    {
        $this->_output .= chr(0);
        return 1;
    }

    function _addNullByte(&$bytes)
    {
        $bytes[] = chr(0);
        return 1;
    }

    function _getBytes($string, $cs)
    {
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

    function startElement($uri, $name, $attributes = array())
    {
        if ($this->_subParser == null) {
            if (!$this->_hasWrittenHeader) {
                $this->writeHeader($uri);
            }
            if ($this->_currentURI != $uri) {
                $this->changecodepage($uri);
            }
            if ($this->_subParser == null) {
                $this->writeTag($name, $attributes, true, $this->_charset);
            } else {
                $this->_subParser->startElement($uri, $name, $attributes);
            }
        } else {
            $this->_subParserStack++;
            $this->_subParser->startElement($uri, $name, $attributes);
        }
    }

    function _startElement($parser, $tag, $attributes)
    {
        list($uri, $name) = $this->_splitURI($tag);

        $this->startElement($uri, $name, $attributes);
    }

    function opaque($o)
    {
        $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_OPAQUE);
        XML_WBXML::intToMBUInt32($this->_output, strlen($o));
        $this->_output .= $o;
    }

    function characters($chars)
    {
        $chars = trim($chars);

        if (strlen($chars)) {
            /* We definitely don't want any whitespace. */
            if ($this->_subParser == null) {
                $i = $this->_stringTable->get($chars);
                if ($i != null) {
                    $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_STR_T);
                    XML_WBXML::intToMBUInt32($this->_output, $i);
                } else {
                    $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_STR_I);
                    $this->writeString($chars, $this->_charset);
                }
            } else {
                $this->_subParser->characters($chars);
            }
        }
    }

    function _characters($parser, $chars)
    {
        $this->characters($chars);
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
                    $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_LITERAL);
                } elseif ($attrs == null && $hasContent) {
                    $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_LITERAL_A);
                } elseif ($attrs != null && $hasContent) {
                    $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_LITERAL_C);
                } elseif ($attrs != null && !$hasContent) {
                    $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_LITERAL_AC);
                }

                XML_WBXML::intToMBUInt32($this->_output, $i);
            }
        } else {
            if ($attrs == null && !$hasContent) {
                $this->_output .= chr($t);
            } elseif ($attrs == null && $hasContent) {
                $this->_output .= chr($t | 64);
            } elseif ($attrs != null && $hasContent) {
                $this->_output .= chr($t | 128);
            } elseif ($attrs != null && !$hasContent) {
                $this->_output .= chr($t | 192);
            }
        }

        if ($attrs != null && is_array($attrs) && count($attrs) > 0) {
            $this->writeAttributes($attrs, $cs);
        }
    }

    function writeAttributes($attrs, $cs)
    {
        foreach ($attrs as $name => $value) {
            $this->writeAttribute($name, $value, $cs);
        }

        $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_END);
    }

    function writeAttribute($name, $value, $cs)
    {
        $a = $this->_dtd->toAttribute($name);
        if ($a == -1) {
            $i = $this->_stringTable->get($name);
            if ($i == null) {
                return $this->raiseError($name . ' is not found in String Table or DTD');
            } else {
                $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_LITERAL);
                XML_WBXML::intToMBUInt32($this->_output, $i);
            }
        } else {
            $this->_output .= $a;
        }

        $i = $this->_stringTable->get($name);
        if ($i != null) {
            $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_STR_T);
            XML_WBXML::intToMBUInt32($this->_output, $i);
        } else {
            $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_STR_I);
            $this->writeString($value, $cs);
        }
    }

    function endElement($uri, $name)
    {
        if ($this->_subParser == null) {
            $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_END);
        } else {
            $this->_subParser->endElement($uri, $name);
            $this->_subParserStack--;

            if ($this->_subParserStack == 0) {
                $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_OPAQUE);

                XML_WBXML::intToMBUInt32($this->_output,
                                         strlen($this->_subParser->getOutput()));
                $this->_output .= $this->_subParser->getOutput();

                $this->_subParser = null;
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
        // @todo: this is a hack!
        if ($this->_dtd->getVersion() == 2 && !preg_match('/1\.2$/', $uri)) {
            $uri .= '1.2';
        }
        if ($this->_dtd->getVersion() == 1 && !preg_match('/1\.1$/', $uri)) {
            $uri .= '1.1';
        }
        if ($this->_dtd->getVersion() == 0 && !preg_match('/1\.0$/', $uri)) {
            $uri .= '1.0';
        }

        $cp = $this->_dtd->toCodePageURI($uri);
        if (strlen($cp)) {
            $this->_dtd = &$this->_dtdManager->getInstanceURI($uri);

            $this->_output .= chr(XML_WBXML_GLOBAL_TOKEN_SWITCH_PAGE);
            $this->_output .= chr($cp);
            $this->_currentURI = $uri;

        } else {
            $this->_subParser = &new XML_WBXML_Encoder(true);
            $this->_subParserStack = 1;
        }
    }

    /**
     * Getter for property output.
     */
    function getOutput()
    {
        return $this->_output;
    }

    function getOutputSize()
    {
        return strlen($this->_output);
    }

}
