<?php
/**
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @author   Mike Naberezny <mike@maintainable.com>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Argv
 */

/**
 * Raised if an invalid option is seen on the command line.
 *
 * @category Horde
 * @package  Horde_Argv
 */
class Horde_Argv_BadOptionException extends Horde_Argv_OptionException
{
    public function __construct($opt_str)
    {
        parent::__construct(sprintf(_("no such option: %s"), $opt_str));
    }

}
