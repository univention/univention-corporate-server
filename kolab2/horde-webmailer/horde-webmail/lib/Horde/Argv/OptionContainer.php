<?php
/**
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @author   Mike Naberezny <mike@maintainable.com>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Argv
 */

/**
 *   Abstract base class.
 *
 *  Class attributes:
 *    standardOptionList : [Option]
 *      list of standard options that will be accepted by all instances
 *      of this parser class (intended to be overridden by subclasses).
 *
 *  Instance attributes:
 *    optionList : [Option]
 *      the list of Option objects contained by this OptionContainer
 *    shortOpt : { string : Option }
 *      dictionary mapping short option strings, eg. "-f" or "-X",
 *      to the Option instances that implement them.  If an Option
 *      has multiple short option strings, it will appears in this
 *      dictionary multiple times. [1]
 *    longOpt : { string : Option }
 *      dictionary mapping long option strings, eg. "--file" or
 *      "--exclude", to the Option instances that implement them.
 *      Again, a given Option can occur multiple times in this
 *      dictionary. [1]
 *    defaults : { string : any }
 *      dictionary mapping option destination names to default
 *      values for each destination [1]
 *
 *  [1] These mappings are common to (shared by) all components of the
 *      controlling Horde_Argv_Parser, where they are initially created.
 *
 * @category Horde
 * @package  Horde_Argv
 */
class Horde_Argv_OptionContainer
{
    public $description = '';
    public $optionList = array();
    public $optionClass = 'Horde_Argv_Option';
    public $defaults = array();
    public $shortOpt = array();
    public $longOpt = array();
    public $conflictHandler;

    /**
     * Initialize the option list and related data structures.
     * This method must be provided by subclasses, and it must
     * initialize at least the following instance attributes:
     * optionList, shortOpt, longOpt, defaults.
    */
    public function __construct($optionClass, $conflictHandler, $description)
    {
        $this->_createOptionList();

        $this->optionClass = $optionClass;
        $this->setConflictHandler($conflictHandler);
        $this->setDescription($description);
    }

    /**
     * For use by Horde_Argv_Parser constructor -- create the master
     * option mappings used by this Horde_Argv_Parser and all
     * OptionGroups that it owns.
     */
    protected function _createOptionMappings()
    {
        $this->shortOpt = array();       // single letter -> Option instance
        $this->longOpt = array();        // long option -> Option instance
        $this->defaults = array();       // maps option dest -> default value
    }

    /**
     * For use by OptionGroup constructor -- use shared option
     * mappings from the Horde_Argv_Parser that owns this OptionGroup.
     */
    protected function _shareOptionMappings($parser)
    {
        $this->shortOpt =& $parser->shortOpt;
        $this->longOpt =& $parser->longOpt;
        $this->defaults = $parser->defaults;
    }

    public function setConflictHandler($handler)
    {
        if (!in_array($handler, array('error', 'resolve'))) {
            throw new InvalidArgumentException('invalid conflictHandler ' . var_export($handler, true));
        }
        $this->conflictHandler = $handler;
    }

    public function setDescription($description)
    {
        $this->description = $description;
    }

    public function getDescription()
    {
        return $this->description;
    }

    // -- Option-adding methods -----------------------------------------

