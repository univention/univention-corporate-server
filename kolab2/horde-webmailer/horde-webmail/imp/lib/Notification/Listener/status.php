<?php

require_once 'Horde/Notification/Listener/status.php';

/**
 * The Notification_Listener_status_imp:: class extends the
 * Notification_Listener_status:: class to display the messages for
 * IMP's special message types 'imp.forward' and 'imp.reply'.
 *
 * $Horde: imp/lib/Notification/Listener/status.php,v 1.7.10.4 2007-12-20 13:59:28 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Notification
 */
class Notification_Listener_status_imp extends Notification_Listener_status {

    /**
     * Constructor
     */
    function Notification_Listener_status_imp()
    {
        parent::Notification_Listener_status();
        $this->_handles['imp.reply'] = true;
        $this->_handles['imp.forward'] = true;
        $this->_handles['imp.redirect'] = true;
    }

    /**
     * Outputs one message if it's an IMP message or calls the parent
     * method otherwise.
     *
     * @param array $message  One message hash from the stack.
     */
    function getMessage($message)
    {
        $event = $this->getEvent($message);
        switch ($message['type']) {
        case 'imp.reply':
            return '<p class="notice">' . Horde::img('mail_answered.png') . '&nbsp;&nbsp;' . $event->getMessage() . '</p>';

        case 'imp.forward':
        case 'imp.redirect':
            return '<p class="notice">' . Horde::img('mail_forwarded.png') . '&nbsp;&nbsp;' . $event->getMessage() . '</p>';
        }

        return parent::getMessage($message);
    }

}
