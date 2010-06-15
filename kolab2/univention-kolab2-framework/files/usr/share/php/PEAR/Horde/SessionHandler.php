<?php
/**
 * SessionHandler:: defines an API for implementing custom session
 * handlers for PHP.
 *
 * $Horde: framework/SessionHandler/SessionHandler.php,v 1.12 2004/04/07 14:43:13 chuck Exp $
 *
 * Copyright 2002-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_SessionHandler
 */
class SessionHandler {

    /**
     * Attempts to return a concrete SessionHandler instance based on
     * $driver.
     *
     * @param string $driver          The type of concrete SessionHandler
     *                                subclass to return. The is based on the
     *                                driver ($driver). The code is
     *                                dynamically included.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters
     *                                a subclass might need.
     *
     * @return mixed    The newly created concrete SessionHandler instance, or
     *                  false on an error.
     */
    function &factory($driver, $params = null)
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);

        if (is_null($params)) {
            require_once 'Horde.php';
            $params = Horde::getDriverConfig('sessionhandler', $driver);
        }

        if (!empty($app)) {
            require_once $GLOBALS['registry']->getParam('fileroot', $app) . '/lib/SessionHandler/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/SessionHandler/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/SessionHandler/' . $driver . '.php';
        } else {
            @include_once 'Horde/SessionHandler/' . $driver . '.php';
        }

        $class = 'SessionHandler_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete SessionHandler
     * instance based on $driver. It will only create a new instance
     * if no SessionHandler instance with the same parameters
     * currently exists.
     *
     * This method must be invoked as: $var = &SessionHandler::singleton()
     *
     * @param string $driver          See SessionHandler::factory().
     * @param optional array $params  See SessionHandler::factory().
     *
     * @return mixed  The created concrete SessionHandler instance, or false
     *                on error.
     */
    function &singleton($driver, $params = null)
    {
        static $instances = array();

        $signature = serialize(array($driver, $params));
        if (empty($instances[$signature])) {
            $instances[$signature] = &SessionHandler::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
