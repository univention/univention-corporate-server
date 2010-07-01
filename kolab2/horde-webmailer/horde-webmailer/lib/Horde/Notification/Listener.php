<?php
/**
 * The Notification_Listener:: class provides functionality for displaying
 * messages from the message stack as a status line.
 *
 * $Horde: framework/Notification/Notification/Listener.php,v 1.16.2.14 2009-01-06 15:23:28 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 2.1
 * @package Horde_Notification
 */
class Notification_Listener {

    /**
     * Array of message types that this listener handles.
     *
     * @var array
     */
    var $_handles = array();

    /**
     * Constructor
     */
    function Notification_Listener()
    {
    }

    /**
     * Does this listener handle a certain type of message?
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
     * @param array &$messageStack  The stack of messages.
     * @param array $options        An array of options.
     */
    function notify(&$messageStacks, $options = array())
    {
    }

    /**
     * Processes one message from the message stack.
     *
     * @param array $message  One message hash from the stack.
     */
    function getMessage($message)
    {
    }

    /**
     * Unserialize an event from the message stack, checking to see if the
     * appropriate class exists and kludging it into a base Notification_Event
     * object if not.
     */
    function getEvent($message)
    {
        $ob = false;
        if (class_exists($message['class'])) {
            $ob = @unserialize($message['event']);
        } else {
            require_once dirname(__FILE__) . '/Event.php';
            $ob = @unserialize($message['event']);
            if (!is_callable(array($ob, 'getMessage'))) {
                if (isset($ob->_message)) {
                    $ob = new Notification_Event($ob->_message);
                }
            }
        }

        /* If we've failed to create a valid Notification_Event object
         * (or subclass object) so far, return a PEAR_Error. */
        if (!is_callable(array($ob, 'getMessage'))) {
            $ob = PEAR::raiseError('Unable to decode message event: ' . $message['event']);
        }

        /* Specially handle PEAR_Error objects and add userinfo if
         * it's there. */
        if (is_callable(array($ob, 'getUserInfo'))) {
            $userinfo = $ob->getUserInfo();
            if ($userinfo) {
                if (is_array($userinfo)) {
                    $userinfo_elts = array();
                    foreach ($userinfo as $userinfo_elt) {
                        if (is_scalar($userinfo_elt)) {
                            $userinfo_elts[] = $userinfo_elt;
                        } elseif (is_object($userinfo_elt)) {
                            if (is_callable(array($userinfo_elt, '__toString'))) {
                                $userinfo_elts[] = $userinfo_elt->__toString();
                            } elseif (is_callable(array($userinfo_elt, 'getMessage'))) {
                                $userinfo_elts[] = $userinfo_elt->getMessage();
                            }
                        }
                    }
                    $userinfo = implode(', ', $userinfo_elts);
                }

                $ob->_message = $ob->getMessage() . ' : ' . $userinfo;
            }
        }

        return $ob;
    }

    /**
     * Unserialize an array of event flags from the message stack.  If this
     * event has no flags, or the flags array could not be unserialized, an
     * empty array is returned.
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
