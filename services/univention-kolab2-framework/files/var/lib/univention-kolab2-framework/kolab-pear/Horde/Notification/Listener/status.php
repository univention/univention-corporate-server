<?php

require_once 'Horde/Notification/Listener.php';

/**
 * The Notification_Listener_status:: class provides functionality for
 * displaying messages from the message stack as a status line.
 *
 * $Horde: framework/Notification/Notification/Listener/status.php,v 1.22 2004/04/07 14:43:11 chuck Exp $
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
class Notification_Listener_status extends Notification_Listener {

    /**
     * Constructor
     *
     * @access public
     */
    function Notification_Listener_status()
    {
        $this->_handles = array('horde.error'   => array('alerts/error.gif', _("Error")),
                                'horde.success' => array('alerts/success.gif', _("Success")),
                                'horde.warning' => array('alerts/warning.gif', _("Warning")),
                                'horde.message' => array('alerts/message.gif', _("Message")));
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
        return 'status';
    }

    /**
     * Outputs the status line if there are any messages on the 'status'
     * message stack.
     *
     * @access public
     *
     * @param array &$messageStack     The stack of messages.
     * @param optional array $options  An array of options.
     *                                 Options: 'nospace'
     */
    function notify(&$messageStack, $options = array())
    {
        if (count($messageStack)) {
            echo '<table width="100%" border="0" cellpadding="0" cellspacing="0"><tr><td class="item"><table border="0" cellspacing="1" cellpadding="2" width="100%">';
            while ($message = array_shift($messageStack)) {
                $this->getMessage($message);
            }
            echo "</table></td></tr></table>\n";
            if (empty($options['nospace'])) {
                echo "<br />\n";
            }
        }
    }

    /**
     * Outputs one message.
     *
     * @access public
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

        echo '<tr><td class="notice">' . Horde::img($this->_handles[$message['type']][0], $this->_handles[$message['type']][1], '', $registry->getParam('graphics', 'horde')) . '&nbsp;&nbsp;<b>' . $text . '</b></td></tr>';
    }

}
