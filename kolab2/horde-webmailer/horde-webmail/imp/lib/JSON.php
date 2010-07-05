<?php
/**
 * Converts to and from JSON format.
 *
 * JSON (JavaScript Object Notation) is a lightweight data-interchange
 * format. It is easy for humans to read and write. It is easy for
 * machines to parse and generate. It is based on a subset of the
 * JavaScript Programming Language, Standard ECMA-262 3rd Edition -
 * December 1999.  This feature can also be found in Python. JSON is a
 * text format that is completely language independent but uses
 * conventions that are familiar to programmers of the C-family of
 * languages. These properties make JSON an ideal data-interchange
 * language.
 *
 * This package provides a simple encoder and decoder for JSON notation. It
 * is intended for use with client-side Javascript applications that make
 * use of HTTPRequest to perform server communication functions - data can
 * be encoded into JSON notation for use in a client-side javascript, or
 * decoded from incoming Javascript requests. JSON format is native to
 * Javascript, and can be directly eval()'ed with no further parsing
 * overhead
 *
 * All strings should be in ASCII or UTF-8 format.
 *
 * PHP versions 4 and 5
 *
 * LICENSE: Redistribution and use in source and binary forms, with or
 * without modification, are permitted provided that the following
 * conditions are met: Redistributions of source code must retain the
 * above copyright notice, this list of conditions and the following
 * disclaimer. Redistributions in binary form must reproduce the above
 * copyright notice, this list of conditions and the following disclaimer
 * in the documentation and/or other materials provided with the
 * distribution.
 *
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN
 * NO EVENT SHALL CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
 * TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
 * USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
 * DAMAGE.
 *
 * For information the UTF-8 encoding operations please see
 * http://www.cl.cam.ac.uk/~mgk25/unicode.html
 *
 * @package Horde_Serialize
 * @author Michal Migurski <mike-json@teczno.com>
 * @author Matt Knapp <mdknapp[at]gmail[dot]com>
 * @author Brett Stimmerman <brettstimmerman[at]gmail[dot]com>
 * @copyright 2005 Michal Migurski
 * @license http://www.opensource.org/licenses/bsd-license.php
 * @todo Remove for Horde 4.0
 */

/**
 * Marker constant for JSON::decode(), used to flag stack state.
 */
define('IMP_SERIALIZE_JSON_SLICE', 1);
define('IMP_SERIALIZE_JSON_IN_STR', 2);
define('IMP_SERIALIZE_JSON_IN_ARR', 4);
define('IMP_SERIALIZE_JSON_IN_OBJ', 8);
define('IMP_SERIALIZE_JSON_IN_CMT', 16);

/**
 * Converts to and from JSON format.
 *
 * @package Horde_Serialize
 * @author Michal Migurski <mike-json@teczno.com>
 * @author Matt Knapp <mdknapp[at]gmail[dot]com>
 * @author Brett Stimmerman <brettstimmerman[at]gmail[dot]com>
 * @copyright 2005 Michal Migurski
 */
class IMP_Serialize_JSON {

    /**
     * Added to IMP's json.php to use json_encode() if available.
     */
    function encode($var)
    {
        if (Util::extensionExists('json')) {
            return json_encode($var);
        } else {
            require_once 'Horde/String.php';
            return IMP_Serialize_JSON::_encode($var);
        }
    }

