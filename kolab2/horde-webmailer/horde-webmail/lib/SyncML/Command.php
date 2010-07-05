<?php
/**
 * The SyncML_Command class provides a base class for handling all <SyncBody>
 * commands.
 *
 * A SyncML command is a protocol primitive. Each SyncML command specifies to
 * a recipient an individual operation that is to be performed.
 *
 * The SyncML_Command objects are hooked into the XML parser of the
 * SyncML_ContentHandler class and are reponsible for parsing a single command
 * inside the SyncBody section of a SyncML message. All actions that must be
 * executed for a single SyncML command are handled by these objects, by means
 * of the handleCommand() method.
 *
 * $Horde: framework/SyncML/SyncML/Command.php,v 1.4.10.13 2009-04-05 20:24:42 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anthony Mills <amills@pyramid6.com>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package SyncML
 */
class SyncML_Command {

    /**
     * Name of the command, like 'Put'.
     *
     * Must be overwritten by a sub class.
     *
     * @var string
     */
    var $_cmdName;

    /**
     * The command ID (<CmdID>).
     *
     * @var integer
     */
    var $_cmdID;

    /**
     * Stack for holding the XML elements during creation of the object from
     * the XML event flow.
     *
     * @var array
     */
    var $_stack = array();

    /**
     * Buffer for the parsed character data.
     *
     * @var string
     */
    var $_chars = '';

    /**
     * A SyncML_XMLOutput instance responsible for generating the output.
     *
     * @var SyncML_XMLOutput
     */
    var $_outputHandler;

    /**
     * Constructor.
     *
     * @param SyncML_XMLOutput $outputHandler  A SyncML_XMLOutput object.
     */
    function SyncML_Command(&$outputHandler)
    {
        $this->_outputHandler = &$outputHandler;
    }

    /**
     * Start element handler for the XML parser, delegated from
     * SyncML_ContentHandler::startElement().
     *
     * @param string $uri      The namespace URI of the element.
     * @param string $element  The element tag name.
     * @param array $attrs     A hash with the element's attributes.
     */
    function startElement($uri, $element, $attrs)
    {
        $this->_stack[] = $element;
    }

    /**
     * End element handler for the XML parser, delegated from
     * SyncML_ContentHandler::endElement().
     *
     * @param string $uri      The namespace URI of the element.
     * @param string $element  The element tag name.
     */
    function endElement($uri, $element)
    {
        if (count($this->_stack) == 2 &&
            $element == 'CmdID') {
            $this->_cmdID = intval(trim($this->_chars));
        }

        if (strlen($this->_chars)) {
            $this->_chars = '';
        }

        array_pop($this->_stack);
    }

    /**
     * Character data handler for the XML parser, delegated from
     * SyncML_ContentHandler::characters().
     *
     * @param string $str  The data string.
     */
    function characters($str)
    {
        $this->_chars .= $str;
    }

    /**
     * Returns the command name this instance is reponsible for.
     *
     * @return string  The command name this object is handling.
     */
    function getCommandName()
    {
        return $this->_cmdName;
    }

    /**
     * This method is supposed to implement the actual business logic of the
     * command once the XML parsing is complete.
     *
     * @abstract
     */
    function handleCommand($debug = false)
    {
    }

    /**
     * Attempts to return a concrete SyncML_Command instance based on
     * $command.
     *
     * @param string $command                  The type of the concrete
     *                                         SyncML_Comment subclass to
     *                                         return.
     * @param SyncML_XMLOutput $outputHandler  A SyncML_XMLOutput object.
     *
     * @return SyncML_Command  The newly created concrete SyncML_Command
     *                         instance, or false on error.
     */
    function &factory($command, &$outputHandler)
    {
        $command = basename($command);
        $class = 'SyncML_Command_' . $command;

        if (!class_exists($class)) {
            include 'SyncML/Command/' . $command . '.php';
        }
        if (class_exists($class)) {
            $cmd = new $class($outputHandler);
        } else {
            $msg = 'Class definition of ' . $class . ' not found.';
            $GLOBALS['backend']->logMessage($msg, __FILE__, __LINE__,
                                            PEAR_LOG_ERR);
            require_once 'PEAR.php';
            $cmd = PEAR::raiseError($msg);
        }

        return $cmd;
    }

}


