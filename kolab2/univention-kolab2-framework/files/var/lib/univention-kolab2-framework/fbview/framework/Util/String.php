<?php

$GLOBALS['_HORDE_STRING_CHARSET'] = 'iso-8859-1';

/**
 * The String:: class provides static methods for charset and locale safe 
 * string manipulation.
 *
 * $Horde: framework/Util/String.php,v 1.33 2004/05/04 11:17:42 jan Exp $
 *
 * Copyright 2003-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Util
 */
class String {

    /**
     * Sets a default charset that the String:: methods will use if none is
     * explicitely specified.
     *
     * @param string $charset  The charset to use as the default one.
     */
    function setDefaultCharset($charset)
    {
        $GLOBALS['_HORDE_STRING_CHARSET'] = $charset;
    }

    /**
     * Converts a string from one charset to another.
     *
     * Works only if either the iconv or the mbstring extension
     * are present and best if both are available.
     * The original string is returned if conversion failed or none
     * of the extensions were available.
     *
     * @param mixed $input  The data to be converted. If $input is an an
     *                      array, the array's values get converted recursively.
     * @param string $from  The string's current charset.
     * @param string $to    (optional) The charset to convert the string to. If
     *                      not specified, the global variable
     *                      $_HORDE_STRING_CHARSET will be used.
     *
     * @return string  The converted string.
     */
    function convertCharset($input, $from, $to = null)
    {
        if (is_array($input)) {
            $tmp = array();
            foreach ($input as $key => $val) {
                $tmp[String::convertCharset($key, $from, $to)] = String::convertCharset($val, $from, $to);
            }
            return $tmp;
        }
        if (is_object($input)) {
            $vars = get_object_vars($input);
            foreach ($vars as $key => $val) {
                $input->$key = String::convertCharset($val, $from, $to);
            }
            return $input;
        }

        if (!is_string($input)) {
            return $input;
        }

        $output = false;

        /* Get the user's default character set if none passed in. */
        if (is_null($to)) {
            $to = $GLOBALS['_HORDE_STRING_CHARSET'];
        }

        /* If the from and to chaacter sets are identical, return now. */
        $str_from = String::lower($from);
        $str_to = String::lower($to);
        if ($str_from == $str_to) {
            return $input;
        }

        /* Use utf8_[en|de]code() if possible. */
        $str_from_check = (($str_from == 'iso-8859-1') || ($str_from == 'us-ascii'));
        if ($str_from_check && ($str_to == 'utf-8')) {
            return utf8_encode($input);
        }

        $str_to_check = (($str_to == 'iso-8859-1') || ($str_to == 'us-ascii'));
        if (($str_from == 'utf-8') && $str_to_check) {
            return utf8_decode($input);
        }

        /* First try iconv with transliteration. */
        if ($str_from != 'utf7-imap' && 
            $str_to != 'utf7-imap' && 
            Util::extensionExists('iconv')) {
            ini_set('track_errors', 1);
            /* We need to tack an extra character temporarily
               because of a bug in iconv() if the last character
               is not a 7 bit ASCII character. */
            $output = @iconv($from, $to . '//TRANSLIT', $input . 'x');
            if (isset($php_errormsg)) {
                $output = false;
            } else {
                $output = String::substr($output, 0, -1, $to);
            }
            ini_restore('track_errors');
        }

        /* Next try mbstring. */
        if (!$output && Util::extensionExists('mbstring')) {
            $output = @mb_convert_encoding($input, $to, $from);
        }

        /* At last try imap_utf7_[en|de]code if appropriate. */
        if (!$output && Util::extensionExists('imap')) {
            if ($str_from_check && ($str_to == 'utf7-imap')) {
                return @imap_utf7_encode($input);
            }
            if (($str_from == 'utf7-imap') && $str_to_check) {
                return @imap_utf7_decode($input);
            }
        }

        return (!$output) ? $input : $output;
    }

    /**
     * Makes a string lowercase.
     *
     * @param string $string  The string to be converted.
     * @param bool $locale    (optional) If true the string will be converted
     *                        based on a given charset, locale independent else.
     * @param string $charset (optional) If $locale is true, the charset to use 
     *                        when converting. If not provided the current
     *                        charset.
     *
     * @return string         The string with lowercase characters
     */
    function lower($string, $locale = false, $charset = null)
    {
        static $lowers;

        if ($locale) {
            /* The existence of mb_strtolower() depends on the platform. */
            if (Util::extensionExists('mbstring') &&
                function_exists('mb_strtolower')) {
                if (is_null($charset)) {
                    $charset = $GLOBALS['_HORDE_STRING_CHARSET'];
                }
                $ret = @mb_strtolower($string, $charset);
                if (!empty($ret)) {
                    return $ret;
                }
            }
            return strtolower($string);
        }

        if (!isset($lowers)) {
            $lowers = array();
        }
        if (!isset($lowers[$string])) {
            $language = setlocale(LC_CTYPE, 0);
            setlocale(LC_CTYPE, 'en');
            $lowers[$string] = strtolower($string);
            setlocale(LC_CTYPE, $language);
        }

        return $lowers[$string];
    }

