<?php
/**
 * The Horde_Array:: class provides various methods for array manipulation.
 *
 * $Horde: framework/Util/Array.php,v 1.21 2004/04/22 18:38:27 chuck Exp $
 *
 * Copyright 2003-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 * Copyright 2003-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @author  Marko Djukic <marko@oblo.com>
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Util
 */
class Horde_Array {

    /**
     * Prepare a list of addresses for storage.
     * Namely, trims and lowercases all addresses and then sort.
     *
     * @access public
     *
     * @param array $addr  The list of addresses.
     *
     * @return array  The list of addresses, prepared for storage.
     */
    function prepareAddressList($addr)
    {
        /* Remove any extra space in the address and make it lowercase. */
        $addr = array_map('trim', $addr);
        $addr = array_map(array('String', 'lower'), $addr);

        /* Remove duplicate entries. */
        $addr = array_unique($addr);

        /* Sort the list. */
        usort($addr, array('Horde_Array', 'sortAddressList'));

        return $addr;
    }

    /**
     * Function used by usort() to sort an address list.
     * e.g. usort($foo, array('Horde_Array', 'sortAddressList'));
     *
     * @access public
     *
     * @param string $a  Address #1.
     * @param string $b  Address #2.
     *
     * @return integer  -1, 0, or 1.
     */
    function sortAddressList($a, $b)
    {
        $a = explode('@', $a);
        $b = explode('@', $b);

        /* One of the addresses doesn't have a host name. */
        if (empty($a[0])) {
            array_shift($a);
        }
        if (empty($b[0])) {
            array_shift($b);
        }
        if (count($a) != count($b)) {
            return (count($a) > count($b));
        }

        /* The addresses have different hostname or not hostname and
           different mailbox names. */
        if ($a[(count($a) - 1)] != $b[(count($b) - 1)]) {
            return strcmp($a[(count($a) - 1)], $b[(count($b) - 1)]);
        }

        /* Compare mailbox names. */
        return strcmp($a[0], $b[0]);
    }

    /**
     * Sorts an array on a specified key. If the key does not exist,
     * defaults to the first key of the array.
     *
     * @access public
     *
     * @param array &$array                The array to be sorted, passed
     *                                     by reference.
     * @param optional string $key         The key by which to sort. If not
     *                                     specified then the first key is
     *                                     used.
     * @param optional integer $direction  Sort direction
     *                                     0 = ascending (default)
     *                                     1 = descending
     */
    function arraySort(&$array, $key = null, $direction = 0)
    {
        /* Return if the array is empty. */
        if (empty($array)) {
            return;
        }

        /* If no key to sort by is specified, use the first key. */
        if (is_null($key)) {
            $keys = array_keys($array);
            $key = $keys[0];
        }

        /* Create the function that will be used to sort the keys. */
        $function = sprintf('return String::lower($a[\'%1$s\']) %2$s String::lower($b[\'%1$s\']) ? 1 : -1;', $key, ($direction ? '<' : '>'));

        /* Call the sort function, preserving array key
         * association. */
        uasort($array, create_function('$a, $b', $function));
    }

    /**
     * Given an HTML type array field "example[key1][key2][key3]" breaks up
     * the keys so that they could be used to reference a regular PHP array.
     *
     * @access public
     *
     * @param string $field  The field name to be examined.
     * @param string &$base  Set to the base element.
     * @param array &$keys   Set to the list of keys.
     *
     * @access boolean  True on sucess, false on error.
     */
    function getArrayParts($field, &$base, &$keys)
    {
        if (preg_match('|([^\[]*)((\[[^\[\]]*\])+)|', $field, $matches)) {
            $base = $matches[1];
            $keys = explode('][', $matches[2]);
            $keys[0] = substr($keys[0], 1);
            $keys[count($keys) - 1] = substr($keys[count($keys) - 1], 0, strlen($keys[count($keys) - 1]) - 1);
            return true;
        } else {
            return false;
        }
    }

    /**
     * Using an array of keys itarate through the array following the keys to
     * find the final key value. If a value is passed then set that value.
     *
     * @access public
     *
     * @param array &$array          The array to be used.
     * @param array &$keys           The key path to follow as an array.
     * @param optional array $value  If set the target element will have this
     *                               value set to it.
     *
     * @returns mixed  The final value of the key path.
     */
    function getElement(&$array, &$keys, $value = null)
    {
        if (count($keys) > 0) {
            $key = array_shift($keys);
            if (isset($array[$key])) {
                return Horde_Array::getElement($array[$key], $keys, $value);
            } else {
                return $array;
            }
        } else {
            if (!is_null($value)) {
                $array = $value;
            }
            return $array;
        }
    }

    /**
     * Returns a rectangle of a two-dimensional array.
     *
     * @access public
     *
     * @param array &$array    The array to extract the rectangle from.
     * @param integer $row     The start row of the rectangle.
     * @param integer $col     The start column of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param integer $width   The width of the rectangle.
     *
     * @return array  The extracted rectangle.
     */
    function &getRectangle(&$array, $row, $col, $height, $width)
    {
        $rec = array();
        for ($y = $row; $y < $row + $height; $y++) {
            $rec[] = array_slice($array[$y], $col, $width);
        }
        return $rec;
    }

    /**
     * Given an array, returns an associative array with each element key
     * derived from its value.
     * For example:
     *   array(0 => 'foo', 1 => 'bar')
     * would become:
     *   array('foo' => 'foo', 'bar' => 'bar')
     *
     * @access public
     *
     * @param array $array  An array of values.
     *
     * @return array  An array with keys the same as values.
     */
    function valuesToKeys($array)
    {
        $mapped = array();
        foreach ($array as $value) {
            $mapped[$value] = $value;
        }
        return $mapped;
    }

    /**
     * Creates an array by using one array for keys and another for
     * its values. Only exists in PHP5, so we call array_combine if it
     * exists and otherwise emulate it.
     *
     * @param array $keys    Key array.
     * @param array $values  Value array.
     *
     * @return mixed  False if there are no elements, or the combined array.
     */
    function combine($keys, $values)
    {
        if (function_exists('array_combine')) {
            return array_combine($keys, $values);
        }

        $size = count($keys);
        if (($size != count($values)) || ($size == 0)) {
            return false;
        }

        for ($x = 0; $x < $size; $x++) {
            $array[$keys[$x]] = $values[$x];
        }
        return $array;
    }

}
