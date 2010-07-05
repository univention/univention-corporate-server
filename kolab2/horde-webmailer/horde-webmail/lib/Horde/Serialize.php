<?php

/**
 * We rely on the Horde Util:: package.
 */
require_once 'Horde/Util.php';

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
define('SERIALIZE_UTF7_BASIC', 15);
define('SERIALIZE_JSON', 16);
define('SERIALIZE_LZF', 17);

/**
 * The Serialize:: class provides various methods of encapsulating data.
 *
 * $Horde: framework/Serialize/Serialize.php,v 1.25.10.16 2009-01-06 15:23:34 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stephane Huther <shuther1@free.fr>
 * @since   Horde 2.0
 * @package Horde_Serialize
 */
class Horde_Serialize {

    /**
     * Serialize a value.
     *
     * See the list of constants at the top of the file for the serializing
     * techniques that can be used.
     *
     * @static
     *
     * @param mixed $data    The data to be serialized.
     * @param mixed $mode    The mode of serialization. Can be either a single
     *                       mode or array of modes.  If array, will be
     *                       serialized in the order provided.
     * @param mixed $params  Any additional parameters the serialization method
     *                       requires.
     *
     * @return string  The serialized data.
     *                 Returns PEAR_Error on error.
     */
    function serialize($data, $mode = array(SERIALIZE_BASIC), $params = null)
    {
        if (!is_array($mode)) {
            $mode = array($mode);
        }

        /* Parse through the list of serializing modes. */
        foreach ($mode as $val) {
            /* Check to make sure the mode is supported. */
            if (!Horde_Serialize::hasCapability($val)) {
                return PEAR::raiseError('Unsupported serialization type');
            }
            $data = Horde_Serialize::_serialize($data, $val, $params);
            if (is_a($data, 'PEAR_Error')) {
                break;
            }
        }

        return $data;
    }

    /**
     * Unserialize a value.
     *
     * See the list of constants at the top of the file for the serializing
     * techniques that can be used.
     *
     * @param mixed $data    The data to be unserialized.
     * @param mixed $mode    The mode of unserialization.  Can be either a
     *                       single mode or array of modes.  If array, will be
     *                       unserialized in the order provided.
     * @param mixed $params  Any additional parameters the unserialization
     *                       method requires.
     *
     * @return string  The unserialized data.
     *                 Returns PEAR_Error on error.
     */
    function unserialize($data, $mode = SERIALIZE_BASIC, $params = null)
    {
        if (!is_array($mode)) {
            $mode = array($mode);
        }

        /* Parse through the list of unserializing modes. */
        foreach ($mode as $val) {
            /* Check to make sure the mode is supported. */
            if (!Horde_Serialize::hasCapability($val)) {
                return PEAR::raiseError('Unsupported unserialization type');
            }
            $data = Horde_Serialize::_unserialize($data, $val, $params);
            if (is_a($data, 'PEAR_Error')) {
                break;
            }
        }

        return $data;
    }

