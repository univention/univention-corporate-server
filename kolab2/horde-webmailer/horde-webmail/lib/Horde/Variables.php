<?php
/**
 * $Horde: framework/Util/Variables.php,v 1.8.10.7 2007-12-20 13:50:16 jan Exp $
 *
 * @package Horde_Util
 */

/** Horde_Util */
require_once 'Horde/Util.php';

/** Horde_Array */
require_once 'Horde/Array.php';

/**
 * Variables:: class.
 *
 * @author  Robert E. Coyle <robertecoyle@hotmail.com>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Util
 */
class Variables {

    var $_vars;
    var $_expectedVariables = array();

    function Variables($vars = array())
    {
        if (is_null($vars)) {
            $vars = Util::dispelMagicQuotes($_REQUEST);
        }
        if (isset($vars['_formvars'])) {
            $this->_expectedVariables = @unserialize($vars['_formvars']);
            unset($vars['_formvars']);
        }
        $this->_vars = $vars;
    }

    function &getDefaultVariables()
    {
        $vars = new Variables(null);
        return $vars;
    }

    function count()
    {
        return count($this->_vars);
    }

    function exists($varname)
    {
        return $this->__isset($varname);
    }

    function __isset($varname)
    {
        if (count($this->_expectedVariables) &&
            $this->_exists($this->_expectedVariables, $varname, false)) {
            return true;
        }
        return $this->_exists($this->_vars, $varname, false);
    }

    function get($varname)
    {
        return $this->__get($varname);
    }

    function __get($varname)
    {
        $this->_getExists($this->_vars, $varname, $value);
        return $value;
    }

    function getExists($varname, &$exists)
    {
        $exists = $this->_getExists($this->_vars, $varname, $value);
        return $value;
    }

    function set($varname, $value)
    {
        return $this->__set($varname, $value);
    }

    function __set($varname, $value)
    {
        $keys = array();
        if (!Horde_Array::getArrayParts($varname, $base, $keys)) {
            $this->_vars[$varname] = $value;
        } else {
            array_unshift($keys, $base);
            $place = &$this->_vars;

            while (count($keys)) {
                $key = array_shift($keys);
                if (!isset($place[$key])) {
                    $place[$key] = array();
                }
                $place = &$place[$key];
            }

            $place = $value;
        }
    }

    function remove($varname)
    {
        return $this->__unset($varname);
    }

    function __unset($varname)
    {
        Horde_Array::getArrayParts($varname, $base, $keys);
        if (!is_null($base)) {
            $ptr = &$this->_vars[$base];
            $end = count($keys) - 1;
            foreach ($keys as $key => $val) {
                if (!isset($ptr[$val])) {
                    break;
                }
                if ($end == $key) {
                    array_splice($ptr, array_search($val, array_keys($ptr)), 1);
                } else {
                    $ptr = &$ptr[$val];
                }
            }
        } else {
            unset($this->_vars[$varname]);
        }
    }

    function merge($vars)
    {
        foreach ($vars as $varname => $value) {
            $this->set($varname, $value);
        }
    }

    /**
     * Set $varname to $value ONLY if it's not already present.
     */
    function add($varname, $value)
    {
        if ($this->exists($varname)) {
            return false;
        }
        $this->_vars[$varname] = $value;
    }

    /**
     * Find out whether or not $varname was set in $array.
     *
     * @access private
     *
     * @param array   $array                   The array to search in (usually
     *                                         either $this->_vars or
     *                                         $this->_expectedVariables).
     * @param string  $varname                 The name of the variable to look
     *                                         for.
     * @param boolean $checkExpectedVariables  If we don't find $varname,
     *                                         should we check
     *                                         $this->_expectedVariables to see
     *                                         if should have existed (like a
     *                                         checkbox or select multiple).
     *
     * @return  Whether or not the variable was set (or, if we've checked
     *          $this->_expectedVariables, should have been set).
     */
    function _exists($array, $varname, $checkExpectedVariables = true)
    {
        return $this->_getExists($array, $varname, $value, $checkExpectedVariables);
    }

    /**
     * Fetch the requested variable ($varname) into $value, and return
     * whether or not the variable was set in $array.
     *
     * @access private
     *
     * @param array   $array                   The array to search in (usually
     *                                         either $this->_vars or
     *                                         $this->_expectedVariables).
     * @param string  $varname                 The name of the variable to look
     *                                         for.
     * @param mixed  &$value                   $varname's value gets assigned
     *                                         to.
     *                                         this variable.
     * @param boolean $checkExpectedVariables  If we don't find $varname,
     *                                         should we check
     *                                         $this->_expectedVariables to see
     *                                         if it should have existed (like
     *                                         a checkbox or select multiple).
     *
     * @return  Whether or not the variable was set (or, if we've checked
     *          $this->_expectedVariables, should have been set).
     */
    function _getExists($array, $varname, &$value, $checkExpectedVariables = true)
    {
        if (Horde_Array::getArrayParts($varname, $base, $keys)) {
            if (!isset($array[$base])) {
                $value = null;
                // If we're supposed to check $this->_expectedVariables, do so,
                // but make sure not to check it again.
                return $checkExpectedVariables ? $this->_exists($this->_expectedVariables, $varname, false) : false;
            } else {
                $searchspace = &$array[$base];
                while (count($keys)) {
                    $key = array_shift($keys);
                    if (!isset($searchspace[$key])) {
                        $value = null;
                        // If we're supposed to check
                        // $this->_expectedVariables, do so, but make
                        // sure not to check it again.
                        return $checkExpectedVariables ? $this->_exists($this->_expectedVariables, $varname, false) : false;
                    }
                    $searchspace = &$searchspace[$key];
                }
                $value = $searchspace;
                return true;
            }
        } else {
            $value = isset($array[$varname]) ? $array[$varname] : null;
            if (!is_null($value)) {
                return true;
            } elseif ($checkExpectedVariables) {
                // If we're supposed to check
                // $this->_expectedVariables, do so, but make sure not
                // to check it again.
                return $this->_exists($this->_expectedVariables, $varname, false);
            } else {
                return false;
            }
        }
    }

}
