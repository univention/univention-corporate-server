<?php
/**
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @author   Mike Naberezny <mike@maintainable.com>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Argv
 */

/**
 * Defines the Option class and some standard value-checking functions.
 *
 * Instance attributes:
 *    shortOpts : [string]
 *    longOpts : [string]
 *
 *    action : string
 *    type : string
 *    dest : string
 *    default : any
 *    nargs : int
 *    const : any
 *    choices : [string]
 *    callback : function
 *    callbackArgs : (any*)
 *    help : string
 *    metavar : string
 *
 * @category Horde
 * @package  Horde_Argv
 */
class Horde_Argv_Option
{
    const SUPPRESS_HELP = "SUPPRESS HELP";
    const SUPPRESS_USAGE = "SUPPRESS USAGE";

    /**
     * Not supplying a default is different from a default of None,
     * so we need an explicit "not supplied" value.
     */
    public static $NO_DEFAULT = array("NO", "DEFAULT");

    public static function parseNumber($value)
    {
        if (!strlen($value)) {
            return false;
        }

        // Values to check against or compute with.
        $first = substr($value, 0, 1);
        $prefix = substr($value, 0, 2);
        $suffix = substr($value, 2);

        // Hex
        if ($prefix == '0x' || $prefix == '0X') {
            if (strspn($suffix, '0123456789abcdefABCDEF') != strlen($suffix)) {
                return false;
            }
            return hexdec($value);
        }

        // Binary
        if ($prefix == '0b' || $prefix == '0B') {
            if (strspn($suffix, '01') != strlen($suffix)) {
                return false;
            }
            return bindec($value);
        }

        // Octal
        if ($first == '0') {
            $suffix = substr($value, 1);
            if (strspn($suffix, '01234567') != strlen($suffix)) {
                return false;
            }
            return octdec($suffix);
        }

        // Base 10
        if (!is_numeric($value)) {
            return false;
        }
        return intval($value);
    }

    public function checkBuiltin($opt, $value)
    {
        switch ($this->type) {
        case 'int':
        case 'long':
            $number = self::parseNumber($value);
            if ($number === false) {
                $message = $this->type == 'int'
                    ? _("option %s: invalid integer value: '%s'")
                    : _("option %s: invalid long integer value: '%s'");
                throw new Horde_Argv_OptionValueException(
                    sprintf($message, $opt, $value));
            }
            return $number;

        case 'float':
            if (!is_numeric($value)) {
                throw new Horde_Argv_OptionValueException(
                    sprintf(_("option %s: invalid floating-point value: '%s'"),
                            $opt, $value));
            }
            return floatval($value);
        }
    }

    public function checkChoice($opt, $value)
    {
        if (in_array($value, $this->choices)) {
            return $value;
        } else {
            $choices = array();
            foreach ($this->choices as $choice) {
                $choices[] = (string)$choice;
            }
            $choices = "'" . implode("', '", $choices) . "'";
            throw new Horde_Argv_OptionValueException(sprintf(
                _("option %s: invalid choice: '%s' (choose from %s)"),
                $opt, $value, $choices));
        }
    }


    # The list of instance attributes that may be set through
    # keyword args to the constructor.
    public $ATTRS = array('action',
             'type',
             'dest',
             'default',
             'nargs',
             'const',
             'choices',
             'callback',
             'callbackArgs',
             'help',
             'metavar',
    );

    # The set of actions allowed by option parsers.  Explicitly listed
    # here so the constructor can validate its arguments.
    public $ACTIONS = array("store",
               "store_const",
               "store_true",
               "store_false",
               "append",
               "append_const",
               "count",
               "callback",
               "help",
               "version",
    );

    /**
     * The set of actions that involve storing a value somewhere;
     * also listed just for constructor argument validation.  (If
     * the action is one of these, there must be a destination.)
     */
    public $STORE_ACTIONS = array("store",
                     "store_const",
                     "store_true",
                     "store_false",
                     "append",
                     "append_const",
                     "count",
    );

