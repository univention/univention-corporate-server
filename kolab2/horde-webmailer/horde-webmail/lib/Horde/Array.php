<?php

require_once dirname(__FILE__) . '/String.php';

/**
 * The Horde_Array:: class provides various methods for array manipulation.
 *
 * $Horde: framework/Util/Array.php,v 1.26.2.12 2009-01-06 15:23:45 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @author  Marko Djukic <marko@oblo.com>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Util
 */
class Horde_Array {

    /**
     * Prepare a list of addresses for storage.
     * Namely, trims and lowercases all addresses and then sort.
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
     * @param array &$array       The array to be sorted, passed by reference.
     * @param string $key         The key by which to sort. If not specified
     *                            then the first key is used.
     * @param integer $direction  Sort direction
     *                             0 = ascending (default)
     *                             1 = descending
     * @param boolean $associate  Keep key value association?
     */
    function arraySort(&$array, $key = null, $direction = 0, $associate = true)
    {
        /* Return if the array is empty. */
        if (empty($array)) {
            return;
        }

        /* If no key to sort by is specified, use the first key of the
         * first element. */
        if (is_null($key)) {
            reset($array);
            $key = array_shift(array_keys(current($array)));
        }

        /* Call the appropriate sort function. */
        $helper = new Horde_Array_Sort_Helper;
        $helper->key = $key;
        $function = $direction ? 'reverseCompare' : 'compare';
        if ($associate) {
            uasort($array, array($helper, $function));
        } else {
            usort($array, array($helper, $function));
        }
    }

    /**
     * Given an HTML type array field "example[key1][key2][key3]" breaks up
     * the keys so that they could be used to reference a regular PHP array.
     *
     * @param string $field  The field name to be examined.
     * @param string &$base  Set to the base element.
     * @param array &$keys   Set to the list of keys.
     *
     * @return boolean  True on sucess, false on error.
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
     * Using an array of keys iterate through the array following the
     * keys to find the final key value. If a value is passed then set
     * that value.
     *
     * @param array &$array  The array to be used.
     * @param array &$keys   The key path to follow as an array.
     * @param array $value   If set the target element will have this value set
     *                       to it.
     *
     * @return mixed  The final value of the key path.
     */
    function getElement(&$array, &$keys, $value = null)
    {
        if (count($keys)) {
            $key = array_shift($keys);
            if (isset($array[$key])) {
                return Horde_Array::getElement($array[$key], $keys, $value);
            } else {
                return false;
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
     * @param array   $array   The array to extract the rectangle from.
     * @param integer $row     The start row of the rectangle.
     * @param integer $col     The start column of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param integer $width   The width of the rectangle.
     *
     * @return array  The extracted rectangle.
     */
    function getRectangle($array, $row, $col, $height, $width)
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
     * @param array $array  An array of values.
     *
     * @return array  An array with keys the same as values.
     */
    function valuesToKeys($array)
    {
        if (!$array) {
            return array();
        }

        $values = array_values($array);
        return Horde_Array::combine($values, $values);
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

    /**
     * Enhanced array_merge_recursive() function.  Main difference from PHP's
     * stock function is later value always overwrites earlier value (stock
     * function will instead create an array with all values of key).
     *
     * @since Horde 3.2
     *
     * @param array $a1  The old array.
     * @param array $a2  The new array.
     *
     * @return array  The merged array.
     */
    function array_merge_recursive_overwrite($a1, $a2)
    {
        foreach ($a2 as $key => $val) {
            if (!isset($a1[$key])) {
                $a1[$key] = array();
            }

            $a1[$key] = (is_array($val))
                ? Horde_Array::array_merge_recursive_overwrite($a1[$key], $val)
                : $val;
        }

        return $a1;
    }

}

/**
 * @package Horde_Util
 *
 * Helper class for sorting arrays on arbitrary criteria for
 * usort/uasort.
 */
class Horde_Array_Sort_Helper {

    /**
     * The array key to sort by.
     *
     * @var string
     */
    var $key;

    /**
     * Compare two associative arrays by the array key defined in
     * self::$key.
     *
     * @param array $a
     * @param array $b
     */
    function compare($a, $b)
    {
        return strcoll(String::lower($a[$this->key], true), String::lower($b[$this->key], true));
    }

    /**
     * Compare, in reverse order, two associative arrays by the array
     * key defined in self::$key.
     *
     * @param array $a
     * @param array $b
     */
    function reverseCompare($a, $b)
    {
        return strcoll(String::lower($b[$this->key], true), String::lower($a[$this->key], true));
    }

    /**
     * Compare array keys case insensitively for uksort.
     *
     * @param scalar $a
     * @param scalar $b
     */
    function compareKeys($a, $b)
    {
        return strcoll(String::lower($a, true), String::lower($b, true));
    }

    /**
     * Compare, in reverse order, array keys case insensitively for
     * uksort.
     *
     * @param scalar $a
     * @param scalar $b
     */
    function reverseCompareKeys($a, $b)
    {
        return strcoll(String::lower($b, true), String::lower($a, true));
    }

}
