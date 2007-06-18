<?php

require_once 'Net/IMSP.php';

/**
 * The Net_IMSP_Auth class abstract class for IMSP authentication.
 *
 * Required Parameters:
 * ====================
 * 'username'       -- Username to logon to IMSP server as.
 * 'password'       -- Password for current user.
 * 'server'         -- The hostname of the IMSP server.
 * 'port'           -- The port of the IMSP server.
 *
 * $Horde: framework/Net_IMSP/IMSP/Auth.php,v 1.8 2004/04/19 20:27:37 chuck Exp $
 *
 * Copyright 2003-2004 Michael Rubinsky <mike@theupstairsroom.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @version $Revision 1.5 $
 * @author  Michael Rubinsky <mike@theupstairsroom.com>
 * @package Net_IMSP
 */
class Net_IMSP_Auth {

    /**
     * Attempts to login to IMSP server.
     *
     * @access public
     * @param array $params         Parameters for Net_IMSP
     * @param boolean $login        Should we remain logged in after auth?
     * @return mixed                Returns a Net_IMSP object connected to
     *                              the IMSP server if login is true and
     *                              successful.  Returns boolean true if
     *                              successful and login is false. Returns
     *                              PEAR_Error on failure.
     */
    function &authenticate($params, $login = true)
    {
        $_imsp = &$this->_authenticate($params);

        if (is_a($_imsp, 'PEAR_Error')) {
            return $_imsp;
        }

        if (!$login) {
            $_imsp->logout();
            return true;
        }

        return $_imsp;
    }

    /**
     * Private authentication function. Provides actual authentication
     * code.
     *
     * @abstract
     * @access private
     * @param array $params         Parameters for Net_IMSP_Auth driver.
     * @return mixed                Returns Net_IMSP object connected to server
     *                              if successful, PEAR_Error on failure.
     */
    function &_authenticate($params)
    {

    }
    /**
     * Attempts to return a concrete Net_IMSP_Auth instance based on $driver
     * Must be called as &Net_IMSP_Auth::factory()
     *
     * @access public
     * @param string $driver Type of Net_IMSP_Auth subclass to return.
     * @return mixed The created Net_IMSP_Auth subclass or PEAR_Error.
     */
    function &factory($driver)
    {
        $driver = basename($driver);

        if (empty($driver) || (strcmp($driver, 'none') == 0)) {
            return $ret = &new IMSP_Auth();
        }

        if (file_exists(dirname(__FILE__) . '/Auth/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Auth/' . $driver . '.php';
        }

        $class = 'Net_IMSP_Auth_' . $driver;

        if (class_exists($class)) {
            return $ret = &new $class();
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
     * @param string $driver Type of IMSP_Auth subclass to return.
     * @return object Reference to IMSP_Auth subclass.
     */
    function &singleton($driver)
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Net_IMSP_Auth::factory($driver);
        }

        return $instances[$signature];
    }

}
