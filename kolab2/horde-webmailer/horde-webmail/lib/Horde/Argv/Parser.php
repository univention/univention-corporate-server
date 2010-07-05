<?php
/**
 * Horde command-line argument parsing package.
 *
 * This package is ported from Python's Optik (http://optik.sourceforge.net/).
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @author   Mike Naberezny <mike@maintainable.com>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Argv
 */

/**
 *  Class attributes:
 *    standardOptionList : [Option]
 *      list of standard options that will be accepted by all instances
 *      of this parser class (intended to be overridden by subclasses).
 *
 *  Instance attributes:
 *    usage : string
 *      a usage string for your program.  Before it is displayed
 *      to the user, "%prog" will be expanded to the name of
 *      your program ($this->prog or os.path.basename(sys.argv[0])).
 *    prog : string
 *      the name of the current program (to override
 *      os.path.basename(sys.argv[0])).
 *    epilog : string
 *      paragraph of help text to print after option help
 *
 *    optionGroups : [OptionGroup]
 *      list of option groups in this parser (option groups are
 *      irrelevant for parsing the command-line, but very useful
 *      for generating help)
 *
 *    allow_interspersed_args : bool = true
 *      if true, positional arguments may be interspersed with options.
 *      Assuming -a and -b each take a single argument, the command-line
 *        -ablah foo bar -bboo baz
 *      will be interpreted the same as
 *        -ablah -bboo -- foo bar baz
 *      If this flag were false, that command line would be interpreted as
 *        -ablah -- foo bar -bboo baz
 *      -- ie. we stop processing options as soon as we see the first
 *      non-option argument.  (This is the tradition followed by
 *      Python's getopt module, Perl's Getopt::Std, and other argument-
 *      parsing libraries, but it is generally annoying to users.)
 *
 *    rargs : [string]
 *      the argument list currently being parsed.  Only set when
 *      parseArgs() is active, and continually trimmed down as
 *      we consume arguments.  Mainly there for the benefit of
 *      callback options.
 *    largs : [string]
 *      the list of leftover arguments that we have skipped while
 *      parsing options.  If allow_interspersed_args is false, this
 *      list is always empty.
 *    values : Values
 *      the set of option values currently being accumulated.  Only
 *      set when parseArgs() is active.  Also mainly for callbacks.
 *
 * @category Horde
 * @package  Horde_Argv
 */
class Horde_Argv_Parser extends Horde_Argv_OptionContainer
{
    public $standardOptionList = array();

    protected $_usage;
    public $optionGroups = array();

    public function __construct($args = array())
    {
        $args = array_merge(array(
            'usage' => null,
            'optionList' => null,
            'optionClass' => 'Horde_Argv_Option',
            'version' => null,
            'conflictHandler' => "error",
            'description' => null,
            'formatter' => null,
            'addHelpOption' => true,
            'prog' => null,
            'epilog' => null),
            $args);

        parent::__construct($args['optionClass'], $args['conflictHandler'], $args['description']);
        $this->setUsage($args['usage']);
        $this->prog = $args['prog'];
        $this->version = $args['version'];
        $this->allow_interspersed_args = true;
        if (is_null($args['formatter']))
            $args['formatter'] = new Horde_Argv_IndentedHelpFormatter();
        $this->formatter = $args['formatter'];
        $this->formatter->setParser($this);
        $this->epilog = $args['epilog'];

        // Populate the option list; initial sources are the
        // standardOptionList class attribute, the 'optionList'
        // argument, and (if applicable) the _addVersionOption() and
        // _addHelpOption() methods.
        $this->_populateOptionList($args['optionList'],
                                   $args['addHelpOption']);

        $this->_initParsingState();
    }

    /**
     *  Declare that you are done with this Horde_Argv_Parser.  This cleans up
     *  reference cycles so the Horde_Argv_Parser (and all objects referenced by
     *  it) can be garbage-collected promptly.  After calling destroy(), the
     *  Horde_Argv_Parser is unusable.
     */
    public function __destruct()
    {
        foreach ($this->optionGroups as &$group) {
            unset($group);
        }

        unset($this->optionList);
        unset($this->optionGroups);
        unset($this->formatter);
    }

