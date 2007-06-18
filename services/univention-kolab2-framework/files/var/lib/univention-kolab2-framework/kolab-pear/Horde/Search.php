<?php
/**
 * The Horde_Search:: class provides an abstracted interface into
 * various searching APIs.
 *
 * $Horde: framework/Search/Search.php,v 1.4 2004/01/25 19:07:01 chuck Exp $
 *
 * Copyright 2003-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Search
 */
class Horde_Search {

    /**
     * Attempts to return a concrete Horde_Search instance based on
     * $driver.
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Horde_Search subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is
     *                                dynamically included. If $driver is an
     *                                array, then we will look in
     *                                $driver[0]/lib/Search/ for the subclass
     *                                implementation named $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object Horde_Search  The newly created concrete Horde_Search instance,
     *                              or false on error.
     */
    function &factory($driver, $params = null)
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        if (is_null($params) && class_exists('Horde')) {
            $params = Horde::getDriverConfig('search', $driver);
        }

        if (!empty($app)) {
            global $registry;
            require_once $registry->getParam('fileroot', $app) . '/lib/Search/' . $driver . '.php';
        } elseif (file_exists(dirname(__FILE__) . '/Search/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Search/' . $driver . '.php';
        } else {
            @include_once 'Horde/Search/' . $driver . '.php';
        }
        $class = 'Horde_Search_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete Horde_Search
     * instance based on $driver. It will only create a new instance
     * if no Horde_Search instance with the same parameters currently
     * exists.
     *
     * This should be used if multiple search backends (and, thus,
     * multiple Horde_Search instances) are required.
     *
     * This method must be invoked as:
     * $var = &Horde_Search::singleton()
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Horde_Search subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is
     *                                dynamically included. If $driver is an
     *                                array, then we will look in
     *                                $driver[0]/lib/Search/ for the subclass
     *                                implementation named $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @since Horde 2.2
     *
     * @return object Horde_Search  The concrete Horde_Search reference,
     *                              or false on error.
     */
    function &singleton($driver, $params = null)
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        if (is_null($params) && class_exists('Horde')) {
            $params = Horde::getDriverConfig('search', $driver);
        }

        $signature = serialize(array($driver, $params));
        if (!array_key_exists($signature, $instances)) {
            $instances[$signature] = &Horde_Search::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
