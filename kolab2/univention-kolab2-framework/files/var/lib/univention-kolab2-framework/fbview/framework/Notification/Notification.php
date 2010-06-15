<?php
/**
 * The Notification:: class provides a subject-observer pattern for
 * raising and showing messages of different types and to different
 * listeners.
 *
 * $Horde: framework/Notification/Notification.php,v 1.41 2004/03/09 07:38:31 jon Exp $
 *
 * Copyright 2001-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_Notification
 */
class Notification {

    /**
     * Hash containing all attached listener objects.
     *
     * @var array $_listeners
     */
    var $_listeners = array();

    /**
     * Returns a reference to the global Notification object, only
     * creating it if it doesn't already exist.
     *
     * This method must be invoked as:
     *   $notification = &Notification::singleton()
     *
     * @return object Notification  The Horde Notification instance.
     */
    function &singleton()
    {
        static $notification;

        if (!isset($notification)) {
            $notification = new Notification();
        }

        return $notification;
    }

    /**
     * Initialize the notification system, set up any needed session
     * variables, etc. Should never be called except by
     * &Notification::singleton();
     *
     * @access private
     */
    function Notification()
    {
        /* Make sure the message stack is registered in the session,
         * and obtain a global-scope reference to it. */
        if (!isset($_SESSION['hordeMessageStacks'])) {
            $_SESSION['hordeMessageStacks'] = array();
        }
    }

    /**
     * Registers a listener with the notification object and includes
     * the necessary library file dynamically.
     *
     * @param string $driver          The name of the listener to attach.
     *                                These names must be unique; further
     *                                listeners with the same name will be
     *                                ignored.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters
     *                                a listener driver might need.
     * @param optional string $class  The class name from which the driver
     *                                was instantiated if not the default
     *                                one. If given you have to include the
     *                                library file containing this class
     *                                yourself.
     *                                This is useful if you want the
     *                                listener driver to be overriden by an
     *                                application's implementation.
     */
    function &attach($listener, $params = array(), $class = null)
    {
        $listener = basename($listener);
        if (!empty($this->_listeners[$listener])) {
            return false;
        }

        if (is_null($class)) {
            require_once dirname(__FILE__) . '/Notification/Listener/' . $listener . '.php';
            $class = 'Notification_Listener_' . $listener;
        }
        if (class_exists($class)) {
            $this->_listeners[$listener] = &new $class($params);
            if (!isset($_SESSION['hordeMessageStacks'][$listener])) {
                $_SESSION['hordeMessageStacks'][$listener] = array();
            }
            return $this->_listeners[$listener];
        } else {
            Horde::fatal(PEAR::raiseError(sprintf('Notification listener %s not found.', $listener)), __FILE__, __LINE__);
        }
    }

    /**
     * Remove a listener from the notification list.
     *
     * @access public
     *
     * @param string $listner          The name of the listener to detach.
     */
    function detach($listener)
    {
        $listener = basename($listener);
        if (!isset($this->_listeners[$listener])) {
            return PEAR::raiseError(sprintf('Notification listener %s not found.', $listener));
        }

        $list = $this->_listeners[$listener];
        unset($this->_listeners[$listener]);
        unset($_SESSION['hordeMessageStacks'][$list->getName()]);
        return true;
    }

    /**
     * Add an event to the Horde message stack.
     *
     * The event type parameter should begin with 'horde.' unless the
     * application defines its own Notification_Listener subclass that
     * handles additional codes.
     *
     * @access public
     *
     * @param mixed $event      Notification_Event object or message string.
     * @param optional integer $type  The type of message: 'horde.error',
     *                                'horde.warning', 'horde.success', or
     *                                'horde.message'.
     * @param optional array $flags   Array of optional flags that will be
     *                                passed to the registered listeners.
     */
    function push($event, $type = 'horde.message', $flags = array())
    {
        if (!is_a($event, 'Notification_Event') &&
            !is_a($event, 'PEAR_Error')) {
            /* Transparently create a Notification_Event object and
             * set the message attribute. */
            require_once dirname(__FILE__) . '/Notification/Event.php';
            $event = &new Notification_Event($event);
        }
        if (is_a($event, 'PEAR_Error')) {
            Horde::logMessage($event, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }

        foreach ($this->_listeners as $listener) {
            if ($listener->handles($type)) {
                $_SESSION['hordeMessageStacks'][$listener->getName()][] =
                    array('type' => $type,
                          'class' => get_class($event),
                          'event' => serialize($event),
                          'flags' => serialize($flags));
            }
        }
    }

    /**
     * Passes the message stack to all listeners and asks them to
     * handle their messages.
     *
     * @access public
     *
     * @param optional array $options  An array containing display options
     *                                 for the listeners.
     */
    function notify($options = array())
    {
        if (!isset($options['listeners'])) {
            $options['listeners'] = array_keys($this->_listeners);
        } elseif (!is_array($options['listeners'])) {
            $options['listeners'] = array($options['listeners']);
        }
        foreach ($options['listeners'] as $listener) {
            $this->_listeners[$listener]->notify($_SESSION['hordeMessageStacks'][$this->_listeners[$listener]->getName()], $options);
        }
    }

    /**
     * Return the number of notification messages in the stack.
     *
     * @author David Ulevitch <davidu@everydns.net>
     *
     * @access public
     *
     * @param optional string $my_listener  The name of the listener.
     *
     * @return integer  The number of messages in the stack.
     *
     * @since Horde 2.2
     */
    function count($my_listener = null)
    {
        if (is_null($my_listener)) {
            $count = 0;
            foreach ($this->_listeners as $listener) {
                if (isset($_SESSION['hordeMessageStacks'][$listener->getName()])) {
                    $count += count($_SESSION['hordeMessageStacks'][$listener->getName()]);
                }
            }
            return $count;
        } else {
            return @count($_SESSION['hordeMessageStacks'][$this->_listeners[$my_listener]->getName()]);
        }
    }

}