    // -- Private methods -----------------------------------------------
    // (used by our or OptionContainer's constructor)

    protected function _createOptionList()
    {
        $this->optionList = array();
        $this->optionGroups = array();
        $this->_createOptionMappings();
    }

    protected function _addHelpOption()
    {
        $this->addOption('-h', '--help', array('action' => 'help',
                                               'help' => _("show this help message and exit")));
    }

    protected function _addVersionOption()
    {
        $this->addOption('--version', array('action' => 'version',
                                            'help' => _("show program's version number and exit")));
    }

    protected function _populateOptionList($optionList, $add_help = true)
    {
        if ($this->standardOptionList)
            $this->addOptions($this->standardOptionList);
        if ($optionList)
            $this->addOptions($optionList);
        if ($this->version)
            $this->_addVersionOption();
        if ($add_help)
            $this->_addHelpOption();
    }

    protected function _initParsingState()
    {
        // These are set in parseArgs() for the convenience of callbacks.
        $this->rargs = null;
        $this->largs = null;
        $this->values = null;
    }

    // -- Simple modifier methods ---------------------------------------

    public function setUsage($usage)
    {
        if (is_null($usage))
            $this->_usage = '%prog ' . _("[options]");
        elseif ($usage == Horde_Argv_Option::SUPPRESS_USAGE)
            $this->_usage = null;
        else
            $this->_usage = $usage;
    }

    public function enableInterspersedArgs()
    {
        $this->allow_interspersed_args = true;
    }

    public function disableInterspersedArgs()
    {
        $this->allow_interspersed_args = false;
    }

    public function setDefault($dest, $value)
    {
        $this->defaults[$dest] = $value;
    }

    public function setDefaults($defaults)
    {
        $this->defaults = array_merge($this->defaults, $defaults);
    }

    protected function _getAllOptions()
    {
        $options = $this->optionList;
        foreach ($this->optionGroups as $group) {
            $options = array_merge($options, $group->optionList);
        }
        return $options;
    }

    public function getDefaultValues()
    {
        $defaults = $this->defaults;
        foreach ($this->_getAllOptions() as $option) {
            $default = isset($defaults[$option->dest]) ? $defaults[$option->dest] : null;
            if (is_string($default)) {
                $opt_str = $option->getOptString();
                $defaults[$option->dest] = $option->checkValue($opt_str, $default);
            }
        }

        return new Horde_Argv_Values($defaults);
    }


    // -- OptionGroup methods -------------------------------------------

    public function addOptionGroup()
    {
        // XXX lots of overlap with OptionContainer::addOption()
        $args = func_get_args();

        if (count($args) && is_string($args[0])) {
            $groupFactory = new ReflectionClass('Horde_Argv_OptionGroup');
            array_unshift($args, $this);
            $group = $groupFactory->newInstanceArgs($args);
        } elseif (count($args) == 1) {
            $group = $args[0];
            if (!$group instanceof Horde_Argv_OptionGroup)
                throw new InvalidArgumentException("not an OptionGroup instance: " . var_export($group, true));
            if ($group->parser !== $this)
                throw new InvalidArgumentException("invalid OptionGroup (wrong parser)");
        } else {
            throw new InvalidArgumentException('invalid arguments');
        }

        $this->optionGroups[] = $group;
        return $group;
    }

    public function getOptionGroup($opt_str)
    {
        if (isset($this->shortOpt[$opt_str])) {
            $option = $this->shortOpt[$opt_str];
        } elseif (isset($this->longOpt[$opt_str])) {
            $option = $this->longOpt[$opt_str];
        } else {
            return null;
        }

        if ($option->container !== $this) {
            return $option->container;
        }

        return null;
    }

    // -- Option-parsing methods ----------------------------------------

