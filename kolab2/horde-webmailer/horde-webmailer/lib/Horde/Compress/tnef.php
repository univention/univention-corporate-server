<?php

define('TNEF_SIGNATURE',      0x223e9f78);
define('TNEF_LVL_MESSAGE',    0x01);
define('TNEF_LVL_ATTACHMENT', 0x02);

define('TNEF_STRING', 0x00010000);
define('TNEF_BYTE',   0x00060000);
define('TNEF_WORD',   0x00070000);
define('TNEF_DWORD',  0x00080000);

define('TNEF_ASUBJECT',   TNEF_DWORD  | 0x8004);
define('TNEF_AMCLASS',    TNEF_WORD   | 0x8008);
define('TNEF_ATTACHDATA', TNEF_BYTE   | 0x800f);
define('TNEF_AFILENAME',  TNEF_STRING | 0x8010);
define('TNEF_ARENDDATA',  TNEF_BYTE   | 0x9002);
define('TNEF_AMAPIATTRS', TNEF_BYTE   | 0x9005);
define('TNEF_AVERSION',   TNEF_DWORD  | 0x9006);

define('TNEF_MAPI_NULL',           0x0001);
define('TNEF_MAPI_SHORT',          0x0002);
define('TNEF_MAPI_INT',            0x0003);
define('TNEF_MAPI_FLOAT',          0x0004);
define('TNEF_MAPI_DOUBLE',         0x0005);
define('TNEF_MAPI_CURRENCY',       0x0006);
define('TNEF_MAPI_APPTIME',        0x0007);
define('TNEF_MAPI_ERROR',          0x000a);
define('TNEF_MAPI_BOOLEAN',        0x000b);
define('TNEF_MAPI_OBJECT',         0x000d);
define('TNEF_MAPI_INT8BYTE',       0x0014);
define('TNEF_MAPI_STRING',         0x001e);
define('TNEF_MAPI_UNICODE_STRING', 0x001f);
define('TNEF_MAPI_SYSTIME',        0x0040);
define('TNEF_MAPI_CLSID',          0x0048);
define('TNEF_MAPI_BINARY',         0x0102);

define('TNEF_MAPI_ATTACH_LONG_FILENAME', 0x3707);
define('TNEF_MAPI_ATTACH_MIME_TAG',      0x370E);

define('TNEF_MAPI_NAMED_TYPE_ID',     0x0000);
define('TNEF_MAPI_NAMED_TYPE_STRING', 0x0001);
define('TNEF_MAPI_MV_FLAG',           0x1000);

/**
 * The Horde_Compress_tnef class allows MS-TNEF data to be displayed.
 *
 * The TNEF rendering is based on code by:
 *   Graham Norbury <gnorbury@bondcar.com>
 * Original design by:
 *   Thomas Boll <tb@boll.ch>, Mark Simpson <damned@world.std.com>
 *
 * $Horde: framework/Compress/Compress/tnef.php,v 1.6.12.13 2009-01-06 15:22:59 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_Compress
 */
class Horde_Compress_tnef extends Horde_Compress {