    /**
     * Encodes an arbitrary variable into JSON format.
     *
     * @access private
     *
     * @param mixed $var  Any number, boolean, string, array, or object to be
     *                    encoded. 
     *
     * @return string  JSON string representation of input var.
     */
    function _encode($var)
    {
        switch (gettype($var)) {
        case 'boolean':
            return $var ? 'true' : 'false';

        case 'NULL':
        case 'null':
            return 'null';

        case 'integer':
            return (int) $var;

        case 'double':
        case 'float':
            return (float) $var;

        case 'string':
            // Expected to be in ASCII or UTF-8.
            $strlen = String::length($var, 'utf-8');
            $needles = array('\\', "\x08", "\t", "\n", "\x0c", "\r", '"', '/');
            $replacements = array('\\\\', '\b', '\t', '\n', '\f', '\r', '\"', '\/');

            // Short circuit for ASCII strings.
            if ($strlen == strlen($var)) {
                $var = str_replace($needles, $replacements, $var);
                return '"' . $var . '"';
            }

            // Iterate over every character in the string, escaping with a
            // slash or encoding to UTF-8 code points where necessary.
            $ascii = '';
            preg_match_all("/(.{1})/su", $var, $m);
            foreach ($m[1] as $char) {
                if (strlen($char) == 1) {
                    $ascii .= str_replace($needles, $replacements, $char);
                    continue;
                }
                $ascii .= '\u' . bin2hex(String::convertCharset($char, 'utf-8', 'utf-16be'));
            }

            return '"' . $ascii . '"';

        case 'array':
            /* As per JSON spec if any array key is not an integer we
             * must treat the the whole array as an object. We also
             * try to catch a sparsely populated associative array
             * with numeric keys here because some JS engines will
             * create an array with empty indexes up to max_index
             * which can cause memory issues and because the keys,
             * which may be relevant, will be remapped otherwise.
             *
             * As per the ECMA and JSON specification an object may
             * have any string as a property. Unfortunately due to a
             * hole in the ECMA specification if the key is a ECMA
             * reserved word or starts with a digit the parameter is
             * only accessible using ECMAScript's bracket notation. */

            // Treat as a JSON object.
            if (is_array($var) &&
                count($var) &&
                (array_keys($var) !== range(0, sizeof($var) - 1))) {
                return '{' .
                    implode(',', array_map(array('IMP_Serialize_JSON', '_nameValue'),
                                           array_keys($var),
                                           array_values($var))) . '}';
            }

            // Treat it like a regular array.
            return '[' . implode(',', array_map(array('IMP_Serialize_JSON', '_encode'), $var)) . ']';

        case 'object':
            $vars = get_object_vars($var);
            return '{' .
                implode(',', array_map(array('IMP_Serialize_JSON', '_nameValue'),
                                       array_keys($vars),
                                       array_values($vars))) . '}';

        default:
            return '';
        }
    }

    /**
     * Added to IMP's json.php to use json_decode() if available.
     */
    function decode($var)
    {
        if (Util::extensionExists('json')) {
            return json_decode($var);
        } else {
            require_once 'Horde/String.php';
            return IMP_Serialize_JSON::_decode($var);
        }
    }