    # The set of actions for which it makes sense to supply a value
    # type, ie. which may consume an argument from the command line.
    public $TYPED_ACTIONS = array("store",
                                  "append",
                                  "callback",
    );

    /**
     * The set of actions which *require* a value type, ie. that
     * always consume an argument from the command line.
     */
    public $ALWAYS_TYPED_ACTIONS = array("store",
                                         "append",
    );

    # The set of actions which take a 'const' attribute.
    public $CONST_ACTIONS = array("store_const",
                                  "append_const",
    );

    # The set of known types for option parsers.  Again, listed here for
    # constructor argument validation.
    public $TYPES = array("string", "int", "long", "float", "complex", "choice");

    # Dictionary of argument checking functions, which convert and
    # validate option arguments according to the option type.
    #
    # Signature of checking functions is:
    #   check(option : Option, opt : string, value : string) -> any
    # where
    #   option is the Option instance calling the checker
    #   opt is the actual option seen on the command-line
    #     (eg. "-a", "--file")
    #   value is the option argument seen on the command-line
    #
    # The return value should be in the appropriate Python type
    # for option.type -- eg. an integer if option.type == "int".
    #
    # If no checker is defined for a type, arguments will be
    # unchecked and remain strings.
    public $TYPE_CHECKER = array("int"    => 'checkBuiltin',
                                 "long"   => 'checkBuiltin',
                                 "float"  => 'checkBuiltin',
                                 "complex"=> 'checkBuiltin',
                                 "choice" => 'checkChoice',
    );

    # CHECK_METHODS is a list of unbound method objects; they are called
    # by the constructor, in order, after all attributes are
    # initialized.  The list is created and filled in later, after all
    # the methods are actually defined.  (I just put it here because I
    # like to define and document all class attributes in the same
    # place.)  Subclasses that add another _check_*() method should
    # define their own CHECK_METHODS list that adds their check method
    # to those from this class.
    public $CHECK_METHODS = array('_checkAction',
                                  '_checkType',
                                  '_checkChoice',
                                  '_checkDest',
                                  '_checkConst',
                                  '_checkNargs',
                                  '_checkCallback',
                                  );

    // -- Constructor/initialization methods ----------------------------

    public $shortOpts = array();
    public $longOpts = array();
    public $dest;
    public $default;

    public function __construct()
    {
        // The last argument to this function is an $attrs hash, if it
        // is present and an array. All other arguments are $opts.
        $opts = func_get_args();
        $num = func_num_args();
        if ($num == 0 || $num == 1 || !is_array($opts[$num - 1])) {
            $attrs = array();
        } else {
            $attrs = array_pop($opts);
        }

        // Set shortOpts, longOpts attrs from 'opts' tuple.
        // Have to be set now, in case no option strings are supplied.
        $this->shortOpts = array();
        $this->longOpts = array();
        $opts = $this->_checkOptStrings($opts);
        $this->_setOptStrings($opts);

        // Set all other attrs (action, type, etc.) from 'attrs' dict
        $this->_setAttrs($attrs);

        // Check all the attributes we just set.  There are lots of
        // complicated interdependencies, but luckily they can be farmed
        // out to the _check*() methods listed in CHECK_METHODS -- which
        // could be handy for subclasses!  The one thing these all share
        // is that they raise OptionError if they discover a problem.
        foreach ($this->CHECK_METHODS as $checker) {
            call_user_func(array($this, $checker));
        }
    }

    protected function _checkOptStrings($opts)
    {
        // Filter out None because early versions of Optik had exactly
        // one short option and one long option, either of which
        // could be None.
        $opts = array_filter($opts);
        if (!$opts) {
            throw new InvalidArgumentException('at least one option string must be supplied');
        }
        return $opts;
    }

