<?php
/**
 * @category Horde
 * @package Horde_Xml_Element
 */

/**
 * @category Horde
 * @package Horde_Xml_Element
 */
class Horde_Xml_Element_Exception extends Exception
{

    public function __construct($message = null, $code_or_lasterror = 0)
    {
        if (is_array($code_or_lasterror)) {
            if ($message) {
                $message .= $code_or_lasterror['message'];
            } else {
                $message = $code_or_lasterror['message'];
            }

            $this->file = $code_or_lasterror['file'];
            $this->line = $code_or_lasterror['line'];
            $code = $code_or_lasterror['type'];
        } else {
            $code = $code_or_lasterror;
        }

        parent::__construct($message, $code);
    }

}
