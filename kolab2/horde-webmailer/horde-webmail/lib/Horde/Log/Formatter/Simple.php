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
 * @subpackage Formatters
 * @author   Mike Naberezny <mike@maintainable.com>
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 */

/**
 * @category Horde
 * @package  Horde_Log
 * @subpackage Formatters
 * @author   Mike Naberezny <mike@maintainable.com>
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 */
class Horde_Log_Formatter_Simple
{
    /**
     * Format string
     *
     * @var string
     */
    protected $_format;

    /**
     * Constructor
     */
    public function __construct($options = null)
    {
        if (is_array($options) && isset($options['format'])) {
            $format = $options['format'];
        } else {
            $format = $options;
        }

        if (is_null($format)) {
            $format = '%timestamp% %levelName%: %message%' . PHP_EOL;
        }

        if (!is_string($format)) {
            throw new Horde_Log_Exception('Format must be a string');
        }

        $this->_format = $format;
    }

    /**
     * Formats an event to be written by the handler.
     *
     * @param  array    $event    Log event
     * @return string             formatted line
     */
    public function format($event)
    {
        $output = $this->_format;
        foreach ($event as $name => $value) {
            $output = str_replace("%$name%", $value, $output);
        }
        return $output;
    }

}
