<?php
/**
 * Horde_Scheduler
 *
 * $Horde: framework/Scheduler/Scheduler.php,v 1.21 2004/04/07 14:43:12 chuck Exp $
 *
 * @package Horde_Scheduler
 */
class Horde_Scheduler {

    /**
     * Name of the sleep function.
     * @var string $_sleep
     */
    var $_sleep;

    /**
     * Adjustment factor to sleep in microseconds.
     * @var integer $_sleep_adj
     */
    var $_sleep_adj;

    /**
     * Constructor.
     *
     * Figures out how we can best sleep with microsecond precision
     * based on what platform we're running on.
     */
    function Horde_Scheduler()
    {
        if (substr(PHP_OS, 0, 3) == 'WIN') {
            $this->_sleep = 'sleep';
            $this->_sleep_adj = 1000000;
        } else {
            $this->_sleep = 'usleep';
            $this->_sleep_adj = 1;
        }
    }

    /**
     * Main loop/action function.
     *
     * @abstract
     */
    function run()
    {
    }

    /**
     * Preserve the internal state of the scheduler object that we are
     * passed, and save it to the Horde VFS backend. Horde_Scheduler
     * objects should define __sleep() and __wakeup() serialization
     * callbacks for anything that needs to be done at object
     * serialization or deserialization - handling database
     * connections, etc.
     *
     * @param optional string  $id  An id to uniquely identify this
     *                              scheduler from others of the same class.
     */
    function serialize($id = '')
    {
        require_once 'VFS.php';
        $vfs = &VFS::singleton($GLOBALS['conf']['vfs']['type'],
                               Horde::getDriverConfig('vfs', $GLOBALS['conf']['vfs']['type']));
        if (is_a($vfs, 'PEAR_Error')) {
            Horde::logMessage($vfs, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        $result = $vfs->writeData('.horde/scheduler', get_class($this) . $id, serialize($this), true);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        return true;
    }

    /**
     * Restore a Horde_Scheduler object from the cache.
     *
     * @param string  $class     The name of the Horde_Scheduler object to restore.
     * @param string  $id        An id to uniquely identify this
     *                           scheduler from others of the same class.
     * @param boolean $autosave  (optional) Automatically store (serialize)
     *                           the returned object at script shutdown.
     *                           Defaults to true.
     *
     * @see Horde_Scheduler::serialize()
     */
    function &unserialize($class, $id = '', $autosave = true)
    {
        require_once 'VFS.php';

        // Need a lowercase version of the classname, and a default
        // instance of the scheduler object in case we can't retrieve
        // one.
        $class = strtolower($class);
        $scheduler = &new $class;

        $vfs = &VFS::singleton($GLOBALS['conf']['vfs']['type'],
                               Horde::getDriverConfig('vfs', $GLOBALS['conf']['vfs']['type']));
        if (is_a($vfs, 'PEAR_Error')) {
            Horde::logMessage($vfs, __FILE__, __LINE__, PEAR_LOG_ERR);
        } else {
            $data = $vfs->read('.horde/scheduler', $class . $id);
            if (is_a($data, 'PEAR_Error')) {
                Horde::logMessage($data, __FILE__, __LINE__, PEAR_LOG_ERR);
            } else {
                $scheduler = @unserialize($data);
                if (!$scheduler) {
                    $scheduler = &new $class;
                }
            }
        }

        if ($autosave) {
            register_shutdown_function(array(&$scheduler, 'serialize'));
        }

        return $scheduler;
    }

    /**
     * Platform-independant sleep $msec microseconds.
     *
     * @param integer $msec  Microseconds to sleep.
     */
    function sleep($msec)
    {
        call_user_func($this->_sleep, $msec / $this->_sleep_adj);
    }

    /**
     * Attempts to return a concrete Horde_Scheduler instance based on
     * $driver.
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Horde_Scheduler subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is dynamically
     *                                included. If $driver is an array, then we
     *                                will look in $driver[0]/lib/Horde_Scheduler/ for
     *                                the subclass implementation named
     *                                $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object Horde_Scheduler  The newly created concrete Horde_Scheduler instance, or false
     *                                 on an error.
     */
    function &factory($driver, $params = null)
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);

        if (empty($driver) || (strcmp($driver, 'none') == 0)) {
            return $ret = &new Horde_Scheduler();
        }

        if (!empty($app)) {
            require_once $GLOBALS['registry']->getParam('fileroot', $app) . '/lib/Scheduler/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/Scheduler/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Scheduler/' . $driver . '.php';
        } else {
            // Use include_once here to avoid a fatal error if the
            // class isn't found.
            @include_once 'Horde/Scheduler/' . $driver . '.php';
        }
        $class = 'Horde_Scheduler_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete Horde_Scheduler
     * instance based on $driver. It will only create a new instance
     * if no Horde_Scheduler instance with the same parameters
     * currently exists.
     *
     * This should be used if multiple schedulers (and, thus, multiple
     * Horde_Scheduler instances) are required.
     *
     * This method must be invoked as: $var = &Horde_Scheduler::singleton()
     *
     * @access public
     *
     * @param string $driver          The type of concrete Horde_Scheduler subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is dynamically
     *                                included.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object Horde_Scheduler  The concrete Horde_Scheduler reference, or false on an error.
     */
    function &singleton($driver, $params = null)
    {
        static $instances = array();

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Scheduler::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
