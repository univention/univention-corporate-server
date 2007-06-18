<?php
/**
 * The Horde_Compress:: class provides an API for various compression
 * techniques that can be used by Horde applications.
 *
 * $Horde: framework/Compress/Compress.php,v 1.7 2004/01/01 15:14:12 jan Exp $
 *
 * Copyright 2003-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Compress
 */
class Horde_Compress {

    /**
     * Attempts to return a concrete Horde_Compress instance based on
     * $driver.
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Horde_Compress
     *                                subclass to return. This is based on
     *                                the storage driver ($driver). The code
     *                                is dynamically included. If $driver is
     *                                an array, then we will look in
     *                                $driver[0]/lib/Compress/ for the
     *                                subclass implementation named
     *                                $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or parameters a subclass
     *                                might need.
     *
     * @return object Horde_Compress  The newly created concrete
     *                                Horde_Compress instance, or false on an
     *                                error.
     */
    function &factory($driver, $params = array())
    {
        if (is_array($driver)) {
            list($app, $driver) = $driver;
        }

        $driver = basename($driver);

        if (!empty($app)) {
            require_once $app . '/lib/Compress/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/Compress/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Compress/' . $driver . '.php';
        } else {
            @include_once 'Horde/Compress/' . $driver . '.php';
        }

        $class = 'Horde_Compress_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return false;
        }
    }

    /**
     * Attempts to return a reference to a concrete Horde_Compress instance
     * based on $driver. It will only create a new instance if no
     * Horde_Compress instance with the same parameters currently exists.
     *
     * This method must be invoked as:
     *   $var = &Horde_Compress::singleton();
     *
     * @access public
     *
     * @param mixed $driver           See Horde_Compress::factory().
     * @param optional array $params  See Horde_Compress::factory().
     *
     * @return object Horde_Compress  The concrete Horde_Compress reference,
     *                                or false on an error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!array_key_exists($signature, $instances)) {
            $instances[$signature] = &Horde_Compress::factory($driver, $params);
        }

        return $instances[$signature];
    }

    /**
     * Constructor.
     *
     * @access public
     *
     * @param optional array $params  Parameter array.
     */
    function Horde_Compress($params = array())
    {
    }

    /**
     * Compress the data.
     *
     * @access public
     *
     * @param string $data            The data to compress.
     * @param optional array $params  An array of arguments needed to
     *                                compress the data.
     *
     * @return mixed  The compressed data.
     *                Returns PEAR_Error object on error.
     */
    function &compress($data, $params = array())
    {
        return PEAR::raiseError('Unsupported');
    }

    /**
     * Decompress the data.
     *
     * @access public
     *
     * @param string $data            The data to decompress.
     * @param optional array $params  An array of arguments needed to
     *                                decompress the data.
     *
     * @return array  The decompressed data.
     *                Returns PEAR_Error object on error.
     */
    function &decompress($data, $params = array())
    {
        return PEAR::raiseError('Unsupported');
    }

}
