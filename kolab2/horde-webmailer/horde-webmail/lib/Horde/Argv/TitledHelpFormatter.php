<?php
/**
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @author   Mike Naberezny <mike@maintainable.com>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Argv
 */

/**
 * Format help with underlined section headers.
 *
 * @category Horde
 * @package  Horde_Argv
 */
class Horde_Argv_TitledHelpFormatter extends Horde_Argv_HelpFormatter
{
    public function __construct(
        $indent_increment = 0,
        $max_help_position = 24,
        $width = null,
        $short_first = false)
    {
        parent::__construct($indent_increment, $max_help_position, $width, $short_first);
    }

    public function formatUsage($usage)
    {
        return sprintf("%s  %s\n", $this->formatHeading(_("Usage")), $usage);
    }

    public function formatHeading($heading)
    {
        $prefix = array('=', '-');
        return sprintf("%s\n%s\n", $heading, str_repeat($prefix[$this->level], strlen($heading)));
    }

}
