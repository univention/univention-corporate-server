<?php

/**
 * Constants are from Binary XML Content Format Specification Version 1.3, 25
 * July 2001 found at http://www.wapforum.org
 */

/**
 * From 7.1 Global Tokens.
 */

define('XML_WBXML_GLOBAL_TOKEN_SWITCH_PAGE', 0);  // 0x00
define('XML_WBXML_GLOBAL_TOKEN_END', 1);          // 0x01
define('XML_WBXML_GLOBAL_TOKEN_ENTITY', 2);       // 0x02
define('XML_WBXML_GLOBAL_TOKEN_STR_I', 3);        // 0x03
define('XML_WBXML_GLOBAL_TOKEN_LITERAL', 4);      // 0x04

define('XML_WBXML_GLOBAL_TOKEN_EXT_I_0', 64);     // 0x40
define('XML_WBXML_GLOBAL_TOKEN_EXT_I_1', 65);     // 0x41
define('XML_WBXML_GLOBAL_TOKEN_EXT_I_2', 66);     // 0x42
define('XML_WBXML_GLOBAL_TOKEN_PI', 67);          // 0x43
define('XML_WBXML_GLOBAL_TOKEN_LITERAL_C', 68);   // 0x44

define('XML_WBXML_GLOBAL_TOKEN_EXT_T_0', 128);    // 0x80
define('XML_WBXML_GLOBAL_TOKEN_EXT_T_1', 129);    // 0x81
define('XML_WBXML_GLOBAL_TOKEN_EXT_T_2', 130);    // 0x82
define('XML_WBXML_GLOBAL_TOKEN_STR_T', 131);      // 0x83
define('XML_WBXML_GLOBAL_TOKEN_LITERAL_A', 132);  // 0x84

define('XML_WBXML_GLOBAL_TOKEN_EXT_0', 192);      // 0xC0
define('XML_WBXML_GLOBAL_TOKEN_EXT_1', 193);      // 0xC1
define('XML_WBXML_GLOBAL_TOKEN_EXT_2', 194);      // 0xC2
define('XML_WBXML_GLOBAL_TOKEN_OPAQUE', 195);     // 0xC3
define('XML_WBXML_GLOBAL_TOKEN_LITERAL_AC', 196); // 0xC4

/**
 * Not sure where defined.
 * ADD CHAPTER
 */
define('DPI_DTD_WML_1_0', '-//WAPFORUM//DTD WML 1.0//EN');
define('DPI_DTD_WTA_1_0', '-//WAPFORUM//DTD WTA 1.0//EN');
define('DPI_DTD_WML_1_1', '-//WAPFORUM//DTD WML 1.1//EN');
define('DPI_DTD_SI_1_1', '-//WAPFORUM//DTD SI 1.1//EN');
define('DPI_DTD_SL_1_0', '-//WAPFORUM//DTD SL 1.0//EN');
define('DPI_DTD_CO_1_0', '-//WAPFORUM//DTD CO 1.0//EN');
define('DPI_DTD_CHANNEL_1_1', '-//WAPFORUM//DTD CHANNEL 1.1//EN');
define('DPI_DTD_WML_1_2', '-//WAPFORUM//DTD WML 1.2//EN');
define('DPI_DTD_WML_1_3', '-//WAPFORUM//DTD WML 1.3//EN');
define('DPI_DTD_PROV_1_0', '-//WAPFORUM//DTD PROV 1.0//EN');
define('DPI_DTD_WTA_WML_1_2', '-//WAPFORUM//DTD WTA-WML 1.2//EN');
define('DPI_DTD_CHANNEL_1_2', '-//WAPFORUM//DTD CHANNEL 1.2//EN');

define('DPI_DTD_SYNCML_1_0', '-//SYNCML//DTD SyncML 1.0//EN');
define('DPI_DTD_DEVINF_1_0', '-//SYNCML//DTD DevInf 1.0//EN');
define('DPI_DTD_METINF_1_0', '-//SYNCML//DTD MetInf 1.0//EN');
define('DPI_DTD_SYNCML_1_1', '-//SYNCML//DTD SyncML 1.1//EN');
define('DPI_DTD_DEVINF_1_1', '-//SYNCML//DTD DevInf 1.1//EN');
define('DPI_DTD_METINF_1_1', '-//SYNCML//DTD MetInf 1.1//EN');
define('DPI_DTD_SYNCML_1_2', '-//SYNCML//DTD SyncML 1.2//EN');
define('DPI_DTD_DEVINF_1_2', '-//SYNCML//DTD DevInf 1.2//EN');
define('DPI_DTD_METINF_1_2', '-//SYNCML//DTD MetInf 1.2//EN');

