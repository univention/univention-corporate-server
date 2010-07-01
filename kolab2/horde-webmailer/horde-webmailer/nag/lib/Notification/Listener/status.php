<?php

require_once 'Horde/Notification/Listener/status.php';

/**
 * The Notification_Listener_status_nag:: class extends the
 * Notification_Listener_status:: class to display the messages for
 * Nag's special message type 'nag.alarm'.
 *
 * $Horde: nag/lib/Notification/Listener/status.php,v 1.6.10.6 2007-12-20 14:23:08 jan Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Nag 2.0
 * @package Horde_Notification
 */
class Notification_Listener_status_nag extends Notification_Listener_status {

    /**
     * Constructor
     */
    function Notification_Listener_status_nag()
    {
        parent::Notification_Listener_status();
        $this->_handles['nag.alarm'] = true;
    }

    /**
     * Outputs one message if it's a Nag message or calls the
     * parent method otherwise.
     *
     * @param array $message    One message hash from the stack.
     */
    function getMessage($message)
    {
        $event = $this->getEvent($message);
        switch ($message['type']) {
        case 'nag.alarm':
            return '<p class="notice">' . Horde::img('alarm.png') . '&nbsp;&nbsp;' . $event->getMessage() . '</p>';
        }

        return parent::getMessage($message);
    }

}
