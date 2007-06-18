<?php

define('SERIALIZE_UNKNOWN', -1);
define('SERIALIZE_NONE', 0);
define('SERIALIZE_WDDX', 1);
define('SERIALIZE_BZIP', 2);
define('SERIALIZE_IMAP8', 3);
define('SERIALIZE_IMAPUTF7', 4);
define('SERIALIZE_IMAPUTF8', 5);
define('SERIALIZE_BASIC', 6);
define('SERIALIZE_GZ_DEFLATE', 7);
define('SERIALIZE_GZ_COMPRESS', 8);
define('SERIALIZE_GZ_ENCOD', 9);
define('SERIALIZE_BASE64', 10);
define('SERIALIZE_SQLXML', 11);
define('SERIALIZE_RAW', 12);
define('SERIALIZE_URL', 13);
define('SERIALIZE_UTF7', 14);

/** Use SERIALIZE_UTF7 and SERIALIZE_BASIC stacked.  */
define('SERIALIZE_UTF7_BASIC', 15);


/* Specific default values */
/* BZIP */
/** Define the block size (1-9). */
define('SERIALIZE_BZIP_BLOCK', 9);

/** Work factor - not used. */
define('SERIALIZE_BZIP_FACTOR', 30);

/** Try to minimize memory use. */
define('SERIALIZE_BZIP_SMALLMEM', false);

/* Gzip */
/** Level of compression - deflate (1-9). */
define('SERIALIZE_GZ_DEFLATE_LEVEL', 9);

/** Max length of the uncompressed string (in bytes). */
define('SERIALIZE_GZ_DEFLATE_LENGTH', 2048);

/** Level of compression - compress (1-9). */
define('SERIALIZE_GZ_COMPRESS_LEVEL', 9);

/** Max length of the uncompressed string. */
define('SERIALIZE_GZ_COMPRESS_LENGTH', 2048);

/** Level of compression - Encode (1-9). */
define('SERIALIZE_GZ_ENCOD_LEVEL', 9);

/**
 * The Serialize:: class provides various methods of encapsulating data.
 *
 * $Horde: framework/Serialize/Serialize.php,v 1.25 2004/04/07 14:43:13 chuck Exp $
 *
 * Copyright 2001-2004 Stephane Huther <shuther@bigfoot.com>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stephane Huther <shuther@bigfoot.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.0
 * @package Horde_Serialize
 */
class Horde_Serialize {

    /**
     * Serialize a value.
     * See the list of constants at the top of the file for the serializing
     * techniques that can be used.
     *
     * @access public
     *
     * @param mixed $data             The data to be serialized.
     * @param optional mixed $mode    The mode of serialization. Can be
     *                                either a single mode or array of modes.
     *                                If array, will be serialized in the
     *                                order provided.
     * @param optional mixed $params  Any additional parameters the
     *                                serialization method requires.
     *
     * @return string  The serialized data.
     *                 Returns PEAR_Error on error.
     */
    function serialize($data, $mode = array(SERIALIZE_BASIC), $params = null)
    {
        if (!is_array($mode)) {
            $mode = array($mode);
        }

        /* Return now if no data. */
        if (empty($data) && !is_array($data)) {
            return $data;
        }

        /* Parse through the list of serializing modes. */
        foreach ($mode as $val) {
            /* Check to make sure the mode is supported. */
            if (!Horde_Serialize::hasCapability($val)) {
                return PEAR::raiseError('Unsupported serialization type');
            }
            Horde_Serialize::_serialize($data, $val, $params);
            if (is_a($data, 'PEAR_Error')) {
                break;
            }
        }

        return $data;
    }

    /**
     * Serialize data.
     *
     * @access private
     *
     * @param mixed &$data            The data to be serialized.
     * @param mixed $mode             The mode of serialization. Can be
     *                                either a single mode or array of modes.
     *                                If array, will be serialized in the
     *                                order provided.
     * @param optional mixed $params  Any additional parameters the
     *                                serialization method requires.
     */
    function _serialize(&$data, $mode, $params = null)
    {
        switch ($mode) {
        case SERIALIZE_NONE:
            break;

        case SERIALIZE_BZIP:
            $data = bzcompress($data, SERIALIZE_BZIP_BLOCK, SERIALIZE_BZIP_FACTOR);
            break;

        case SERIALIZE_WDDX:
            $data = wddx_serialize_value($data);
            break;

        case SERIALIZE_IMAP8:
            $data = imap_8bit($data);
            break;

        case SERIALIZE_IMAPUTF7:
            $data = imap_utf7_encode($data);
            break;

        case SERIALIZE_IMAPUTF8:
            $data = imap_utf8($data);
            break;

        case SERIALIZE_GZ_DEFLATE:
            $data = gzdeflate($data, SERIALIZE_GZ_DEFLATE_LEVEL);
            break;

        case SERIALIZE_BASIC:
            $data = serialize($data);
            break;

        case SERIALIZE_GZ_COMPRESS:
            $data = gzcompress($data, SERIALIZE_GZ_COMPRESS_LEVEL);
            break;

        case SERIALIZE_BASE64:
            $data = base64_encode($data);
            break;

        case SERIALIZE_GZ_ENCOD:
            $data = gzencode($data, SERIALIZE_GZ_ENCOD_LEVEL);
            break;

        case SERIALIZE_RAW:
            $data = rawurlencode($data);
            break;

        case SERIALIZE_URL:
            $data = urlencode($data);
            break;

        case SERIALIZE_SQLXML:
            require_once 'DB.php';
            require_once 'XML/sql2xml.php';
            $sql2xml = &new xml_sql2xml();
            $data = $sql2xml->getXML($data);
            break;

        case SERIALIZE_UTF7:
            require_once 'Horde/String.php';
            $data = String::convertCharset($data, $params, 'utf-7');
            break;

        case SERIALIZE_UTF7_BASIC:
            Horde_Serialize::_serialize($data, SERIALIZE_UTF7, $params);
            Horde_Serialize::_serialize($data, SERIALIZE_BASIC, $params);
            break;
        }
    }

