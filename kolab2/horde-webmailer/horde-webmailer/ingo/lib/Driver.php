<?php
/**
 * Ingo_Driver:: defines an API to activate filter scripts on a server.
 *
 * $Horde: ingo/lib/Driver.php,v 1.10.10.8 2007-12-20 14:05:47 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Ingo
 */
class Ingo_Driver {

    /**
     * Driver specific parameters
     *
     * @var array
     */
    var $_params = array(
        'username' => null,
        'password' => null
    );

    /**
     * Whether this driver allows managing other users' rules.
     *
     * @var boolean
     */
    var $_support_shares = false;

    /**
     * Attempts to return a concrete Ingo_Driver instance based on $driver.
     *
     * @param string $driver  The type of concrete Ingo_Driver subclass to
     *                        return.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return mixed  The newly created concrete Ingo_Driver instance, or
     *                false on error.
     */
    function factory($driver, $params = array())
    {
        $driver = basename($driver);
        require_once dirname(__FILE__) . '/Driver/' . $driver . '.php';
        $class = 'Ingo_Driver_' . $driver;
        if (class_exists($class)) {
            return new $class($params);
        } else {
            return false;
        }
    }

    /**
     * Constructor.
     */
    function Ingo_Driver($params = array())
    {
        $this->_params = array_merge($this->_params, $params);
    }

    /**
     * Sets a script running on the backend.
     *
     * @param string $script  The filter script.
     *
     * @return mixed  True on success, false if script can't be activated.
     *                Returns PEAR_Error on error.
     */
    function setScriptActive($script)
    {
        return false;
    }

    /**
     * Returns whether the driver supports managing other users' rules.
     *
     * @return boolean  True if the driver supports shares.
     */
    function supportShares()
    {
        return $this->_support_shares && !empty($_SESSION['ingo']['backend']['shares']);
    }

}
