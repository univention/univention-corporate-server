<?php

require_once 'Net/IMSP.php';

/**
 * The Net_IMSP_Auth class abstract class for IMSP authentication.
 *
 * Required Parameters:<pre>
 *   'username'  Username to logon to IMSP server as.
 *   'password'  Password for current user.
 *   'server'    The hostname of the IMSP server.
 *   'port'      The port of the IMSP server.</pre>
 *
 * $Horde: framework/Net_IMSP/IMSP/Auth.php,v 1.8.10.15 2009-01-06 15:23:27 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @package Net_IMSP
 */
class Net_IMSP_Auth {
    /**
     * Class variable to hold the resulting Net_IMSP object
     *
     * @var Net_IMSP
     */
    var $_imsp;

     /**
     * Attempts to login to IMSP server.
     *
     * @param array $params         Parameters for Net_IMSP
     * @param boolean $login        Should we remain logged in after auth?
     *
     * @return mixed                Returns a Net_IMSP object connected to
     *                              the IMSP server if login is true and
     *                              successful.  Returns boolean true if
     *                              successful and login is false. Returns
     *                              PEAR_Error on failure.
     */
    function &authenticate($params, $login = true)
    {
        $this->_imsp = &$this->_authenticate($params);

        if (is_a($this->_imsp, 'PEAR_Error')) {
            return $this->_imsp;
        }

        if (!$login) {
            $this->_imsp->logout();
            return true;
        }

        return $this->_imsp;
    }

    /**
     * Private authentication function. Provides actual authentication
     * code.
     *
     * @access private
     * @param  array   $params      Parameters for Net_IMSP_Auth driver.
     *
     * @return mixed                Returns Net_IMSP object connected to server
     *                              if successful, PEAR_Error on failure.
     * @abstract
     */
    function _authenticate($params)
    {

    }

    /**
     * Returns the type of this driver.
     *
     * @abstract
     * @return string Type of IMSP_Auth driver instance
     */
    function getDriverType()
    {

    }

    /**
     * Force a logout from the underlying IMSP stream.
     *
     */
    function logout()
    {

    }

    /**
     * Attempts to return a concrete Net_IMSP_Auth instance based on $driver
     * Must be called as &Net_IMSP_Auth::factory()
     *
     * @param  string $driver Type of Net_IMSP_Auth subclass to return.
     *
     * @return mixed  The created Net_IMSP_Auth subclass or PEAR_Error.
     */
    function factory($driver)
    {
        $driver = basename($driver);

        if (empty($driver) || (strcmp($driver, 'none') == 0)) {
            return new Net_IMSP_Auth();
        }

        if (file_exists(dirname(__FILE__) . '/Auth/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Auth/' . $driver . '.php';
        }

        $class = 'Net_IMSP_Auth_' . $driver;

        if (class_exists($class)) {
            return new $class();
        } else {
            Horde::fatal(PEAR::raiseError(sprintf(_("Unable to load the definition of %s."), $class)), __FILE__, __LINE__);
        }
    }

    /**
     * Attempts to return a concrete Net_IMSP_Auth instance based on $driver.
     * Will only create a new object if one with the same parameters already
     * does not exist.
     * Must be called like: $var = &Net_IMSP_Auth::singleton('driver_type');
     *
     * @param  string $driver Type of IMSP_Auth subclass to return.
     *
     * @return object Reference to IMSP_Auth subclass.
     */
    function &singleton($driver)
    {
        static $instances;
        /* Check for any imtest driver instances and kill them.
           Otherwise, the socket will hang between requests from
           seperate drivers (an Auth request and an Options request).*/
        if (is_array($instances)) {
            foreach ($instances as $obj) {
                if ($obj->getDriverType() == 'imtest') {
                    $obj->logout();
                }
            }
        }
        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver));
        if (!isset($instances[$signature])) {
            $instances[$signature] = Net_IMSP_Auth::factory($driver);
        }

        return $instances[$signature];
    }

}
