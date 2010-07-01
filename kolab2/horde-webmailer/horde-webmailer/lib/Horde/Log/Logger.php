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
 * @author   Mike Naberezny <mike@maintainable.com>
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 */

/**
 * @category Horde
 * @package  Horde_Log
 * @author   Mike Naberezny <mike@maintainable.com>
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 *
 * @method void LOGLEVEL() LOGLEVEL($event) Log an event at LOGLEVEL, where LOGLEVEL has been added with addLevel() or already exists
 * @method void emerg() emerg($event) Log an event at the EMERG log level
 * @method void alert() alert($event) Log an event at the ALERT log level
 * @method void crit() crit($event) Log an event at the CRIT log level
 * @method void err() err($event) Log an event at the ERR log level
 * @method void warn() warn($event) Log an event at the WARN log level
 * @method void notice() notice($event) Log an event at the NOTICE log level
 * @method void info() info($event) Log an event at the INFO log level
 * @method void debug() debug($event) Log an event at the DEBUG log level
 */
class Horde_Log_Logger
{
    /**
     * @var array of log levels where the keys are the
     * level priorities and the values are the level names
     */
    private $_levels = array();

    /**
     * @var array of Horde_Log_Handler_Abstract objects
     */
    private $_handlers = array();

    /**
     * @var array of Horde_Log_Filter_Interface objects
     */
    private $_filters = array();

    /**
     * Class constructor.  Create a new logger
     *
     * @param Horde_Log_Handler_Abstract|null  $handler  default handler
     */
    public function __construct($handler = null)
    {
        $r = new ReflectionClass('Horde_Log');
        $this->_levels = array_flip($r->getConstants());

        if ($handler !== null) {
            $this->addHandler($handler);
        }
    }

    /**
     * Undefined method handler allows a shortcut:
     *   $log->levelName('message')
     *     instead of
     *   $log->log('message', Horde_Log_LEVELNAME)
     *
     * @param  string  $method  log level name
     * @param  string  $params  message to log
     * @return void
     */
    public function __call($method, $params)
    {
        $level = strtoupper($method);
        if (($level = array_search($level, $this->_levels)) !== false) {
            $this->log(array_shift($params), $level);
        } else {
            throw new Horde_Log_Exception('Bad log level');
        }
    }

    /**
     * Log a message at a level
     *
     * @param  mixed    $event  Message to log, either an array or a string
     * @param  integer  $level  Log level of message, required if $message is a string
     * @return void
     */
    public function log($event, $level = null)
    {
        if (empty($this->_handlers)) {
            throw new Horde_Log_Exception('No handlers were added');
        }

        // Create an event array from the given arguments.
        if (is_array($event)) {
            // If we are passed an array, it must contain 'message'
            // and 'level' indices.
            if (!isset($event['message'])) {
                throw new Horde_Log_Exception('Event array did not contain a message');
            }
            if (!isset($event['level'])) {
                if ($level === null) {
                    throw new Horde_Log_Exception('Event array did not contain a log level');
                } else {
                    $event['level'] = $level;
                }
            }
        } else {
            // Create an event array from the message and level
            // arguments.
            $event = array('message' => $event, 'level' => $level);
        }

        if (!isset($this->_levels[$event['level']])) {
            throw new Horde_Log_Exception('Bad log level');
        }

        // Fill in the level name and timestamp for filters, formatters, handlers
        $event['levelName'] = $this->_levels[$event['level']];

        if (!isset($event['timestamp'])) {
            $event['timestamp'] = date('c');
        }

        // If any global filter rejects the event, don't log it.
        foreach ($this->_filters as $filter) {
            if (!$filter->accept($event)) {
                return;
            }
        }

        foreach ($this->_handlers as $handler) {
            $handler->log($event);
        }
    }

    /**
     * Add a custom log level
     *
     * @param  string  $name    Name of level
     * @param  integer  $level  Numeric level
     * @return void
     */
    public function addLevel($name, $level)
    {
        // Log level names must be uppercase for predictability.
        $name = strtoupper($name);

        if (isset($this->_levels[$level])
            || array_search($name, $this->_levels)) {
            throw new Horde_Log_Exception('Existing log levels cannot be overwritten');
        }

        $this->_levels[$level] = $name;
    }

    /**
     * Add a filter that will be applied before all log handlers.
     * Before a message will be received by any of the handlers, it
     * must be accepted by all filters added with this method.
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
     * Add a handler.  A handler is responsible for taking a log
     * message and writing it out to storage.
     *
     * @param  Horde_Log_Handler_Abstract $handler
     * @return void
     */
    public function addHandler($handler)
    {
        $this->_handlers[] = $handler;
    }

}