    /**
     * Unserialize a value.
     * See the list of constants at the top of the file for the serializing
     * techniques that can be used.
     *
     * @access public
     *
     * @param mixed $data             The data to be unserialized.
     * @param optional mixed $mode    The mode of unserialization. Can be
     *                                either a single mode or array of modes.
     *                                If array, will be unserialized in the
     *                                order provided.
     * @param optional mixed $params  Any additional parameters the
     *                                unserialization method requires.
     *
     * @return string  The unserialized data.
     *                 Returns PEAR_Error on error.
     */
    function unserialize($data, $mode = SERIALIZE_BASIC, $params = null)
    {
        if (!is_array($mode)) {
            $mode = array($mode);
        }

        /* Return now if no data. */
        if (empty($data)) {
            return $data;
        }

        /* Parse through the list of unserializing modes. */
        foreach ($mode as $val) {
            /* Check to make sure the mode is supported. */
            if (!Horde_Serialize::hasCapability($val)) {
                return PEAR::raiseError('Unsupported unserialization type');
            }
            Horde_Serialize::_unserialize($data, $val, $params);
            if (is_a($data, 'PEAR_Error')) {
                break;
            }
        }

        return $data;
    }

    /**
     * Unserialize data.
     *
     * @access private
     *
     * @param mixed &$data            The data to be unserialized.
     * @param mixed $mode             The mode of unserialization. Can be
     *                                either a single mode or array of modes.
     *                                If array, will be unserialized in the
     *                                order provided.
     * @param optional mixed $params  Any additional parameters the
     *                                unserialization method requires.
     */
    function _unserialize(&$data, $mode, $params = null)
    {
        switch ($mode) {
        case SERIALIZE_NONE:
        case SERIALIZE_SQLXML:
            break;

        case SERIALIZE_RAW:
            $data = rawurldecode($data);
            break;

        case SERIALIZE_URL:
            $data = urldecode($data);
            break;

        case SERIALIZE_WDDX:
            $data = wddx_deserialize($data);
            break;

        case SERIALIZE_BZIP:
            $data = bzdecompress($data, SERIALIZE_BZIP_SMALLMEM);
            break;

        case SERIALIZE_IMAPUTF7:
            $data = imap_utf7_decode($data);
            break;

        case SERIALIZE_BASIC:
            $data = @unserialize($data);
            break;

        case SERIALIZE_GZ_DEFLATE:
            $data = gzinflate($data, SERIALIZE_GZ_DEFLATE_LENGTH);
            break;

        case SERIALIZE_BASE64:
            $data = base64_decode($data);
            break;

        case SERIALIZE_GZ_COMPRESS:
            $data = gzuncompress($data, SERIALIZE_GZ_COMPRESS_LENGTH);
            break;

        case SERIALIZE_UTF7:
            require_once 'Horde/String.php';
            $data = String::convertCharset($data, 'utf-7', $params);
            break;

        case SERIALIZE_UTF7_BASIC:
            Horde_Serialize::_unserialize($data, SERIALIZE_BASIC, $params);
            Horde_Serialize::_unserialize($data, SERIALIZE_UTF7, $params);
            break;
        }
    }

    /**
     * Check whether or not a serialization method is supported.
     *
     * @access public
     *
     * @param integer $mode  The serialization method.
     *
     * @return boolean  True if supported, false if not.
     */
    function hasCapability($mode)
    {
        switch ($mode) {
        case SERIALIZE_BZIP:
            return Util::extensionExists('bz2');

        case SERIALIZE_WDDX:
            return Util::extensionExists('wddx');

        case SERIALIZE_IMAPUTF7:
        case SERIALIZE_IMAPUTF8:
        case SERIALIZE_IMAP8:
            return Util::extensionExists('imap');

        case SERIALIZE_GZ_DEFLATE:
        case SERIALIZE_GZ_COMPRESS:
        case SERIALIZE_GZ_ENCOD:
            return Util::extensionExists('zlib');

        case SERIALIZE_NONE:
        case SERIALIZE_BASIC:
        case SERIALIZE_BASE64:
        case SERIALIZE_SQLXML:
        case SERIALIZE_RAW:
        case SERIALIZE_URL:
        case SERIALIZE_UTF7:
        case SERIALIZE_UTF7_BASIC:
            return true;

        default:
            return false;
        }
    }

}