/**
 * Only default character encodings from J2SE are currently supported.
 */
define('CHARSET_US_ASCII', 'US-ASCII');
define('CHARSET_ISO_8859_1', 'ISO-8859-1');
define('CHARSET_UTF_8', 'UTF-8');
define('CHARSET_UTF_16BE', 'UTF-16BE');
define('CHARSET_UTF_16LE', 'UTF-16LE');
define('CHARSET_UTF_16', 'UTF-16');

/**
 * $Horde: framework/XML_WBXML/WBXML.php,v 1.13.12.12 2009-01-06 15:23:49 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anthony Mills <amills@pyramid6.com>
 * @package XML_WBXML
 */
class XML_WBXML {

    /**
     * Decoding Multi-byte Integers from Section 5.1
     *
     * Use long because it is unsigned.
     */
    function MBUInt32ToInt($in, &$pos)
    {
        $val = 0;

        do {
            $b = ord($in[$pos++]);
            $val <<= 7; // Bitshift left 7 bits.
            $val += ($b & 127);
        } while (($b & 128) != 0);

        return $val;
    }

    /**
     * Encoding Multi-byte Integers from Section 5.1
     */
    function intToMBUInt32(&$out, $i)
    {
        if ($i > 268435455) {
            $bytes0 = 0 | XML_WBXML::getBits(0, $i);
            $bytes1 = 128 | XML_WBXML::getBits(1, $i);
            $bytes2 = 128 | XML_WBXML::getBits(2, $i);
            $bytes3 = 128 | XML_WBXML::getBits(3, $i);
            $bytes4 = 128 | XML_WBXML::getBits(4, $i);

            $out .= chr($bytes4) . chr($bytes3) . chr($bytes2) . chr($bytes1) . chr($bytes0);
        } elseif ($i > 2097151) {
            $bytes0 = 0 | XML_WBXML::getBits(0, $i);
            $bytes1 = 128 | XML_WBXML::getBits(1, $i);
            $bytes2 = 128 | XML_WBXML::getBits(2, $i);
            $bytes3 = 128 | XML_WBXML::getBits(3, $i);

            $out .= chr($bytes3) . chr($bytes2) . chr($bytes1) . chr($bytes0);
        } elseif ($i > 16383) {
            $bytes0 = 0 | XML_WBXML::getBits(0, $i);
            $bytes1 = 128 | XML_WBXML::getBits(1, $i);
            $bytes2 = 128 | XML_WBXML::getBits(2, $i);

            $out .= chr($bytes2) . chr($bytes1) . chr($bytes0);
        } elseif ($i > 127) {
            $bytes0 = 0 | XML_WBXML::getBits(0, $i);
            $bytes1 = 128 | XML_WBXML::getBits(1, $i);

            $out .= chr($bytes1) . chr($bytes0);
        } else {
            $bytes0 = 0 | XML_WBXML::getBits(0, $i);

            $out .= chr($bytes0);
        }
    }

    function getBits($num, $l)
    {
        switch ($num) {
        case 0:
            return $l & 127; // 0x7F

        case 1:
            return ($l >> 7) & 127; // 0x7F

        case 2:
            return ($l >> 14) & 127; // 0x7F

        case 3:
            return ($l >> 21) & 127; // 0x7F

        case 4:
            return ($l >> 28) & 127; // 0x7F
        }

        return 0;
    }

