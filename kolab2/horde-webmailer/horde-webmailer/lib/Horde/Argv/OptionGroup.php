<?php
/**
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @author   Mike Naberezny <mike@maintainable.com>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Argv
 */

/**
 * @category Horde
 * @package  Horde_Argv
 */
class Horde_Argv_OptionGroup extends Horde_Argv_OptionContainer
{
    protected $_title;

    public function __construct($parser, $title, $description = null)
    {
        $this->parser = $parser;
        parent::__construct($parser->optionClass, $parser->conflictHandler, $description);
        $this->_title = $title;
    }

    protected function _createOptionList()
    {
        $this->optionList = array();
        $this->_shareOptionMappings($this->parser);
    }

    public function setTitle($title)
    {
        $this->_title = $title;
    }

    public function __destruct()
    {
        unset($this->optionList);
    }

    // -- Help-formatting methods ---------------------------------------

    public function formatHelp($formatter = null)
    {
        if (is_null($formatter))
            return '';

        $result = $formatter->formatHeading($this->_title);
        $formatter->indent();
        $result .= parent::formatHelp($formatter);
        $formatter->dedent();
        return $result;
    }

}
