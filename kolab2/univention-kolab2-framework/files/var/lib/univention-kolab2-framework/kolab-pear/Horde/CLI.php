<?php
/**
 * Horde_CLI:: API for basic command-line functionality/checks.
 *
 * $Horde: framework/CLI/CLI.php,v 1.35 2004/04/12 00:46:40 jon Exp $
 *
 * Copyright 2003-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 2003-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_CLI
 */
class Horde_CLI {

    /**
     * Are we running on a console?
     * @var bool $_console
     */
    var $_console;

    /**
     * The newline string to use.
     * @var string $_newline
     */
    var $_newline;

    /**
     * The indent string to use.
     * @var string $_indent
     */
    var $_indent;

    /**
     * The string to mark the beginning of bold text.
     * @var string $_bold_start
     */
    var $_bold_start = '';

    /**
     * The string to mark the end of bold text.
     * @var string $_bold_start
     */
    var $_bold_end = '';

    /**
     * The strings to mark the beginning of coloured text.
     */
    var $_red_start    = '';
    var $_green_start  = '';
    var $_yellow_start = '';
    var $_blue_start   = '';

    /**
     * The strings to mark the end of coloured text.
     */
    var $_red_end      = '';
    var $_green_end    = '';
    var $_yellow_end   = '';
    var $_blue_end     = '';

    /**
     * Returns a single instance of the Horde_CLI class.
     */
    function &singleton()
    {
        static $instance;
        if (!isset($instance)) {
            $instance = &new Horde_CLI();
        }
        return $instance;
    }

    /**
     * Constructor.
     * Detects the current environment (web server or console)
     * and sets internal values accordingly.
     */
    function Horde_CLI()
    {
        $this->_console = $this->runningFromCLI();

        if ($this->_console) {
            $this->_newline = "\n";
            $this->_indent  = '    ';

            $term = getenv('TERM');
            if ($term) {
                if (preg_match('/^(xterm|vt220|linux)/', $term)) {
                    $this->_bold_start   = "\x1b[1m";
                    $this->_red_start    = "\x1b[01;31m";
                    $this->_green_start  = "\x1b[01;32m";
                    $this->_yellow_start = "\x1b[01;33m";
                    $this->_blue_start   = "\x1b[01;34m";
                    $this->_bold_end = $this->_red_end = $this->_green_end = $this->_yellow_end = $this->_blue_end = "\x1b[0m";
                } elseif (preg_match('/^vt100/', $term)) {
                    $this->_bold_start = "\x1b[1m";
                    $this->_bold_end   = "\x1b[0m";
                }
            }
        } else {
            $this->_newline = '<br />';
            $this->_indent  = str_repeat('&nbsp;', 4);

            $this->_bold_start  = '<strong>';
            $this->_bold_end    = '</strong>';
            $this->_red_start   = '<span style="color:red">';
            $this->_green_start = '<span style="color:green">';
            $this->_yellow_start = '<span style="color:yellow">';
            $this->_blue_start   = '<span style="color:blue">';
            $this->_red_end = $this->_green_end = $this->_yellow_end = $this->_blue_end = '</span>';
        }
    }

    /**
     * Prints $text on a single line.
     *
     * @param string $text  The text to print.
     * @param bool $pre     If true the linebreak is printed before
     *                      the text instead of after it.
     */
    function writeln($text = '', $pre = false)
    {
        if ($pre) {
            echo $this->_newline . $text;
        } else {
            echo $text . $this->_newline;
        }
    }

    /**
     * Returns the indented string.
     *
     * @param string $text  The text to indent.
     */
    function indent($text)
    {
        return $this->_indent . $text;
    }

    /**
     * Returns a bold version of $text.
     *
     * @param string $text  The text to bold.
     */
    function bold($text)
    {
        return $this->_bold_start . $text . $this->_bold_end;
    }

    /**
     * Returns a red version of $text.
     *
     * @param string $text  The text to print in red.
     */
    function red($text)
    {
        return $this->_red_start . $text . $this->_red_end;
    }