    protected function _getArgs($args = null)
    {
        if (is_null($args)) {
            $args = $_SERVER['argv'];
            array_shift($args);
            return $args;
        } else {
            return $args;
        }
    }

    /**
     *  Parse the command-line options found in 'args' (default:
     *  sys.argv[1:]).  Any errors result in a call to 'parserError()', which
     *  by default prints the usage message to stderr and calls
     *  exit() with an error message.  On success returns a pair
     *  (values, args) where 'values' is an Values instance (with all
     *  your option values) and 'args' is the list of arguments left
     *  over after parsing options.
     */
    public function parseArgs($args = null, $values = null)
    {
        $rargs = $this->_getArgs($args);
        $largs = array();
        if (is_null($values))
            $values = $this->getDefaultValues();

        // Store the halves of the argument list as attributes for the
        // convenience of callbacks:
        //   rargs
        //     the rest of the command-line (the "r" stands for
        //     "remaining" or "right-hand")
        //   largs
        //     the leftover arguments -- ie. what's left after removing
        //     options and their arguments (the "l" stands for "leftover"
        //     or "left-hand")
        $this->rargs =& $rargs;
        $this->largs =& $largs;
        $this->values = $values;

        try {
            $this->_processArgs($largs, $rargs, $values);
        } catch (Horde_Argv_BadOptionException $e) {
            $this->parserError($e->getMessage());
        } catch (Horde_Argv_OptionValueException $e) {
            $this->parserError($e->getMessage());
        }

        $args = array_merge($largs, $rargs);
        return $this->checkValues($values, $args);
    }

    /**
     *  Check that the supplied option values and leftover arguments are
     *  valid.  Returns the option values and leftover arguments
     *  (possibly adjusted, possibly completely new -- whatever you
     *  like).  Default implementation just returns the passed-in
     *  values; subclasses may override as desired.
     */
    public function checkValues($values, $args)
    {
        return array($values, $args);
    }

    /**
     *  _process_args(largs : [string],
     *                rargs : [string],
     *                values : Values)
     *
     *  Process command-line arguments and populate 'values', consuming
     *  options and arguments from 'rargs'.  If 'allow_interspersed_args' is
     *  false, stop at the first non-option argument.  If true, accumulate any
     *  interspersed non-option arguments in 'largs'.
     */
    protected function _processArgs(&$largs, &$rargs, &$values)
    {
        while ($rargs) {
            $arg = $rargs[0];
            // We handle bare "--" explicitly, and bare "-" is handled by the
            // standard arg handler since the short arg case ensures that the
            // len of the opt string is greater than 1.
            if ($arg == '--') {
                array_shift($rargs);
                return;
            } elseif (substr($arg, 0, 2) == '--') {
                // process a single long option (possibly with value(s))
                $this->_processLongOpt($rargs, $values);
            } elseif (substr($arg, 0, 1) == '-' && strlen($arg) > 1) {
                // process a cluster of short options (possibly with
                // value(s) for the last one only)
                $this->_processShortOpts($rargs, $values);
            } elseif ($this->allow_interspersed_args) {
                $largs[] = $arg;
                array_shift($rargs);
            } else {
                // stop now, leave this arg in rargs
                return;
            }
        }

        // Say this is the original argument list:
        // [arg0, arg1, ..., arg(i-1), arg(i), arg(i+1), ..., arg(N-1)]
        //                            ^
        // (we are about to process arg(i)).
        //
        // Then rargs is [arg(i), ..., arg(N-1)] and largs is a *subset* of
        // [arg0, ..., arg(i-1)] (any options and their arguments will have
        // been removed from largs).
        //
        // The while loop will usually consume 1 or more arguments per pass.
        // If it consumes 1 (eg. arg is an option that takes no arguments),
        // then after _process_arg() is done the situation is:
        //
        //   largs = subset of [arg0, ..., arg(i)]
        //   rargs = [arg(i+1), ..., arg(N-1)]
        //
        // If allow_interspersed_args is false, largs will always be
        // *empty* -- still a subset of [arg0, ..., arg(i-1)], but
        // not a very interesting subset!
    }