    /**
     * Makes a string uppercase.
     *
     * @param string $string  The string to be converted.
     * @param bool $locale    (optional) If true the string will be converted 
     *                        based on a given charset, locale independent else.
     * @param string $charset (optional) If $locale is true, the charset to use 
     *                        when converting. If not provided the current 
     *                        charset.
     *
     * @return string         The string with uppercase characters
     */
    function upper($string, $locale = false, $charset = null)
    {
        static $uppers;

        if ($locale) {
            /* The existence of mb_strtoupper() depends on the platform. */
            if (Util::extensionExists('mbstring') &&
                function_exists('mb_strtoupper')) {
                if (is_null($charset)) {
                    $charset = $GLOBALS['_HORDE_STRING_CHARSET'];
                }
                $ret = @mb_strtoupper($string, $charset);
                if (!empty($ret)) {
                    return $ret;
                }
            }
            return strtoupper($string);
        }

        if (!isset($uppers)) {
            $uppers = array();
        }
        if (!isset($uppers[$string])) {
            $language = setlocale(LC_CTYPE, 0);
            setlocale(LC_CTYPE, 'en');
            $uppers[$string] = strtoupper($string);
            setlocale(LC_CTYPE, $language);
        }

        return $uppers[$string];
    }

    /**
     * Returns part of a string.
     *
     * @param string $string  The string to be converted.
     * @param int $start      The part's start position, zero based.
     * @param int $length     (optional) The part's length.
     * @param string $charset (optional) The charset to use when calculating 
     *                        the part's position and length, defaults to 
     *                        current charset.
     *
     * @return string         The string's part.
     */
    function substr($string, $start, $length = null, $charset = null)
    {
        if (Util::extensionExists('mbstring')) {
            if (is_null($charset)) {
                $charset = $GLOBALS['_HORDE_STRING_CHARSET'];
            }
            if (is_null($length)) {
                $length = String::length($string, $charset);
            }
            $ret = @mb_substr($string, $start, $length, $charset);
            if (!empty($ret)) {
                return $ret;
            }
        }
        if (is_null($length)) {
            $length = String::length($string);
        }
        return substr($string, $start, $length);
    }

    /**
     * Returns the character (not byte) length of a string.
     *
     * @param string $string  The string to return the length of.
     * @param string $charset (optional) The charset to use when calculating
     *                        the string's length.
     *
     * @return string         The string's part.
     */
    function length($string, $charset = null)
    {
        if (Util::extensionExists('mbstring')) {
            if (is_null($charset)) {
                $charset = $GLOBALS['_HORDE_STRING_CHARSET'];
            }
            $ret = @mb_strlen($string, $charset);
            if (!empty($ret)) {
                return $ret;
            }
        }
        return strlen($string);
    }

    /**
     * Returns the numeric position of the first occurrence of $needle in
     * the $haystack string.
     *
     * @param string $haystack  The string to search through.
     * @param string $needle    The string to search for.
     * @param int $offset       (optional) Allows to specify which character in 
     *                          haystack to start searching.
     * @param string $charset   (optional) The charset to use when searching 
     *                          for the $needle string.
     *
     * @return int              The position of first occurrence.
     */
    function pos($haystack, $needle, $offset = 0, $charset = null)
    {
        if (Util::extensionExists('mbstring')) {
            if (is_null($charset)) {
                $charset = $GLOBALS['_HORDE_STRING_CHARSET'];
            }
            ini_set('track_errors', 1);
            $ret = @mb_strpos($haystack, $needle, $offset, $charset);
            ini_restore('track_errors');
            if (!isset($php_errormsg)) {
                return $ret;
            }
        }
        return strpos($haystack, $needle, $offset);
    }

    function isAlpha($string, $charset = null)
    {
        return ctype_alpha($string);
    }

    /**
     * Returns true if every character in the parameter is a lowercase
     * letter in the current locale.
     *
     * @param $string   The string to test.
     * @param $charset  (optional) The charset to use when testing the string.
     *
     * @return bool     True if the parameter was lowercase.
     */
    function isLower($string, $charset = null)
    {
        return ((String::lower($string, true, $charset) === $string) &&
                String::isAlpha($string, $charset));
    }

    /**
     * Returns true if every character in the parameter is an uppercase
     * letter in the current locale.
     *
     * @param string $string   The string to test.
     * @param string $charset  (optional) The charset to use when testing the string.
     *
     * @return boolean  True if the parameter was uppercase.
     */
    function isUpper($string, $charset = null)
    {
        return ((String::upper($string, true, $charset) === $string) &&
                String::isAlpha($string, $charset));
    }

}
