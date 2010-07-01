<?php

require_once 'PEAR.php';

define('TEXT_HTML_PASSTHRU', 0);
define('TEXT_HTML_SYNTAX', 1);
define('TEXT_HTML_MICRO', 2);
define('TEXT_HTML_MICRO_LINKURL', 3);
define('TEXT_HTML_NOHTML', 4);
define('TEXT_HTML_NOHTML_NOBREAK', 5);

/**
 * Text_Filter:: is a parent class for defining stackable text filters.
 *
 * $Horde: framework/Text_Filter/Filter.php,v 1.15.2.13 2009-01-06 15:23:42 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Text
 */
class Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Constructor.
     *
     * @param array $params  Any parameters that the filter instance needs.
     */
    function Text_Filter($params = array())
    {
        $this->_params = array_merge($this->_params, $params);
    }

    /**
     * Applies a set of patterns to a block of text.
     *
     * @param string $text     The text to filter.
     * @param array $patterns  The array of patterns to filter with.
     *
     * @return string  The transformed text.
     */
    function filter($text, $filters = array(), $params = array())
    {
        if (!is_array($filters)) {
            $filters = array($filters);
            $params = array($params);
        }

        foreach ($filters as $num => $filter) {
            $filterOb = Text_Filter::factory($filter, isset($params[$num]) ? $params[$num] : array());
            if (is_a($filterOb, 'PEAR_Error')) {
                return $filterOb->getMessage();
            }
            $patterns = $filterOb->getPatterns();

            /* Pre-processing. */
            $text = $filterOb->preProcess($text);

            /* str_replace() simple patterns. */
            if (isset($patterns['replace'])) {
                $from = array_keys($patterns['replace']);
                $to = array_values($patterns['replace']);
                $text = str_replace($from, $to, $text);
            }

            /* preg_replace complex patterns. */
            if (isset($patterns['regexp'])) {
                $from = array_keys($patterns['regexp']);
                $to = array_values($patterns['regexp']);
                $text = preg_replace($from, $to, $text);
            }

            /* Post-processing. */
            $text = $filterOb->postProcess($text);
        }

        return $text;
    }

    /**
     * Executes any code necessaray before applying the filter
     * patterns.
     *
     * @param string $text  The text before the filtering.
     *
     * @return string  The modified text.
     */
    function preProcess($text)
    {
        return $text;
    }

    /**
     * Returns a hash with replace patterns.
     *
     * @return array  Patterns hash.
     */
    function getPatterns()
    {
        return array();
    }

    /**
     * Executes any code necessaray after applying the filter
     * patterns.
     *
     * @param string $text  The text after the filtering.
     *
     * @return string  The modified text.
     */
    function postProcess($text)
    {
        return $text;
    }

    /**
     * Attempts to return a concrete Text_filter instance based on
     * $driver.
     *
     * @param mixed $driver  The type of concrete Text_Filter subclass to
     *                       return. This is based on the filter driver
     *                       ($driver). The code is dynamically included. If
     *                       $driver is an array, then we will look in
     *                       $driver[0] for the subclass implementation named
     *                       $driver[1].php.
     * @param array $params  A hash containing any additional configuration
     *                       parameters a subclass might need.
     *
     * @return Text_Filter  The newly created concrete Text_Filter instance,
     *                      or false on an error.
     */
    function &factory($driver, $params = array())
    {
        if (is_array($driver)) {
            list($dir, $driver) = $driver;
        }

        $class = 'Text_Filter_' . $driver;
        if (!class_exists($class)) {
            if (!empty($dir)) {
                include_once $dir . '/' . $driver . '.php';
            } else {
                include_once 'Horde/Text/Filter/' . $driver . '.php';
            }
        }

        if (class_exists($class)) {
            $filter = new $class($params);
        } else {
            $filter = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $filter;
    }

}