    /**
     *  opt : string) -> string
     *
     *    Determine which long option string 'opt' matches, ie. which one
     *    it is an unambiguous abbrevation for.  Raises BadOptionError if
     *    'opt' doesn't unambiguously match any long option string.
     */
    protected function _matchLongOpt($opt)
    {
        return self::matchAbbrev($opt, $this->longOpt);
    }

    /**
     *  (s : string, wordmap : {string : Option}) -> string
     *
     *  Return the string key in 'wordmap' for which 's' is an unambiguous
     *  abbreviation.  If 's' is found to be ambiguous or doesn't match any of
     *  'words', raise BadOptionError.
     */
    public static function matchAbbrev($s, $wordmap)
    {
        // Is there an exact match?
        if (array_key_exists($s, $wordmap)) {
            return $s;
        }

        // Isolate all words with s as a prefix.
        $possibilities = array();
        foreach (array_keys($wordmap) as $word) {
            if (strncmp($word, $s, strlen($s)) === 0) {
                $possibilities[] = $word;
            }
        }

        // No exact match, so there had better be just one possibility.
        if (count($possibilities) == 1) {
            return $possibilities[0];
        } elseif (!$possibilities) {
            throw new Horde_Argv_BadOptionException($s);
        } else {
            // More than one possible completion: ambiguous prefix.
            sort($possibilities);
            throw new Horde_Argv_AmbiguousOptionException($s, $possibilities);
        }
    }

    protected function _processLongOpt(&$rargs, &$values)
    {
        $arg = array_shift($rargs);

        // Value explicitly attached to arg?  Pretend it's the next
        // argument.
        if (strpos($arg, '=') !== false) {
            list($opt, $next_arg) = explode('=', $arg, 2);
            array_unshift($rargs, $next_arg);
            $had_explicit_value = true;
        } else {
            $opt = $arg;
            $had_explicit_value = false;
        }

        $opt = $this->_matchLongOpt($opt);
        $option = $this->longOpt[$opt];
        if ($option->takesValue()) {
            $nargs = $option->nargs;
            if (count($rargs) < $nargs) {
                if ($nargs == 1)
                    $this->parserError(sprintf(_("%s option requires an argument"), $opt));
                else
                    $this->parserError(sprintf(_("%s option requires %d arguments"),
                                               $opt, $nargs));
            } elseif ($nargs == 1) {
                $value = array_shift($rargs);
            } else {
                $value = array_splice($rargs, 0, $nargs);
            }

        } elseif ($had_explicit_value) {
            $this->parserError(sprintf(_("%s option does not take a value"), $opt));

        } else {
            $value = null;
        }

        $option->process($opt, $value, $values, $this);
    }

    protected function _processShortOpts(&$rargs, &$values)
    {
        $arg = array_shift($rargs);
        $stop = false;
        $i = 1;
        for ($c = 1, $c_max = strlen($arg); $c < $c_max; $c++) {
            $ch = $arg[$c];
            $opt = '-' . $ch;
            $option = isset($this->shortOpt[$opt]) ? $this->shortOpt[$opt] : null;
            $i++; // we have consumed a character

            if (!$option)
                throw new Horde_Argv_BadOptionException($opt);

            if ($option->takesValue()) {
                // Any characters left in arg?  Pretend they're the
                // next arg, and stop consuming characters of arg.
                if ($i < strlen($arg)) {
                    array_unshift($rargs, substr($arg, $i));
                    $stop = true;
                }

                $nargs = $option->nargs;
                if (count($rargs) < $nargs) {
                    if ($nargs == 1)
                        $this->parserError(sprintf(_("%s option requires an argument"), $opt));
                    else
                        $this->parserError(sprintf(_("%s option requires %d arguments"), $opt, $nargs));

                } elseif ($nargs == 1) {
                    $value = array_shift($rargs);
                } else {
                    $value = array_splice($rargs, 0, $nargs);
                }

            } else {
                // option doesn't take a value
                $value = null;
            }

            $option->process($opt, $value, $values, $this);

            if ($stop)
                break;
        }
    }