    protected function _setOptStrings($opts)
    {
        foreach ($opts as &$opt) {
            $opt = (string)$opt;

            if (strlen($opt) < 2) {
                throw new Horde_Argv_OptionException(sprintf("invalid option string '%s': must be at least two characters long", $opt), $this);
            } elseif (strlen($opt) == 2) {
                if (!($opt[0] == "-" && $opt[1] != "-")) {
                    throw new Horde_Argv_OptionException(sprintf(
                        "invalid short option string '%s': " .
                        "must be of the form -x, (x any non-dash char)", $opt), $this);
                }
                $this->shortOpts[] = $opt;
            } else {
                if (!(substr($opt, 0, 2) == '--' && $opt[2] != '-')) {
                    throw new Horde_Argv_OptionException(sprintf(
                        "invalid long option string '%s': " .
                        "must start with --, followed by non-dash", $opt), $this);
                }
                $this->longOpts[] = $opt;
            }
        }
    }

    protected function _setAttrs($attrs)
    {
        foreach ($this->ATTRS as $attr) {
            if (array_key_exists($attr, $attrs)) {
                $this->$attr = $attrs[$attr];
                unset($attrs[$attr]);
            } else {
                if ($attr == 'default') {
                    $this->$attr = self::$NO_DEFAULT;
                } else {
                    $this->$attr = null;
                }
            }
        }

        if ($attrs) {
            $attrs = array_keys($attrs);
            sort($attrs);
            throw new Horde_Argv_OptionException(sprintf(
                "invalid keyword arguments: %s", implode(", ", $attrs)), $this);
        }
    }


    // -- Constructor validation methods --------------------------------

    public function _checkAction()
    {
        if (is_null($this->action)) {
            $this->action = "store";
        } elseif (!in_array($this->action, $this->ACTIONS)) {
            throw new Horde_Argv_OptionException(sprintf("invalid action: '%s'", $this->action), $this);
        }
    }

    public function _checkType()
    {
        if (is_null($this->type)) {
            if (in_array($this->action, $this->ALWAYS_TYPED_ACTIONS)) {
                if (!is_null($this->choices)) {
                    // The "choices" attribute implies "choice" type.
                    $this->type = "choice";
                } else {
                    // No type given?  "string" is the most sensible default.
                    $this->type = "string";
                }
            }
        } else {
            if ($this->type == "str") {
                $this->type = "string";
            }

            if (!in_array($this->type, $this->TYPES)) {
                throw new Horde_Argv_OptionException(sprintf("invalid option type: '%s'", $this->type), $this);
            }

            if (!in_array($this->action, $this->TYPED_ACTIONS)) {
                throw new Horde_Argv_OptionException(sprintf(
                    "must not supply a type for action '%s'", $this->action), $this);
            }
        }
    }

    public function _checkChoice()
    {
        if ($this->type == "choice") {
            if (is_null($this->choices)) {
                throw new Horde_Argv_OptionException(
                    "must supply a list of choices for type 'choice'", $this);
            } elseif (!(is_array($this->choices) || $this->choices instanceof Iterator)) {
                throw new Horde_Argv_OptionException(sprintf(
                    "choices must be a list of strings ('%s' supplied)",
                    gettype($this->choices)), $this);
            }
        } elseif (!is_null($this->choices)) {
            throw new Horde_Argv_OptionException(sprintf(
                "must not supply choices for type '%s'", $this->type), $this);
        }
    }

    public function _checkDest()
    {
        // No destination given, and we need one for this action.  The
        // $this->type check is for callbacks that take a value.
        $takes_value = (in_array($this->action, $this->STORE_ACTIONS) ||
                        !is_null($this->type));
        if (is_null($this->dest) && $takes_value) {
            // Glean a destination from the first long option string,
            // or from the first short option string if no long options.
            if ($this->longOpts) {
                // eg. "--foo-bar" -> "foo_bar"
                $this->dest = str_replace('-', '_', substr($this->longOpts[0], 2));
            } else {
                $this->dest = $this->shortOpts[0][1];
            }
        }
    }

    public function _checkConst()
    {
        if (!in_array($this->action, $this->CONST_ACTIONS) && !is_null($this->const)) {
            throw new Horde_Argv_OptionException(sprintf(
                "'const' must not be supplied for action '%s'", $this->action),
                $this);
        }
    }

