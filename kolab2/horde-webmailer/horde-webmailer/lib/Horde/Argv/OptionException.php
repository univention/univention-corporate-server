<?php
/**
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @author   Mike Naberezny <mike@maintainable.com>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Argv
 */

/**
 * Raised if an Option instance is created with invalid or
 * inconsistent arguments.
 *
 * @category Horde
 * @package  Horde_Argv
 */
class Horde_Argv_OptionException extends Horde_Argv_Exception
{
    public function __construct($msg, $option = null)
    {
        $this->optionId = (string)$option;
        if ($this->optionId) {
            parent::__construct(sprintf(_("option %s: %s"), $this->optionId, $msg));
        } else {
            parent::__construct($msg);
        }
    }

}
