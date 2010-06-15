<?php
/**
 * The Notification_Listener:: class provides functionality for displaying
 * messages from the message stack as a status line.
 *
 * $Horde: framework/Notification/Notification/Listener.php,v 1.13 2004/03/22 20:43:59 chuck Exp $
 *
 * Copyright 2001-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_Notification
 */
class Notification_Listener {

    /**
     * Array of message types that this listener handles.
     *
     * @var array $_handles
     */
    var $_handles = array();

    /**
     * Constructor
     *
     * @access public
     */
    function Notification_Listener()
    {
    }

    /**
     * Does this listener handle a certain type of message?
     *
     * @access public
     *
     * @param string $type  The message type in question.
     *
     * @return boolean  Whether this listener handles the type.
     */
    function handles($type)
    {
        return isset($this->_handles[$type]);
    }

    /**
     * Return a unique identifier for this listener.
     *
     * @access public
     *
     * @return string  Unique id.
     */
    function getName()
    {
        return get_class($this);
    }

    /**
     * Outputs the status line, sends emails, pages, etc., if there
     * are any messages on this listener's message stack.
     *
     * @access public
     *
     * @param array &$messageStack     The stack of messages.
     * @param optional array $options  An array of options.
     *                                 Options: 'nospace'
     */
    function notify(&$messageStacks, $options)
    {
    }

    /**
     * Processes one message from the message stack.
     *
     * @access public
     *
     * @param array $message  One message hash from the stack.
     */
    function getMessage($message)
    {
    }

    /**
     * Unserialize an event from the message stack, checking to see if
     * the appropriate class exists and kludging it into a base
     * Notification_Event object if not.
     *
     * @access public
     */
    function getEvent($message)
    {
        $ob = false;
        if (class_exists($message['class'])) {
            $ob = @unserialize($message['event']);
        } else {
            require_once dirname(__FILE__) . '/Event.php';
            $ob = @unserialize($message['event']);
            if (!method_exists($ob, 'getMessage')) {
                if (isset($ob->_message)) {
                    $ob = &new Notification_Event($ob->_message);
                }
            }
        }

        /* If we've failed to create a valid Notification_Event object
         * (or subclass object) so far, return a PEAR_Error. */
        if (!method_exists($ob, 'getMessage')) {
            $ob = PEAR::raiseError('Unable to decode message event: ' . $message['event']);
        }

        return $ob;
    }

    /**
     * Unserialize an array of event flags from the message stack.  If
     * this event has no flags, or the flags array could not be
     * unserialized, an empty array is returned.
     *
     * @access public
     *
     * @return array  An array of flags.
     */
    function getFlags($message)
    {
        /* If this message doesn't have any flags, return an empty
         * array. */
        if (empty($message['flags'])) {
            return array();
        }

        /* Unserialize the flags array from the message. */
        $flags = @unserialize($message['flags']);

        /* If we couldn't unserialize the flags array, return an empty
         * array. */
        if (!is_array($flags)) {
            return array();
        }

        return $flags;
    }

}
