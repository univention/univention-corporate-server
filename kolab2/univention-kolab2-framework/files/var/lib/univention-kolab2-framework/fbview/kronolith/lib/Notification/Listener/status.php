<?php

require_once 'Horde/Notification/Listener/status.php';

/**
 * The Notification_Listener_status_kronolith:: class extends the
 * Notification_Listener_status:: class to display the messages for
 * Kronolith's special message types 'kronolith.alarm' and
 * 'kronolith.event'.
 *
 * $Horde: kronolith/lib/Notification/Listener/status.php,v 1.9 2004/05/20 15:53:21 jan Exp $
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Kronolith 2.0
 * @package Horde_Notification
 */
class Notification_Listener_status_kronolith extends Notification_Listener_status {

    /**
     * Constructor
     *
     * @access public
     */
    function Notification_Listener_status_kronolith()
    {
        parent::Notification_Listener_status();
        $this->_handles['kronolith.alarm'] = true;
        $this->_handles['kronolith.event'] = true;
    }

    /**
     * Outputs one message if it's a Kronolith message or calls the
     * parent method otherwise.
     *
     * @param array $message    One message hash from the stack.
     */
    function getMessage($message)
    {
        $event = $this->getEvent($message);
        switch ($message['type']) {
        case 'kronolith.alarm':
            echo '<tr><td class="notice">' . Horde::img('alarm.gif') . '&nbsp;&nbsp;<b>' . $event->getMessage() . '</b></td></tr>';
            break;

        case 'kronolith.event':
            echo '<tr><td class="notice">' . Horde::img('event.gif') . '&nbsp;&nbsp;<b>' . $event->getMessage() . '</b></td></tr>';
            break;

        default:
            parent::getMessage($message);
            break;
        }
    }

}
