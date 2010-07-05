<?php
/**
 * The Horde_Compress:: class provides an API for various compression
 * techniques that can be used by Horde applications.
 *
 * $Horde: framework/Compress/Compress.php,v 1.7.12.14 2009-01-06 15:22:58 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_Compress
 */
class Horde_Compress {

    /**
     * Attempts to return a concrete Horde_Compress instance based on $driver.
     *
     * @param mixed $driver  The type of concrete Horde_Compress subclass to
     *                       return. If $driver is an array, then we will look
     *                       in $driver[0]/lib/Compress/ for the subclass
     *                       implementation named $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       parameters a subclass might need.
     *
     * @return Horde_Compress  The newly created concrete Horde_Compress
     *                         instance, or false on an error.
     */
    function &factory($driver, $params = array())
    {
        if (is_array($driver)) {
            list($app, $driver) = $driver;
        }

        $driver = basename($driver);
        $class = 'Horde_Compress_' . $driver;
        if (!class_exists($class)) {
            if (!empty($app)) {
                include_once $app . '/lib/Compress/' . $driver . '.php';
            } else {
                include_once 'Horde/Compress/' . $driver . '.php';
            }
        }

        if (class_exists($class)) {
            $compress = new $class($params);
        } else {
            $compress = false;
        }

        return $compress;
    }

    /**
     * Attempts to return a reference to a concrete Horde_Compress instance
     * based on $driver. It will only create a new instance if no
     * Horde_Compress instance with the same parameters currently exists.
     *
     * This method must be invoked as:
     *   $var = &Horde_Compress::singleton();
     *
     * @param mixed $driver  See Horde_Compress::factory().
     * @param array $params  See Horde_Compress::factory().
     *
     * @return Horde_Compress  The concrete Horde_Compress reference, or false
     *                         on an error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances = array();

        $signature = md5(serialize(array($driver, $params)));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Compress::factory($driver, $params);
        }

        return $instances[$signature];
    }

    /**
     * Constructor.
     *
     * @param array $params  Parameter array.
     */
    function Horde_Compress($params = array())
    {
    }

    /**
     * Compress the data.
     *
     * @param string $data   The data to compress.
     * @param array $params  An array of arguments needed to compress the data.
     *
     * @return mixed  The compressed data.
     *                Returns PEAR_Error object on error.
     */
    function compress($data, $params = array())
    {
        return PEAR::raiseError('Unsupported');
    }

    /**
     * Decompress the data.
     *
     * @param string $data   The data to decompress.
     * @param array $params  An array of arguments needed to decompress the
     *                       data.
     *
     * @return array  The decompressed data.
     *                Returns PEAR_Error object on error.
     */
    function decompress($data, $params = array())
    {
        return PEAR::raiseError('Unsupported');
    }

}