    /**
     * Check whether or not a serialization method is supported.
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

        case SERIALIZE_SQLXML:
            return @include_once 'XML/sql2xml.php';

        case SERIALIZE_LZF:
            return Util::extensionExists('lzf');

        case SERIALIZE_NONE:
        case SERIALIZE_BASIC:
        case SERIALIZE_BASE64:
        case SERIALIZE_RAW:
        case SERIALIZE_URL:
        case SERIALIZE_UTF7:
        case SERIALIZE_UTF7_BASIC:
        case SERIALIZE_JSON:
            return true;

        default:
            return false;
        }
    }

    /**
     * Serialize data.
     *
     * @access private
     *
     * @param mixed $data    The data to be serialized.
     * @param mixed $mode    The mode of serialization. Can be
     *                       either a single mode or array of modes.
     *                       If array, will be serialized in the
     *                       order provided.
     * @param mixed $params  Any additional parameters the serialization method
     *                       requires.
     *
     * @return string  A serialized string or PEAR_Error on error.
     */
    function _serialize($data, $mode, $params = null)
    {
        switch ($mode) {
        case SERIALIZE_NONE:
            break;

        // $params['level'] = Level of compression (default: 3)
        // $params['workfactor'] = How does compression phase behave when given
        //                         worst case, highly repetitive, input data
        //                         (default: 30)
        case SERIALIZE_BZIP:
            $data = bzcompress($data, isset($params['level']) ? $params['level'] : 3, isset($params['workfactor']) ? $params['workfactor'] : 30);
            if (is_integer($data)) {
                $data = false;
            }
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

        // $params['level'] = Level of compression (default: 3)
        case SERIALIZE_GZ_DEFLATE:
            $data = gzdeflate($data, isset($params['level']) ? $params['level'] : 3);
            break;

        case SERIALIZE_BASIC:
            $data = serialize($data);
            break;

        // $params['level'] = Level of compression (default: 3)
        case SERIALIZE_GZ_COMPRESS:
            $data = gzcompress($data, isset($params['level']) ? $params['level'] : 3);
            break;

        case SERIALIZE_BASE64:
            $data = base64_encode($data);
            break;

        // $params['level'] = Level of compression (default: 3)
        case SERIALIZE_GZ_ENCOD:
            $data = gzencode($data, isset($params['level']) ? $params['level'] : 3);
            break;

        case SERIALIZE_RAW:
            $data = rawurlencode($data);
            break;

        case SERIALIZE_URL:
            $data = urlencode($data);
            break;

        case SERIALIZE_SQLXML:
            require_once 'DB.php';
            $sql2xml = &new xml_sql2xml();
            $data = $sql2xml->getXML($data);
            break;

        // $params = Source character set
        case SERIALIZE_UTF7:
            require_once 'Horde/String.php';
            $data = String::convertCharset($data, $params, 'utf-7');
            break;

        // $params = Source character set
        case SERIALIZE_UTF7_BASIC:
            $data = Horde_Serialize::serialize($data, array(SERIALIZE_UTF7, SERIALIZE_BASIC), $params);
            break;

        // $params = Source character set
        case SERIALIZE_JSON:
            require_once 'Horde/String.php';
            if (!empty($params)) {
                $data = String::convertCharset($data, $params, 'utf-8');
            }
            if (Util::extensionExists('json')) {
                $data = json_encode($data);
            } else {
                require_once 'Horde/Serialize/JSON.php';
                $data = Horde_Serialize_JSON::encode($data);
            }
            break;

        case SERIALIZE_LZF:
            $data = lzf_compress($data);
            break;
        }

        if ($data === false) {
            return PEAR::raiseError('Serialization failed.');
        }
        return $data;
    }

    /**
     * Unserialize data.
     *
     * @access private
     *
     * @param mixed $data    The data to be unserialized.
     * @param mixed $mode    The mode of unserialization. Can be either a
     *                       single mode or array of modes.  If array, will be
     *                       unserialized in the order provided.
     * @param mixed $params  Any additional parameters the unserialization
     *                       method requires.
     *
     * @return mixed  Unserialized data on success or PEAR_Error on error.
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
            // $params['small'] = Use bzip2 'small memory' mode?
            $data = bzdecompress($data, isset($params['small']) ? $params['small'] : false);
            break;

        case SERIALIZE_IMAPUTF7:
            $data = imap_utf7_decode($data);
            break;

        case SERIALIZE_BASIC:
            $data2 = @unserialize($data);
            // Unserialize can return false both on error and if $data is the
            // false value.
            if (($data2 === false) && ($data == serialize(false))) {
                return $data2;
            }
            $data = $data2;
            break;

        case SERIALIZE_GZ_DEFLATE:
            $data = gzinflate($data);
            break;

        case SERIALIZE_BASE64:
            $data = base64_decode($data);
            break;

        case SERIALIZE_GZ_COMPRESS:
            $data = gzuncompress($data);
            break;

        // $params = Output character set
        case SERIALIZE_UTF7:
            require_once 'Horde/String.php';
            $data = String::convertCharset($data, 'utf-7', $params);
            break;

        // $params = Output character set
        case SERIALIZE_UTF7_BASIC:
            $data = Horde_Serialize::unserialize($data, array(SERIALIZE_BASIC, SERIALIZE_UTF7), $params);
            break;

        case SERIALIZE_JSON:
            if (Util::extensionExists('json')) {
                $data = json_decode($data);
            } else {
                require_once 'Horde/Serialize/JSON.php';
                $data = Horde_Serialize_JSON::decode($data);
            }
            break;

        case SERIALIZE_LZF:
            $data = @lzf_decompress($data);
            break;
        }

        if ($data === false) {
            return PEAR::raiseError('Unserialization failed.');
        }
        return $data;
    }

}