    /**
     * Decompress the data.
     *
     * @param string $data   The data to decompress.
     * @param array $params  An array of arguments needed to decompress the
     *                       data.
     *
     * @return mixed  The decompressed data.
     *                Returns a PEAR_Error object on error.
     */
    function decompress($data, $params = array())
    {
        $out = array();

        if ($this->_geti($data, 32) == TNEF_SIGNATURE) {
            $this->_geti($data, 16);

            while (strlen($data) > 0) {
                switch ($this->_geti($data, 8)) {
                case TNEF_LVL_MESSAGE:
                    $this->_decodeMessage($data);
                    break;

                case TNEF_LVL_ATTACHMENT:
                    $this->_decodeAttachment($data, $out);
                    break;
                }
            }
        }

        return array_reverse($out);
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string &$data  The data string.
     * @param integer $bits  How many bits to retrieve.
     *
     * @return TODO
     */
    function _getx(&$data, $bits)
    {
        $value = null;

        if (strlen($data) >= $bits) {
            $value = substr($data, 0, $bits);
            $data = substr_replace($data, '', 0, $bits);
        }

        return $value;
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string &$data  The data string.
     * @param integer $bits  How many bits to retrieve.
     *
     * @return TODO
     */
    function _geti(&$data, $bits)
    {
        $bytes = $bits / 8;
        $value = null;

        if (strlen($data) >= $bytes) {
            $value = ord($data[0]);
            if ($bytes >= 2) {
                $value += (ord($data[1]) << 8);
            }
            if ($bytes >= 4) {
                $value += (ord($data[2]) << 16) + (ord($data[3]) << 24);
            }
            $data = substr_replace($data, '', 0, $bytes);
        }

        return $value;
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string &$data      The data string.
     * @param string $attribute  TODO
     */
    function _decodeAttribute(&$data, $attribute)
    {
        /* Data. */
        $this->_getx($data, $this->_geti($data, 32));

        /* Checksum. */
        $this->_geti($data, 16);
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string $data             The data string.
     * @param array &$attachment_data  TODO
     */
    function _extractMapiAttributes($data, &$attachment_data)
    {
        /* Number of attributes. */
        $number = $this->_geti($data, 32);

        while ((strlen($data) > 0) && $number--) {
            $have_mval = false;
            $num_mval = 1;
            $named_id = $value = null;
            $attr_type = $this->_geti($data, 16);
            $attr_name = $this->_geti($data, 16);

            if (($attr_type & TNEF_MAPI_MV_FLAG) != 0) {
                $have_mval = true;
                $attr_type = $attr_type & ~TNEF_MAPI_MV_FLAG;
            }

            if (($attr_name >= 0x8000) && ($attr_name < 0xFFFE)) {
                $this->_getx($data, 16);
                $named_type = $this->_geti($data, 32);

                switch ($named_type) {
                case TNEF_MAPI_NAMED_TYPE_ID:
                    $named_id = $this->_geti($data, 32);
                    $attr_name = $named_id;
                    break;

                case TNEF_MAPI_NAMED_TYPE_STRING:
                    $attr_name = 0x9999;
                    $idlen = $this->_geti($data, 32);
                    $datalen = $idlen + ((4 - ($idlen % 4)) % 4);
                    $named_id = substr($this->_getx($data, $datalen), 0, $idlen);
                    break;
                }
            }

            if ($have_mval) {
                $num_mval = $this->_geti($data, 32);
            }

            switch ($attr_type) {
            case TNEF_MAPI_SHORT:
                $value = $this->_geti($data, 16);
                break;

            case TNEF_MAPI_INT:
            case TNEF_MAPI_BOOLEAN:
                for ($i = 0; $i < $num_mval; $i++) {
                    $value = $this->_geti($data, 32);
                }
                break;

            case TNEF_MAPI_FLOAT:
            case TNEF_MAPI_ERROR:
                $value = $this->_getx($data, 4);
                break;

            case TNEF_MAPI_DOUBLE:
            case TNEF_MAPI_APPTIME:
            case TNEF_MAPI_CURRENCY:
            case TNEF_MAPI_INT8BYTE:
            case TNEF_MAPI_SYSTIME:
                $value = $this->_getx($data, 8);
                break;

            case TNEF_MAPI_STRING:
            case TNEF_MAPI_UNICODE_STRING:
            case TNEF_MAPI_BINARY:
            case TNEF_MAPI_OBJECT:
                $num_vals = ($have_mval) ? $num_mval : $this->_geti($data, 32);
                for ($i = 0; $i < $num_vals; $i++) {
                    $length = $this->_geti($data, 32);

                    /* Pad to next 4 byte boundary. */
                    $datalen = $length + ((4 - ($length % 4)) % 4);

                    if ($attr_type == TNEF_MAPI_STRING) {
                        $length -= 1;
                    }

                    /* Read and truncate to length. */
                    $value = substr($this->_getx($data, $datalen), 0, $length);
                }
                break;
            }

            /* Store any interesting attributes. */
            switch ($attr_name) {
            case TNEF_MAPI_ATTACH_LONG_FILENAME:
                /* Used in preference to AFILENAME value. */
                $attachment_data[0]['name'] = preg_replace('/.*[\/](.*)$/', '\1', $value);
                $attachment_data[0]['name'] = str_replace("\0", '', $attachment_data[0]['name']);
                break;

            case TNEF_MAPI_ATTACH_MIME_TAG:
                /* Is this ever set, and what is format? */
                $attachment_data[0]['type'] = preg_replace('/^(.*)\/.*/', '\1', $value);
                $attachment_data[0]['subtype'] = preg_replace('/.*\/(.*)$/', '\1', $value);
                $attachment_data[0]['subtype'] = str_replace("\0", '', $attachment_data[0]['subtype']);
                break;
            }
        }
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string &$data  The data string.
     */
    function _decodeMessage(&$data)
    {
        $this->_decodeAttribute($data, $this->_geti($data, 32));
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string &$data            The data string.
     * @param array &$attachment_data  TODO
     */
    function _decodeAttachment(&$data, &$attachment_data)
    {
        $attribute = $this->_geti($data, 32);

        switch ($attribute) {
        case TNEF_ARENDDATA:
            /* Marks start of new attachment. */
            $this->_getx($data, $this->_geti($data, 32));

            /* Checksum */
            $this->_geti($data, 16);

            /* Add a new default data block to hold details of this
               attachment. Reverse order is easier to handle later! */
            array_unshift($attachment_data, array('type'    => 'application',
                                                  'subtype' => 'octet-stream',
                                                  'name'    => 'unknown',
                                                  'stream'  => ''));
            break;

        case TNEF_AFILENAME:
            /* Strip path. */
            $attachment_data[0]['name'] = preg_replace('/.*[\/](.*)$/', '\1', $this->_getx($data, $this->_geti($data, 32)));
            $attachment_data[0]['name'] = str_replace("\0", '', $attachment_data[0]['name']);

            /* Checksum */
            $this->_geti($data, 16);
            break;

        case TNEF_ATTACHDATA:
            /* The attachment itself. */
            $length = $this->_geti($data, 32);
            $attachment_data[0]['size'] = $length;
            $attachment_data[0]['stream'] = $this->_getx($data, $length);

            /* Checksum */
            $this->_geti($data, 16);
            break;

        case TNEF_AMAPIATTRS:
            $length = $this->_geti($data, 32);
            $value = $this->_getx($data, $length);

            /* Checksum */
            $this->_geti($data, 16);
            $this->_extractMapiAttributes($value, $attachment_data);
            break;

        default:
            $this->_decodeAttribute($data, $attribute);
        }
    }

}
