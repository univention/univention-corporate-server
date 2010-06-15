<?php

include_once 'XML/WBXML.php';
include_once 'XML/WBXML/DTDManager.php';
include_once 'XML/WBXML/ContentHandler.php';

/**
 * $Horde: framework/XML_WBXML/WBXML/Decoder.php,v 1.18 2004/04/07 17:43:43 chuck Exp $
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
class XML_WBXML_Decoder extends XML_WBXML_ContentHandler {

    /**
     * Document Public Identifier type
     * 1 mb_u_int32 well known type
     * 2 string table
     * from spec but converted into a string.
     *
     * Document Public Identifier
     * Used with dpiType.
     */
    var $_dpi;

    /**
     * String table as defined in 5.7
     */
    var $_stringTable = array();

    /**
     * Content handler.
     * Currently just outputs raw XML.
     */
    var $_ch;

    var $_tagDTD;

    var $_prevAttributeDTD;

    var $_attributeDTD;

    /**
     * State variables.
     */
    var $_tagStack = array();
    var $_isAttribute;
    var $_isData = false;

    /**
     * The DTD Manager.
     * @var object XML_WBXML_DTDManager $dtdManager
     */
    var $_dtdManager;


    /**
     * The string position.
     * @var integer string position
     */
    var $_strpos;

    /**
     * Use wbxml2xml from libwbxml.
     * @var String
     */
    var $_wbxml2xml = '/usr/bin/wbxml2xml -o ';

    /**
     * Constructor.
     */
    function XML_WBXML_Decoder()
    {
        $this->_dtdManager = &new XML_WBXML_DTDManager();
    }

    /**
     * Return one byte from the input stream.
     */
    function getByte($input)
    {
        return ord($input[$this->_strpos++]);
    }

    function decode($input)
    {
        if (isset($this->_wbxml2xml)) {
            $tmp_id = mt_rand();
            $tmp_file = '/tmp/wbxml_decoder_' . $tmp_id;

            $fp = fopen($tmp_file . '.wbxml', 'wb');
            fwrite($fp, $input);
            fclose($fp);

            exec($this->_wbxml2xml . $tmp_file . '.xml ' . $tmp_file . '.wbxml');

            $ret = file_get_contents($tmp_file . '.xml');
            unlink($tmp_file . '.xml');
            unlink($tmp_file . '.wbxml');
            return $ret;
        } else {
            $this->_strpos = 0;
            // Get Version Number from Section 5.4
            // version = u_int8
            // currently 1, 2 or 3
            $this->_wbxmlVersion = $this->getVersionNumber($input);

            // Get Document Public Idetifier from Section 5.5
            // publicid = mb_u_int32 | (zero index)
            // zero = u_int8
            // Containing the value zero (0)
            // The actual DPI is determined after the String Table is read.
            $dpiStruct = $this->getDocumentPublicIdentifier($input);

            // Get Charset from 5.6
            // charset = mb_u_int32
            $this->_charset = $this->getCharset($input);

            // Get String Table from 5.7
            // strb1 = length *byte
            $this->_stringTable = $this->getStringTable($input, $this->_charset);

            // Get Document Public Idetifier from Section 5.5.
            $this->_dpi = $this->getDocumentPublicIdentifierImpl($dpiStruct['dpiType'],
                                                                 $dpiStruct['dpiNumber'],
                                                                 $this->_stringTable);

            // Now the real fun begins.
            // from Sections 5.2 and 5.8

            // Default content handler.
            $this->_ch = &new XML_WBXML_ContentHandler();

            // Default content handler.
            $this->_dtdManager = &new XML_WBXML_DTDManager();

            // Get the starting DTD.
            $this->_tagDTD = $this->_dtdManager->getInstance($this->_dpi);
            if (!$this->_tagDTD) {
                return $this->raiseError('No DTD found for ' . $this->_dpi);
            }

            $this->_attributeDTD = $this->_tagDTD;

            while ($this->_strpos < strlen($input)) {
                $this->_decode($input);
            }

            return $this->_ch->getOutput();
        }

    }

    function getVersionNumber($input)
    {
        return $this->getByte($input);
    }

    function getDocumentPublicIdentifier($input)
    {
        // 'dpiType' 'dpiNumber'
        $dpistruct = array();

        $i = XML_WBXML::MBUInt32ToInt($input, $this->_strpos);

        if ($i == 0) {
            $dpiStruct['dpiType'] = 2;
            $dpiStruct['dpiNumber'] = $this->getByte($input);
        } else {
            $dpiStruct['dpiType'] = 1;
            $dpiStruct['dpiNumber'] = $i;
        }

        return $dpiStruct;
    }

    function getDocumentPublicIdentifierImpl($dpiType, $dpiNumber, $st)
    {
        if ($dpiType == 1) {
            return XML_WBXML::getDPIString($dpiNumber);
        } else {
            return isset($st[$dpiNumber]) ? $st[$dpiNumber] : null;
        }
    }

    /**
     * Returns the character encoding. Only default character
     * encodings from J2SE are supported.  From
     * http://www.iana.org/assignments/character-sets and
     * http://java.sun.com/j2se/1.4.2/docs/api/java/nio/charset/Charset.html
     */
    function getCharset($input)
    {
        $cs = XML_WBXML::MBUInt32ToInt($input, $this->_strpos);
        return $charset = XML_WBXML::getCharsetString($cs);
    }

    /**
     * @TODO needs to be fixed. Does this still really need to be
     * fixed?
     */
    function getStringTable($input, $cs)
    {
        $stringTable = array();
        $size = XML_WBXML::MBUInt32ToInt($input, $this->_strpos);

        // A hack to make it work with arrays.
        // How/why is this necessary?
        $str = 'j';

        $numstr = 0;
        $start = 0;
        $j = 0;
        for ($i = 0; $i < $size; $i++ ) {
            /* May need to fix the null detector for more than single
             * byte charsets like ASCII, UTF-8, etc. */
            $ch = $input[$this->_strpos++];
            if (ord($ch) == 0) {
                $stringTable[$numstr++] = $str;
                $str = '#';
                $start = $i + 1;
            } else {
                $str[$j++] = $ch;
            }
        }

        if ($start < $size) {
            $stringTable[$numstr++] = $str;
        }

        return $stringTable;
    }

    function _decode($input)
    {
        $token = $this->getByte($input);
        $str = '';

        switch ($token) {
        case XML_WBXML_GLOBAL_TOKEN_STR_I:
            // Section 5.8.4.1
            $str = $this->termstr($input);
            $this->_ch->characters($str);
            break;

        case XML_WBXML_GLOBAL_TOKEN_STR_T:
            // Section 5.8.4.1
            $str = $this->_stringTable[XML_WBXML::MBUInt32ToInt($intput)];
            $this->_ch->characters($str);
            break;

        case XML_WBXML_GLOBAL_TOKEN_EXT_I_0:
        case XML_WBXML_GLOBAL_TOKEN_EXT_I_1:
        case XML_WBXML_GLOBAL_TOKEN_EXT_I_2:
            // Section 5.8.4.2
            $str = $this->termstr($input);
            $this->_ch->characters($str);
            break;

        case XML_WBXML_GLOBAL_TOKEN_EXT_T_0:
        case XML_WBXML_GLOBAL_TOKEN_EXT_T_1:
        case XML_WBXML_GLOBAL_TOKEN_EXT_T_2:
            // Section 5.8.4.2
            $str = $this->_stringTable[XML_WBXML::MBUInt32ToInt($intput)];
            $this->_ch->characters($str);
            break;

        case XML_WBXML_GLOBAL_TOKEN_EXT_0:
        case XML_WBXML_GLOBAL_TOKEN_EXT_1:
        case XML_WBXML_GLOBAL_TOKEN_EXT_2:
            // Section 5.8.4.2
            $extension = $this->getByte($input);
            $this->_ch->characters($extension);
            break;

        case XML_WBXML_GLOBAL_TOKEN_ENTITY:
            // Section 5.8.4.3
            // UCS-4 chracter encoding?
            $entity = $this->entity(XML_WBXML::MBUInt32ToInt($input, $this->_strpos));

            $this->_ch->characters('&#' . $entity . ';');
            break;

        case XML_WBXML_GLOBAL_TOKEN_PI:
            // Section 5.8.4.4
            // throw new IOException("WBXML global token processing instruction(PI, " + token + ") is unsupported!");
            break;

        case XML_WBXML_GLOBAL_TOKEN_LITERAL:
            // Section 5.8.4.5
            $str = $this->_stringTable[XML_WBXML::MBUInt32ToInt($input, $this->_strpos)];
            $this->parseTag($input, $str, false, false);
            break;

        case XML_WBXML_GLOBAL_TOKEN_LITERAL_A:
            // Section 5.8.4.5
            $str = $this->_stringTable[XML_WBXML::MBUInt32ToInt($input, $this->_strpos)];
            $this->parseTag($input, $str, true, false);
            break;

        case XML_WBXML_GLOBAL_TOKEN_LITERAL_AC:
            // Section 5.8.4.5
            $str = $this->_stringTable[XML_WBXML::MBUInt32ToInt($input, $this->_strpos)];
            $this->parseTag($input, $string, true, true);
            break;

        case XML_WBXML_GLOBAL_TOKEN_LITERAL_C:
            // Section 5.8.4.5
            $str = $this->_stringTable[XML_WBXML::MBUInt32ToInt($input, $this->_strpos)];
            $this->parseTag($input, $str, false, true);
            break;

        case XML_WBXML_GLOBAL_TOKEN_OPAQUE:
            // Section 5.8.4.6
            $size = XML_WBXML::MBUInt32ToInt($input, $this->_strpos);
            $b = substr($input, $this->_strpos, $this->_strpos + $size);
            $this->_strpos += $size;
            $this->_ch->opaque($b);

            // FIXME Opaque is used by SYNCML.  Opaque data that depends on the context
            // if (contentHandler instanceof OpaqueContentHandler) {
            //     ((OpaqueContentHandler)contentHandler).opaque(b);
            // } else {
            //     String str = new String(b, 0, size, charset);
            //     char[] chars = str.toCharArray();

            //     contentHandler.characters(chars, 0, chars.length);
            // }

            // This can cause some problems. We may have to use a
            // event based decoder.
            break;

        case XML_WBXML_GLOBAL_TOKEN_END:
            // Section 5.8.4.7.1
            $str = $this->endTag();
            break;

        case XML_WBXML_GLOBAL_TOKEN_SWITCH_PAGE:
            // Section 5.8.4.7.2
            $codePage = $this->getByte($input);
            $this->switchElementCodePage($codePage);
            break;

        default:
            // Section 5.8.2
            // Section 5.8.3
            $hasAttributes = (($token & 0x80) != 0);
            $hasContent = (($token & 0x40) != 0);
            $realToken = $token & 0x3F;
            $str = $this->getTag($realToken);

            $this->parseTag($input, $str, $hasAttributes, $hasContent);

            if ($realToken == 0x0f) {
                // FIXME Don't remember this one.
                $this->_isData = true;
            }
            break;
        }
    }

    function parseTag($input, $tag, $hasAttributes, $hasContent)
    {
        $attrs = array();
        if ($hasAttributes) {
            $attrs = $this->getAttributes($input);
        }

        $this->_ch->startElement($this->getCurrentURI(), $tag, $attrs);

        if ($hasContent) {
            // FIXME I forgot what does this does. Not sure if this is
            // right?
            $this->_tagStack[] = $tag;
        } else {
            $this->_ch->endElement($this->getCurrentURI(), $tag);
        }
    }

    function endTag()
    {
        if (count($this->_tagStack)) {
            $tag = array_pop($this->_tagStack);
        } else {
            $tag = 'Unknown';
        }

        if ($tag == 'Data') {
            $this->_isData = false;
        }

        $this->_ch->endElement($this->getCurrentURI(), $tag);

        return $tag;
    }

    function getAttributes($input)
    {
        $this->startGetAttributes();
        $hasMoreAttributes = true;

        $attrs = array();
        $attr = null;
        $value = null;
        $token = null;

        while ($hasMoreAttributes) {
            $token = $this->getByte($input);

            switch ($token) {
            // Attribute specified.
            case XML_WBXML_GLOBAL_TOKEN_LITERAL:
                // Section 5.8.4.5
                if (isset($attr)) {
                    $attrs[] = array('attribute' => $attr,
                                     'value' => $value);
                }

                $attr = $this->_stringTable[XML_WBXML::MBUInt32ToInt($input, $this->_strpos)];
                break;

            // Value specified.
            case XML_WBXML_GLOBAL_TOKEN_EXT_I_0:
            case XML_WBXML_GLOBAL_TOKEN_EXT_I_1:
            case XML_WBXML_GLOBAL_TOKEN_EXT_I_2:
                // Section 5.8.4.2
                $value .= $this->termstr($input);
                break;

            case XML_WBXML_GLOBAL_TOKEN_EXT_T_0:
            case XML_WBXML_GLOBAL_TOKEN_EXT_T_1:
            case XML_WBXML_GLOBAL_TOKEN_EXT_T_2:
                // Section 5.8.4.2
                $value .= $this->_stringTable[XML_WBXML::MBUInt32ToInt($input, $this->_strpos)];
                break;

            case XML_WBXML_GLOBAL_TOKEN_EXT_0:
            case XML_WBXML_GLOBAL_TOKEN_EXT_1:
            case XML_WBXML_GLOBAL_TOKEN_EXT_2:
                // Section 5.8.4.2
                $value .= $input[$this->_strpos++];
                break;

            case XML_WBXML_GLOBAL_TOKEN_ENTITY:
                // Section 5.8.4.3
                $value .= $this->entity(XML_WBXML::MBUInt32ToInt($input, $this->_strpos));
                break;

            case XML_WBXML_GLOBAL_TOKEN_STR_I:
                // Section 5.8.4.1
                $value .= $this->termstr($input);
                break;

            case XML_WBXML_GLOBAL_TOKEN_STR_T:
                // Section 5.8.4.1
                $value .= $this->_stringTable[XML_WBXML::MBUInt32ToInt($input, $this->_strpos)];
                break;

            case XML_WBXML_GLOBAL_TOKEN_OPAQUE:
                // Section 5.8.4.6
                $size = XML_WBXML::MBUInt32ToInt($input, $this->_strpos);
                $b = substr($input, $this->_strpos, $this->_strpos + $size);
                $this->_strpos += $size;

                $value .= $b;
                break;

            case XML_WBXML_GLOBAL_TOKEN_END:
                // Section 5.8.4.7.1
                $hasMoreAttributes = false;
                if (isset($attr)) {
                    $attrs[] = array('attribute' => $attr,
                                     'value' => $value);
                }
                break;

            case XML_WBXML_GLOBAL_TOKEN_SWITCH_PAGE:
                // Section 5.8.4.7.2
                $codePage = $this->getByte($input);
                if (!$this->_prevAttributeDTD) {
                    $this->_prevAttributeDTD = $this->_attributeDTD;
                }

                $this->switchAttributeCodePage($codePage);
                break;

            default:
                if ($token > 128) {
                    if (isset($attr)) {
                        $attrs[] = array('attribute' => $attr,
                                         'value' => $value);
                    }
                    $attr = $this->_attributeDTD->toAttribute($token);
                } else {
                    // Value.
                    $value .= $this->_attributeDTD->toAttribute($token);
                }
                break;
            }
        }

        if (!$this->_prevAttributeDTD) {
            $this->_attributeDTD = $this->_prevAttributeDTD;
            $this->_prevAttributeDTD = false;
        }

        $this->stopGetAttributes();
    }

    function startGetAttributes()
    {
        $this->_isAttribute = true;
    }

    function stopGetAttributes()
    {
        $this->_isAttribute = false;
    }

    function getCurrentURI()
    {
        if ($this->_isAttribute) {
            return $this->_tagDTD->getURI();
        } else {
            return $this->_attributeDTD->getURI();
        }
    }

    function writeString($str)
    {
        $this->_ch->characters($str);
    }

    function getTag($tag)
    {
        // Should know which state it is in.
        return $this->_tagDTD->toTagStr($tag);
    }

    function getAttribute($attribute)
    {
        // Should know which state it is in.
        $this->_attributeDTD->toAttributeInt($attribute);
    }

    function switchElementCodePage($codePage)
    {
        $this->_tagDTD = &$this->_dtdManager->getInstance($this->_tagDTD->toCodePageStr($codePage));
        $this->switchAttributeCodePage($codePage);
    }

    function switchAttributeCodePage($codePage)
    {
        $this->_attributeDTD = &$this->_dtdManager->getInstance($this->_attributeDTD->toCodePageStr($codePage));
    }

    /**
     * Return the hex version of the base 10 $entity.
     */
    function entity($entity)
    {
        return dechex($entity);
    }

    /**
     * @TODO FIXME reads a null terminated string.
     */
    function termstr($input)
    {
        $str = '#';
        $i = 0;
        $ch = $input[$this->_strpos++];
        while (ord($ch) != 0) {
            $str[$i++] = $ch;
            $ch = $input[$this->_strpos++];
        }

        return $str;
    }

    /**
     * For debugging.
     */
    function dumpStringTable($st)
    {
        echo 'String Table: ';
        foreach ($st as $s) {
            echo $s . ', ';
        }
        echo "\n";
    }

}