    // -- Feedback methods ----------------------------------------------

    public function getProgName()
    {
        if (is_null($this->prog))
            return basename($_SERVER['argv'][0]);
        else
            return $this->prog;
    }

    public function expandProgName($s)
    {
        return str_replace("%prog", $this->getProgName(), $s);
    }

    public function getDescription()
    {
        return $this->expandProgName($this->description);
    }

    public function parserExit($status = 0, $msg = null)
    {
        if ($msg)
            fwrite(STDERR, $msg);
        exit($status);
    }

    /**
     * Print a usage message incorporating $msg to stderr and exit.
     * If you override this in a subclass, it should not return -- it
     * should either exit or raise an exception.
     *
     * @param string $msg
     */
    public function parserError($msg)
    {
        $this->printUsage(STDERR);
        $this->parserExit(2, sprintf("%s: error: %s\n", $this->getProgName(), $msg));
    }

    public function getUsage($formatter = null)
    {
        if (is_null($formatter))
            $formatter = $this->formatter;
        if ($this->_usage)
            return $formatter->formatUsage($this->expandProgName($this->_usage));
        else
            return '';
    }

    /**
     *  (file : file = stdout)
     *
     *  Print the usage message for the current program ($this->_usage) to
     *  'file' (default stdout).  Any occurence of the string "%prog" in
     *  $this->_usage is replaced with the name of the current program
     *  (basename of sys.argv[0]).  Does nothing if $this->_usage is empty
     *  or not defined.
     */
    public function printUsage($file = null)
    {
        if (!$this->_usage)
            return;

        if (is_null($file))
            echo $this->getUsage();
        else
            fwrite($file, $this->getUsage());
    }

    public function getVersion()
    {
        if ($this->version)
            return $this->expandProgName($this->version);
        else
            return '';
    }

    /**
     * file : file = stdout
     *
     *    Print the version message for this program ($this->version) to
     *    'file' (default stdout).  As with printUsage(), any occurence
     *    of "%prog" in $this->version is replaced by the current program's
     *    name.  Does nothing if $this->version is empty or undefined.
     */
    public function printVersion($file = null)
    {
        if (!$this->version)
            return;

        if (is_null($file))
            echo $this->getVersion() . "\n";
        else
            fwrite($file, $this->getVersion() . "\n");
    }

    public function formatOptionHelp($formatter = null)
    {
        if (is_null($formatter))
            $formatter = $this->formatter;
        $formatter->storeOptionStrings($this);
        $result = array();
        $result[] = $formatter->formatHeading(_("Options"));
        $formatter->indent();
        if ($this->optionList) {
            $result[] = parent::formatOptionHelp($formatter);
            $result[] = "\n";
        }
        foreach ($this->optionGroups as $group) {
            $result[] = $group->formatHelp($formatter);
            $result[] = "\n";
        }
        $formatter->dedent();
        // Drop the last "\n", or the header if no options or option groups:
        array_pop($result);
        return implode('', $result);
    }

    public function formatEpilog($formatter)
    {
        return $formatter->formatEpilog($this->epilog);
    }

    public function formatHelp($formatter = null)
    {
        if (is_null($formatter))
            $formatter = $this->formatter;
        $result = array();
        if ($this->_usage)
            $result[] = $this->getUsage($formatter) . "\n";
        if ($this->description)
            $result[] = $this->formatDescription($formatter) . "\n";
        $result[] = $this->formatOptionHelp($formatter);
        $result[] = $this->formatEpilog($formatter);
        return implode('', $result);
    }

    /**
     *  file : file = stdout
     *
     *  Print an extended help message, listing all options and any
     *  help text provided with them, to 'file' (default stdout).
     */
    public function printHelp($file = null)
    {
        if (is_null($file))
            echo $this->formatHelp();
        else
            fwrite($file, $this->formatHelp());
    }

}
