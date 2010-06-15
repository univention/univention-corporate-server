<?php
/**
 * Variables:: class.
 *
 * $Horde: framework/Util/Variables.php,v 1.4 2004/04/07 14:43:14 chuck Exp $
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
            require_once dirname(__FILE__) . '/../Util.php';
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
        require_once dirname(__FILE__) . '/Util.php';
        return $ret = &new Variables(Util::dispelMagicQuotes($_REQUEST));
    }

    function exists($varname)
    {
        if (count($this->_expectedVariables) &&
            $this->_exists($this->_expectedVariables, $varname, false)) {
            return true;
        }
        return $this->_exists($this->_vars, $varname, false);
    }

    function get($varname)
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
        $this->_vars[$varname] = $value;
    }

    function add($varname, $value)
    {
        if ($this->exists($varname)) {
            return false;
        }
        $this->_vars[$varname] = $value;
    }

    function remove($varname)
    {
        require_once 'Horde/Array.php';
        Horde_Array::getArrayParts($varname, $base, $keys);
        if (!is_null($base)) {
            eval("unset(\$this->_vars['" . $base . "']['" . join("']['", $keys) . "']);");
        } else {
            unset($this->_vars[$varname]);
        }
    }

    /**
     * Find out whether or not $varname was set in $array.
     *
     * @access private
     *
     * @param array   $array                  The array to search in (usually
     *                                        either $this->_vars or
     *                                        $this->_expectedVariables).
     * @param string  $varname                The name of the variable to look for.
     * @param optional boolean $checkExpectedVariables  If we don't find $varname, should we
     *                                        check $this->_expectedVariables to see if it
     *                                        should have existed (like a checkbox
     *                                        or select multiple).
     *
     * @return  Whether or not the variable was set (or, if we've checked
     *          $this->_expectedVariables, should have been set).
     */
    function _exists($array, $varname, $checkExpectedVariables = true)
    {
        return $this->_getExists($array, $varname, $value, $checkExpectedVariables);
    }

    /**
     * Fetch the requested variable ($varname) into $value, and return whether
     * or not the variable was set in $array.
     *
     * @access private
     *
     * @param array   $array               The array to search in (usually
     *                                     either $this->_vars or
     *                                     $this->_expectedVariables).
     * @param string  $varname             The name of the variable to look for.
     * @param mixed  &$value               $varname's value gets assigned to
     *                                     this variable.
     * @param optional bool $checkExpectedVariables  If we don't find $varname, should we
     *                                     check $this->_expectedVariables to see if it
     *                                     should have existed (like a checkbox
     *                                     or select multiple).
     *
     * @return  Whether or not the variable was set (or, if we've checked
     *          $this->_expectedVariables, should have been set).
     */
    function _getExists($array, $varname, &$value, $checkExpectedVariables = true)
    {
        require_once 'Horde/Array.php';
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
                        // If we're supposed to check $this->_expectedVariables,
                        // do so, but make sure not to check it again.
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
                // If we're supposed to check $this->_expectedVariables, do so,
                // but make sure not to check it again.
                return $this->_exists($this->_expectedVariables, $varname, false);
            } else {
                return false;
            }
        }
    }

}
