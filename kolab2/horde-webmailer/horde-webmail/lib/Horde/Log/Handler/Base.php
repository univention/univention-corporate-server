<?php
/**
 * Horde Log package
 *
 * This package is based on Zend_Log from the Zend Framework
 * (http://framework.zend.com).  Both that package and this
 * one were written by Mike Naberezny and Chuck Hagenbuch.
 *
 * @category Horde
 * @package  Horde_Log
 * @subpackage Handlers
 * @author   Mike Naberezny <mike@maintainable.com>
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 */

/**
 * @category Horde
 * @package  Horde_Log
 * @subpackage Handlers
 * @author   Mike Naberezny <mike@maintainable.com>
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 */
abstract class Horde_Log_Handler_Base
{
    /**
     * @var array of key/value pair options
     */
    protected $_options = array();

    /**
     * @var array of Horde_Log_Filter_Interface
     */
    protected $_filters = array();

    /**
     * Add a filter specific to this handler.
     *
     * @param  Horde_Log_Filter_Interface  $filter
     * @return void
     */
    public function addFilter($filter)
    {
        if (is_integer($filter)) {
            $filter = new Horde_Log_Filter_Level($filter);
        }

        $this->_filters[] = $filter;
    }

    /**
     * Log a message to this handler.
     *
     * @param  array    $event    Log event
     * @return void
     */
    public function log($event)
    {
        // if any local filter rejects the message, don't log it.
        foreach ($this->_filters as $filter) {
            if (!$filter->accept($event)) {
                return;
            }
        }

        $this->write($event);
    }

    /**
     * Sets an option specific to the implementation of the log handler.
     *
     * @param  $optionKey      Key name for the option to be changed.  Keys are handler-specific
     * @param  $optionValue    New value to assign to the option
     * @return bool            True
     */
    public function setOption($optionKey, $optionValue)
    {
        if (!isset($this->_options[$optionKey])) {
            throw new Horde_Log_Exception("Unknown option \"$optionKey\".");
        }
        $this->_options[$optionKey] = $optionValue;

        return true;
    }

    /**
     * Buffer a message to be stored in the storage
     * implemented by this handler.
     *
     * @param  array    $event    Log event
     */
    abstract public function write($event);

}
