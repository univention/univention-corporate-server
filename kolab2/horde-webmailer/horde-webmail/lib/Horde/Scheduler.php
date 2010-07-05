<?php

require_once 'Horde.php';
require_once 'VFS.php';

/**
 * Horde_Scheduler
 *
 * $Horde: framework/Scheduler/lib/Horde/Scheduler.php,v 1.1.2.1 2007-12-20 13:49:37 jan Exp $
 *
 * @package Horde_Scheduler
 */
class Horde_Scheduler {

    /**
     * Name of the sleep function.
     *
     * @var string
     */
    var $_sleep;

    /**
     * Adjustment factor to sleep in microseconds.
     *
     * @var integer
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
        if (!strncasecmp(PHP_OS, 'WIN', 3)) {
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
     * @param string  $id  An id to uniquely identify this scheduler from
     *                     others of the same class.
     */
    function serialize($id = '')
    {
        $vfs = &VFS::singleton($GLOBALS['conf']['vfs']['type'],
                               Horde::getDriverConfig('vfs', $GLOBALS['conf']['vfs']['type']));
        if (is_a($vfs, 'PEAR_Error')) {
            Horde::logMessage($vfs, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        $result = $vfs->writeData('.horde/scheduler', String::lower(get_class($this)) . $id, serialize($this), true);
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
     * @param boolean $autosave  Automatically store (serialize) the returned
     *                           object at script shutdown.
     *
     * @see Horde_Scheduler::serialize()
     */
    function &unserialize($class, $id = '', $autosave = true)
    {
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
                Horde::logMessage($data, __FILE__, __LINE__, PEAR_LOG_INFO);
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
     * Attempts to return a concrete Horde_Scheduler instance based on $driver.
     *
     * @param string $driver The type of concrete Horde_Scheduler subclass to
     *                       return.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Horde_Scheduler  The newly created concrete Horde_Scheduler
     *                          instance, or an error object.
     */
    function factory($driver, $params = null)
    {
        $driver = basename($driver);
        $class = 'Horde_Scheduler_' . $driver;
        if (!class_exists($class)) {
            include 'Horde/Scheduler/' . $driver . '.php';
        }

        if (class_exists($class)) {
            return new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

}