    public function _checkNargs()
    {
        if (in_array($this->action, $this->TYPED_ACTIONS)) {
            if (is_null($this->nargs)) {
                $this->nargs = 1;
            }
        } elseif (!is_null($this->nargs)) {
            throw new Horde_Argv_OptionException(sprintf(
                "'nargs' must not be supplied for action '%s'", $this->action),
                $this);
        }
    }

    public function _checkCallback()
    {
        if ($this->action == "callback") {
            if (!is_callable($this->callback)) {
                $callback_name = is_array($this->callback) ?
                    is_object($this->callback[0]) ? get_class($this->callback[0] . '#' . $this->callback[1]) : implode('#', $this->callback) :
                    $this->callback;
                throw new Horde_Argv_OptionException(sprintf(
                    "callback not callable: '%s'", $callback_name), $this);
            }
            if (!is_null($this->callbackArgs) && !is_array($this->callbackArgs)) {
                throw new Horde_Argv_OptionException(sprintf(
                    "callbackArgs, if supplied, must be an array: not '%s'",
                    $this->callbackArgs), $this);
            }
        } else {
            if (!is_null($this->callback)) {
                $callback_name = is_array($this->callback) ?
                    is_object($this->callback[0]) ? get_class($this->callback[0] . '#' . $this->callback[1]) : implode('#', $this->callback) :
                    $this->callback;
                throw new Horde_Argv_OptionException(sprintf(
                    "callback supplied ('%s') for non-callback option",
                    $callback_name), $this);
            }
            if (!is_null($this->callbackArgs)) {
                throw new Horde_Argv_OptionException(
                    "callbackArgs supplied for non-callback option", $this);
            }
        }
    }


    // -- Miscellaneous methods -----------------------------------------

    public function __toString()
    {
        return implode('/', array_merge($this->shortOpts, $this->longOpts));
    }

    public function takesValue()
    {
        return !is_null($this->type);
    }

    public function getOptString()
    {
        if ($this->longOpts)
            return $this->longOpts[0];
        else
            return $this->shortOpts[0];
    }


    // -- Processing methods --------------------------------------------

    public function checkValue($opt, $value)
    {
        if (!isset($this->TYPE_CHECKER[$this->type])) {
            return $value;
        }
        $checker = $this->TYPE_CHECKER[$this->type];
        return call_user_func(array($this, $checker), $opt, $value);
    }

    public function convertValue($opt, $value)
    {
        if (!is_null($value)) {
            if ($this->nargs == 1) {
                return $this->checkValue($opt, $value);
            } else {
                $return = array();
                foreach ($value as $v) {
                    $return[] = $this->checkValue($opt, $v);
                }
                return $return;
            }
        }
    }

    public function process($opt, $value, $values, $parser)
    {
        // First, convert the value(s) to the right type.  Howl if any
        // value(s) are bogus.
        $value = $this->convertValue($opt, $value);

        // And then take whatever action is expected of us.
        // This is a separate method to make life easier for
        // subclasses to add new actions.
        return $this->takeAction(
            $this->action, $this->dest, $opt, $value, $values, $parser);
    }

    public function takeAction($action, $dest, $opt, $value, $values, $parser)
    {
        if ($action == 'store')
            $values->$dest = $value;
        elseif ($action == 'store_const')
            $values->$dest = $this->const;
        elseif ($action == 'store_true')
            $values->$dest = true;
        elseif ($action == 'store_false')
            $values->$dest = false;
        elseif ($action == 'append') {
            $values->{$dest}[] = $value;
        } elseif ($action == 'append_const') {
            $values->{$dest}[] = $this->const;
        } elseif ($action == 'count') {
            $values->ensureValue($dest, 0);
            $values->$dest++;
        } elseif ($action == 'callback') {
            call_user_func($this->callback, $this, $opt, $value, $parser, $this->callbackArgs);
        } elseif ($action == 'help') {
            $parser->printHelp();
            $parser->parserExit();
        } elseif ($action == 'version') {
            $parser->printVersion();
            $parser->parserExit();
        } else {
            throw new RuntimeException('unknown action ' . $this->action);
        }

        return 1;
    }

}
