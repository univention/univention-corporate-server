<?php
/**
 * Horde Log package
 *
 * This package is based on Zend_Log from the Zend Framework
 * (http://framework.zend.com).  Both that package and this
 * one were written by Mike Naberezny and Chuck Hagenbuch.
 *
 * @package  Horde_Log
 * @author   Mike Naberezny <mike@maintainable.com>
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 */

/**
 * @package  Horde_Log
 * @author   Mike Naberezny <mike@maintainable.com>
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 */
class Horde_Log_Filter_Level implements Horde_Log_Filter_Interface
{
    /**
     * @var integer
     */
    protected $_level;

    /**
     * Filter out any log messages greater than $level.
     *
     * @param  integer  $level  Maximum log level to pass through the filter
     */
    public function __construct($level)
    {
        if (! is_integer($level)) {
            throw new Horde_Log_Exception('Level must be an integer');
        }

        $this->_level = $level;
    }

    /**
     * Returns TRUE to accept the message, FALSE to block it.
     *
     * @param  array    $event    Log event
     * @return boolean            accepted?
     */
    public function accept($event)
    {
        return $event['level'] <= $this->_level;
    }

}
