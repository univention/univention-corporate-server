<?php
/**
 * Editor Class
 *
 * The Editor:: package provides an rte editor for the Horde
 * Application Framework.
 *
 * $Horde: framework/Editor/Editor.php,v 1.6 2004/01/01 15:15:50 jan Exp $
 *
 * Copyright 2003-2004 Nuno Loureiro <nuno@co.sapo.pt>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Nuno Loureiro <nuno@co.sapo.pt>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Editor
 */
class Horde_Editor {

    /**
     * Attempts to return a concrete Horde_Editor instance based on
     * $driver.
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Horde_Editor subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is
     *                                dynamically included. If $driver is an
     *                                array, then we will look in
     *                                $driver[0]/lib/Driver/ for the subclass
     *                                implementation named $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object Horde_Editor  The newly created concrete Horde_Editor instance,
     *                             or false on error.
     */
    function &factory($driver, $params = null)
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);
        if (empty($driver) || $driver == 'none') {
            return $ret = &new Horde_Editor($params);
        }

        if (is_null($params) && class_exists('Horde')) {
            $params = Horde::getDriverConfig('editor', $driver);
        }

        if (!empty($app)) {
            global $registry;
            require_once $registry->getParam('fileroot', $app) . '/lib/Editor/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/Editor/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Editor/' . $driver . '.php';
        } else {
            @include_once 'Horde/Editor/' . $driver . '.php';
        }
        $class = 'Horde_Editor_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete Horde_Editor
     * instance based on $driver. It will only create a new instance
     * if no Horde_Editor instance with the same parameters currently
     * exists.
     *
     * This should be used if multiple cache backends (and, thus,
     * multiple Horde_Editor instances) are required.
     *
     * This method must be invoked as:
     * $var = &Horde_Editor::singleton()
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Horde_Editor subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is
     *                                dynamically included. If $driver is an
     *                                array, then we will look in
     *                                $driver[0]/lib/Editor/ for the subclass
     *                                implementation named $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @since Horde 2.2
     *
     * @return object Horde_Editor  The concrete Horde_Editor reference,
     *                             or false on error.
     */
    function &singleton($driver, $params = null)
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        if (is_null($params) && class_exists('Horde')) {
            $params = Horde::getDriverConfig('cache', $driver);
        }

        $signature = serialize(array($driver, $params));
        if (!array_key_exists($signature, $instances)) {
            $instances[$signature] = &Horde_Editor::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
