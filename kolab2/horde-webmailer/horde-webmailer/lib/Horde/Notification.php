<?php
/**
 * @package Horde_Notification
 *
 * $Horde: framework/Notification/Notification.php,v 1.46.2.17 2009-01-06 15:23:28 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 */

/** Notification_Event */
require_once dirname(__FILE__) . '/Notification/Event.php';

/**
 * The Notification:: class provides a subject-observer pattern for
 * raising and showing messages of different types and to different
 * listeners.
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 2.1
 * @package Horde_Notification
 */
class Notification {

    /**
     * Hash containing all attached listener objects.
     *
     * @var array
     */
    var $_listeners = array();

    /**
     * The name of the session variable where we store the messages.
     *
     * @var string
     */
    var $_stack = 'hordeMessageStacks';

    /**
     * A Horde_Alarm instance.
     *
     * @var Horde_Alarm
     */
    var $_alarm;

    /**
     * Returns a reference to the global Notification object, only
     * creating it if it doesn't already exist.
     *
     * This method must be invoked as:
     *   $notification = &Notification::singleton()
     *
     * @param string $stack  The name of the message stack to use.
     *
     * @return Notification  The Horde Notification instance.
     */
    function &singleton($stack = 'hordeMessageStacks')
    {
        static $notification = array();

        if (!isset($notification[$stack])) {
            $notification[$stack] = &new Notification($stack);
        }

        return $notification[$stack];
    }

    /**
     * Initialize the notification system, set up any needed session
     * variables, etc. Should never be called except by
     * &Notification::singleton();
     *
     * @param string $stack  The name of the message stack to use.
     */
    function Notification($stack = 'hordeMessageStacks')
    {
        $this->_stack = $stack;

        /* Make sure the message stack is registered in the session,
         * and obtain a global-scope reference to it. */
        if (!isset($_SESSION[$this->_stack])) {
            $_SESSION[$this->_stack] = array();
        }

        if (!empty($GLOBALS['conf']['alarms']['driver'])) {
            require_once 'Horde/Alarm.php';
            $this->_alarm = Horde_Alarm::factory();
        }
    }

    /**
     * Registers a listener with the notification object and includes
     * the necessary library file dynamically.
     *
     * @param string $listener The name of the listener to attach. These names
     *                         must be unique; further listeners with the same
     *                         name will be ignored.
     * @param array $params    A hash containing any additional configuration or
     *                         connection parameters a listener driver might
     *                         need.
     * @param string $class    The class name from which the driver was
     *                         instantiated if not the default one. If given
     *                         you have to include the library file containing
     *                         this class yourself. This is useful if you want
     *                         the listener driver to be overriden by an
     *                         application's implementation.
     */
    function &attach($listener, $params = array(), $class = null)
    {
        $listener = basename($listener);
        if (!empty($this->_listeners[$listener])) {
            return $this->_listeners[$listener];
        }

        if (is_null($class)) {
            include_once dirname(__FILE__) . '/Notification/Listener/' . $listener . '.php';
            $class = 'Notification_Listener_' . $listener;
        }
        if (class_exists($class)) {
            $this->_listeners[$listener] = new $class($params);
            if (!isset($_SESSION[$this->_stack][$listener])) {
                $_SESSION[$this->_stack][$listener] = array();
            }
            return $this->_listeners[$listener];
        } else {
            return PEAR::raiseError(sprintf('Notification listener %s not found.', $listener));
        }
    }

    /**
     * Remove a listener from the notification list.
     *
     * @param string $listner  The name of the listener to detach.
     */
    function detach($listener)
    {
        $listener = basename($listener);
        if (!isset($this->_listeners[$listener])) {
            return PEAR::raiseError(sprintf('Notification listener %s not found.', $listener));
        }

        $list = $this->_listeners[$listener];
        unset($this->_listeners[$listener]);
        unset($_SESSION[$this->_stack][$list->getName()]);
        return true;
    }

    /**
     * Add an event to the Horde message stack.
     *
     * The event type parameter should begin with 'horde.' unless the
     * application defines its own Notification_Listener subclass that
     * handles additional codes.
     *
     * @param mixed $event   Notification_Event object or message string.
     * @param integer $type  The type of message: 'horde.error',
     *                       'horde.warning', 'horde.success', or
     *                       'horde.message'.
     * @param array $flags   Array of optional flags that will be passed to the
     *                       registered listeners.
     */
    function push($event, $type = null, $flags = array())
    {
        if (!is_a($event, 'Notification_Event') &&
            !is_a($event, 'PEAR_Error')) {
            /* Transparently create a Notification_Event object and
             * set the message attribute. */
            $event = new Notification_Event($event);
        }
        if (is_a($event, 'PEAR_Error')) {
            if (!isset($type)) {
                $type = 'horde.error';
            }
            Horde::logMessage($event, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }
        if (!isset($type)) {
            $type = 'horde.message';
        }

        foreach ($this->_listeners as $listener) {
            if ($listener->handles($type)) {
                $_SESSION[$this->_stack][$listener->getName()][] =
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
     * @param array $options  An array containing display options for the
     *                        listeners.
     */
    function notify($options = array())
    {
        if (!isset($options['listeners'])) {
            $options['listeners'] = array_keys($this->_listeners);
        } elseif (!is_array($options['listeners'])) {
            $options['listeners'] = array($options['listeners']);
        }

        if ($this->_alarm && in_array('status', $options['listeners'])) {
            $this->_alarm->notify(Auth::getAuth());
        }

        foreach ($options['listeners'] as $listener) {
            if (isset($this->_listeners[$listener])) {
                $this->_listeners[$listener]->notify($_SESSION[$this->_stack][$this->_listeners[$listener]->getName()], $options);
            }
        }
    }

    /**
     * Return the number of notification messages in the stack.
     *
     * @author David Ulevitch <davidu@everydns.net>
     *
     * @param string $my_listener  The name of the listener.
     *
     * @return integer  The number of messages in the stack.
     */
    function count($my_listener = null)
    {
        if (is_null($my_listener)) {
            $count = 0;
            foreach ($this->_listeners as $listener) {
                if (isset($_SESSION[$this->_stack][$listener->getName()])) {
                    $count += count($_SESSION[$this->_stack][$listener->getName()]);
                }
            }
            return $count;
        } else {
            return @count($_SESSION[$this->_stack][$this->_listeners[$my_listener]->getName()]);
        }
    }

}