    protected function _checkConflict($option)
    {
        $conflictOpts = array();
        foreach ($option->shortOpts as $opt) {
            if (isset($this->shortOpt[$opt])) {
                $conflictOpts[$opt] = $this->shortOpt[$opt];
            }
        }
        foreach ($option->longOpts as $opt) {
            if (isset($this->longOpt[$opt])) {
                $conflictOpts[$opt] = $this->longOpt[$opt];
            }
        }

        if ($conflictOpts) {
            $handler = $this->conflictHandler;
            if ($handler == 'error') {
                throw new Horde_Argv_OptionConflictException(sprintf(
                    'conflicting option string(s): %s',
                    implode(', ', array_keys($conflictOpts))), $option);
            } elseif ($handler == 'resolve') {
                foreach ($conflictOpts as $opt => $c_option) {
                    if (strncmp($opt, '--', 2) === 0) {
                        $key = array_search($opt, $c_option->longOpts);
                        if ($key !== false) {
                            unset($c_option->longOpts[$key]);
                        }
                        unset($this->longOpt[$opt]);
                    } else {
                        $key = array_search($opt, $c_option->shortOpts);
                        if ($key !== false) {
                            unset($c_option->shortOpts[$key]);
                        }
                        unset($this->shortOpt[$opt]);
                    }

                    if (! ($c_option->shortOpts || $c_option->longOpts)) {
                        $key = array_search($c_option, $c_option->container->optionList);
                        unset($c_option->container->optionList[$key]);
                    }
                }
            }
        }
    }

    public function addOption()
    {
        $opts = func_get_args();

        if (count($opts) && is_string($opts[0])) {
            $optionFactory = new ReflectionClass($this->optionClass);
            $option = $optionFactory->newInstanceArgs($opts);
        } elseif (count($opts) == 1) {
            $option = $opts[0];
            if (!$option instanceof Horde_Argv_Option)
                throw new InvalidArgumentException('not an Option instance: ' . var_export($option, true));
        } else {
            throw new InvalidArgumentException('invalid arguments');
        }

        $this->_checkConflict($option);

        $this->optionList[] = $option;
        $option->container = $this;
        foreach ($option->shortOpts as $opt) {
            $this->shortOpt[$opt] = $option;
        }
        foreach ($option->longOpts as $opt) {
            $this->longOpt[$opt] = $option;
        }

        if (!is_null($option->dest)) {
            // option has a dest, we need a default
            if ($option->default !== Horde_Argv_Option::$NO_DEFAULT) {
                $this->defaults[$option->dest] = $option->default;
            } elseif (!isset($this->defaults[$option->dest])) {
                $this->defaults[$option->dest] = null;
            }
        }

        return $option;
    }

    public function addOptions($optionList)
    {
        foreach ($optionList as $option) {
            $this->addOption($option);
        }
    }

    // -- Option query/removal methods ----------------------------------

    public function getOption($opt_str)
    {
        if (isset($this->shortOpt[$opt_str])) {
            return $this->shortOpt[$opt_str];
        } elseif (isset($this->longOpt[$opt_str])) {
            return $this->longOpt[$opt_str];
        } else {
            return null;
        }
    }

    public function hasOption($opt_str)
    {
        return isset($this->shortOpt[$opt_str])
            || isset($this->longOpt[$opt_str]);
    }

    public function removeOption($opt_str)
    {
        $option = $this->getOption($opt_str);
        if (is_null($option))
            throw new InvalidArgumentException("no such option '$opt_str'");

        foreach ($option->shortOpts as $opt) {
            unset($this->shortOpt[$opt]);
        }
        foreach ($option->longOpts as $opt) {
            unset($this->longOpt[$opt]);
        }
        $key = array_search($option, $option->container->optionList);
        unset($option->container->optionList[$key]);
    }


    // -- Help-formatting methods ---------------------------------------

    public function formatOptionHelp($formatter = null)
    {
        if (!$this->optionList)
            return '';
        $result = array();
        foreach ($this->optionList as $option) {
            if ($option->help != Horde_Argv_Option::SUPPRESS_HELP)
                $result[] = $formatter->formatOption($option);
        }
        return implode('', $result);
    }

    public function formatDescription($formatter = null)
    {
        return $formatter->formatDescription($this->getDescription());
    }

    public function formatHelp($formatter = null)
    {
        $result = array();
        if ($this->description)
            $result[] = $this->formatDescription($formatter);
        if ($this->optionList)
            $result[] = $this->formatOptionHelp($formatter);
        return implode("\n", $result);
    }

}