    /**
     * Returns a green version of $text.
     *
     * @param string $text  The text to print in green.
     */
    function green($text)
    {
        return $this->_green_start . $text . $this->_green_end;
    }

    /**
     * Returns a blue version of $text.
     *
     * @param string $text  The text to print in blue.
     */
    function blue($text)
    {
        return $this->_blue_start . $text . $this->_blue_end;
    }

    /**
     * Returns a yellow version of $text.
     *
     * @param string $text  The text to print in yellow.
     */
    function yellow($text)
    {
        return $this->_yellow_start . $text . $this->_yellow_end;
    }

    /**
     * Displays a message.
     *
     * @param string $event          The message string.
     * @param optional string $type  The type of message: 'cli.error',
     *                               'cli.warning', 'cli.success', or
     *                               'cli.message'.
     */
    function message($message, $type = 'cli.message')
    {
        switch ($type) {
        case 'cli.error':
            $type_message = $this->red('[ ERROR! ] ');
            break;
        case 'cli.warning':
            $type_message = $this->yellow('[  WARN  ] ');
            break;
        case 'cli.success':
            $type_message = $this->green('[   OK   ] ');
            break;
        case 'cli.message':
            $type_message = $this->blue('[  INFO  ] ');
            break;
        }

        $this->writeln($type_message . $message);
    }

    /**
     * Displays a fatal error message.
     *
     * @param string $error  The error text to display.
     */
    function fatal($error)
    {
        $this->writeln($this->red('===================='));
        $this->writeln();
        $this->writeln($this->red(_("Fatal Error!")));
        $this->writeln($this->red($error));
        $this->writeln();
        $this->writeln($this->red('===================='));
        exit;
    }

    /**
     * Prompts for a user response.
     *
     * @param string $prompt            The message to display when
     *                                  prompting the user.
     * @param optional array $choices   The choices available to the
     *                                  user or null for a text input.
     *
     * @return mixed   The user's response to the prompt.
     */
    function prompt($prompt, $choices = null)
    {
        $stdin = fopen('php://stdin', 'r');

        // Main event loop to capture top level command.
        while (true) {
            // Print out the prompt message.
            $this->writeln($prompt . ' ', !is_array($choices));
            if (is_array($choices) && !empty($choices)) {
                foreach ($choices as $key => $choice) {
                    $key = $this->bold($key);
                    $this->writeln($this->indent('(' . $key . ') ' . $choice));
                }
                $this->writeln(_("Type your choice: "), true);

                // Get the user choice.
                $response = trim(fgets($stdin, 256));

                if (isset($choices[$response])) {
                    // Close standard in.
                    fclose($stdin);
                    return $response;
                } else {
                    $this->writeln(sprintf(_("'%s' is not a valid choice."), $response));
                }
            } else {
                $response = trim(fgets($stdin, 256));
                fclose($stdin);
                return $response;
            }
        }

        return true;
    }

    /**
     * CLI scripts shouldn't timeout, so try to set the time limit to
     * none. Also initialize a few variables in $_SERVER that aren't
     * present from the CLI.
     *
     * @access static
     */
    function init()
    {
        @set_time_limit(0);
        ob_implicit_flush(true);
        ini_set('html_errors', false);
        $_SERVER['HTTP_HOST'] = '127.0.0.1';
        $_SERVER['SERVER_NAME'] = '127.0.0.1';
        $_SERVER['SERVER_PORT'] = '';
        $_SERVER['REMOTE_ADDR'] = '';
        $_SERVER['PHP_SELF'] = isset($argv) ? $argv[0] : '';
    }

    /**
     * Make sure we're being called from the command line, and not via
     * the web.
     *
     * @access static
     *
     * @return boolean  True if we are, false otherwise.
     */
    function runningFromCLI()
    {
        // STDIN isn't a CLI constant before 4.3.0
        $sapi = php_sapi_name();
        if (version_compare(PHP_VERSION, '4.3.0') >= 0 && $sapi != 'cgi') {
            return @is_resource(STDIN);
        } else {
            return in_array($sapi, array('cli', 'cgi')) && empty($_SERVER['REMOTE_ADDR']);
        }
    }

}
