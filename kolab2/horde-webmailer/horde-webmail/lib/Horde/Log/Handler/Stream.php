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
class Horde_Log_Handler_Stream extends Horde_Log_Handler_Base
{
    /**
     * Formats the log message before writing.
     * @var Horde_Log_Formatter_Interface
     */
    protected $_formatter;

    /**
     * Holds the PHP stream to log to.
     * @var null|stream
     */
    protected $_stream = null;

    /**
     * Class Constructor
     *
     * @param mixed $streamOrUrl   Stream or URL to open as a stream
     * @param string $mode         Mode, only applicable if a URL is given
     */
    public function __construct($streamOrUrl, $mode = 'a+')
    {
        $this->_formatter = new Horde_Log_Formatter_Simple();

        if (is_resource($streamOrUrl)) {
            if (get_resource_type($streamOrUrl) != 'stream') {
                throw new Horde_Log_Exception('Resource is not a stream');
            }

            if ($mode != 'a+') {
                throw new Horde_Log_Exception('Mode cannot be changed on existing streams');
            }

            $this->_stream = $streamOrUrl;
        } else {
            if (! $this->_stream = @fopen($streamOrUrl, $mode, false)) {
                $msg = "\"$streamOrUrl\" cannot be opened with mode \"$mode\"";
                throw new Horde_Log_Exception($msg);
            }
        }
    }

    /**
     * Write a message to the log.
     *
     * @param  array    $event    Log event
     * @return bool               Always True
     */
    public function write($event)
    {
        $line = $this->_formatter->format($event);

        if (! @fwrite($this->_stream, $line)) {
            throw new Horde_Log_Exception("Unable to write to stream");
        }

        return true;
    }

}
