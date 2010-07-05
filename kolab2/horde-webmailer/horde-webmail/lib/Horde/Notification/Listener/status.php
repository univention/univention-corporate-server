<?php

require_once 'Horde/Notification/Listener.php';

/**
 * The Notification_Listener_status:: class provides functionality for
 * displaying messages from the message stack as a status line.
 *
 * $Horde: framework/Notification/Notification/Listener/status.php,v 1.29.2.9 2009-01-06 15:23:29 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 2.1
 * @package Horde_Notification
 */
class Notification_Listener_status extends Notification_Listener {

    /**
     * Constructor
     */
    function Notification_Listener_status()
    {
        $this->_handles = array('horde.error'   => array('alerts/error.png', _("Error")),
                                'horde.success' => array('alerts/success.png', _("Success")),
                                'horde.warning' => array('alerts/warning.png', _("Warning")),
                                'horde.message' => array('alerts/message.png', _("Message")),
                                'horde.alarm' => array('alerts/alarm.png', _("Alarm")));
    }

    /**
     * Return a unique identifier for this listener.
     *
     * @return string  Unique id.
     */
    function getName()
    {
        return 'status';
    }

    /**
     * Outputs the status line if there are any messages on the 'status'
     * message stack.
     *
     * @param array &$messageStack  The stack of messages.
     * @param array $options        An array of options.
     */
    function notify(&$messageStack, $options = array())
    {
        if (count($messageStack)) {
            echo '<ul class="notices">';
            while ($message = array_shift($messageStack)) {
                $message = $this->getMessage($message);
                $message = preg_replace('/^<p class="notice">(.*)<\/p>$/', '<li>$1</li>', $message);
                echo $message;
            }
            echo '</ul>';
        }
    }

    /**
     * Outputs one message.
     *
     * @param array $message  One message hash from the stack.
     */
    function getMessage($message)
    {
        global $registry;

        $event = $this->getEvent($message);
        $text = $event->getMessage();

        if (!in_array('content.raw', $this->getFlags($message))) {
            $text = htmlspecialchars($text);
        }

        return '<li>' . Horde::img($this->_handles[$message['type']][0], $this->_handles[$message['type']][1], '', $registry->getImageDir('horde')) . $text . '</li>';
    }

}