    /**
     * Decodes a JSON string into appropriate variable.
     *
     * @access private
     *
     * @param string $str  JSON-formatted string.
     *
     * @return mixed  Number, boolean, string, array, or object corresponding
     *                to given JSON input string. Note that decode() always
     *                returns strings in ASCII or UTF-8 format.
     */
    function _decode($str)
    {
        $str = IMP_Serialize_JSON::_reduce($str);

        switch (strtolower($str)) {
        case 'true':
            return true;

        case 'false':
            return false;

        case 'null':
            return null;

        default:
            if (is_numeric($str)) {
                // Return float or int, as appropriate.
                return ((float)$str == (integer)$str)
                    ? (integer)$str
                    : (float)$str;

            } elseif (preg_match('/^("|\').+(\1)$/s', $str, $m) && $m[1] == $m[2]) {
                // Strings are returned in UTF-8.
                $delim = substr($str, 0, 1);
                $chrs = substr($str, 1, -1);
                $utf8 = '';
                $strlen_chrs = strlen($chrs);

                for ($c = 0; $c < $strlen_chrs; ++$c) {
                    $substr_chrs_c_2 = substr($chrs, $c, 2);
                    $ord_chrs_c = ord($chrs{$c});

                    switch (true) {
                    case $substr_chrs_c_2 == '\b':
                        $utf8 .= chr(0x08);
                        ++$c;
                        break;

                    case $substr_chrs_c_2 == '\t':
                        $utf8 .= chr(0x09);
                        ++$c;
                        break;

                    case $substr_chrs_c_2 == '\n':
                        $utf8 .= chr(0x0A);
                        ++$c;
                        break;

                    case $substr_chrs_c_2 == '\f':
                        $utf8 .= chr(0x0C);
                        ++$c;
                        break;

                    case $substr_chrs_c_2 == '\r':
                        $utf8 .= chr(0x0D);
                        ++$c;
                        break;

                    case $substr_chrs_c_2 == '\\"':
                    case $substr_chrs_c_2 == '\\\'':
                    case $substr_chrs_c_2 == '\\\\':
                    case $substr_chrs_c_2 == '\\/':
                        if (($delim == '"' && $substr_chrs_c_2 != '\\\'') ||
                            ($delim == "'" && $substr_chrs_c_2 != '\\"')) {
                            $utf8 .= $chrs{++$c};
                        }
                        break;

                    case preg_match('/\\\u[0-9A-F]{4}/i', substr($chrs, $c, 6)):
                        // Single, escaped unicode character.
                        $utf16 = chr(hexdec(substr($chrs, ($c + 2), 2))) . chr(hexdec(substr($chrs, ($c + 4), 2)));
                        $utf8 .= String::convertCharset($utf16, 'utf-16', 'utf-8');
                        $c += 5;
                        break;

                    case ($ord_chrs_c >= 0x20) && ($ord_chrs_c <= 0x7F):
                        $utf8 .= $chrs{$c};
                        break;

                    case ($ord_chrs_c & 0xE0) == 0xC0:
                        // Characters U-00000080 - U-000007FF, mask 110XXXXX
                        $utf8 .= substr($chrs, $c, 2);
                        ++$c;
                        break;

                    case ($ord_chrs_c & 0xF0) == 0xE0:
                        // Characters U-00000800 - U-0000FFFF, mask 1110XXXX
                        $utf8 .= substr($chrs, $c, 3);
                        $c += 2;
                        break;

                    case ($ord_chrs_c & 0xF8) == 0xF0:
                        // Characters U-00010000 - U-001FFFFF, mask 11110XXX
                        $utf8 .= substr($chrs, $c, 4);
                        $c += 3;
                        break;

                    case ($ord_chrs_c & 0xFC) == 0xF8:
                        // Characters U-00200000 - U-03FFFFFF, mask 111110XX
                        $utf8 .= substr($chrs, $c, 5);
                        $c += 4;
                        break;

                    case ($ord_chrs_c & 0xFE) == 0xFC:
                        // Characters U-04000000 - U-7FFFFFFF, mask 1111110X
                        $utf8 .= substr($chrs, $c, 6);
                        $c += 5;
                        break;
                    }
                }

                return $utf8;
            } elseif (preg_match('/^\[.*\]$/s', $str) || preg_match('/^\{.*\}$/s', $str)) {
                // Array or object notation.
                if ($str[0] == '[') {
                    $stk = array(IMP_SERIALIZE_JSON_IN_ARR);
                    $arr = array();
                } else {
                    $stk = array(IMP_SERIALIZE_JSON_IN_OBJ);
                    $obj = new stdClass();
                }

                array_push($stk, array('what'  => IMP_SERIALIZE_JSON_SLICE,
                                       'where' => 0,
                                       'delim' => false));

                $chrs = substr($str, 1, -1);
                $chrs = IMP_Serialize_JSON::_reduce($chrs);

                if ($chrs == '') {
                    if (reset($stk) == IMP_SERIALIZE_JSON_IN_ARR) {
                        return $arr;
                    } else {
                        return $obj;
                    }
                }

                $strlen_chrs = strlen($chrs);

                for ($c = 0; $c <= $strlen_chrs; ++$c) {
                    $top = end($stk);
                    $substr_chrs_c_2 = substr($chrs, $c, 2);

                    if (($c == $strlen_chrs) || (($chrs{$c} == ',') && ($top['what'] == IMP_SERIALIZE_JSON_SLICE))) {
                        // Found a comma that is not inside a string,
                        // array, etc., OR we've reached the end of
                        // the character list.
                        $slice = substr($chrs, $top['where'], ($c - $top['where']));
                        array_push($stk, array('what' => IMP_SERIALIZE_JSON_SLICE, 'where' => ($c + 1), 'delim' => false));

                        if (reset($stk) == IMP_SERIALIZE_JSON_IN_ARR) {
                            // We are in an array, so just push an
                            // element onto the stack.
                            array_push($arr, IMP_Serialize_JSON::_decode($slice));

                        } elseif (reset($stk) == IMP_SERIALIZE_JSON_IN_OBJ) {
                            // We are in an object, so figure out the
                            // property name and set an element in an
                            // associative array for now.
                            if (preg_match('/^\s*(["\'].*[^\\\]["\'])\s*:\s*(\S.*),?$/Uis', $slice, $parts)) {
                                // "name":value pair
                                $key = IMP_Serialize_JSON::_decode($parts[1]);
                                $val = IMP_Serialize_JSON::_decode($parts[2]);

                                $obj->$key = $val;
                            } elseif (preg_match('/^\s*(\w+)\s*:\s*(\S.*),?$/Uis', $slice, $parts)) {
                                // name:value pair, where name is unquoted
                                $key = $parts[1];
                                $obj->$key = IMP_Serialize_JSON::_decode($parts[2]);
                            }
                        }
                    } elseif ((($chrs{$c} == '"') || ($chrs{$c} == "'")) && ($top['what'] != IMP_SERIALIZE_JSON_IN_STR)) {
                        // Found a quote, and we are not inside a string.
                        array_push($stk, array('what' => IMP_SERIALIZE_JSON_IN_STR, 'where' => $c, 'delim' => $chrs{$c}));

                    } elseif (($chrs{$c} == $top['delim']) &&
                              ($top['what'] == IMP_SERIALIZE_JSON_IN_STR) &&
                              (($chrs{$c - 1} != "\\") ||
                               ($chrs{$c - 1} == "\\" && $chrs{$c - 2} == "\\"))) {
                        // Found a quote, we're in a string, and it's
                        // not escaped.
                        array_pop($stk);

                    } elseif (($chrs{$c} == '[') &&
                              in_array($top['what'], array(IMP_SERIALIZE_JSON_SLICE, IMP_SERIALIZE_JSON_IN_ARR, IMP_SERIALIZE_JSON_IN_OBJ))) {
                        // Found a left-bracket, and we are in an
                        // array, object, or slice.
                        array_push($stk, array('what' => IMP_SERIALIZE_JSON_IN_ARR, 'where' => $c, 'delim' => false));

                    } elseif (($chrs{$c} == ']') && ($top['what'] == IMP_SERIALIZE_JSON_IN_ARR)) {
                        // found a right-bracket, and we're in an array
                        array_pop($stk);

                    } elseif (($chrs{$c} == '{') &&
                              in_array($top['what'], array(IMP_SERIALIZE_JSON_SLICE, IMP_SERIALIZE_JSON_IN_ARR, IMP_SERIALIZE_JSON_IN_OBJ))) {
                        // Found a left-brace, and we are in an array,
                        // object, or slice.
                        array_push($stk, array('what' => IMP_SERIALIZE_JSON_IN_OBJ, 'where' => $c, 'delim' => false));

                    } elseif (($chrs{$c} == '}') && ($top['what'] == IMP_SERIALIZE_JSON_IN_OBJ)) {
                        // Found a right-brace, and we're in an object.
                        array_pop($stk);

                    } elseif (($substr_chrs_c_2 == '/*') &&
                              in_array($top['what'], array(IMP_SERIALIZE_JSON_SLICE, IMP_SERIALIZE_JSON_IN_ARR, IMP_SERIALIZE_JSON_IN_OBJ))) {
                        // Found a comment start, and we are in an
                        // array, object, or slice.
                        array_push($stk, array('what' => IMP_SERIALIZE_JSON_IN_CMT, 'where' => $c, 'delim' => false));
                        $c++;

                    } elseif (($substr_chrs_c_2 == '*/') && ($top['what'] == IMP_SERIALIZE_JSON_IN_CMT)) {
                        // Found a comment end, and we're in one now.
                        array_pop($stk);
                        $c++;

                        for ($i = $top['where']; $i <= $c; ++$i) {
                            $chrs = substr_replace($chrs, ' ', $i, 1);
                        }
                    }
                }

                if (reset($stk) == IMP_SERIALIZE_JSON_IN_ARR) {
                    return $arr;
                } elseif (reset($stk) == IMP_SERIALIZE_JSON_IN_OBJ) {
                    return $obj;
                }
            }
        }
    }

    /**
     * Array-walking function for use in generating JSON-formatted
     * name-value pairs.
     *
     * @access private
     *
     * @param string $name  Name of key to use.
     * @param mixed $value  Reference to an array element to be encoded.
     *
     * @return string  JSON-formatted name-value pair, like '"name":value'.
     */
    function _nameValue($name, $value)
    {
        return IMP_Serialize_JSON::_encode(strval($name)) . ':' . IMP_Serialize_JSON::_encode($value);
    }

    /**
     * Reduce a string by removing leading and trailing comments and
     * whitespace.
     *
     * @access private
     *
     * @param $str string  String value to strip of comments and whitespace.
     *
     * @return string  String value stripped of comments and whitespace.
     */
    function _reduce($str)
    {
        $str = preg_replace(array(
            // Eliminate single line comments in '// ...' form.
            '#^\s*//(.+)$#m',

            // Eliminate multi-line comments in '/* ... */' form, at
            // start of string.
            '#^\s*/\*(.+)\*/#Us',

            // Eliminate multi-line comments in '/* ... */' form, at
            // end of string.
            '#/\*(.+)\*/\s*$#Us'
            ), '', $str);

        // Eliminate extraneous space.
        return trim($str);
    }

}
