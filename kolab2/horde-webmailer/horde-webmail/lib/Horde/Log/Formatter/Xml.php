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
class Horde_Log_Formatter_Xml
{
    protected $_options = array('elementEntry'     => 'log',
                                'elementTimestamp' => 'timestamp',
                                'elementMessage'   => 'message',
                                'elementLevel'     => 'level',
                                'lineEnding'       => PHP_EOL);

    public function __construct($options = array())
    {
        $this->_options = array_merge($this->_options, $options);
    }

    /**
     * Formats an event to be written by the handler.
     *
     * @param  array    $event    Log event
     * @return string             XML string
     */
    public function format($event)
    {
        $dom = new DOMDocument();

        $elt = $dom->appendChild(new DOMElement($this->_options['elementEntry']));
        $elt->appendChild(new DOMElement($this->_options['elementTimestamp'], date('c')));
        $elt->appendChild(new DOMElement($this->_options['elementMessage'], $event['message']));
        $elt->appendChild(new DOMElement($this->_options['elementLevel'], $event['level']));

        $xml = $dom->saveXML();
        $xml = preg_replace('/<\?xml version="1.0"( encoding="[^\"]*")?\?>\n/u', '', $xml);

        return $xml . $this->_options['lineEnding'];
    }

}