    function getDPIString($i)
    {
        /**
         * ADD CHAPTER
         */
        $DPIString = array(2 => DPI_DTD_WML_1_0,
                           3 => DPI_DTD_WTA_1_0,
                           4 => DPI_DTD_WML_1_1,
                           5 => DPI_DTD_SI_1_1,
                           6 => DPI_DTD_SL_1_0,
                           7 => DPI_DTD_CO_1_0,
                           8 => DPI_DTD_CHANNEL_1_1,
                           9 => DPI_DTD_WML_1_2,
                           10 => DPI_DTD_WML_1_3,
                           11 => DPI_DTD_PROV_1_0,
                           12 => DPI_DTD_WTA_WML_1_2,
                           13 => DPI_DTD_CHANNEL_1_2,

                           // Not all SyncML clients know this, so we
                           // should use the string table.
                           // 0xFD1 => DPI_DTD_SYNCML_1_1,
                           // These codes are taken from libwbxml wbxml_tables.h:
                           4049 => DPI_DTD_SYNCML_1_0, // 0x0fd1
                           4050 => DPI_DTD_DEVINF_1_0, // 0x0fd2
                           4051 => DPI_DTD_SYNCML_1_1, // 0x0fd3
                           4052 => DPI_DTD_DEVINF_1_1, // 0x0fd4
                           4609 => DPI_DTD_SYNCML_1_2, // 0x1201
                           //@todo: verify this:
                           4611 => DPI_DTD_DEVINF_1_2  // 0x1203
// taken from libxml but might be wrong:
//                           4610 => DPI_DTD_DEVINF_1_2, // 0x1202
//                           4611 => DPI_DTD_METINF_1_2  // 0x1203
                           );
        return isset($DPIString[$i]) ? $DPIString[$i] : null;
    }

    function getDPIInt($dpi)
    {
        /**
         * ADD CHAPTER
         */
        $DPIInt = array(DPI_DTD_WML_1_0 => 2,
                        DPI_DTD_WTA_1_0 => 3,
                        DPI_DTD_WML_1_1 => 4,
                        DPI_DTD_SI_1_1 => 5,
                        DPI_DTD_SL_1_0 => 6,
                        DPI_DTD_CO_1_0 => 7,
                        DPI_DTD_CHANNEL_1_1 => 8,
                        DPI_DTD_WML_1_2 => 9,
                        DPI_DTD_WML_1_3 => 10,
                        DPI_DTD_PROV_1_0 => 11,
                        DPI_DTD_WTA_WML_1_2 => 12,
                        DPI_DTD_CHANNEL_1_2 => 13,

                        // Not all SyncML clients know this, so maybe we
                        // should use the string table.
                           // These codes are taken from libwbxml wbxml_tables.h:
                        DPI_DTD_SYNCML_1_0 => 4049,
                        DPI_DTD_DEVINF_1_0 => 4050,
                        DPI_DTD_SYNCML_1_1 => 4051,
                        DPI_DTD_DEVINF_1_1 => 4052,
                        DPI_DTD_SYNCML_1_2 => 4609, // 0x1201
//                        DPI_DTD_DEVINF_1_2 => 4610, // 0x1202
//                        DPI_DTD_METINF_1_2 => 4611  // 0x1203
                        //@todo: verify this
                        DPI_DTD_DEVINF_1_2 => 4611  // 0x1203
                        // DPI_DTD_SYNCML_1_1 => 0xFD1,
                        // DPI_DTD_DEVINF_1_1 => 0xFD2,
                        );

        return isset($DPIInt[$dpi]) ? $DPIInt[$dpi] : 0;
    }

    /**
     * Returns the character encoding.
     * only default character encodings from J2SE are supported
     * from http://www.iana.org/assignments/character-sets
     * and http://java.sun.com/j2se/1.4.2/docs/api/java/nio/charset/Charset.html
     */
    function getCharsetString($cs)
    {
        /**
         * From http://www.iana.org/assignments/character-sets
         */
        $charsetString = array(3 => 'US-ASCII',
                               4 => 'ISO-8859-1',
                               106 => 'UTF-8',
                               1013 => 'UTF-16BE',
                               1014 => 'UTF-16LE',
                               1015 => 'UTF-16');

        return isset($charsetString[$cs]) ? $charsetString[$cs] : null;
    }

    /**
     * Returns the character encoding.
     *
     * Only default character encodings from J2SE are supported.
     *
     * From http://www.iana.org/assignments/character-sets and
     * http://java.sun.com/j2se/1.4.2/docs/api/java/nio/charset/Charset.html
     */
    function getCharsetInt($cs)
    {
        /**
         * From http://www.iana.org/assignments/character-sets
         */
        $charsetInt = array('US-ASCII' => 3,
                            'ISO-8859-1' => 4,
                            'UTF-8' => 106,
                            'UTF-16BE' => 1013,
                            'UTF-16LE' => 1014,
                            'UTF-16' => 1015);

        return isset($charsetInt[$cs]) ? $charsetInt[$cs] : null;
    }

}

/**
 * @package XML_WBXML
 */
class XML_WBXML_HashTable {

    var $_h;

    function set($k, $v)
    {
        $this->_h[$k] = $v;
    }

    function get($k)
    {
        return isset($this->_h[$k]) ? $this->_h[$k] : null;
    }

}
