<?php
/**
 * $Horde: framework/Feed/lib/Horde/Feed/Exception.php,v 1.1.2.2 2008-01-02 11:33:42 jan Exp $
 *
 * @category Horde
 * @package Horde_Feed
 */

/**
 * @category Horde
 * @package Horde_Feed
 */
class Horde_Feed_Exception extends Exception {

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
